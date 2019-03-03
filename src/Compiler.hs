{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}
{-# LANGUAGE FlexibleInstances #-}

module Compiler where

import Control.Monad.Identity
import Control.Monad.Trans.Class
import Control.Monad.Trans.State
import Control.Monad.Trans.Reader
import Data.Char
import Data.List
import qualified Data.Map as M

import AbsPyxell hiding (Type)
import ParPyxell
import LayoutPyxell (resolveLayout)
import ErrM

import CodeGen
import Utils


-- | Initializes the environment and outputs LLVM code with function declarations.
initCompiler :: Run Env
initCompiler = do
    lift $ modify (M.insert "$number" (Number 0))
    lift $ modify (M.insert "$label-main" (Label "entry"))
    writeTop $ [ "" ]
    declare (tFunc [tInt] (tPtr tChar)) "@malloc"
    declare (tFunc [tPtr tChar, tPtr tChar, tInt] (tPtr tChar)) "@memcpy"
    declare (tFunc [tChar] (tInt)) "@putchar"
    write $ [ "" ]
    ask

-- | Outputs LLVM code for all statements in the program.
compileProgram :: Program Pos -> Run Env
compileProgram program = case program of
    Program _ stmts -> localScope "main" $ compileStmts stmts ask

-- | Outputs LLVM code for a block of statements.
compileBlock :: Block Pos -> Run ()
compileBlock block = case block of
    SBlock _ stmts -> compileStmts stmts skip

-- | Outputs LLVM code for a bunch of statements and runs the continuation.
compileStmts :: [Stmt Pos] -> Run a -> Run a
compileStmts statements cont = case statements of
    [] -> cont
    s:ss -> compileStmt s (compileStmts ss cont)

-- | Outputs LLVM code for a single statement and runs the continuation.
compileStmt :: Stmt Pos -> Run a -> Run a
compileStmt statement cont = case statement of
    SFunc _ id args ret body -> do
        r <- case ret of
            FFunc _ t -> return $ t
            FProc _ -> return $ tVoid
        t <- case body of
            FDef _ b -> return $ tFuncDef id args r b
            FExtern _ -> return $ tFuncExt id args r
        localFunction id t cont
    SRetVoid _ -> do
        retVoid
        cont
    SRetExpr _ expr -> do
        (t, v) <- compileExpr expr
        ret t v
        cont
    SSkip _ -> do
        cont
    SPrint _ expr -> do
        (t, v) <- compileExpr expr
        compilePrint t v
        call tInt "@putchar" [(tChar, "10")]
        cont
    SPrintEmpty _ -> do
        call tInt "@putchar" [(tChar, "10")]
        cont
    SAssg _ exprs -> case exprs of
        e:[] -> do
            compileExpr e
            cont
        e1:e2:[] -> do
            (t, v) <- compileExpr e2
            case (e1, t) of
                (ETuple _ es, TTuple _ ts) -> do
                    compileAssgs (zip3 ts es [0..]) t v cont
                otherwise -> do
                    compileAssg t e1 v cont
        e1:e2:es -> do
            compileStmt (SAssg _pos (e2:es)) (compileStmt (SAssg _pos [e1, e2]) cont)
    SAssgMul _pos expr1 expr2 -> do
        compileAssgOp EMul expr1 expr2 cont
    SAssgDiv pos expr1 expr2 -> do
        compileAssgOp EDiv expr1 expr2 cont
    SAssgMod pos expr1 expr2 -> do
        compileAssgOp EMod expr1 expr2 cont
    SAssgAdd pos expr1 expr2 -> do
        compileAssgOp EAdd expr1 expr2 cont
    SAssgSub pos expr1 expr2 -> do
        compileAssgOp ESub expr1 expr2 cont
    SAssgBShl pos expr1 expr2 -> do
        compileAssgOp EBShl expr1 expr2 cont
    SAssgBShr pos expr1 expr2 -> do
        compileAssgOp EBShr expr1 expr2 cont
    SAssgBAnd pos expr1 expr2 -> do
        compileAssgOp EBAnd expr1 expr2 cont
    SAssgBOr pos expr1 expr2 -> do
        compileAssgOp EBOr expr1 expr2 cont
    SAssgBXor pos expr1 expr2 -> do
        compileAssgOp EBXor expr1 expr2 cont
    SIf _ brs el -> do
        l <- nextLabel
        compileBranches brs l
        case el of
            EElse _ block -> do
                compileBlock block
            EEmpty _ -> do
                skip
        goto l >> label l
        cont
    SWhile _ expr block -> do
        [l1, l2, l3] <- sequence (replicate 3 nextLabel)
        goto l1 >> label l1
        (_, v) <- compileExpr expr
        branch v l2 l3
        label l2
        localLabel "#break" l3 $ localLabel "#continue" l1 $ compileBlock block
        goto l1
        label l3
        cont
    SUntil _ expr block -> do
        [l1, l2] <- sequence (replicate 2 nextLabel)
        goto l1 >> label l1
        localLabel "#break" l2 $ localLabel "#continue" l1 $ compileBlock block
        (_, v) <- compileExpr expr
        branch v l2 l1
        label l2
        cont
    SFor _ expr1 expr2 block -> do
        compileFor expr1 expr2 "1" block cont
    SForStep _ expr1 expr2 expr3 block -> do
        (_, v) <- compileExpr expr3
        compileFor expr1 expr2 v block cont
    SBreak _ -> do
        (_, l) <- asks (M.! (Ident "#break"))
        goto l
        cont
    SContinue _ -> do
        (_, l) <- asks (M.! (Ident "#continue"))
        goto l
        cont
    where
        compilePrint typ val = case typ of
            TTuple _ ts -> do
                forM_ (zip [0..] ts) $ \(i, t) -> do
                    v <- gep typ val ["0"] [i] >>= load t
                    compilePrint t v
                    if i == length ts - 1 then skip
                    else call tInt "@putchar" [(tChar, "32")] >> skip
            otherwise -> do
                compileMethod typ (Ident "write") [val] >> skip
        compileAssgs rs typ val cont = case rs of
            [] -> cont
            (t, e, i):rs -> do
                v <- case val of
                    "" -> return $ ""
                    otherwise -> gep typ val ["0"] [i] >>= load t
                compileAssg t e v (compileAssgs rs typ val cont)
        compileAssg typ expr val cont = do
            e <- case expr of
                ETuple _ [e] -> return $ e
                otherwise -> return $ expr
            r <- compileLval expr
            case (r, e) of
                (Just (t, p), _) -> do
                    store typ val p
                    cont
                (Nothing, EVar _ id) -> do
                    variable typ id val cont
        compileAssgOp op expr1 expr2 cont = do
            compileStmt (SAssg _pos [expr1, op _pos expr1 expr2]) cont
        compileBranches brs exit = case brs of
            [] -> skip
            b:bs -> case b of
                BElIf _ expr block -> do
                    (t, v) <- compileExpr expr
                    l1 <- nextLabel
                    l2 <- nextLabel
                    branch v l1 l2
                    label l1
                    compileBlock block
                    goto exit
                    label l2
                    compileBranches bs exit
        initForRangeIncl from to step = do
            [(t, v1), (_, v2)] <- mapM compileExpr [from, to]
            v3 <- case t of
                TInt _ -> return $ step
                otherwise -> trunc tInt t step
            v4 <- binop "icmp sgt" t v3 "0"
            let cmp v = do
                v5 <- binop "icmp sle" t v v2
                v6 <- binop "icmp sge" t v v2
                select v4 tBool v5 v6
            return $ (t, t, v1, v3, cmp, return)
        initForRangeExcl from to step = do
            [(t, v1), (_, v2)] <- mapM compileExpr [from, to]
            v3 <- case t of
                TInt _ -> return $ step
                otherwise -> trunc tInt t step
            v4 <- binop "icmp sgt" t v3 "0"
            let cmp v = do
                v5 <- binop "icmp slt" t v v2
                v6 <- binop "icmp sgt" t v v2
                select v4 tBool v5 v6
            return $ (t, t, v1, v3, cmp, return)
        initForRangeInf from step = do
            (t, v1) <- compileExpr from
            v2 <- case t of
                TInt _ -> return $ step
                otherwise -> trunc tInt t step
            let cmp _ = return $ "true"
            return $ (t, t, v1, v2, cmp, return)
        initForIterable iter step = do
            (t, v1) <- compileExpr iter
            t' <- case t of
                TString _ -> return $ tChar
                TArray _ t' -> return $ t'
            v2 <- gep t v1 ["0"] [0] >>= load (tPtr t')
            v3 <- gep t v1 ["0"] [1] >>= load tInt
            v4 <- binop "sub" tInt v3 "1"
            v5 <- binop "icmp sgt" tInt step "0"
            v6 <- select v5 tInt "0" v4
            let cmp v = do
                v7 <- binop "icmp sle" tInt v v4
                v8 <- binop "icmp sge" tInt v "0"
                select v5 tBool v7 v8
            let get v = gep (tPtr t') v2 [v] [] >>= load t'
            return $ (tInt, t', v6, step, cmp, get)
        initFor expr step = do
            case expr of
                ERangeIncl _ e1 e2 -> forM [step] $ initForRangeIncl e1 e2
                ERangeExcl _ e1 e2 -> forM [step] $ initForRangeExcl e1 e2
                ERangeInf _ e1 -> forM [step] $ initForRangeInf e1
                ETuple _ es -> forM es $ \e -> do
                    r <- initFor e step
                    return $ head r
                otherwise -> forM [step] $ initForIterable expr
        compileFor expr1 expr2 step block cont = do
            es <- case expr1 of
                ETuple _ es -> return $ es
                otherwise -> return $ [expr1]
            rs <- initFor expr2 step
            let (ts1, ts2, starts, steps, cmps, gets) = unzip6 rs
            ps <- mapM alloca ts1
            forM (zip3 ts1 starts ps) $ \(t, v, p) -> store t v p
            [l1, l2, l3] <- sequence (replicate 3 nextLabel)
            ts3 <- case (es, ts2) of
                (_:_:_, [TTuple _ ts']) -> return $ ts'  -- for a, b in [(1, 2)] do
                ([_], _:_:_) -> return $ [tTuple ts2]  -- for t in 1..2, 3..4 do
                otherwise -> return $ ts2
            compileAssgs (zip3 ts3 es [0..]) (tTuple ts3) "" $ do
                goto l1 >> label l1
                vs1 <- forM (zip ts1 ps) $ \(t, p) -> load t p
                forM (zip cmps vs1) $ \(cmp, v) -> do
                    l4 <- nextLabel
                    v' <- cmp v
                    branch v' l4 l2
                    label l4
                vs2 <- forM (zip gets vs1) $ \(get, v) -> get v
                case (es, ts2) of
                    (_:_:_, [TTuple _ ts']) -> do   -- for a, b in [(1, 2)] do
                        compileAssgs (zip3 ts' es [0..]) (head ts2) (head vs2) skip
                    ([e], _:_:_) -> do  -- for t in 1..2, 3..4 do
                        p <- alloca (tDeref (tTuple ts2))
                        forM (zip3 ts2 vs2 [0..]) $ \(t, v, i) -> gep (tTuple ts2) p ["0"] [i] >>= store t v
                        compileAssg (tTuple ts2) e p skip
                    otherwise -> forM_ (zip3 ts2 es vs2) $ \(t, e, v) -> compileAssg t e v skip
                localLabel "#break" l2 $ localLabel "#continue" l3 $ compileBlock block
                goto l3 >> label l3
                vs3 <- forM (zip3 ts1 vs1 steps) $ \(t, v, s) -> binop "add" t v s
                forM (zip3 ts1 vs3 ps) $ \(t, v, p) -> store t v p
                goto l1
                label l2
                cont

-- | Outputs LLVM code for a function definition and initialization of its default arguments.
compileFunc :: Ident -> [FArg Pos] -> Type -> Maybe (Block Pos) -> Run Value
compileFunc id args rt block = do
    (_, p) <- asks (M.! id)
    c <- lift $ gets (M.lookup p)
    case c of
        Nothing -> return $ p
        Just (Function env) -> local (const env) $ do  -- environment is restored to the point of function definition
            lift $ modify (M.delete p)
            let as = map typeArg args
            let r = reduceType rt
            let t = tFunc as r
            i <- case r of  -- if the return type is a tuple, the result is in the zeroth argument
                TTuple _ _ -> return $ 1
                otherwise -> return $ 0
            f <- functionName id
            forM args $ compileDefaultArg f
            case block of
                Just b -> define t id $ compileArgs args i $ localType (Ident "#return") r $ do
                    l <- nextLabel
                    goto l >> label l
                    compileBlock b
                    case r of
                        TTuple _ _ -> retVoid
                        otherwise -> ret r (defaultValue r)
                Nothing -> do
                    localScope "!global" $ external p t
                    skip
            return $ p
    where
        compileDefaultArg f arg = case arg of
            ANoDefault _ _ _ -> skip
            ADefault _ t id' e -> do
                let p = argumentPointer id id'
                localScope f $ writeTop $ [ p ++ " = global " ++ strType t ++ " " ++ defaultValue t ]
                localScope "main" $ do
                    (_, v) <- compileExpr e
                    store t v p
        compileArgs args idx cont = case args of
             [] -> cont
             a:as -> compileArg a idx (compileArgs as (idx+1) cont)
        compileArg arg idx cont = case arg of
            ANoDefault _ typ id -> do
                variable (reduceType typ) id ("%" ++ show idx) cont
            ADefault _ typ id _ -> do
                variable (reduceType typ) id ("%" ++ show idx) cont


-- | Gets an identifier from the environment.
getIdent :: Ident -> Run (Maybe Result)
getIdent id = do
    r <- asks (M.lookup id)
    case r of
        Just (TFuncDef _ id as r b, _) -> compileFunc id as r (Just b)
        Just (TFuncExt _ id as r, _) -> compileFunc id as r Nothing
        otherwise -> return $ ""
    return $ r

-- | Outputs LLVM code that evaluates a given expression. Returns type and name of the result.
compileExpr :: Expr Pos -> Run Result
compileExpr expression = case expression of
    EInt _ num -> return $ (tInt, show num)
    EFloat _ num -> return $ (tFloat, show num)
    ETrue _ -> return $ (tBool, "true")
    EFalse _ -> return $ (tBool, "false")
    EChar _ char -> return $ (tChar, show (ord char))
    EString _ str -> do
        let (txts, tags) = interpolateString (read str)
        if length txts == 1 then do
            p <- initString (txts !! 0)
            return $ (tString, p)
        else do
            p1 <- initArray tString [] (replicate 2 (show (length txts * 2 - 1)))
            p2 <- gep (tArray tString) p1 ["0"] [0] >>= load (tPtr tString)
            forM (zip3 txts tags [0..]) $ \(txt, tag, i) -> do
                p3 <- gep (tPtr tString) p2 [show (2*i)] []
                p4 <- initString txt
                store tString p4 p3
                if tag == "" then skip
                else do
                    p5 <- gep (tPtr tString) p2 [show (2*i+1)] []
                    (_, v) <- case pExpr $ resolveLayout False $ myLexer tag of
                        Ok expr -> do
                            (t, v) <- compileExpr expr
                            compileMethod t (Ident "toString") [v]
                    store tString v p5
            p7 <- initString ""
            compileMethod (tArray tString) (Ident "join") [p1, p7]
    EArray _ exprs -> do
        rs <- mapM compileExpr exprs
        t <- case rs of
            r:_ -> return $ fst r
        p <- initArray t (map snd rs) []
        return $ (tArray t, p)
    EVar _ _ -> compileRval expression
    EIndex _ _ _ -> compileRval expression
    EAttr _ _ _ -> compileRval expression
    ECall _ expr args -> do
        (typ, f) <- compileExpr expr
        (args1, args2, rt) <- case typ of
            TFunc _ as r -> return $ (as, [], r)
            TFuncDef _ id as r b -> return $ (map typeArg as, as, reduceType r)
            TFuncExt _ id as r -> return $ (map typeArg as, as, reduceType r)
        args3 <- case expr of
            EAttr _ e _ -> return $ APos _pos e : args  -- if this is a method, the object is passed as the first argument
            otherwise -> return $ args
        -- Build a map of arguments and their positions.
        let m = M.empty
        m <- foldM' m (zip [0..] args3) $ \m (i, a) -> do
            (e, i) <- case a of
                APos _ e -> return $ (e, i)
                ANamed _ id e -> do
                    let Just (i', _) = getArgument args2 id
                    return $ (e, i')
            (t, v) <- case convertLambda _pos e of
                ELambda _ ids e' -> do
                    let t = args1 !! i
                    let TFunc _ as r = t
                    n <- nextNumber
                    let id = Ident (".lambda" ++ show n)
                    b <- case r of
                        TVoid _ -> return $ SBlock _pos [SAssg _pos [e']]
                        otherwise -> return $ SBlock _pos [SRetExpr _pos e']
                    p <- localFunction id t $ compileFunc id [ANoDefault _pos t' id' | (t', id') <- zip as ids] r (Just b)
                    v <- load t p
                    return $ (t, v)
                otherwise -> do
                    compileExpr e
            return $ M.insert i (t, v) m
        -- Extend the map using default arguments.
        m <- foldM' m (zip [0..] args2) $ \m (i, a) -> case (a, M.lookup i m) of
            (ADefault _ t id' _, Nothing) -> do
                id <- case typ of
                    TFuncDef _ id _ _ _ -> return $ id
                    TFuncExt _ id _ _ -> return $ id
                t <- return $ reduceType t
                let p = argumentPointer id id'
                v <- load t p
                return $ M.insert i (t, v) m
            otherwise -> return $ m
        -- Call the function.
        v <- call rt f (M.elems m)
        return $ (rt, v)
    EPow _ expr1 expr2 -> compileBinary "pow" expr1 expr2
    EMinus _ expr -> do
        (t, v1) <- compileExpr expr
        v2 <- case t of
            TInt _ -> binop "sub" t "0" v1
            TFloat _ -> binop "fsub" t "0.0" v1
        return $ (t, v2)
    EPlus _ expr -> do
        (t, v1) <- compileExpr expr
        v2 <- case t of
            TInt _ -> binop "add" t "0" v1
            TFloat _ -> binop "fadd" t "0.0" v1
        return $ (t, v2)
    EBNot _ expr -> compileBinary "xor" (EInt _pos (-1)) expr
    EMul _ expr1 expr2 -> compileBinary "mul" expr1 expr2
    EDiv _ expr1 expr2 -> do
        (t1, v1) <- compileExpr expr1
        (t2, v2) <- compileExpr expr2
        case (t1, t2) of
            (TInt _, TInt _) -> do
                v3 <- binop "sdiv" t1 v1 v2
                v4 <- binop "sub" t1 v3 "1"
                v5 <- binop "xor" t1 v1 v2
                v6 <- binop "icmp slt" t1 v5 "0"
                v7 <- select v6 t1 v4 v3
                v8 <- binop "mul" t1 v3 v2
                v9 <- binop "icmp ne" t1 v8 v1
                v10 <- select v9 t1 v7 v3
                return $ (t1, v10)
            otherwise -> compileBinary "div" expr1 expr2
    EMod _ expr1 expr2 -> do
        (t, v1) <- compileExpr expr1
        (t, v2) <- compileExpr expr2
        v3 <- binop "srem" t v1 v2
        v4 <- binop "add" t v3 v2
        v5 <- binop "xor" t v1 v2
        v6 <- binop "icmp slt" t v5 "0"
        v7 <- select v6 t v4 v3
        v8 <- binop "icmp eq" t v3 "0"
        v9 <- select v8 t v3 v7
        return $ (t, v9)
    EAdd _ expr1 expr2 -> compileBinary "add" expr1 expr2
    ESub _ expr1 expr2 -> compileBinary "sub" expr1 expr2
    EBShl _ expr1 expr2 -> compileBinary "shl" expr1 expr2
    EBShr _ expr1 expr2 -> compileBinary "ashr" expr1 expr2
    EBAnd _ expr1 expr2 -> compileBinary "and" expr1 expr2
    EBOr _ expr1 expr2 -> compileBinary "or" expr1 expr2
    EBXor _ expr1 expr2 -> compileBinary "xor" expr1 expr2
    ECmp _ cmp -> case cmp of
        Cmp1 _ e1 op e2 -> do
            (t1, v1) <- compileExpr e1
            (t2, v2) <- compileExpr e2
            (t, v1', v2') <- unifyValues t1 v1 t2 v2
            v <- case op of
                CmpEQ _ -> compileCmp "eq" t v1' v2'
                CmpNE _ -> compileCmp "ne" t v1' v2'
                CmpLT _ -> compileCmp "lt" t v1' v2'
                CmpLE _ -> compileCmp "le" t v1' v2'
                CmpGT _ -> compileCmp "gt" t v1' v2'
                CmpGE _ -> compileCmp "ge" t v1' v2'
            return $ (tBool, v)
        Cmp2 _ e1 op cmp -> do
            e2 <- case cmp of
                Cmp1 pos e2 _ _ -> return $ e2
                Cmp2 pos e2 _ _ -> return $ e2
            compileExpr (EAnd _pos (ECmp _pos (Cmp1 _pos e1 op e2)) (ECmp _pos cmp))
    ENot _ expr -> compileBinary "xor" (ETrue _pos) expr
    EAnd _ expr1 expr2 -> do
        l <- nextLabel
        v <- compileAnd expr1 expr2 [] l
        return $ (tBool, v)
    EOr _ expr1 expr2 -> do
        l <- nextLabel
        v <- compileOr expr1 expr2 [] l
        return $ (tBool, v)
    ECond _ expr1 expr2 expr3 -> do
        (t1, v1) <- compileExpr expr1
        (t2, v2) <- compileExpr expr2
        (t3, v3) <- compileExpr expr3
        let Just t4 = unifyTypes t2 t3
        v4 <- select v1 t4 v2 v3
        return $ (t4, v4)
    ETuple _ exprs -> do
        rs <- mapM compileExpr exprs
        case rs of
            r:[] -> return $ r
            otherwise -> do
                let t = tTuple (map fst rs)
                p <- initTuple rs
                return $ (t, p)
    where
        compileBinary op expr1 expr2 = do
            (t1, v1) <- compileExpr expr1
            (t2, v2) <- compileExpr expr2
            case (t1, t2, op) of
                (TString _, TString _, "add") -> do
                    compileStringConcat v1 v2
                (TString _, TChar _, "add") -> do
                    (_, v3) <- compileMethod tChar (Ident "toString") [v2]
                    compileStringConcat v1 v3
                (TChar _, TString _, "add") -> do
                    (_, v3) <- compileMethod tChar (Ident "toString") [v1]
                    compileStringConcat v3 v2
                (TString _, TInt _, "mul") -> do
                    p <- compileArrayMul tChar v1 v2
                    return $ (tString, p)
                (TInt _, TString _, "mul") -> do
                    p <- compileArrayMul tChar v2 v1
                    return $ (tString, p)
                (TArray _ t', TInt _, "mul") -> do
                    p <- compileArrayMul t' v1 v2
                    return $ (t1, p)
                (TInt _, TArray _ t', "mul") -> do
                    p <- compileArrayMul t' v2 v1
                    return $ (t2, p)
                (_, _, "pow") -> do
                    (t, v1', v2') <- unifyValues t1 v1 t2 v2
                    compileMethod t (Ident "pow") [v1', v2']
                otherwise -> do
                    (t, v1', v2') <- unifyValues t1 v1 t2 v2
                    v3 <- case t of
                        TFloat _ -> binop ("f" ++ op) t v1' v2'
                        otherwise -> binop op t v1' v2'
                    return $ (t, v3)
        compileStringConcat val1 val2 = do
            p1 <- gep tString val1 ["0"] [0] >>= load (tPtr tChar)
            p2 <- gep tString val2 ["0"] [0] >>= load (tPtr tChar)
            v1 <- gep tString val1 ["0"] [1] >>= load tInt
            v2 <- gep tString val2 ["0"] [1] >>= load tInt
            v3 <- binop "add" tInt v1 v2
            p3 <- initArray tChar [] [v3, v3]
            p4 <- gep tString p3 ["0"] [0] >>= load (tPtr tChar)
            call (tPtr tChar) "@memcpy" [(tPtr tChar, p4), (tPtr tChar, p1), (tInt, v1)]
            p5 <- gep (tPtr tChar) p4 [v1] []
            call (tPtr tChar) "@memcpy" [(tPtr tChar, p5), (tPtr tChar, p2), (tInt, v2)]
            return $ (tString, p3)
        compileArrayMul typ val1 val2 = do
            let t = tArray typ
            p1 <- gep t val1 ["0"] [0] >>= load (tPtr typ)
            v1 <- gep t val1 ["0"] [1] >>= load tInt
            v2 <- binop "mul" tInt v1 val2
            p2 <- initArray typ [] [v2, v2]
            p3 <- gep t p2 ["0"] [0] >>= load (tPtr typ)
            p4 <- alloca tInt
            p5 <- alloca tInt
            [l1, l2, l3, l4, l5, l6] <- sequence (replicate 6 nextLabel)
            store tInt "0" p4
            goto l1 >> label l1
            v3 <- load tInt p4
            v4 <- binop "icmp slt" tInt v3 v1
            branch v4 l2 l3
            label l2
            v5 <- gep (tPtr typ) p1 [v3] [] >>= load typ
            do
                store tInt v3 p5
                goto l4 >> label l4
                v6 <- load tInt p5
                v7 <- binop "icmp slt" tInt v6 v2
                branch v7 l5 l6
                label l5
                gep (tPtr typ) p3 [v6] [] >>= store typ v5
                v8 <- binop "add" tInt v6 v1
                store tInt v8 p5
                goto l4
                label l6
            v9 <- binop "add" tInt v3 "1"
            store tInt v9 p4
            goto l1
            label l3
            return $ p2
        compileCmp op typ val1 val2 = do
            (t, v1, v2) <- case typ of
                TString _ -> do
                    (_, v3) <- compileMethod tString (Ident "compare") [val1, val2]
                    return $ (tInt, v3, "0")
                otherwise -> return $ (typ, val1, val2)
            case (op, t) of
                (_, TTuple _ ts) -> do
                    lt <- nextLabel
                    lf <- nextLabel
                    compileTupleCmp op t v1 v2 0 lt lf
                ("eq", TFloat _) -> binop ("fcmp o" ++ op) t v1 v2
                ("eq", _) -> binop ("icmp " ++ op) t v1 v2
                ("ne", TFloat _) -> binop ("fcmp o" ++ op) t v1 v2
                ("ne", _) -> binop ("icmp " ++ op) t v1 v2
                (_, TBool _) -> binop ("icmp u" ++ op) t v1 v2
                (_, TFloat _) -> binop ("fcmp o" ++ op) t v1 v2
                otherwise -> binop ("icmp s" ++ op) t v1 v2
        compileTupleCmp op typ val1 val2 idx lt lf = do
            t <- case typ of
                TTuple _ ts -> return $ ts !! idx
            v1 <- gep typ val1 ["0"] [idx] >>= load t
            v2 <- gep typ val2 ["0"] [idx] >>= load t
            v3 <- compileCmp op t v1 v2
            case typ of
                TTuple _ ts -> do
                    if idx == length ts - 1 then do
                        l1 <- getLabel
                        l2 <- nextLabel
                        goto l2
                        label lt >> goto l2
                        label lf >> goto l2
                        label l2
                        phi [("true", lt), ("false", lf), (v3, l1)]
                    else do
                        l1 <- nextLabel
                        case op of
                            "eq" -> do
                                branch v3 l1 lf
                                label l1
                            "ne" -> do
                                branch v3 lt l1
                                label l1
                            otherwise -> do
                                branch v3 lt l1
                                label l1
                                v4 <- compileCmp "eq" t v1 v2
                                l2 <- nextLabel
                                branch v4 l2 lf
                                label l2
                        compileTupleCmp op typ val1 val2 (idx+1) lt lf
        compileAnd expr1 expr2 preds exit = do
            (_, v1) <- compileExpr expr1
            l1 <- getLabel
            l2 <- nextLabel
            branch v1 l2 exit
            label l2
            case expr2 of
                EAnd pos e1 e2 -> compileAnd e1 e2 (l1:preds) exit
                otherwise -> do
                    (_, v2) <- compileExpr expr2
                    l3 <- getLabel
                    goto exit >> label exit
                    phi ([("false", l) | l <- l1:preds] ++ [(v2, l3)])
        compileOr expr1 expr2 preds exit = do
            (_, v1) <- compileExpr expr1
            l1 <- getLabel
            l2 <- nextLabel
            branch v1 exit l2
            label l2
            case expr2 of
                EOr pos e1 e2 -> compileOr e1 e2 (l1:preds) exit
                otherwise -> do
                    (_, v2) <- compileExpr expr2
                    l3 <- getLabel
                    goto exit >> label exit
                    phi ([("true", l) | l <- l1:preds] ++ [(v2, l3)])

-- | Outputs LLVM code that evaluates a given expression as an r-value. Returns type and name of the result.
compileRval :: Expr Pos -> Run Result
compileRval expr = do
    Just (t, p) <- compileLval expr
    v <- load t p
    return $ (t, v)

-- | Outputs LLVM code that evaluates a given expression as an l-value. Returns type and name (location) of the result or Nothing.
compileLval :: Expr Pos -> Run (Maybe Result)
compileLval expr = case expr of
    EVar _ id -> do
        getIdent id
    EIndex _ e1 e2 -> do
        (t1, v1) <- compileExpr e1
        (t2, v2) <- compileExpr e2
        case t1 of
            TString _ -> getIndex tChar v1 v2
            TArray _ t1' -> getIndex t1' v1 v2
    EAttr _ e id -> do
        (t, v) <- compileExpr e
        compileAttr t v id
    where
        getIndex typ arr idx = do
            v1 <- gep (tArray typ) arr ["0"] [1] >>= load tInt
            v2 <- binop "add" tInt v1 idx
            v3 <- binop "icmp sge" tInt idx "0"
            v4 <- select v3 tInt idx v2
            v5 <- gep (tArray typ) arr ["0"] [0] >>= load (tPtr typ)
            v6 <- gep (tPtr typ) v5 [v4] []
            return $ Just (typ, v6)

-- | Outputs LLVM code that evaluates a given attribute as an l-value. Returns type and name (location) of the result or Nothing.
compileAttr :: Type -> Value -> Ident -> Run (Maybe Result)
compileAttr typ val (Ident attr) = case typ of
    -- TODO: toString() for other types
    TInt _ -> case attr of
        "write" -> getIdent (Ident "writeInt")
        "toString" -> getIdent (Ident "Int_toString")
        "toFloat" -> getIdent (Ident "Int_toFloat")
        "pow" -> getIdent (Ident "Int_pow")
    TFloat _ -> case attr of
        "write" -> getIdent (Ident "writeFloat")
        "toString" -> getIdent (Ident "Float_toString")
        "toInt" -> getIdent (Ident "Float_toInt")
        "pow" -> getIdent (Ident "Float_pow")
    TBool _ -> case attr of
        "write" -> getIdent (Ident "writeBool")
        "toString" -> getIdent (Ident "Bool_toString")
    TChar _ -> case attr of
        "write" -> getIdent (Ident "writeChar")
        "toString" -> getIdent (Ident "Char_toString")
    TString _ -> case attr of
        "write" -> getIdent (Ident "write")
        "length" -> getAttr (tArray tChar) val tInt 1
        "toString" -> getIdent (Ident "String_toString")
        "toInt" -> getIdent (Ident "String_toInt")
        "toFloat" -> getIdent (Ident "String_toFloat")
        "compare" -> getIdent (Ident "String_compare")
    TArray _ t' -> case (t', attr) of
        (_, "length") -> getAttr typ val tInt 1
        (TChar _, "join") -> getIdent (Ident "CharArray_join")
        (TString _, "join") -> getIdent (Ident "StringArray_join")
    TTuple _ ts -> do
        let i = ord (attr !! 0) - ord 'a'
        getAttr typ val (ts !! i) i
    where
        getAttr typ1 obj typ2 idx = do
            p <- gep typ1 obj ["0"] [idx]
            return $ Just (typ2, p)

-- | Outputs LLVM code that calls a method with given arguments. Returns type and name of the result.
compileMethod :: Type -> Ident -> [Value] -> Run Result
compileMethod typ id args = do
    Just (t, p1) <- compileAttr typ "" id
    let TFunc _ as r = reduceType t
    p2 <- load t p1
    v <- call r p2 (zip as args)
    return $ (r, v)
