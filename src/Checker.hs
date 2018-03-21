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

-- | Compilation error type.
data StaticError = NotComparable Type Type
                 | IllegalAssignment Type Type
                 | NoBinaryOperator String Type Type
                 | NoUnaryOperator String Type
                 | WrongFunctionCall Type Int
                 | UndeclaredIdentifier Ident

-- | Show instance for displaying compilation errors.
instance Show StaticError where
    show err = case err of
        NotComparable typ1 typ2 -> "Cannot compare `" ++ show typ1 ++ "` with `" ++ show typ2 ++ "`."
        IllegalAssignment typ1 typ2 -> "Illegal assignment from `" ++ show typ1 ++ "` to `" ++ show typ2 ++ "`."
        NoBinaryOperator op typ1 typ2 -> "No binary operator `" ++ op ++ "` defined for `" ++ show typ1 ++ "` and `" ++ show typ2 ++ "`."
        NoUnaryOperator op typ -> "No unary operator `" ++ op ++ "` defined for `" ++ show typ ++ "`."
        WrongFunctionCall typ n -> "Type `" ++ show typ ++ "` is not a function taking " ++ show n ++ " arguments."
        UndeclaredIdentifier (Ident x) -> "Undeclared identifier `" ++ x ++ "`."


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
    SExpr pos expr -> do
        checkExpr expr
        cont
    SAssg pos ident expr -> do
        t1 <- checkExpr expr
        r <- getIdent ident
        case r of
            Just t2 -> case (t1, t2) of
                (TInt _, TInt _) -> cont
                (TBool _, TBool _) -> cont
                otherwise -> throw pos $ IllegalAssignment t1 t2
            Nothing -> declare t1 ident cont
    SIf pos brs el -> do
        checkBranches brs
        case el of
            EElse pos b -> do
                checkBlock b
                cont
            EEmpty pos -> cont
    SWhile pos expr block -> do
        checkCond pos expr block
        cont
    where
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


-- | Checks an expression.
checkExpr :: Expr Pos -> Run Type
checkExpr expr =
    case expr of
        EInt pos _ -> return $ tInt
        ETrue pos -> return $ tBool
        EFalse pos -> return $ tBool
        EVar pos ident -> checkIdent pos ident
        EMul pos e1 e2 -> checkBinary pos "*" e1 e2
        EDiv pos e1 e2 -> checkBinary pos "/" e1 e2
        EMod pos e1 e2 -> checkBinary pos "%" e1 e2
        EAdd pos e1 e2 -> checkBinary pos "+" e1 e2
        ESub pos e1 e2 -> checkBinary pos "-" e1 e2
        ENeg pos e -> checkUnary pos "-" e
        ECmp pos e1 op e2 -> checkCmp pos op e1 e2
        ENot pos e -> checkUnary pos "not" e
        EAnd pos e1 e2 -> checkBinary pos "and" e1 e2
        EOr pos e1 e2 -> checkBinary pos "or" e1 e2
    where
        checkIdent pos ident = do
            r <- getIdent ident
            case r of
                Just t -> return $ t
                Nothing -> throw pos $ UndeclaredIdentifier ident
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
        checkCmp pos op e1 e2 = do
            t1 <- checkExpr e1
            t2 <- checkExpr e2
            case (t1, t2) of
                (TInt _, TInt _) -> return $ tBool
                (TBool _, TBool _) -> return $ tBool
                otherwise -> throw pos $ NotComparable t1 t2
