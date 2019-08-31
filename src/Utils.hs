
module Utils where

import Control.Monad
import Control.Monad.Identity
import Control.Monad.Trans.Class
import Control.Monad.Trans.State
import Control.Monad.Trans.Writer
import Control.Monad.Reader
import Data.Char
import Data.Maybe
import Data.List
import qualified Data.Map as M
import qualified Data.Set as S
import Numeric
import Text.Regex

import AbsPyxell hiding (Type)
import qualified AbsPyxell as Abs (Type)


-- | Representation of a position in the program's source code.
type Pos = Maybe (Int, Int)

-- | Alias for Type without passing Pos.
type Type = Abs.Type Pos

-- | Instances for displaying and comparing types and classes.
instance {-# OVERLAPS #-} Show Type where
    show typ = case typ of
        TUnknown _ -> "<unknown>"
        TVar _ (Ident x) -> x
        TVoid _ -> "Void"
        TInt _ -> "Int"
        TFloat _ -> "Float"
        TBool _ -> "Bool"
        TChar _ -> "Char"
        TString _ -> "String"
        TArray _ t' -> "[" ++ show t' ++ "]"
        TNullable _ t' -> show t' ++ "?"
        TTuple _ ts -> intercalate "*" (map show ts)
        TFunc _ as r -> intercalate "," (map show as) ++ "->" ++ show r
        TFuncDef _ _ _ as r _ -> show (tFunc (map typeArg as) r)
        TFuncExt _ _ as r -> show (tFunc (map typeArg as) r)
        TClass _ (Ident c) _ _ -> c
        TModule _ -> "<module>"
        TAny _ -> "Any"
        TNum _ -> "Num"

instance {-# OVERLAPS #-} Eq Type where
    typ1 == typ2 = case (reduceType typ1, reduceType typ2) of
        (TUnknown _, TUnknown _) -> True
        (TVar _ id1, TVar _ id2) -> id1 == id2
        (TVoid _, TVoid _) -> True
        (TInt _, TInt _) -> True
        (TFloat _, TFloat _) -> True
        (TBool _, TBool _) -> True
        (TChar _, TChar _) -> True
        (TString _, TString _) -> True
        (TArray _ t1', TArray _ t2') -> t1' == t2'
        (TNullable _ t1', TNullable _ t2') -> t1' == t2'
        (TTuple _ ts1, TTuple _ ts2) -> ts1 == ts2
        (TFunc _ as1 r1, TFunc _ as2 r2) -> as1 == as2 && r1 == r2
        (TClass _ id1 _ _, TClass _ id2 _ _) -> id1 == id2
        otherwise -> False

-- | Some useful versions of standard functions.
find' a f = find f a
foldM' b a f = foldM f b a
third (_, _, x) = x

-- | Returns a common supertype of given types, assuming that the first one is being assigned to the second one.
-- | If cast is not allowed, returns Nothing.
castType :: Type -> Type -> Maybe Type
castType typ1 typ2 = do
    let t1 = reduceType typ1
    let t2 = reduceType typ2
    case (t1, t2) of
        (TUnknown _, _) -> Just t2
        (TVar _ id1, TVar _ id2) -> if id1 == id2 then Just t1 else Nothing
        (TVoid _, TVoid _) -> Just tVoid
        (TInt _, TInt _) -> Just tInt
        (TFloat _, TFloat _) -> Just tFloat
        (TBool _, TBool _) -> Just tBool
        (TChar _, TChar _) -> Just tChar
        (TString _, TString _) -> Just tString
        (TArray _ t1', TArray _ t2') ->
            if t1' == t2' then Just t1
            else if unifyTypes t1' (tArray tUnknown) == Just (tArray tUnknown) then Just (tArray tUnknown)
            else Nothing  -- arrays are not covariant
        (TNullable _ t1', TNullable _ t2') -> fmap tNullable (unifyTypes t1' t2')
        (_, TNullable _ t2') -> fmap tNullable (unifyTypes t1 t2')
        (TTuple _ ts1, TTuple _ ts2) ->
            if length ts1 == length ts2 then fmap tTuple (sequence (map (uncurry unifyTypes) (zip ts1 ts2)))
            else Nothing
        (TFunc _ as1 r1, TFunc _ as2 r2) ->
            if length as1 == length as2 then case (sequence (map (uncurry unifyTypes) (zip as1 as2)), (unifyTypes r1 r2)) of
                (Just as, Just r) -> Just (tFunc as r)
                otherwise -> Nothing
            else Nothing
        (TClass {}, TClass {}) -> if isSubclass t1 t2 then Just t2 else Nothing
        otherwise -> Nothing
    where
        isSubclass t1@(TClass _ id1 bs1 _) t2@(TClass _ id2 _ _) =
            if id1 == id2 then True
            else case bs1 of
                [b] -> isSubclass b t2
                [] -> False

-- | Returns a common supertype of given types, or Nothing.
unifyTypes :: Type -> Type -> Maybe Type
unifyTypes typ1 typ2 = do
    let t1 = reduceType typ1
    let t2 = reduceType typ2
    case (t1, t2) of
        (TClass {}, TClass {}) -> findCommonSuperclass t1 t2 t1 t2
        otherwise -> case castType typ1 typ2 of
            Just t -> Just t
            Nothing -> castType typ2 typ1
    where
        findCommonSuperclass t1 t2 t1'@(TClass _ id1 bs1 _) t2'@(TClass _ id2 bs2 _) =
            if id1 == id2 then Just t1'
            else case (bs1, bs2) of
                ([b1], [b2]) -> findCommonSuperclass t1 t2 b1 b2
                ([b1], []) -> findCommonSuperclass t1 t2 b1 t1
                ([], [b2]) -> findCommonSuperclass t1 t2 t2 b2
                ([], []) -> Nothing

-- | Returns whether a given type contains an unknown.
isUnknown :: Type -> Bool
isUnknown t = case reduceType t of
    TUnknown _ -> True
    TArray _ t' -> isUnknown t'
    TNullable _ t' -> isUnknown t'
    TTuple _ ts -> any isUnknown ts
    TFunc _ as r -> any isUnknown as || isUnknown r
    otherwise -> False

-- | Tries to reduce compound type to a simpler version (e.g. one-element tuple to the base type).
-- | Also removes position data from the type.
reduceType :: Type -> Type
reduceType t = case t of
    TUnknown _ -> tUnknown
    TVar _ id -> tVar id
    TVoid _ -> tVoid
    TInt _ -> tInt
    TFloat _ -> tFloat
    TBool _ -> tBool
    TChar _ -> tChar
    TString _ -> tString
    TArray _ t' -> tArray (reduceType t')
    TNullable _ t' -> tNullable (reduceType t')
    TTuple _ ts -> if length ts == 1 then reduceType (head ts) else tTuple (map reduceType ts)
    TFunc _ as r -> tFunc (map reduceType as) (reduceType r)
    TFuncDef _ _ _ as r _ -> tFunc (map typeArg as) (reduceType r)
    TFuncAbstract _ _ _ as r -> tFunc (map typeArg as) (reduceType r)
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
    TNullable _ t' -> retrieveType t' >>= return.tNullable
    TTuple _ ts -> if length ts == 1 then retrieveType (head ts) else mapM retrieveType ts >>= return.tTuple
    TFunc _ as r -> do
        as <- mapM retrieveType as
        r <- retrieveType r
        return $ tFunc as r
    TFuncDef _ _ _ as r _ -> retrieveType (tFunc (map typeArg as) r)
    TFuncAbstract _ _ _ as r -> retrieveType (tFunc (map typeArg as) r)
    TFuncExt _ _ as r -> retrieveType (tFunc (map typeArg as) r)
    otherwise -> return $ t

-- | Shorter name for none position.
_pos = Nothing

-- | Helper functions for initializing Type without a position.
tPtr = TPtr _pos
tArr = TArr _pos
tDeref = TDeref _pos
tUnknown = TUnknown _pos
tVar = TVar _pos
tVoid = TVoid _pos
tInt = TInt _pos
tFloat = TFloat _pos
tBool = TBool _pos
tChar = TChar _pos
tString = TString _pos
tArray = TArray _pos
tNullable = TNullable _pos
tTuple = TTuple _pos
tFunc = TFunc _pos
tFuncDef = TFuncDef _pos
tFuncAbstract = TFuncAbstract _pos
tFuncExt = TFuncExt _pos
tClass = TClass _pos
tModule = TModule _pos
tAny = TAny _pos
tNum = TNum _pos

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

-- | Returns type from function type variable data.
typeFVar :: FVar Pos -> Type
typeFVar (FVar _ _ id) = tVar id

-- | Returns type from function return header.
typeFRet :: FRet Pos -> Type
typeFRet ret = case ret of
    FFunc _ t -> reduceType t
    FProc _ -> tVoid

-- | Returns type from function argument data.
typeArg :: FArg Pos -> Type
typeArg arg = case arg of
    ANoDefault _ t _ -> reduceType t
    ADefault _ t _ _ -> reduceType t

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
            ~[e1, e2] <- mapM convertExpr [e1, e2]
            return $ op e1 e2
        convertTernary op e1 e2 e3 = do
            ~[e1, e2, e3] <- mapM convertExpr [e1, e2, e3]
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

-- | Processes a list of members of a class to add necessary information and provide consistency.
prepareMembers :: Ident -> [CMemb Pos] -> [CMemb Pos]
prepareMembers (Ident c) membs = flip map membs $ \memb ->
    let self = ANoDefault _pos (tVar (Ident c)) (Ident "self") in
    case memb of
        MMethodCode pos (Ident f) as ret body -> case body of
            MDef _ b -> MMethod pos (Ident f) (tFuncDef (Ident (c ++ "_" ++ f)) [] (self : as) (typeFRet ret) b)
            MAbstract _ -> MMethod pos (Ident f) (tFuncAbstract (Ident (c ++ "_" ++ f)) [] (self : as) (typeFRet ret))
        MConstructor pos as b ->
            MMethod pos (Ident ("_constructor")) (tFuncDef (Ident (c ++ "__constructor")) [] (self : as) tVoid b)
        otherwise -> memb

-- | Merges two lists of members, assuming that the second class is a subclass of the first one.
extendMembers :: [CMemb Pos] -> [CMemb Pos] -> [CMemb Pos]
extendMembers membs1 membs2 = do
    let ids1 = S.fromList (map idMember membs1)
    let ids2 = S.fromList (map idMember membs2)
    let membs1' = flip map membs1 $ \memb -> do
        let id = idMember memb
        if S.member id ids2 then third $ fromJust $ findMember membs2 id else memb
    let membs2' = flip filter membs2 $ \memb -> not $ S.member (idMember memb) ids1
    membs1' ++ membs2'

-- | Retrieves identifier of a class member.
idMember :: CMemb Pos -> Ident
idMember memb = case memb of
    MField _ _ id -> id
    MFieldDefault _ _ id _ -> id
    MMethod _ id _ -> id

-- | Retrieves type of a class member.
typeMember :: CMemb Pos -> Type
typeMember memb = case memb of
    MField _ t _ -> reduceType t
    MFieldDefault _ t _ _ -> reduceType t
    MMethod _ _ t -> t

-- | Retrieves position data of a class member.
posMember :: CMemb Pos -> Pos
posMember memb = case memb of
    MField pos _ _ -> pos
    MFieldDefault pos _ _ _ -> pos
    MMethod pos _ _ -> pos

-- | Finds class member by its name.
findMember :: [CMemb Pos] -> Ident -> Maybe (Int, Type, CMemb Pos)
findMember membs id = findMember' membs id 0
    where
        findMember' membs id i = case membs of
            [] -> Nothing
            memb:ms ->
                if id == idMember memb then Just (i, typeMember memb, memb)
                else findMember' ms id (i+1)

-- | Finds constructor of a class.
findConstructor :: [CMemb Pos] -> Maybe (Int, Type, CMemb Pos)
findConstructor membs = findMember membs (Ident "_constructor")

-- | Returns list of arguments for a constructor of a class.
getConstructorArgs :: [CMemb Pos] -> [FArg Pos]
getConstructorArgs membs = case findMember membs (Ident "_constructor") of
    Just (_, TFuncDef _ _ _ as _ _, _) -> tail as
    Nothing -> []

-- | Returns whether the class has any abstract methods.
isAbstract :: [CMemb Pos] -> Bool
isAbstract membs = case membs of
    (MMethod _ _ (TFuncAbstract {})):_ -> True
    [] -> False
    _:ms -> isAbstract ms
