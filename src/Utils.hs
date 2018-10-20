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
        TBool _ -> "Bool"
        TChar _ -> "Char"
        TObject _ -> "Object"
        TString _ -> "String"
        TArray _ t' -> "[" ++ show t' ++ "]"
        TTuple _ ts -> intercalate "*" (map show ts)
        TFunc _ as r -> intercalate "," (map show as) ++ "->" ++ show r
        TArgN _ t' _ -> show t'
        TArgD _ t' _ _ -> show t'


-- | Some useful versions of standard functions.
find' a f = find f a
foldM' b a f = foldM f b a

-- | Unification function. Returns a common supertype of given types.
unifyTypes :: Type -> Type -> Maybe Type
unifyTypes t1 t2 = do
    case (t1, t2) of
        (TVoid _, TVoid _) -> Just tInt
        (TInt _, TInt _) -> Just tInt
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
        (TArgN _ t1' _, _) -> unifyTypes t1' t2
        (TArgD _ t1' _ _, _) -> unifyTypes t1' t2
        (_, TArgN _ t2' _) -> unifyTypes t1 t2'
        (_, TArgD _ t2' _ _) -> unifyTypes t1 t2'
        otherwise -> Nothing

-- | Try to reduce compound type to a simpler version (e.g. one-element tuple to the base type).
reduceType :: Type -> Type
reduceType t = do
    case t of
        TArray _ t' -> tArray (reduceType t')
        TTuple _ ts -> if length ts == 1 then reduceType (head ts) else tTuple (map reduceType ts)
        TFunc _ as r -> tFunc (map reduceType as) (reduceType r)
        otherwise -> t

-- | Helper functions for initializing types without a position.
tPtr = TPtr Nothing
tArr = TArr Nothing
tDeref = TDeref Nothing
tLabel = TLabel Nothing
tVoid = TVoid Nothing
tInt = TInt Nothing
tBool = TBool Nothing
tChar = TChar Nothing
tObject = TObject Nothing
tString = TString Nothing
tArray = TArray Nothing
tTuple = TTuple Nothing
tFunc = TFunc Nothing
tArgN  = TArgN Nothing
tArgD = TArgD Nothing

-- | Shorter name for none position.
_pos = Nothing

-- | Debug logging function.
debug x = liftIO $ print x

-- | Changes apostrophes to hyphens.
escapeName (Ident name) = [if c == '\'' then '-' else c | c <- name]

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
getArgument :: [Type] -> Ident -> Maybe (Int, Type)
getArgument args id = find' (zip [0..] args) $ \(_, a) -> case a of
    TArgN _ _ id' -> id == id'
    TArgD _ _ id' _ -> id == id'
    otherwise -> False

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
            EElem pos e idx -> convertUnary (\e -> EElem pos e idx) e
            EIndex pos e1 e2 -> convertBinary (EIndex pos) e1 e2
            EAttr pos e id -> convertUnary (\e -> EAttr pos e id) e
            ECall pos e args -> do
                e <- convertExpr e
                as <- mapM convertArg args
                return $ ECall pos e as
            EPow pos e1 e2 -> convertBinary (EPow pos) e1 e2
            EMul pos e1 e2 -> convertBinary (EMul pos) e1 e2
            EDiv pos e1 e2 -> convertBinary (EDiv pos) e1 e2
            EMod pos e1 e2 -> convertBinary (EMod pos) e1 e2
            EAdd pos e1 e2 -> convertBinary (EAdd pos) e1 e2
            ESub pos e1 e2 -> convertBinary (ESub pos) e1 e2
            ENeg pos e -> convertUnary (ENeg pos) e
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

