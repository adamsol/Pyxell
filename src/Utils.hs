{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}
{-# LANGUAGE FlexibleInstances #-}
{-# LANGUAGE FlexibleContexts #-}

module Utils where

import Control.Monad
import Control.Monad.Identity
import Control.Monad.Trans.Class
import Control.Monad.Trans.State
import Control.Monad.Trans.Writer
import Control.Monad.Reader
import Data.Char
import Data.List
import qualified Data.Map as M
import Numeric
import Text.Regex

import AbsPyxell hiding (Type, Class)
import qualified AbsPyxell as Abs (Type, Class)


-- | Representation of a position in the program's source code.
type Pos = Maybe (Int, Int)

-- | Aliases for Type and Class without passing Pos.
type Type = Abs.Type Pos
type Class = Abs.Class Pos

-- | Instances for displaying and comparing types and classes.
instance {-# OVERLAPS #-} Show Type where
    show typ = case typ of
        TVar _ (Ident x) -> x
        TVoid _ -> "Void"
        TInt _ -> "Int"
        TFloat _ -> "Float"
        TBool _ -> "Bool"
        TChar _ -> "Char"
        TString _ -> "String"
        TArray _ t' -> "[" ++ show t' ++ "]"
        TTuple _ ts -> intercalate "*" (map show ts)
        TFunc _ as r -> intercalate "," (map show as) ++ "->" ++ show r
        TFuncDef _ _ _ as r _ -> show (tFunc (map typeArg as) r)
        TFuncExt _ _ as r -> show (tFunc (map typeArg as) r)
        TClass _ c -> show c

instance {-# OVERLAPS #-} Eq Type where
    typ1 == typ2 = case (typ1, typ2) of
        (TVar _ id1, TVar _ id2) -> id1 == id2
        otherwise -> False

instance {-# OVERLAPS #-} Show Class where
    show cls = case cls of
        CAny _ -> "Any"
        CNum _ -> "Num"

instance {-# OVERLAPS #-} Eq Class where
    cls1 == cls2 = case (cls1, cls2) of
        (CAny _, CAny _) -> True
        (CNum _, CNum _) -> True
        otherwise -> False

-- | Some useful versions of standard functions.
find' a f = find f a
foldM' b a f = foldM f b a

-- | Returns a common supertype of given types.
unifyTypes :: Type -> Type -> Maybe Type
unifyTypes t1 t2 = do
    case (reduceType t1, reduceType t2) of
        (TVar _ id1, TVar _ id2) -> if id1 == id2 then Just t1 else Nothing
        (TVoid _, TVoid _) -> Just tVoid
        (TInt _, TInt _) -> Just tInt
        (TFloat _, TFloat _) -> Just tFloat
        (TBool _, TBool _) -> Just tBool
        (TChar _, TChar _) -> Just tChar
        (TString _, TString _) -> Just tString
        (TArray _ t1', TArray _ t2') -> fmap tArray (unifyTypes t1' t2')
        (TTuple _ ts1, TTuple _ ts2) ->
            if length ts1 == length ts2 then fmap tTuple (sequence (map (uncurry unifyTypes) (zip ts1 ts2)))
            else Nothing
        (TFunc _ as1 r1, TFunc _ as2 r2) ->
            if length as1 == length as2 then case (sequence (map (uncurry unifyTypes) (zip as1 as2)), (unifyTypes r1 r2)) of
                (Just as, Just r) -> Just (tFunc as r)
                otherwise -> Nothing
            else Nothing
        otherwise -> Nothing

-- | Tries to reduce compound type to a simpler version (e.g. one-element tuple to the base type).
-- | Also removes position data from the type.
reduceType :: Type -> Type
reduceType t = case t of
    TVar _ id -> tVar id
    TVoid _ -> tVoid
    TInt _ -> tInt
    TFloat _ -> tFloat
    TBool _ -> tBool
    TChar _ -> tChar
    TString _ -> tString
    TArray _ t' -> tArray (reduceType t')
    TTuple _ ts -> if length ts == 1 then reduceType (head ts) else tTuple (map reduceType ts)
    TFunc _ as r -> tFunc (map reduceType as) (reduceType r)
    TFuncDef _ _ _ as r _ -> tFunc (map typeArg as) (reduceType r)
    TFuncExt _ _ as r -> tFunc (map typeArg as) (reduceType r)
    otherwise -> t

-- | Similar to `reduceType`, but runs in a monad and additionally retrieves type from type variables.
retrieveType :: MonadReader (M.Map Ident (Type, t)) m => Type -> m Type
retrieveType t = case t of
    TVar _ id -> do
        r <- asks (M.lookup id)
        case r of
            Just (t', _) -> return $ t'  -- TODO: recursion for nested types
            otherwise -> return $ t
    TArray _ t' -> retrieveType t' >>= return.tArray
    TTuple _ ts -> if length ts == 1 then retrieveType (head ts) else mapM retrieveType ts >>= return.tTuple
    TFunc _ as r -> do
        as <- mapM retrieveType as
        r <- retrieveType r
        return $ tFunc as r
    TFuncDef _ _ _ as r _ -> retrieveType (tFunc (map typeArg as) r)
    TFuncExt _ _ as r -> retrieveType (tFunc (map typeArg as) r)
    otherwise -> return $ t

-- | Returns type from function type variable data.
typeFVar :: FVar Pos -> Type
typeFVar (FVar _ _ id) = tVar id

-- | Returns type from function argument data.
typeArg :: FArg Pos -> Type
typeArg arg = case arg of
    ANoDefault _ t _ -> reduceType t
    ADefault _ t _ _ -> reduceType t

-- | Shorter name for none position.
_pos = Nothing

-- | Helper functions for initializing Type and Class without a position.
tPtr = TPtr _pos
tArr = TArr _pos
tDeref = TDeref _pos
tVar = TVar _pos
tVoid = TVoid _pos
tInt = TInt _pos
tFloat = TFloat _pos
tBool = TBool _pos
tChar = TChar _pos
tString = TString _pos
tArray = TArray _pos
tTuple = TTuple _pos
tFunc = TFunc _pos
tFuncDef = TFuncDef _pos
tFuncExt = TFuncExt _pos
tClass = TClass _pos
tModule = TModule _pos
cAny = CAny _pos
cNum = CNum _pos

-- | Helper functions for initializing expressions.
eVar x = EVar _pos (Ident ('$':x))
eInt = EInt _pos

-- | Debug logging function.
debug x = liftIO $ print x

-- | Changes apostrophes to hyphens.
escapeName (Ident name) = intercalate "" [if isAlphaNum c || c == '_' then [c] else '$' : showHex (ord c) "" | c <- name]

-- | Splits a string into formatting parts.
interpolateString :: String -> ([String], [String])
interpolateString str =
    let r = mkRegex "\\{[^{}]+\\}" in
    case matchRegexAll r str of
        Just (before, match, after, _) ->
            let (txts, tags) = interpolateString after in
            (before : txts, tail (init match) : tags)
        Nothing -> ([str], [""])

-- | Gets function argument by its name.
getArgument :: [FArg Pos] -> Ident -> Maybe (Int, Type)
getArgument args id = getArgument' args id 0
    where
        getArgument' args id i = case args of
            [] -> Nothing
            (ANoDefault _ t id'):as -> if id == id' then Just (i, t) else getArgument' as id (i+1)
            (ADefault _ t id' _):as -> if id == id' then Just (i, t) else getArgument' as id (i+1)

-- | Builds a lambda expression from expression with placeholders.
convertLambda :: Pos -> Expr Pos -> Expr Pos
convertLambda pos expression = do
    case runIdentity (evalStateT (runWriterT (convertExpr expression)) 0) of
        (e, []) -> e
        (e, ids) -> ELambda pos ids e
    where
        convertExpr :: Expr Pos -> WriterT [Ident] (StateT Int Identity) (Expr Pos)
        convertExpr expr = case expr of
            EStub pos -> do
                n <- lift $ get
                lift $ put (n+1)
                let id = Ident ("_" ++ show n)
                tell [id]
                return $ EVar pos id
            EArray pos es -> convertMultiary (EArray pos) es
            EArrayCpr pos e cprs -> do
                e <- convertExpr e
                cs <- mapM convertCpr cprs
                return $ EArrayCpr pos e cs
            EIndex pos e1 e2 -> convertBinary (EIndex pos) e1 e2
            ESlice pos e slices -> do
                e <- convertExpr e
                ss <- mapM convertSlice slices
                return $ ESlice pos e ss
            EAttr pos e id -> convertUnary (\e -> EAttr pos e id) e
            ECall pos e args -> do
                e <- convertExpr e
                as <- mapM convertArg args
                return $ ECall pos e as
            EPow pos e1 e2 -> convertBinary (EPow pos) e1 e2
            EMinus pos e -> convertUnary (EMinus pos) e
            EPlus pos e -> convertUnary (EPlus pos) e
            EBNot pos e -> convertUnary (EBNot pos) e
            EMul pos e1 e2 -> convertBinary (EMul pos) e1 e2
            EDiv pos e1 e2 -> convertBinary (EDiv pos) e1 e2
            EMod pos e1 e2 -> convertBinary (EMod pos) e1 e2
            EAdd pos e1 e2 -> convertBinary (EAdd pos) e1 e2
            ESub pos e1 e2 -> convertBinary (ESub pos) e1 e2
            EBShl pos e1 e2 -> convertBinary (EBShl pos) e1 e2
            EBShr pos e1 e2 -> convertBinary (EBShr pos) e1 e2
            EBAnd pos e1 e2 -> convertBinary (EBAnd pos) e1 e2
            EBOr pos e1 e2 -> convertBinary (EBOr pos) e1 e2
            EBXor pos e1 e2 -> convertBinary (EBXor pos) e1 e2
            ERangeIncl pos e1 e2 -> convertBinary (ERangeIncl pos) e1 e2
            ERangeExcl pos e1 e2 -> convertBinary (ERangeExcl pos) e1 e2
            ERangeInf pos e -> convertUnary (ERangeInf pos) e
            ECmp pos cmp -> do
                cmp <- convertCmp cmp
                return $ ECmp pos cmp
            ENot pos e -> convertUnary (ENot pos) e
            EAnd pos e1 e2 -> convertBinary (EAnd pos) e1 e2
            EOr pos e1 e2 -> convertBinary (EOr pos) e1 e2
            ECond pos e1 e2 e3 -> convertTernary (ECond pos) e1 e2 e3
            ETuple pos es -> convertMultiary (ETuple pos) es
            otherwise -> return $ expr
        convertUnary op e = do
            e <- convertExpr e
            return $ op e
        convertBinary op e1 e2 = do
            [e1, e2] <- mapM convertExpr [e1, e2]
            return $ op e1 e2
        convertTernary op e1 e2 e3 = do
            [e1, e2, e3] <- mapM convertExpr [e1, e2, e3]
            return $ op e1 e2 e3
        convertMultiary op es = do
            es <- mapM convertExpr es
            return $ op es
        convertCpr cpr = case cpr of
            CprFor pos e1 e2 -> convertBinary (CprFor pos) e1 e2
            CprForStep pos e1 e2 e3 -> convertTernary (CprForStep pos) e1 e2 e3
        convertSlice slice = case slice of
            SliceExpr pos e -> convertUnary (SliceExpr pos) e
            SliceNone _ -> return $ slice
        convertArg arg = case arg of
            APos pos e -> convertUnary (APos pos) e
            ANamed pos id e -> convertUnary (ANamed pos id) e
        convertCmp cmp = case cmp of
            Cmp1 pos e1 op e2 -> do
                e1' <- convertExpr e1
                e2' <- convertExpr e2
                return $ Cmp1 pos e1' op e2'
            Cmp2 pos e op c -> do
                e' <- convertExpr e
                c' <- convertCmp c
                return $ Cmp2 pos e' op c'
