{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}
{-# LANGUAGE FlexibleInstances #-}

module Checker where

import Control.Applicative
import Control.Monad
import Control.Monad.Identity
import Control.Monad.IO.Class
import Control.Monad.Trans.Class
import Control.Monad.Trans.State
import Control.Monad.Trans.Reader
import Control.Monad.Trans.Writer
import Control.Monad.Trans.Error
import Data.List
import qualified Data.Map as M

import AbsPyxell hiding (Type)
import Utils


-- | Checker monad: Reader for identifier environment, ErrorT to report compilation errors.
type Run r = ReaderT (M.Map String Type) (ErrorT String IO) r
--type Run r = ReaderT (M.Map String Type) (ReaderT Int (ErrorT String IO)) r

-- | Compilation error type.
data StaticError = NotComparable Type Type
                 | IllegalAssignment Type Type
                 | NoBinaryOperator String Type Type
                 | NoUnaryOperator String Type
                 | WrongFunctionCall Type Int
                 | UnexpectedStatement String
                 | UndeclaredIdentifier Ident
                 | NotLvalue
                 | UnknownType
                 | NotTuple Type
                 | InvalidTupleElem Type Int
                 | CannotUnpack Type Int
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
        WrongFunctionCall typ n -> "Type `" ++ show typ ++ "` is not a function taking " ++ show n ++ " arguments."
        UnexpectedStatement str -> "Unexpected `" ++ str ++ "` statement."
        UndeclaredIdentifier (Ident x) -> "Undeclared identifier `" ++ x ++ "`."
        NotLvalue -> "Expression cannot be assigned to."
        UnknownType -> "Expression cannot be used in this context."
        NotTuple typ -> "Type `" ++ show typ ++ "` is not a tuple."
        InvalidTupleElem typ n -> "Tuple `" ++ show typ ++ "` does not contain " ++ show n ++ " elements."
        CannotUnpack typ n -> "Cannot unpack value of type `" ++ show typ ++ "` into " ++ show n ++ " values."
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

-- | Gets an identifier from the environment.
getIdent :: Ident -> Run (Maybe Type)
getIdent ident = case ident of
    Ident x -> asks (M.lookup x)

-- | Adds an identifier to the environment.
declare :: Type -> Ident -> Run () -> Run ()
declare typ ident cont = case ident of
    Ident x -> local (M.insert x typ) cont


-- | Checks the whole program.
checkProgram :: Program Pos -> Run ()
checkProgram prog = case prog of
    Program pos stmts -> checkStmts stmts skip

-- | Checks a block with statements.
checkBlock :: Block Pos -> Run ()
checkBlock block = case block of
    SBlock pos stmts -> checkStmts stmts skip

-- | Checks a bunch of statements.
checkStmts :: [Stmt Pos] -> Run () -> Run ()
checkStmts stmts cont = case stmts of
    [] -> cont
    s:ss -> checkStmt s (checkStmts ss cont)

-- | Checks a single statement.
checkStmt :: Stmt Pos -> Run () -> Run ()
checkStmt stmt cont = case stmt of
    SSkip pos -> do
        cont
    SPrint pos expr -> do
        checkExpr expr
        cont
    SAssg pos exprs -> case exprs of
        e:[] -> do
            checkExpr e
            cont
        e1:e2:[] -> do
            t <- checkExpr e2
            case (e1, t) of
                (ETuple _ es, TTuple _ ts) -> do
                    if length es == length ts then do
                        checkAssgs pos es ts cont
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
        local (M.insert "#loop" tLabel) $ checkCond pos expr block
        cont
    SFor pos expr1 expr2 block -> case expr2 of
        ERange _ e1 e2 -> do
            checkStmt (SFor pos expr1 (ERangeStep _pos e1 e2 (EInt _pos 1)) block) cont
        ERangeStep _ e1 e2 e3 -> do
            ts <- mapM checkExpr [e1, e2, e3]
            case ts of
                [TInt _, TInt _, TInt _] -> do
                    local (M.insert "#loop" tLabel) $ checkAssg pos expr1 tInt (checkBlock block >> cont)
                [TInt _, TInt _, _] -> throw pos $ IllegalAssignment (ts !! 2) tInt
                [TInt _, _, _] -> throw pos $ IllegalAssignment (ts !! 1) tInt
                otherwise -> throw pos $ IllegalAssignment (ts !! 0) tInt
        otherwise -> do
            t <- checkExpr expr2
            case t of
                TString _ -> do
                    local (M.insert "#loop" tLabel) $ checkAssg pos expr1 tChar (checkBlock block >> cont)
                TArray _ t' -> do
                    local (M.insert "#loop" tLabel) $ checkAssg pos expr1 t' (checkBlock block >> cont)
                otherwise -> throw pos $ NotIterable t
    SBreak pos -> do
        r <- asks (M.lookup "#loop")
        case r of
            Just _ -> cont
            otherwise -> throw pos $ UnexpectedStatement "break"
    SContinue pos -> do
        r <- asks (M.lookup "#loop")
        case r of
            Just _ -> cont
            otherwise -> throw pos $ UnexpectedStatement "continue"
    where
        checkAssgs pos exprs types cont = case (exprs, types) of
            ([], []) -> cont
            (e:es, t:ts) -> checkAssg pos e t (checkAssgs pos es ts cont)
        checkAssg pos expr typ cont = case expr of
            EVar _ id -> do
                r <- getIdent id
                case r of
                    Just t -> do
                        checkCast pos typ t
                        cont
                    Nothing -> do
                        declare typ id cont
            EIndex _ e1 e2 -> do
                t <- checkExpr expr
                checkCast pos typ t
                cont
            otherwise -> throw pos $ NotLvalue
        checkCast pos typ1 typ2 = case unifyTypes typ1 typ2 of
            Just t -> skip
            Nothing -> throw pos $ IllegalAssignment typ1 typ2
        checkBranches brs = case brs of
            [] -> skip
            b:bs -> case b of
                BElIf pos expr block -> do
                    checkCond pos expr block
                    checkBranches bs
        checkCond pos expr block = do
            t <- checkExpr expr
            case t of
                TBool _ -> return $ ()
                otherwise -> throw pos $ IllegalAssignment t tBool
            checkBlock block


-- | Checks an expression and returns its type.
checkExpr :: Expr Pos -> Run Type
checkExpr expr =
    case expr of
        EInt pos _ -> return $ tInt
        ETrue pos -> return $ tBool
        EFalse pos -> return $ tBool
        EChar pos _ -> return $ tChar
        EString pos _ -> return $ tString
        EArray pos es -> do
            ts <- mapM checkExpr es
            case ts of
                [] -> return $ tArray tObject
                t:ts -> case foldM unifyTypes t ts of
                    Just t' -> return $ tArray t'
                    Nothing -> throw pos $ UnknownType
        EVar pos id -> checkIdent pos id
        EElem pos e n -> do
            t <- checkExpr e
            let i = fromInteger n
            case t of
                TTuple _ ts -> do
                    if i < length ts then return $ ts !! i
                    else throw pos $ InvalidTupleElem t (i+1)
                otherwise -> throw pos $ NotTuple t
        EIndex pos e1 e2 -> do
            t1 <- checkExpr e1
            t2 <- checkExpr e2
            case t2 of
                TInt _ -> case t1 of
                    TString _ -> return $ tChar
                    TArray _ t1' -> return $ t1'
                    otherwise -> throw pos $ NotIndexable t1
                otherwise -> throw pos $ IllegalAssignment t2 tInt
        EAttr pos e id -> do
            t <- checkExpr e
            case t of
                TString _ -> case id of
                    Ident "length" -> return $ tInt
                    otherwise -> throw pos $ InvalidAttr t id
                TArray _ _ -> case id of
                    Ident "length" -> return $ tInt
                    otherwise -> throw pos $ InvalidAttr t id
                otherwise -> throw pos $ NotClass t
        EMul pos e1 e2 -> checkBinary pos "*" e1 e2
        EDiv pos e1 e2 -> checkBinary pos "/" e1 e2
        EMod pos e1 e2 -> checkBinary pos "%" e1 e2
        EAdd pos e1 e2 -> checkBinary pos "+" e1 e2
        ESub pos e1 e2 -> checkBinary pos "-" e1 e2
        ENeg pos e -> checkUnary pos "-" e
        ERange pos _ _ -> throw pos $ UnknownType
        ERangeStep pos _ _ _ -> throw pos $ UnknownType
        ECmp pos cmp -> case cmp of
            Cmp1 pos e1 op e2 -> do
                t1 <- checkExpr e1
                t2 <- checkExpr e2
                checkCmp pos op t1 t2
            Cmp2 pos e1 op cmp -> do
                e2 <- case cmp of
                    Cmp1 _ e2 _ _ -> return $ e2
                    Cmp2 _ e2 _ _ -> return $ e2
                checkExpr (ECmp _pos (Cmp1 pos e1 op e2))
                checkExpr (ECmp _pos cmp)
        ENot pos e -> checkUnary pos "not" e
        EAnd pos e1 e2 -> checkBinary pos "and" e1 e2
        EOr pos e1 e2 -> checkBinary pos "or" e1 e2
        ETuple pos es -> do
            ts <- mapM checkExpr es
            case ts of
                t:[] -> return $ t
                otherwise -> return $ tTuple ts
    where
        checkIdent pos id = do
            r <- getIdent id
            case r of
                Just t -> return $ t
                Nothing -> throw pos $ UndeclaredIdentifier id
        checkBinary pos op e1 e2 = do
            t1 <- checkExpr e1
            t2 <- checkExpr e2
            case op of
                "*" -> case (t1, t2) of
                    (TInt _, TInt _) -> return $ tInt
                    otherwise -> throw pos $ NoBinaryOperator "*" t1 t2
                "/" -> case (t1, t2) of
                    (TInt _, TInt _) -> return $ tInt
                    otherwise -> throw pos $ NoBinaryOperator "/" t1 t2
                "%" -> case (t1, t2) of
                    (TInt _, TInt _) -> return $ tInt
                    otherwise -> throw pos $ NoBinaryOperator "%" t1 t2
                "+" -> case (t1, t2) of
                    (TInt _, TInt _) -> return $ tInt
                    (TString _, TString _) -> return $ tString
                    otherwise -> throw pos $ NoBinaryOperator "+" t1 t2
                "-" -> case (t1, t2) of
                    (TInt _, TInt _) -> return $ tInt
                    otherwise -> throw pos $ NoBinaryOperator "-" t1 t2
                "and" -> case (t1, t2) of
                    (TBool _, TBool _) -> return $ tBool
                    otherwise -> throw pos $ NoBinaryOperator "and" t1 t2
                "or" -> case (t1, t2) of
                    (TBool _, TBool _) -> return $ tBool
                    otherwise -> throw pos $ NoBinaryOperator "or" t1 t2
        checkUnary pos op e = do
            t <- checkExpr e
            case op of
                "-" -> case t of
                    TInt _ -> return $ tInt
                    otherwise -> throw pos $ NoUnaryOperator "-" t
                "not" -> case t of
                    TBool _ -> return $ tBool
                    otherwise -> throw pos $ NoUnaryOperator "not" t
        checkCmp pos op t1 t2 = do
            case unifyTypes t1 t2 of
                Just t -> case t of
                    TObject _ -> throw pos $ NotComparable t1 t2
                    TArray _ _ -> throw pos $ NotComparable t1 t2
                    otherwise -> return $ tBool
                Nothing -> throw pos $ NotComparable t1 t2
