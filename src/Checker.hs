{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}
{-# LANGUAGE FlexibleInstances #-}

module Checker where

import Control.Monad
import Control.Monad.Trans.Reader
import Control.Monad.Trans.Error
import Data.Char
import Data.List
import qualified Data.Map as M
import qualified Data.Set as S

import AbsPyxell hiding (Type)
import ParPyxell
import LayoutPyxell (resolveLayout)
import ErrM

import Utils


-- | Identifier environment: type and nesting level or namespace.
data EnvItem = Level Int | Module Env deriving Show
type Env = M.Map Ident (Type, EnvItem)

-- | Checker monad: Reader for identifier environment, Error to report compilation errors.
type Run r = ReaderT Env (ErrorT String IO) r

-- | Compilation error type.
data StaticError = NotComparable Type Type
                 | IllegalAssignment Type Type
                 | IllegalRedefinition Type
                 | NoBinaryOperator String Type Type
                 | NoUnaryOperator String Type
                 | UnexpectedStatement String
                 | NotPrintable Type
                 | UndeclaredIdentifier Ident
                 | RedeclaredIdentifier Ident
                 | RepeatedMember Ident
                 | NotType Ident
                 | NotVariable Ident
                 | VoidDeclaration
                 | NotLvalue
                 | InvalidExpression String
                 | InvalidSlice
                 | UnknownType
                 | NotTuple Type
                 | CannotUnpack Type Int
                 | NotFunction Type
                 | TooManyArguments Type
                 | TooFewArguments Type
                 | MissingDefault Ident
                 | RepeatedArgument Ident
                 | UnexpectedArgument Ident
                 | ExpectedNamedArgument
                 | ClosureRequired Ident
                 | NotIndexable Type
                 | NotIterable Type
                 | NotClass Type
                 | AbstractClass Type
                 | InvalidSuperCall
                 | InvalidAttr Type Ident
                 | InvalidModule Ident

-- | Show instance for displaying compilation errors.
instance Show StaticError where
    show err = case err of
        NotComparable typ1 typ2 -> "Cannot compare `" ++ show typ1 ++ "` with `" ++ show typ2 ++ "`."
        IllegalAssignment typ1 typ2 -> "Illegal assignment from `" ++ show typ1 ++ "` to `" ++ show typ2 ++ "`."
        IllegalRedefinition typ -> "Illegal redefinition of function `" ++ show typ ++ "`."
        NoBinaryOperator op typ1 typ2 -> "No binary operator `" ++ op ++ "` defined for `" ++ show typ1 ++ "` and `" ++ show typ2 ++ "`."
        NoUnaryOperator op typ -> "No unary operator `" ++ op ++ "` defined for `" ++ show typ ++ "`."
        UnexpectedStatement str -> "Unexpected `" ++ str ++ "` statement."
        NotPrintable typ -> "Variable of type `" ++ show typ ++ "` cannot be printed."
        UndeclaredIdentifier (Ident x) -> "Undeclared identifier `" ++ x ++ "`."
        RedeclaredIdentifier (Ident x) -> "Identifier `" ++ x ++ "` is already declared."
        RepeatedMember (Ident x) -> "Repeated member `" ++ x ++ "` in class definition."
        NotType (Ident x) -> "Identifier `" ++ x ++ "` does not represent a type."
        NotVariable (Ident x) -> "Identifier `" ++ x ++ "` does not represent a variable."
        VoidDeclaration -> "Cannot declare variable of type `Void`."
        NotLvalue -> "Expression cannot be assigned to."
        InvalidExpression expr -> "Could not parse expression `" ++ expr ++ "`."
        InvalidSlice -> "Invalid slice syntax."
        UnknownType -> "Cannot settle type of the expression."
        NotTuple typ -> "Type `" ++ show typ ++ "` is not a tuple."
        CannotUnpack typ n -> "Cannot unpack value of type `" ++ show typ ++ "` into " ++ show n ++ " values."
        NotFunction typ -> "Type `" ++ show typ ++ "` is not a function."
        TooManyArguments typ -> "Too many arguments for function `" ++ show typ ++ "`."
        TooFewArguments typ -> "Too few arguments for function `" ++ show typ ++ "`."
        MissingDefault (Ident x) -> "Missing default value for argument `" ++ x ++ "`."
        RepeatedArgument (Ident x) -> "Repeated argument `" ++ x ++ "`."
        UnexpectedArgument (Ident x) -> "Unexpected argument `" ++ x ++ "`."
        ExpectedNamedArgument -> "Expected named argument."
        ClosureRequired (Ident x) -> "Cannot access a non-global and non-local variable `" ++ x ++ "`."
        NotIndexable typ -> "Type `" ++ show typ ++ "` is not indexable."
        NotIterable typ -> "Type `" ++ show typ ++ "` is not iterable."
        NotClass typ -> "Type `" ++ show typ ++ "` is not a class."
        AbstractClass typ -> "Cannot instantiate an abstract class `" ++ show typ ++ "`."
        InvalidSuperCall -> "Cannot call `super` here."
        InvalidAttr typ (Ident a) -> "Type `" ++ show typ ++ "` has no attribute `" ++ a ++  "`."
        InvalidModule (Ident m) -> "Could not load module `" ++ m ++  "`."


-- | Does nothing.
skip :: Run ()
skip = do
    return $ ()

-- | Throws an error and exits compilation.
throw :: Pos -> StaticError -> Run a
throw pos err = case pos of
    Just (r, c) -> fail $ ":" ++ show r ++ ":" ++ show c ++ ": " ++ show err
    Nothing -> fail $ ": " ++ show err


-- | Inserts a label into the map and continues with changed environment.
localLevel :: String -> Int -> Run a -> Run a
localLevel name lvl cont = do
    local (M.insert (Ident name) (tVoid, Level lvl)) cont

-- | Inserts a variable into the map and continues with changed environment.
localType :: Ident -> Type -> Run a -> Run a
localType id typ cont = do
    local (M.insert id (typ, Level (-1))) cont

-- | Inserts a variable into the map and continues with changed environment.
localVar :: Ident -> Type -> Int -> Run a -> Run a
localVar id typ lvl cont = do
    local (M.insert id (typ, Level lvl)) cont

-- | Gets an identifier from the environment.
getIdent :: Ident -> Run (Maybe Type)
getIdent id = do
    r <- asks (M.lookup id)
    case r of
        Just (t, _) -> return $ Just t
        Nothing -> return $ Nothing

-- | Runs continuation on a higher nesting level.
nextLevel :: Run a -> Run a
nextLevel cont = do
    l <- getLevel
    localLevel "#level" (l+1) cont

-- | Returns current nesting level.
getLevel :: Run Int
getLevel = do
    Just (_, Level l) <- asks (M.lookup (Ident "#level"))
    return $ l


-- | Checks whether variable exists in the environment and returns its type.
checkVar :: Pos -> Ident -> Run Type
checkVar pos id = do
    l1 <- getLevel
    r <- asks (M.lookup id)
    case r of
        Just (t, Level l2) -> do
            if l2 > 0 && l1 > l2 then throw pos $ ClosureRequired id
            else if l2 < 0 then case t of
                TClass _ _ _ _ -> return $ t
                otherwise -> throw pos $ NotVariable id
            else return $ t
        Just (TModule _, _) -> do
            return $ tModule
        Nothing -> throw pos $ UndeclaredIdentifier id

-- | Checks whether type identifier exists in the environment and returns the actual type.
checkType :: Pos -> Type -> Run Type
checkType pos typ = case reduceType typ of
    TVar _ id -> do
        r <- asks (M.lookup id)
        case r of
            Just (t, Level (-1)) -> return $ t
            otherwise -> throw pos $ NotType id
    otherwise -> return $ typ

-- | Same as `checkType`, but skips the returned type.
checkType_ :: Pos -> Type -> Run ()
checkType_ pos typ = checkType pos typ >> skip

-- | Declares a variable and continues with changed environment.
checkDecl :: Pos -> Type -> Ident -> Run a -> Run a
checkDecl pos typ id cont = case typ of
    TVoid _ -> throw pos $ VoidDeclaration
    otherwise -> do
        l <- getLevel
        localVar id typ l cont

-- | Checks if one type can be cast to another and returns the unified type.
checkCast :: Pos -> Type -> Type -> Run Type
checkCast pos typ1 typ2 = case (typ1, typ2) of
    (TInt _, TNum _) -> return $ typ1
    (TFloat _, TNum _) -> return $ typ1
    (_, TAny _) -> return $ typ1
    otherwise -> case unifyTypes typ1 typ2 of
        Just t' -> case typ2 of
            TFuncDef _ _ _ _ _ _ -> throw pos $ IllegalRedefinition typ2
            TClass _ _ _ _ -> if typ2 == t' then return $ t' else throw pos $ IllegalAssignment typ1 typ2
            otherwise -> return $ t'
        Nothing -> do
            t1 <- retrieveType typ1
            t2 <- retrieveType typ2
            case unifyTypes t1 t2 of
                Just t' -> case t' of
                    TClass _ _ _ _ -> if t2 == t' then return $ t' else throw pos $ IllegalAssignment typ1 typ2
                    otherwise -> return $ t'
                Nothing -> throw pos $ IllegalAssignment typ1 typ2

-- | Same as `checkCast`, but skips the returned type.
checkCast_ :: Pos -> Type -> Type -> Run ()
checkCast_ pos typ1 typ2 = checkCast pos typ1 typ2 >> skip


-- | Checks the whole program and returns environment.
checkProgram :: Program Pos -> String -> Run Env
checkProgram program name = case program of
    Program pos stmts -> do
        env1 <- ask
        -- `std` module is automatically added to the namespace, unless this is the module being compiled
        env2 <- case name of
            "std" -> checkStmts stmts ask
            otherwise -> checkStmts (SUse _pos (Ident "std") (UAll _pos) : stmts) ask
        return $ M.insert (Ident name) (tModule, Module (M.difference env2 env1)) env1


-- | Checks a block with statements.
checkBlock :: Block Pos -> Run ()
checkBlock block = case block of
    SBlock pos stmts -> checkStmts stmts skip

-- | Checks a bunch of statements.
checkStmts :: [Stmt Pos] -> Run a -> Run a
checkStmts statements cont = case statements of
    [] -> cont
    s:ss -> checkStmt s (checkStmts ss cont)

-- | Checks a single statement.
checkStmt :: Stmt Pos -> Run a -> Run a
checkStmt statement cont = case statement of
    SUse pos id use -> do
        r <- asks (M.lookup id)
        case r of
            Just (TModule _, Module env) -> case use of
                UAll _ -> do
                    local (M.union env) cont
                UOnly pos ids -> do
                    case ids \\ (M.keys env) of
                        [] -> skip
                        id':_ -> throw pos $ UndeclaredIdentifier id'
                    local (M.union (M.filterWithKey (\id _ -> elem id ids) env)) cont
                UHiding _ ids -> do
                    case ids \\ (M.keys env) of
                        [] -> skip
                        id':_ -> throw pos $ UndeclaredIdentifier id'
                    local (M.union (M.filterWithKey (\id _ -> not (elem id ids)) env)) cont
                UAs _ id' -> do
                    local (M.insert id' (tModule, Module env)) cont
            otherwise -> throw pos $ InvalidModule id
    SClass pos id ext membs -> do
        r <- getIdent id
        case r of
            Nothing -> skip
            Just _ -> throw pos $ RedeclaredIdentifier id
        membs <- return $ prepareMembers id membs
        foldM' S.empty membs $ \s m -> let id' = idMember m in case S.member id' s of
            False -> return $ S.insert id' s
            True -> throw (posMember m) $ RepeatedMember id'
        (bases, membs) <- case ext of
            CNoExt _ -> return $ ([], membs)
            CExt _ t' -> do
                t' <- retrieveType t'
                TClass _ _ _ membs' <- case t' of
                    TClass _ _ _ _ -> return $ t'
                    TVar _ id' -> throw pos $ NotType id'
                    otherwise -> throw pos $ NotClass t'
                forM membs $ \m -> case findMember membs' (idMember m) of
                    Just (_, t, _) -> case reduceType t of
                        TFunc _ _ _ -> skip  -- TODO check method compatibility as well
                        otherwise -> checkCast_ (posMember m) (typeMember m) t
                    Nothing -> skip
                return $ ([t'], extendMembers membs' membs)
        let t = tClass id bases membs
        checkDecl pos t id $ localType id t $ do
            forM membs $ \memb -> case memb of
                MField pos t _ -> do
                    checkType_ pos t
                MFieldDefault pos t _ e -> do
                    checkType pos t
                    (t', _) <- checkExpr e
                    checkCast_ pos t' t
                MMethod pos (Ident f) (TFuncDef _ id' _ as r b) -> do
                    c <- case bases of
                        [TClass _ _ _ ms] -> case findMember ms (Ident f) of
                            Just (_, super@(TFuncDef _ _ _ _ _ _), _) -> return $ localVar (Ident "#super") super 0
                            otherwise -> return $ \x -> x
                        [] -> return $ \x -> x
                    c $ checkFunc pos id' [] as r (Just b) skip
                otherwise -> skip
            cont
    SFunc pos id vars args ret body -> do
        vs <- case vars of
            FGen _ vs -> return $ vs
            FStd _ -> return $ []
        let r = typeFRet ret
        b <- case body of
            FDef _ b -> return $ Just b
            FExtern _ -> return $ Nothing
        checkFunc pos id vs args r b cont
    SRetVoid pos -> do
        r <- asks (M.lookup (Ident "#return"))
        case r of
            Just (t, _) -> do
                checkCast pos tVoid t
                cont
            Nothing -> throw pos $ UnexpectedStatement "return"
    SRetExpr pos expr -> do
        (t1, _) <- checkExpr expr
        r <- asks (M.lookup (Ident "#return"))
        case r of
            Just (t2, _) -> do
                checkCast pos t1 t2
                cont
            Nothing -> throw pos $ UnexpectedStatement "return"
    SSkip pos -> do
        cont
    SPrint pos expr -> do
        (t, _) <- checkExpr expr
        t' <- retrieveType t
        b <- checkPrint t'
        case b of
            True -> cont
            False -> throw pos $ NotPrintable t
    SPrintEmpty pos -> do
        cont
    SAssg pos exprs -> case exprs of
        e:[] -> do
            checkExpr e
            cont
        e1:e2:[] -> do
            (t, _) <- checkExpr e2
            case (e1, t) of
                (ETuple _ es, TTuple _ ts) -> do
                    if length es == length ts then checkAssgs pos es ts cont
                    else throw pos $ CannotUnpack t (length es)
                (ETuple _ es, _) -> throw pos $ CannotUnpack t (length es)
                otherwise -> do
                    checkAssgs pos [e1] [t] cont
        e1:e2:es -> do
            checkStmt (SAssg pos (e2:es)) (checkStmt (SAssg pos [e1, e2]) cont)
    SAssgPow pos expr1 expr2 -> do
        checkAssgOp pos EPow expr1 expr2 cont
    SAssgMul pos expr1 expr2 -> do
        checkAssgOp pos EMul expr1 expr2 cont
    SAssgDiv pos expr1 expr2 -> do
        checkAssgOp pos EDiv expr1 expr2 cont
    SAssgMod pos expr1 expr2 -> do
        checkAssgOp pos EMod expr1 expr2 cont
    SAssgAdd pos expr1 expr2 -> do
        checkAssgOp pos EAdd expr1 expr2 cont
    SAssgSub pos expr1 expr2 -> do
        checkAssgOp pos ESub expr1 expr2 cont
    SAssgBShl pos expr1 expr2 -> do
        checkAssgOp pos EBShl expr1 expr2 cont
    SAssgBShr pos expr1 expr2 -> do
        checkAssgOp pos EBShr expr1 expr2 cont
    SAssgBAnd pos expr1 expr2 -> do
        checkAssgOp pos EBAnd expr1 expr2 cont
    SAssgBOr pos expr1 expr2 -> do
        checkAssgOp pos EBOr expr1 expr2 cont
    SAssgBXor pos expr1 expr2 -> do
        checkAssgOp pos EBXor expr1 expr2 cont
    SIf pos brs el -> do
        checkBranches brs
        case el of
            EElse pos b -> do
                checkBlock b
                cont
            EEmpty pos -> cont
    SWhile pos expr block -> do
        localLevel "#loop" 0 $ checkCond pos expr block
        cont
    SUntil pos expr block -> do
        localLevel "#loop" 0 $ checkCond pos expr block
        cont
    SFor pos expr1 expr2 block -> do
        checkStmt (SForStep pos expr1 expr2 (eInt 1) block) cont
    SForStep pos expr1 expr2 expr3 block -> do
        checkFor pos expr1 expr2 expr3 (checkBlock block >> cont)
    SBreak pos -> do
        r <- asks (M.lookup (Ident "#loop"))
        case r of
            Just _ -> cont
            otherwise -> throw pos $ UnexpectedStatement "break"
    SContinue pos -> do
        r <- asks (M.lookup (Ident "#loop"))
        case r of
            Just _ -> cont
            otherwise -> throw pos $ UnexpectedStatement "continue"
    where
        checkPrint typ = case typ of
            TVoid _ -> return $ False
            TTuple _ ts -> do
                bs <- mapM checkPrint ts
                return $ all id bs
            TArray _ t' -> checkPrint t'
            TFunc _ _ _ -> return $ False
            TClass _ _ _ membs -> case findMember membs (Ident "toString") of
                Just (_, TFuncDef _ _ _ _ (TString _) _, _) -> return $ True
                otherwise -> return $ False
            TAny _ -> return $ False
            otherwise -> return $ True
        checkAssgOp pos op expr1 expr2 cont = do
            checkStmt (SAssg pos [expr1, op pos expr1 expr2]) cont
        checkBranches brs = case brs of
            [] -> skip
            b:bs -> case b of
                BElIf pos expr block -> do
                    checkCond pos expr block
                    checkBranches bs
        checkCond pos expr block = do
            checkIf pos expr
            checkBlock block

-- | Checks a list of variable assignments and continues with changed environment.
checkAssgs :: Pos -> [Expr Pos] -> [Type] -> Run a -> Run a
checkAssgs pos exprs types cont = case (exprs, types) of
    ([], []) -> cont
    (e:es, t:ts) -> checkAssg pos e t (checkAssgs pos es ts cont)
    where
        checkAssg pos expr typ cont = case expr of
            EVar _ id -> do
                r <- getIdent id
                case r of
                    Just t -> do
                        checkCast pos typ t
                        cont
                    Nothing -> do
                        checkDecl pos (reduceType typ) id cont
            EIndex _ _ _ -> do
                (t, m) <- checkExpr expr
                if m then do
                    checkCast pos typ t
                    cont
                else throw pos $ NotLvalue
            EAttr _ _ _ -> do
                (t, m) <- checkExpr expr
                if m then do
                    checkCast pos typ t
                    cont
                else throw pos $ NotLvalue
            otherwise -> throw pos $ NotLvalue

-- | Checks a single `if` statement.
checkIf :: Pos -> Expr Pos -> Run Type
checkIf pos expr = do
    (t, _) <- checkExpr expr
    case t of
        TBool _ -> return $ ()
        otherwise -> throw pos $ IllegalAssignment t tBool
    return $ t

-- | Checks a single `for` statement and continues with changed environment.
checkFor :: Pos -> Expr Pos -> Expr Pos -> Expr Pos -> Run a -> Run a
checkFor pos expr1 expr2 expr3 cont = do
    t1 <- checkForExpr pos expr2
    (t2, _) <- checkExpr expr3
    checkForStep pos t2 t1
    localLevel "#loop" 0 $ case (expr1, t1) of
        (ETuple _ es, TTuple _ ts1) -> do
            if length es == length ts1 then case t2 of
                TTuple _ ts2 -> do
                    if length ts2 == length ts1 then checkAssgs pos es ts1 cont
                    else throw pos $ CannotUnpack t2 (length es)
                otherwise -> checkAssgs pos es ts1 cont
            else throw pos $ CannotUnpack t1 (length es)
        otherwise -> checkAssgs pos [expr1] [t1] cont
    where
        checkForExpr pos expr = case expr of
            ERangeIncl _ e1 e2 -> checkForRange pos e1 e2
            ERangeExcl _ e1 e2 -> checkForRange pos e1 e2
            ERangeInf _ e1 -> checkForRange pos e1 e1
            ETuple _ es -> do
                ts <- forM es $ checkForExpr pos
                return $ tTuple ts
            otherwise -> checkForIterable pos expr
        checkForRange pos from to = do
            (t1, _) <- checkExpr from
            (t2, _) <- checkExpr to
            case (t1, t2) of
                (TInt _, TInt _) -> return $ t1
                (TInt _, _) -> throw pos $ IllegalAssignment t2 tInt
                (TFloat _, TFloat _) -> return $ t1
                (TFloat _, _) -> throw pos $ IllegalAssignment t2 tFloat
                (TChar _, TChar _) -> return $ t1
                (TChar _, _) -> throw pos $ IllegalAssignment t2 tChar
                otherwise -> throw pos $ UnknownType
        checkForIterable pos iter = do
            (t, _) <- checkExpr iter
            case t of
                TString _ -> return $ tChar
                TArray _ t' -> return $ t'
                otherwise -> throw pos $ NotIterable t
        checkForStep pos step typ = case typ of
            TTuple _ ts2 -> case step of
                TTuple _ ts1 -> do
                    if length ts1 == length ts2 then do
                        ts <- forM (zip ts1 ts2) $ uncurry (checkForStep pos)
                        return $ tTuple ts
                    else throw pos $ CannotUnpack step (length ts2)
                otherwise -> do
                    ts <- forM ts2 $ checkForStep pos step
                    return $ tTuple ts
            TFloat _ -> checkCast pos step tNum
            otherwise -> checkCast pos step tInt

-- | Checks function's arguments and body.
checkFunc :: Pos -> Ident -> [FVar Pos] -> [FArg Pos] -> Type -> Maybe (Block Pos) -> Run a -> Run a
checkFunc pos id vars args ret block cont = do
    r <- getIdent id
    case r of
        Nothing -> skip
        Just _ -> throw pos $ RedeclaredIdentifier id
    t <- case block of
        Just b -> return $ tFuncDef id vars args ret b
        Nothing -> return $ tFuncExt id args ret
    checkDecl pos t id $ do  -- so global functions are global
        case block of
            Just b -> nextLevel $ checkDecl pos t id $ do  -- so recursion works inside the function
                checkTypeVars vars $ checkArgs args False $ do
                    checkType pos ret
                    localType (Ident "#return") (reduceType ret) $ local (M.delete (Ident "#loop")) $ checkBlock b
            Nothing -> skip
        cont
    where
        checkArgs args dflt cont = case args of
            [] -> cont
            a:as -> checkArg a dflt (\d -> checkArgs as (dflt || d) cont)
        checkArg arg dflt cont = case arg of
            ANoDefault pos typ id -> case dflt of
                False -> do
                    let t = reduceType typ
                    checkType pos t
                    checkDecl pos t id $ cont False
                True -> throw pos $ MissingDefault id
            ADefault pos typ id expr -> do
                (t1, _) <- checkExpr expr
                let t2 = reduceType typ
                checkCast pos t1 t2
                checkDecl pos t2 id $ cont True

-- | Adds function's type variables to the environment.
checkTypeVars :: [FVar Pos] -> Run a -> Run a
checkTypeVars vars cont = case vars of
     [] -> cont
     (FVar pos t id):vs -> do
        t <- case t of
            TAny _ -> return $ t
            TNum _ -> return $ t
            otherwise -> throw pos $ NotClass t
        localType id t $ checkTypeVars vs cont  -- TODO: type scopes


-- | Checks an expression and returns its type and whether it is mutable.
checkExpr :: Expr Pos -> Run (Type, Bool)
checkExpr expression = case expression of
    EStub pos -> throw pos $ UnknownType
    EInt pos _ -> return $ (tInt, False)
    EFloat pos _ -> return $ (tFloat, False)
    ETrue pos -> return $ (tBool, False)
    EFalse pos -> return $ (tBool, False)
    EChar pos _ -> return $ (tChar, False)
    EString pos str -> do
        let (_, tags) = interpolateString (read str)
        forM tags $ \tag -> do
            if tag == "" then skip
            else case pExpr $ resolveLayout False $ myLexer tag of
                Bad err -> throw pos $ InvalidExpression tag
                Ok expr -> checkExpr (ECall _pos (EAttr _pos expr (Ident "toString")) []) >> skip
        return $ (tString, False)
    EArray pos exprs -> do
        rs <- mapM checkExpr exprs
        let (ts, _) = unzip rs
        case ts of
            [] -> throw pos $ UnknownType
            t:ts -> case foldM unifyTypes t ts of
                Just t' -> return $ (tArray t', False)
                Nothing -> throw pos $ UnknownType
    EArrayCpr pos expr cprs -> do
        checkArrayCprs cprs $ do
            (t, _) <- checkExpr expr
            return $ (tArray t, False)
    EVar pos id -> do
        t <- checkVar pos id
        return $ (t, True)
    EIndex pos expr1 expr2 -> do
        (t2, _) <- checkExpr expr2
        checkCast pos t2 tInt
        (t1, _) <- checkExpr expr1
        case t1 of
            TString _ -> return $ (tChar, False)
            TArray _ t1' -> return $ (t1', True)
            otherwise -> do
                t1' <- retrieveType t1
                case t1' of
                    TString _ -> return $ (tChar, False)
                    otherwise -> throw pos $ NotIndexable t1
    ESlice pos expr slices -> do
        case slices of
            _:_:_:_:_ -> throw pos $ InvalidSlice
            otherwise -> skip
        forM slices $ \slice -> case slice of
            SliceExpr pos e -> do
                (t, _) <- checkExpr e
                checkCast pos t tInt
            SliceNone _ -> return $ tVoid
        (t1, _) <- checkExpr expr
        case t1 of
            TString _ -> return $ (t1, False)
            TArray _ _ -> return $ (t1, False)
            otherwise -> do
                t1' <- retrieveType t1
                case t1' of
                    TString _ -> return $ (t1, False)
                    otherwise -> throw pos $ NotIndexable t1
    EAttr pos expr id -> do
        (t1, _) <- checkExpr expr
        t1' <- case t1 of
            TArray _ _ -> return $ t1
            TTuple _ _ -> return $ t1
            otherwise -> retrieveType t1
        let Ident attr = id
        Just t2 <- case t1' of
            TInt _ -> case attr of
                "toString" -> getIdent (Ident "Int_toString")
                "toFloat" -> getIdent (Ident "Int_toFloat")
                otherwise -> throw pos $ InvalidAttr t1' id
            TFloat _ -> case attr of
                "toString" -> getIdent (Ident "Float_toString")
                "toInt" -> getIdent (Ident "Float_toInt")
                otherwise -> throw pos $ InvalidAttr t1' id
            TBool _ -> case attr of
                "toString" -> getIdent (Ident "Bool_toString")
                "toInt" -> getIdent (Ident "Bool_toInt")
                "toFloat" -> getIdent (Ident "Bool_toFloat")
                otherwise -> throw pos $ InvalidAttr t1' id
            TChar _ -> case attr of
                "toString" -> getIdent (Ident "Char_toString")
                "toInt" -> getIdent (Ident "Char_toInt")
                "toFloat" -> getIdent (Ident "Char_toFloat")
                otherwise -> throw pos $ InvalidAttr t1' id
            TString _ -> case attr of
                "length" -> return $ Just tInt
                "toArray" -> getIdent (Ident "String_toArray")
                "toString" -> getIdent (Ident "String_toString")
                "toInt" -> getIdent (Ident "String_toInt")
                "toFloat" -> getIdent (Ident "String_toFloat")
                otherwise -> throw pos $ InvalidAttr t1' id
            TArray _ t' -> case (t', attr) of
                (_, "length") -> return $ Just tInt
                (TChar _, "join") -> do
                    t'' <- getIdent (Ident "CharArray_join")
                    return $ t''
                (TString _, "join") -> do
                    t'' <- getIdent (Ident "StringArray_join")
                    return $ t''
                otherwise -> throw pos $ InvalidAttr t1' id
            TTuple _ ts -> do
                let i = ord (attr !! 0) - ord 'a'
                if "a" <= attr && attr <= "z" && i < length ts then return $ Just (ts !! i)
                else throw pos $ InvalidAttr t1' id
            TClass _ _ _ membs -> case findMember membs id of
                Just (_, t, _) -> return $ Just t
                Nothing -> throw pos $ InvalidAttr t1' id
            TModule _ -> do
                (_, Module env) <- case expr of
                    EVar _ id' -> asks (M.! id')
                r <- local (const env) $ getIdent id
                case r of
                    Just t -> return $ Just t
                    otherwise -> throw pos $ UndeclaredIdentifier id
            otherwise -> throw pos $ InvalidAttr t1' id
        m <- case t1' of
            TClass _ _ _ _ -> return $ True
            otherwise -> return $ False
        return $ (t2, m)
    ECall pos expr args -> do
        (typ, _) <- checkExpr expr
        (vars, args1, args2, ret) <- case typ of
            TFunc _ as r -> return $ ([], as, [], r)
            TFuncDef _ _ vs as r _ -> return $ (vs, map typeArg as, as, reduceType r)
            TFuncExt _ _ as r -> return $ ([], map typeArg as, as, reduceType r)
            TClass _ id _ membs -> case isAbstract membs of
                False -> do
                    let as = getConstructorArgs membs
                    return $ ([], map typeArg as, as, typ)
                True -> throw pos $ AbstractClass typ
            otherwise -> throw pos $ NotFunction typ
        -- Build a map of arguments and their positions.
        let m = M.empty
        m <- case expr of
            EAttr pos e id -> do  -- if this is a method, the object will be passed as the first argument
                (t, _) <- checkExpr e
                case t of
                    TModule _ -> return $ m
                    otherwise -> return $ M.insert 0 (Left t) m
            otherwise -> return $ m
        (m, _) <- foldM' (m, False) (zip [(M.size m)..] args) $ \(m, named) (i, a) -> do
            (pos', e, i, named) <- case (a, named) of
                (APos pos' e, False) -> return $ (pos', e, i, False)
                (ANamed pos' id e, _) -> case getArgument args2 id of
                    Just (i', _) -> case M.lookup i' m of
                        Nothing -> return $ (pos', e, i', True)
                        Just _ -> throw pos' $ RepeatedArgument id
                    Nothing -> throw pos' $ UnexpectedArgument id
                (APos pos' _, True) -> throw pos' $ ExpectedNamedArgument
            r <- case convertLambda pos' e of
                e'@(ELambda _ _ _) -> return $ Right e'
                otherwise -> do
                    (t, _) <- checkExpr e
                    return $ Left t
            return $ (M.insert i r m, named)
        -- Extend the map using default arguments.
        m <- foldM' m (zip [0..] args2) $ \m (i, a) -> case (a, M.lookup i m) of
            (ADefault _ t _ _, Nothing) -> return $ M.insert i (Left t) m
            otherwise -> return $ m
        -- Check whether all (and no redundant) arguments have been provided.
        if any (>= length args1) (M.keys m) then throw pos $ TooManyArguments typ
        else if M.size m < length args1 then throw pos $ TooFewArguments typ
        else skip
        -- Check if all arguments have correct types.
        checkTypeVars vars $ checkArgs (M.elems m) args1 $ checkLambdas (M.elems m) args1 $ do
            r <- retrieveType ret
            r <- case r of
                TAny _ -> return $ ret
                TNum _ -> return $ ret
                otherwise -> return $ r
            return $ (r, False)
        where
            checkArgs as1 as2 cont = case (as1, as2) of
                (_, []) -> cont
                ((Left t1):as1, t2:as2) -> checkArg t1 t2 $ do
                    checkCast pos t1 t2
                    checkArgs as1 as2 cont
                (_:as1, _:as2) -> checkArgs as1 as2 cont
            checkArg t1 t2 cont = case (reduceType t1, reduceType t2) of
                (_, t2'@(TVar _ id)) -> do
                    checkType pos t2
                    t3 <- retrieveType t2
                    t4 <- case (t1, t3) of
                        (TInt _, TNum _) -> return $ t1
                        (TFloat _, TNum _) -> return $ t1
                        (_, TAny _) -> return $ t1
                        otherwise -> checkCast pos t1 t2
                    if t2' == t4 then cont  -- to prevent looping
                    else localType id t4 cont
                (TTuple _ ts1, TTuple _ ts2) -> do
                    if length ts1 == length ts2 then checkArgs (map Left ts1) ts2 cont
                    else throw pos $ IllegalAssignment t1 t2
                (TArray _ t1', TArray _ t2') -> do
                    checkArg t1' t2' cont
                (TFunc _ as1 r1, TFunc _ as2 r2) -> do
                    if length as1 == length as2 then checkArgs (map Left as1) as2 (checkArg r1 r2 cont)
                    else throw pos $ IllegalAssignment t1 t2
                otherwise -> do
                    cont
            checkLambdas as1 as2 cont = case (as1, as2) of
                (_, []) -> cont
                ((Right e):as1, t:as2) -> checkLambda e t (checkLambdas as1 as2 cont)
                (_:as1, _:as2) -> checkLambdas as1 as2 cont
            checkLambda e t cont = do
                let ELambda pos' ids e' = e
                let TFunc _ as1 r1 = t
                as2 <- mapM retrieveType as1
                r2 <- retrieveType r1
                if length ids < length as1 then throw pos' $ TooFewArguments t
                else if length ids > length as1 then throw pos' $ TooManyArguments t
                else skip
                let id = Ident ".lambda"
                let b = SBlock pos' [SRetExpr pos' e']
                checkFunc pos' id [] [ANoDefault _pos t' id' | (t', id') <- zip as2 ids] r2 (Just b) skip
                (r3, _) <- checkLambdaArgs (zip as2 ids) $ checkExpr e'
                case r1 of
                    TVar _ id' -> do
                        r4 <- retrieveType r3
                        localType id' r4 $ cont
                    otherwise -> cont
            checkLambdaArgs args cont = case args of
                [] -> cont
                (t, id):as -> checkLambdaArg t id $ checkLambdaArgs as cont
            checkLambdaArg typ id cont = do
                checkDecl _pos typ id $ cont
    ESuper pos args -> do
        r <- asks $ M.lookup (Ident "#super")
        case r of
            Just _ -> do
                checkExpr (ECall _pos (EVar _pos (Ident "#super")) ((APos _pos (EVar _pos (Ident "self"))) : args))
            Nothing -> throw pos $ InvalidSuperCall
    EPow pos expr1 expr2 -> checkBinary pos "^" expr1 expr2
    EMinus pos expr -> checkUnary pos "-" expr
    EPlus pos expr -> checkUnary pos "+" expr
    EBNot pos expr -> checkUnary pos "~" expr
    EMul pos expr1 expr2 -> checkBinary pos "*" expr1 expr2
    EDiv pos expr1 expr2 -> checkBinary pos "/" expr1 expr2
    EMod pos expr1 expr2 -> checkBinary pos "%" expr1 expr2
    EAdd pos expr1 expr2 -> checkBinary pos "+" expr1 expr2
    ESub pos expr1 expr2 -> checkBinary pos "-" expr1 expr2
    EBShl pos expr1 expr2 -> checkBinary pos "<<" expr1 expr2
    EBShr pos expr1 expr2 -> checkBinary pos ">>" expr1 expr2
    EBAnd pos expr1 expr2 -> checkBinary pos "&" expr1 expr2
    EBOr pos expr1 expr2 -> checkBinary pos "|" expr1 expr2
    EBXor pos expr1 expr2 -> checkBinary pos "$" expr1 expr2
    ERangeIncl pos _ _ -> throw pos $ UnknownType
    ERangeExcl pos _ _ -> throw pos $ UnknownType
    ECmp pos cmp -> case cmp of
        Cmp1 pos e1 op e2 -> do
            (t1, _) <- checkExpr e1
            (t2, _) <- checkExpr e2
            checkCmp pos op t1 t2
        Cmp2 pos e1 op cmp -> do
            e2 <- case cmp of
                Cmp1 _ e2 _ _ -> return $ e2
                Cmp2 _ e2 _ _ -> return $ e2
            checkExpr (ECmp _pos (Cmp1 pos e1 op e2))
            checkExpr (ECmp _pos cmp)
    ENot pos expr -> checkUnary pos "not" expr
    EAnd pos expr1 expr2 -> checkBinary pos "and" expr1 expr2
    EOr pos expr1 expr2 -> checkBinary pos "or" expr1 expr2
    ECond pos expr1 expr2 expr3 -> do
        (t1, _) <- checkExpr expr1
        case t1 of
            TBool _ -> skip
            otherwise -> throw pos $ IllegalAssignment t1 tBool
        (t2, _) <- checkExpr expr2
        (t3, _) <- checkExpr expr3
        case unifyTypes t2 t3 of
            Just t4 -> return $ (t4, False)
            Nothing -> throw pos $ UnknownType
    ETuple pos exprs -> do
        rs <- mapM checkExpr exprs
        let (ts, ms) = unzip rs
        case ts of
            t:[] -> return $ (t, all (== True) ms)
            otherwise -> return $ (tTuple ts, all (== True) ms)
    ELambda pos expr1 expr2 -> do
        throw pos $ UnknownType
    where
        checkBinary pos op expr1 expr2 = do
            (t1, _) <- checkExpr expr1
            (t2, _) <- checkExpr expr2
            t1' <- retrieveType t1
            t2' <- retrieveType t2
            case op of
                "*" -> case (t1', t2') of
                    (TString _, TInt _) -> return $ (tString, False)
                    (TInt _, TString _) -> return $ (tString, False)
                    (TArray _ _, TInt _) -> return $ (t1, False)
                    (TInt _, TArray _ _) -> return $ (t2, False)
                    (TInt _, TInt _) -> return $ (tInt, False)
                    (TFloat _, TInt _) -> return $ (tFloat, False)
                    (TInt _, TFloat _) -> return $ (tFloat, False)
                    (TFloat _, TFloat _) -> return $ (tFloat, False)
                    (TNum _, TNum _) -> if t1 == t2 then return $ (t1, False) else throw pos $ NoBinaryOperator "*" t1 t2
                    otherwise -> throw pos $ NoBinaryOperator "*" t1 t2
                "+" -> case (t1', t2') of
                    (TString _, TString _) -> return $ (tString, False)
                    (TString _, TChar _) -> return $ (tString, False)
                    (TChar _, TString _) -> return $ (tString, False)
                    (TArray _ t1', TArray _ t2') -> do
                        t' <- case unifyTypes t1' t2' of
                            Just t' -> return $ t'
                            Nothing -> throw pos $ NoBinaryOperator "+" t1 t2
                        return $ (tArray t', False)
                    (TInt _, TInt _) -> return $ (tInt, False)
                    (TFloat _, TInt _) -> return $ (tFloat, False)
                    (TInt _, TFloat _) -> return $ (tFloat, False)
                    (TFloat _, TFloat _) -> return $ (tFloat, False)
                    (TNum _, TNum _) -> if t1 == t2 then return $ (t1, False) else throw pos $ NoBinaryOperator "+" t1 t2
                    otherwise -> throw pos $ NoBinaryOperator "+" t1 t2
                otherwise -> do
                    if op == "and" || op == "or" then case (t1', t2') of
                        (TBool _, TBool _) -> return $ (tBool, False)
                        otherwise -> throw pos $ NoBinaryOperator op t1 t2
                    else if op == "^" || op == "/" || op == "-" then case (t1', t2') of
                        (TInt _, TInt _) -> return $ (tInt, False)
                        (TFloat _, TInt _) -> return $ (tFloat, False)
                        (TInt _, TFloat _) -> return $ (tFloat, False)
                        (TFloat _, TFloat _) -> return $ (tFloat, False)
                        (TNum _, TNum _) -> if t1 == t2 then return $ (t1, False) else throw pos $ NoBinaryOperator op t1 t2
                        otherwise -> throw pos $ NoBinaryOperator op t1 t2
                    else case (t1', t2') of  -- modulo and bitwise operators
                        (TInt _, TInt _) -> return $ (tInt, False)
                        otherwise -> throw pos $ NoBinaryOperator op t1 t2
        checkUnary pos op expr = do
            (t, _) <- checkExpr expr
            t' <- retrieveType t
            case op of
                "~" -> case t' of
                    TInt _ -> return $ (tInt, False)
                    otherwise -> throw pos $ NoUnaryOperator "~" t
                "not" -> case t' of
                    TBool _ -> return $ (tBool, False)
                    otherwise -> throw pos $ NoUnaryOperator "not" t
                otherwise -> case t' of  -- unary minus/plus
                    TInt _ -> return $ (tInt, False)
                    TFloat _ -> return $ (tFloat, False)
                    TNum _ -> return $ (t, False)
                    otherwise -> throw pos $ NoUnaryOperator op t
        checkCmp pos op typ1 typ2 = do
            t1 <- retrieveType typ1
            t2 <- retrieveType typ2
            case unifyTypes typ1 typ2 of
                Just t' -> case t' of
                    TArray _ t'' -> checkCmp pos op t'' t''
                    TFunc _ _ _ -> throw pos $ NotComparable typ1 typ2
                    TClass _ _ _ _ -> case op of
                        CmpEQ _ -> return $ (tBool, False)
                        CmpNE _ -> return $ (tBool, False)
                        otherwise -> throw pos $ NotComparable typ1 typ2
                    otherwise -> return $ (tBool, False)
                Nothing -> case (t1, t2) of
                    (TInt _, TFloat _) -> return $ (tBool, False)
                    (TFloat _, TInt _) -> return $ (tBool, False)
                    (TInt _, TNum _) -> return $ (tBool, False)
                    (TFloat _, TNum _) -> return $ (tBool, False)
                    (TNum _, TInt _) -> return $ (tBool, False)
                    (TNum _, TFloat _) -> return $ (tBool, False)
                    (TNum _, TNum _) -> return $ (tBool, False)
                    otherwise -> throw pos $ NotComparable typ1 typ2
        checkArrayCprs cprs cont = case cprs of
            [] -> cont
            cpr:cprs -> checkArrayCpr cpr $ checkArrayCprs cprs cont
        checkArrayCpr cpr cont = case cpr of
            CprFor pos e1 e2 -> do
                checkArrayCpr (CprForStep pos e1 e2 (eInt 1)) cont
            CprForStep pos e1 e2 e3 -> do
                checkFor pos e1 e2 e3 cont
            CprIf pos e -> do
                r <- asks (M.lookup (Ident "#loop"))
                case r of
                    Just _ -> do
                        checkIf pos e
                        cont
                    otherwise -> throw pos $ UnexpectedStatement "if"
