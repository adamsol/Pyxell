{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}
{-# LANGUAGE FlexibleInstances #-}

module Utils where

import Control.Monad
import Control.Monad.Identity
import Control.Monad.Trans.Class
import Control.Monad.Trans.State
import Control.Monad.Trans.Writer
import Control.Monad.IO.Class
import Data.List
import Text.Regex

import AbsPyxell hiding (Type)
import qualified AbsPyxell as Abs (Type)


-- | Representation of a position in the program's source code.
type Pos = Maybe (Int, Int)

-- | Alias for Type without passing Pos.
type Type = Abs.Type Pos

-- | Show instance for displaying types.
instance {-# OVERLAPS #-} Show Type where
    show typ = case reduceType typ of
        TVoid _ -> "Void"
        TInt _ -> "Int"
        TFloat _ -> "Float"
        TBool _ -> "Bool"
        TChar _ -> "Char"
        TObject _ -> "Object"
        TString _ -> "String"
        TArray _ t' -> "[" ++ show t' ++ "]"
        TTuple _ ts -> intercalate "*" (map show ts)
        TFunc _ as r -> intercalate "," (map show as) ++ "->" ++ show r


-- | Some useful versions of standard functions.
find' a f = find f a
foldM' b a f = foldM f b a

-- | Returns a common supertype of given types.
unifyTypes :: Type -> Type -> Maybe Type
unifyTypes t1 t2 = do
    case (reduceType t1, reduceType t2) of
        (TVoid _, TVoid _) -> Just tVoid
        (TInt _, TInt _) -> Just tInt
        (TFloat _, TFloat _) -> Just tFloat
        (TBool _, TBool _) -> Just tBool
        (TChar _, TChar _) -> Just tChar
        --(TObject _, _) -> tObject
        --(_, TObject _) -> tObject
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
reduceType :: Type -> Type
reduceType t = do
    case t of
        TArray _ t' -> tArray (reduceType t')
        TTuple _ ts -> if length ts == 1 then reduceType (head ts) else tTuple (map reduceType ts)
        TFunc _ as r -> tFunc (map reduceType as) (reduceType r)
        TDef _ _ as r -> tFunc (map typeArg as) (reduceType r)
        otherwise -> t

-- | Retrieves type from function argument data.
typeArg :: ArgF Pos -> Type
typeArg arg = case arg of
    ANoDefault _ t _ -> reduceType t
    ADefault _ t _ _ -> reduceType t

-- | Helper functions for initializing types without a position.
tPtr = TPtr Nothing
tArr = TArr Nothing
tDeref = TDeref Nothing
tVoid = TVoid Nothing
tInt = TInt Nothing
tFloat = TFloat Nothing
tBool = TBool Nothing
tChar = TChar Nothing
tObject = TObject Nothing
tString = TString Nothing
tArray = TArray Nothing
tTuple = TTuple Nothing
tFunc = TFunc Nothing
tDef = TDef Nothing

-- | Shorter name for none position.
_pos = Nothing

-- | Debug logging function.
debug x = liftIO $ print x

-- | Changes apostrophes to hyphens.
escapeName (Ident name) = [if c == '\'' then '-' else c | c <- name]

-- | Returns a special identifier for function's definition in the environment.
definitionIdent (Ident name) = Ident ("$" ++ name)

-- | Returns a special identifier for function's argument in the environment.
argumentIdent (Ident f) (Ident a) = Ident (f ++ "." ++ a)

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
getArgument :: [ArgF Pos] -> Ident -> Maybe (Int, Type)
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
            EIndex pos e1 e2 -> convertBinary (EIndex pos) e1 e2
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
        convertArg arg = case arg of
            APos pos e -> do
                e' <- convertExpr e
                return $ APos pos e'
            ANamed pos id e -> do
                e' <- convertExpr e
                return $ ANamed pos id e'
        convertCmp cmp = case cmp of
            Cmp1 pos e1 op e2 -> do
                e1' <- convertExpr e1
                e2' <- convertExpr e2
                return $ Cmp1 pos e1' op e2'
            Cmp2 pos e op c -> do
                e' <- convertExpr e
                c' <- convertCmp c
                return $ Cmp2 pos e' op c'
