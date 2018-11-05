{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}
{-# LANGUAGE FlexibleInstances #-}

module Checker where

import Control.Monad
import Control.Monad.Trans.Reader
import Control.Monad.Trans.Error
import qualified Data.Map as M

import AbsPyxell hiding (Type)
import ParPyxell
import LayoutPyxell (resolveLayout)
import ErrM

import Utils


-- | Identifier environment: type and nesting level.
type Level = Int
type Env = M.Map Ident (Type, Level)

-- | Checker monad: Reader for identifier environment, Error to report compilation errors.
type Run r = ReaderT Env (ErrorT String IO) r

-- | Compilation error type.
data StaticError = NotComparable Type Type
                 | IllegalAssignment Type Type
                 | NoBinaryOperator String Type Type
                 | NoUnaryOperator String Type
                 | UnexpectedStatement String
                 | NotPrintable Type
                 | UndeclaredIdentifier Ident
                 | RedeclaredIdentifier Ident
                 | VoidDeclaration
                 | NotLvalue
                 | InvalidExpression String
                 | UnknownType
                 | NotTuple Type
                 | InvalidTupleElem Type Int
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
                 | InvalidAttr Type Ident

-- | Show instance for displaying compilation errors.
instance Show StaticError where
    show err = case err of
        NotComparable typ1 typ2 -> "Cannot compare `" ++ show typ1 ++ "` with `" ++ show typ2 ++ "`."
        IllegalAssignment typ1 typ2 -> "Illegal assignment from `" ++ show typ1 ++ "` to `" ++ show typ2 ++ "`."
        NoBinaryOperator op typ1 typ2 -> "No binary operator `" ++ op ++ "` defined for `" ++ show typ1 ++ "` and `" ++ show typ2 ++ "`."
        NoUnaryOperator op typ -> "No unary operator `" ++ op ++ "` defined for `" ++ show typ ++ "`."
        UnexpectedStatement str -> "Unexpected `" ++ str ++ "` statement."
        NotPrintable typ -> "Variable of type `" ++ show typ ++ "` cannot be printed."
        UndeclaredIdentifier (Ident x) -> "Undeclared identifier `" ++ x ++ "`."
        RedeclaredIdentifier (Ident x) -> "Identifier `" ++ x ++ "` is already declared."
        VoidDeclaration -> "Cannot declare variable of type `Void`."
        NotLvalue -> "Expression cannot be assigned to."
        InvalidExpression expr -> "Could not parse expression `" ++ expr ++ "`."
        UnknownType -> "Cannot settle type of the expression."
        NotTuple typ -> "Type `" ++ show typ ++ "` is not a tuple."
        InvalidTupleElem typ n -> "Tuple `" ++ show typ ++ "` does not contain " ++ show n ++ " elements."
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
        InvalidAttr typ (Ident a) -> "Type `" ++ show typ ++ "` has no attribute `" ++ a ++  "`."


-- | Does nothing.
skip :: Run ()
skip = do
    return $ ()

-- | Throws an error and exits compilation.
throw :: Pos -> StaticError -> Run a
throw pos err = case pos of
    Just (r, c) -> fail $ ":" ++ show r ++ ":" ++ show c ++ ": " ++ show err
    Nothing -> fail $ ": " ++ show err

-- | Returns current nesting level.
getLevel :: Run Level
getLevel = do
    Just (_, l) <- asks (M.lookup (Ident "#level"))
    return $ l

-- | Runs continuation on a higher nesting level.
nextLevel :: Run a -> Run a
nextLevel cont = do
    l <- getLevel
    local (M.insert (Ident "#level") (tLabel, l+1)) cont

-- | Gets an identifier from the environment.
getIdent :: Pos -> Ident -> Run (Maybe Type)
getIdent pos id = do
    l1 <- getLevel
    r <- asks (M.lookup id)
    case r of
        Just (t, l2) -> do
            if l2 > 0 && l1 > l2 then throw pos $ ClosureRequired id
            else return $ Just t
        Nothing -> return $ Nothing

-- | Adds an identifier to the environment.
declare :: Pos -> Type -> Ident -> Run a -> Run a
declare pos typ id cont = case typ of
    TVoid _ -> throw pos $ VoidDeclaration
    otherwise -> do
        l <- getLevel
        local (M.insert id (typ, l)) cont


-- | Checks the whole program and returns environment.
checkProgram :: Program Pos -> Run Env
checkProgram program = case program of
    Program pos stmts -> checkStmts stmts ask

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
    SProc pos id args block -> do
        checkFunc pos id args tVoid (Just block) cont
    SFunc pos id args ret block -> do
        checkFunc pos id args ret (Just block) cont
    SProcExtern pos id args -> do
        checkFunc pos id args tVoid Nothing cont
    SFuncExtern pos id args ret -> do
        checkFunc pos id args ret Nothing cont
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
        case t of
            TVoid _ -> throw pos $ NotPrintable t
            TArray _ _ -> throw pos $ NotPrintable t
            TFunc _ _ _ -> throw pos $ NotPrintable t
            otherwise -> cont
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
                    checkAssg pos e1 t cont
        e1:e2:es -> do
            checkStmt (SAssg pos (e2:es)) (checkStmt (SAssg pos [e1, e2]) cont)
    SAssgMul pos expr1 expr2 -> do
        checkStmt (SAssg pos [expr1, EMul pos expr1 expr2]) cont
    SAssgDiv pos expr1 expr2 -> do
        checkStmt (SAssg pos [expr1, EDiv pos expr1 expr2]) cont
    SAssgMod pos expr1 expr2 -> do
        checkStmt (SAssg pos [expr1, EMod pos expr1 expr2]) cont
    SAssgAdd pos expr1 expr2 -> do
        checkStmt (SAssg pos [expr1, EAdd pos expr1 expr2]) cont
    SAssgSub pos expr1 expr2 -> do
        checkStmt (SAssg pos [expr1, ESub pos expr1 expr2]) cont
    SIf pos brs el -> do
        checkBranches brs
        case el of
            EElse pos b -> do
                checkBlock b
                cont
            EEmpty pos -> cont
    SWhile pos expr block -> do
        local (M.insert (Ident "#loop") (tLabel, 0)) $ checkCond pos expr block
        cont
    SUntil pos expr block -> do
        local (M.insert (Ident "#loop") (tLabel, 0)) $ checkCond pos expr block
        cont
    SFor pos expr1 expr2 block -> do
        checkStmt (SForStep pos expr1 expr2 (EInt _pos 1) block) cont
    SForStep pos expr1 expr2 expr3 block -> do
        (t1, _) <- checkExpr expr3
        checkCast pos t1 tInt
        t2 <- checkFor pos expr2
        local (M.insert (Ident "#loop") (tLabel, 0)) $ case (expr1, t2) of
            (ETuple _ es, TTuple _ ts) -> do
                if length es == length ts then checkAssgs pos es ts (checkBlock block >> cont)
                else throw pos $ CannotUnpack t2 (length es)
            otherwise -> checkAssg pos expr1 t2 (checkBlock block >> cont)
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
        checkAssgs pos exprs types cont = case (exprs, types) of
            ([], []) -> cont
            (e:es, t:ts) -> checkAssg pos e t (checkAssgs pos es ts cont)
        checkAssg pos expr typ cont = case expr of
            EVar _ id -> do
                r <- getIdent pos id
                case r of
                    Just t -> do
                        checkCast pos typ t
                        cont
                    Nothing -> do
                        declare pos typ id cont
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
        checkBranches brs = case brs of
            [] -> skip
            b:bs -> case b of
                BElIf pos expr block -> do
                    checkCond pos expr block
                    checkBranches bs
        checkCond pos expr block = do
            (t, _) <- checkExpr expr
            case t of
                TBool _ -> return $ ()
                otherwise -> throw pos $ IllegalAssignment t tBool
            checkBlock block
        checkForRange pos from to = do
            (t1, _) <- checkExpr from
            (t2, _) <- checkExpr to
            case (t1, t2) of
                (TInt _, TInt _) -> return $ t1
                (TInt _, _) -> throw pos $ IllegalAssignment t2 tInt
                (TChar _, TChar _) -> return $ t1
                (TChar _, _) -> throw pos $ IllegalAssignment t2 tChar
                otherwise -> throw pos $ UnknownType
        checkForIterable pos iter = do
            (t, _) <- checkExpr iter
            case t of
                TString _ -> return $ tChar
                TArray _ t' -> return $ t'
                otherwise -> throw pos $ NotIterable t
        checkFor pos expr = case expr of
                ERangeIncl _ e1 e2 -> checkForRange pos e1 e2
                ERangeExcl _ e1 e2 -> checkForRange pos e1 e2
                ERangeInf _ e1 -> checkForRange pos e1 e1
                ETuple _ es -> do
                    ts <- forM es $ \e -> checkFor pos e
                    return $ tTuple ts
                otherwise -> checkForIterable pos expr

-- | Checks function's arguments and body.
checkFunc :: Pos -> Ident -> [ArgF Pos] -> Type -> Maybe (Block Pos) -> Run a -> Run a
checkFunc pos id args ret block cont = do
    r <- getIdent pos id
    case r of
        Nothing -> skip
        Just _ -> throw pos $ RedeclaredIdentifier id
    as <- forM args $ \a -> case a of
        ANoDefault _ t id -> return $ tArgN (reduceType t) id
        ADefault _ t id _ -> return $ tArgD (reduceType t) id ""
    let r = reduceType ret
    declare pos (tFunc as r) id $ do  -- so global functions are global
        case block of
            Just b -> nextLevel $ declare pos (tFunc as r) id $ do  -- so recursion works inside the function
                checkArgs args False $ local (M.insert (Ident "#return") (r, 0)) $ local (M.delete (Ident "#loop")) $ checkBlock b
            Nothing -> skip
        cont
    where
        checkArgs args def cont = case args of
             [] -> cont
             a:as -> checkArg a def (\d -> checkArgs as (def || d) cont)
        checkArg arg def cont = case arg of
            ANoDefault pos typ id -> case def of
                False -> declare pos (reduceType typ) id (cont False)
                True -> throw pos $ MissingDefault id
            ADefault pos typ id expr -> do
                (t, _) <- checkExpr expr
                checkCast pos t (reduceType typ)
                declare pos (reduceType typ) id (cont True)

-- | Checks if one type can be cast to another.
checkCast :: Pos -> Type -> Type -> Run ()
checkCast pos typ1 typ2 = case unifyTypes typ1 typ2 of
    Just _ -> skip
    Nothing -> throw pos $ IllegalAssignment typ1 typ2


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
            [] -> return $ (tArray tObject, False)
            t:ts -> case foldM unifyTypes t ts of
                Just t' -> return $ (tArray t', False)
                Nothing -> throw pos $ UnknownType
    EVar pos id -> checkIdent pos id
    EElem pos expr n -> do
        (t, m) <- checkExpr expr
        let i = fromInteger n
        case t of
            TTuple _ ts -> do
                if i < length ts then return $ (ts !! i, m)
                else throw pos $ InvalidTupleElem t (i+1)
            otherwise -> throw pos $ NotTuple t
    EIndex pos expr1 expr2 -> do
        (t1, m1) <- checkExpr expr1
        (t2, m2) <- checkExpr expr2
        case t2 of
            TInt _ -> case t1 of
                TString _ -> return $ (tChar, False)
                TArray _ t1' -> return $ (t1', True)
                otherwise -> throw pos $ NotIndexable t1
            otherwise -> throw pos $ IllegalAssignment t2 tInt
    EAttr pos expr id -> do
        (t1, m) <- checkExpr expr
        let Ident attr = id
        Just t2 <- case t1 of
            TInt _ -> case attr of
                "toString" -> getIdent _pos (Ident "Int_toString")
            TFloat _ -> case attr of
                "toString" -> getIdent _pos (Ident "Float_toString")
            TBool _ -> case attr of
                "toString" -> getIdent _pos (Ident "Bool_toString")
            TChar _ -> case attr of
                "toString" -> getIdent _pos (Ident "Char_toString")
            TString _ -> case attr of
                "length" -> return $ Just tInt
                "toString" -> getIdent _pos (Ident "String_toString")
                "toInt" -> getIdent _pos (Ident "String_toInt")
                "toFloat" -> getIdent _pos (Ident "String_toFloat")
                otherwise -> throw pos $ InvalidAttr t1 id
            TArray _ t' -> case (t', attr) of
                (_, "length") -> return $ Just tInt
                (TChar _, "join") -> do
                    t'' <- getIdent _pos (Ident "CharArray_join")
                    return $ t''
                (TString _, "join") -> do
                    t'' <- getIdent _pos (Ident "StringArray_join")
                    return $ t''
                otherwise -> throw pos $ InvalidAttr t1 id
            otherwise -> throw pos $ InvalidAttr t1 id
        return $ (t2, False)
    ECall pos expr args -> do
        (t, _) <- checkExpr expr
        args2 <- case expr of
            EAttr _ e _ -> return $ APos _pos e : args
            otherwise -> return $ args
        case t of
            TFunc _ args1 ret -> do
                -- Build a map of arguments and their positions.
                let m = M.empty
                (m, _) <- foldM' (m, False) (zip [0..] args2) $ \(m, named) (i, a) -> do
                    (pos', e, i, named) <- case (a, named) of
                        (APos pos' e, False) -> return $ (pos', e, i, False)
                        (ANamed pos' id e, _) -> do
                            case getArgument args1 id of
                                Just (i', _) -> case M.lookup i' m of
                                    Nothing -> return $ (pos', e, i', True)
                                    Just _ -> throw pos' $ RepeatedArgument id
                                Nothing -> throw pos' $ UnexpectedArgument id
                        (APos pos' _, True) -> throw pos' $ ExpectedNamedArgument
                    t <- case convertLambda pos' e of
                        ELambda _ ids e' -> do
                            t <- case args1 !! i of
                                TArgN _ t _ -> return $ t
                                TArgD _ t _ _ -> return $ t
                            let TFunc _ args rt = t
                            if length ids < length args then throw pos' $ TooFewArguments t
                            else if length ids > length args then throw pos' $ TooManyArguments t
                            else skip
                            let id = Ident ".lambda"
                            let as = [ANoDefault _pos t id | (t, id) <- zip args ids]
                            let b = SBlock pos' [SRetExpr pos' e']
                            checkFunc pos' id as rt (Just b) skip
                            return $ t
                        otherwise -> do
                            (t, _) <- checkExpr e
                            return $ t
                    return $ (M.insert i t m, named)
                -- Extend the map using default arguments.
                m <- foldM' m (zip [0..] args1) $ \m (i, a) -> case (a, M.lookup i m) of
                    (TArgD _ t _ _, Nothing) -> return $ M.insert i t m
                    otherwise -> return $ m
                -- Check whether all (and no redundant) arguments have been provided.
                if any (>= length args1) (M.keys m) then throw pos $ TooManyArguments t
                else if M.size m < length args1 then throw pos $ TooFewArguments t
                else skip
                -- Check if all arguments have correct types.
                forM (zip (M.elems m) args1) (uncurry $ checkCast pos)
                return $ (ret, False)
            otherwise -> throw pos $ NotFunction t
    EPow pos expr1 expr2 -> checkBinary pos "**" expr1 expr2
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
    EBXor pos expr1 expr2 -> checkBinary pos "^" expr1 expr2
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
        case unifyTypes (reduceType t2) (reduceType t3) of
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
        checkIdent pos id = do
            r <- getIdent pos id
            case r of
                Just t -> return $ (t, True)
                Nothing -> throw pos $ UndeclaredIdentifier id
        checkBinary pos op expr1 expr2 = do
            (t1, _) <- checkExpr expr1
            (t2, _) <- checkExpr expr2
            case op of
                "*" -> case (t1, t2) of
                    (TString _, TInt _) -> return $ (tString, False)
                    (TInt _, TString _) -> return $ (tString, False)
                    (TArray _ _, TInt _) -> return $ (t1, False)
                    (TInt _, TArray _ _) -> return $ (t2, False)
                    (TInt _, TInt _) -> return $ (tInt, False)
                    (TFloat _, TInt _) -> return $ (tFloat, False)
                    (TInt _, TFloat _) -> return $ (tFloat, False)
                    (TFloat _, TFloat _) -> return $ (tFloat, False)
                    otherwise -> throw pos $ NoBinaryOperator "*" t1 t2
                "+" -> case (t1, t2) of
                    (TString _, TString _) -> return $ (tString, False)
                    (TString _, TChar _) -> return $ (tString, False)
                    (TChar _, TString _) -> return $ (tString, False)
                    (TInt _, TInt _) -> return $ (tInt, False)
                    (TFloat _, TInt _) -> return $ (tFloat, False)
                    (TInt _, TFloat _) -> return $ (tFloat, False)
                    (TFloat _, TFloat _) -> return $ (tFloat, False)
                    otherwise -> throw pos $ NoBinaryOperator "+" t1 t2
                otherwise -> do
                    if op == "and" || op == "or" then case (t1, t2) of
                        (TBool _, TBool _) -> return $ (tBool, False)
                        otherwise -> throw pos $ NoBinaryOperator op t1 t2
                    else if op == "**" || op == "/" || op == "-" then case (t1, t2) of
                        (TInt _, TInt _) -> return $ (tInt, False)
                        (TFloat _, TInt _) -> return $ (tFloat, False)
                        (TInt _, TFloat _) -> return $ (tFloat, False)
                        (TFloat _, TFloat _) -> return $ (tFloat, False)
                        otherwise -> throw pos $ NoBinaryOperator op t1 t2
                    else case (t1, t2) of  -- modulo and bitwise operators
                        (TInt _, TInt _) -> return $ (tInt, False)
                        otherwise -> throw pos $ NoBinaryOperator op t1 t2
        checkUnary pos op expr = do
            (t, _) <- checkExpr expr
            case op of
                "~" -> case t of
                    TInt _ -> return $ (tInt, False)
                    otherwise -> throw pos $ NoUnaryOperator "~" t
                "not" -> case t of
                    TBool _ -> return $ (tBool, False)
                    otherwise -> throw pos $ NoUnaryOperator "not" t
                otherwise -> case t of  -- unary minus/plus
                    TInt _ -> return $ (tInt, False)
                    TFloat _ -> return $ (tFloat, False)
                    otherwise -> throw pos $ NoUnaryOperator op t
        checkCmp pos op typ1 typ2 = do
            case unifyTypes typ1 typ2 of
                Just t -> case t of
                    TObject _ -> throw pos $ NotComparable typ1 typ2
                    TArray _ _ -> throw pos $ NotComparable typ1 typ2
                    TFunc _ _ _ -> throw pos $ NotComparable typ1 typ2
                    otherwise -> return $ (tBool, False)
                Nothing -> case (typ1, typ2) of
                    (TFloat _, TInt _) -> return $ (tBool, False)
                    (TInt _, TFloat _) -> return $ (tBool, False)
                    otherwise -> throw pos $ NotComparable typ1 typ2
