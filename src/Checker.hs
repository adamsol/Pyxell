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
                 | NotTuple Type
                 | InvalidTupleElem Type Int
                 | CannotUnpack Type Int

-- | Show instance for displaying compilation errors.
instance Show StaticError where
    show err = case err of
        NotComparable typ1 typ2 -> "Cannot compare `" ++ show typ1 ++ "` with `" ++ show typ2 ++ "`."
        IllegalAssignment typ1 typ2 -> "Illegal assignment from `" ++ show typ1 ++ "` to `" ++ show typ2 ++ "`."
        NoBinaryOperator op typ1 typ2 -> "No binary operator `" ++ op ++ "` defined for `" ++ show typ1 ++ "` and `" ++ show typ2 ++ "`."
        NoUnaryOperator op typ -> "No unary operator `" ++ op ++ "` defined for `" ++ show typ ++ "`."
        WrongFunctionCall typ n -> "Type `" ++ show typ ++ "` is not a function taking " ++ show n ++ " arguments."
        UndeclaredIdentifier (Ident x) -> "Undeclared identifier `" ++ x ++ "`."
        NotTuple typ -> "Type `" ++ show typ ++ "` is not a tuple."
        InvalidTupleElem typ n -> "Tuple `" ++ show typ ++ "` does not contain " ++ show n ++ " elements."
        CannotUnpack typ n -> "Cannot unpack value of type `" ++ show typ ++ "` into " ++ show n ++ " values."


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
    SAssg pos idents expr -> do
        t <- checkExpr expr
        case (idents, t) of
            ([id], _) -> do
                checkAssg pos t id cont
            (_, TTuple _ ts) -> do
                let n = length idents
                if length idents == length ts then do
                    checkAssgs pos ts idents cont
                else throw pos $ CannotUnpack t n
            otherwise -> throw pos $ CannotUnpack t (length idents)
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
        checkAssgs pos types idents cont = case (idents, types) of
            ([], []) -> cont
            (id:ids, t:ts) -> checkAssg pos t id (checkAssgs pos ts ids cont)
        checkAssg pos typ ident cont = do
            r <- getIdent ident
            case r of
                Just t -> do
                    checkCast pos (typ, t)
                    cont
                Nothing -> declare typ ident cont
        checkCast pos (typ1, typ2) = case (typ1, typ2) of
            (TInt _, TInt _) -> skip
            (TBool _, TBool _) -> skip
            (TTuple _ ts1, TTuple _ ts2) -> do
                mapM_ (checkCast pos) (zip ts1 ts2)
            otherwise -> throw pos $ IllegalAssignment typ1 typ2
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
        EElem pos e n -> do
            t <- checkExpr e
            let i = fromInteger n
            case t of
                TTuple _ ts -> do
                    if i < length ts then return $ ts !! i
                    else throw pos $ InvalidTupleElem t (i+1)
                otherwise -> throw pos $ NotTuple t
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
        ETuple pos es -> do
            ts <- mapM checkExpr es
            case ts of
                t:[] -> return $ t
                otherwise -> return $ tTuple ts
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
