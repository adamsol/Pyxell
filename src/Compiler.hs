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
import qualified Data.Set as S

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
    declare (tFunc [tPtr tChar, tInt] (tPtr tChar)) "@realloc"
    declare (tFunc [tPtr tChar, tPtr tChar, tInt] (tPtr tChar)) "@memcpy"
    declare (tFunc [tChar] (tInt)) "@putchar"
    write $ [ "" ]
    ask

-- | Outputs LLVM code for all statements in the program.
compileProgram :: Program Pos -> String -> Run Env
compileProgram program name = case program of
    Program _ stmts -> localScope "main" $ do
        env1 <- ask
        -- `std` module is automatically added to the namespace, unless this is the module being compiled
        env2 <- case name of
            "std" -> compileStmts stmts ask
            otherwise -> compileStmts (SUse _pos (Ident "std") (UAll _pos) : stmts) ask
        lift $ modify (M.insert name (Module (M.difference env2 env1)))
        return $ M.insert (Ident name) (tModule, name) env1

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
    SUse _ id use -> do
        let Ident name = id
        Module env <- lift $ gets (M.! name)
        case use of
            UAll _ -> local (M.union env) cont
            UOnly _ ids -> local (M.union (M.filterWithKey (\id _ -> elem id ids) env)) cont
            UHiding _ ids -> local (M.union (M.filterWithKey (\id _ -> not (elem id ids)) env)) cont
            UAs _ id' -> local (M.insert id' (tModule, name)) cont
    SFunc _ id vars args ret body -> do
        vs <- case vars of
            FGen _ vs -> return $ vs
            FStd _ -> return $ []
        r <- case ret of
            FFunc _ r -> return $ r
            FProc _ -> return $ tVoid
        t <- case body of
            FDef _ b -> return $ tFuncDef id vs args r b
            FExtern _ -> return $ tFuncExt id args r
        localFunc id t cont
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
        t' <- retrieveType t
        compilePrint t' v
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
    SAssgPow _pos expr1 expr2 -> do
        compileAssgOp EPow expr1 expr2 cont
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
        compileFor expr1 expr2 "1" (compileBlock block) (const cont)
    SForStep _ expr1 expr2 expr3 block -> do
        (_, v) <- compileExpr expr3
        compileFor expr1 expr2 v (compileBlock block) (const cont)
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
            TArray _ t' -> do
                call tInt "@putchar" [(tChar, "91")] -- [
                n <- nextNumber
                let a = eVar ("a" ++ show n)
                let i = eVar ("i" ++ show n)
                compileAssg typ a val $ do
                    flip (compileFor i (ERangeExcl _pos (eInt 0) (EAttr _pos a (Ident "length"))) "1") (const skip) $ do
                        l <- nextLabel
                        flip (compileIf (ECmp _pos (Cmp1 _pos i (CmpGT _pos) (eInt 0)))) l $ do
                            call tInt "@putchar" [(tChar, "44")]  -- ,
                            call tInt "@putchar" [(tChar, "32")] >> skip
                        goto l >> label l
                        (_, v) <- compileExpr (EIndex _pos a i)
                        compilePrint t' v
                call tInt "@putchar" [(tChar, "93")] >> skip  -- ]
            otherwise -> do
                compileMethod typ (Ident "write") [val] >> skip
        compileAssgOp op expr1 expr2 cont = do
            compileStmt (SAssg _pos [expr1, op _pos expr1 expr2]) cont
        compileBranches brs exit = case brs of
            [] -> skip
            b:bs -> case b of
                BElIf _ expr block -> do
                    compileIf expr (compileBlock block) exit
                    compileBranches bs exit

-- | Compiles a list of variable assignments and continues with changed environment.
compileAssgs :: [(Type, Expr Pos, Int)] -> Type -> Value -> Run a -> Run a
compileAssgs rs typ val cont = case rs of
    [] -> cont
    (t, e, i):rs -> do
        v <- case val of
            "" -> return $ ""
            otherwise -> gep typ val ["0"] [i] >>= load t
        compileAssg t e v (compileAssgs rs typ val cont)

-- | Compiles a single variable assignment and continues with changed environment.
compileAssg :: Type -> Expr Pos -> Value -> Run a -> Run a
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

-- | Compiles a single `if` statement.
compileIf :: Expr Pos -> Run a -> Value -> Run a
compileIf expr body exit = do
    (t, v) <- compileExpr expr
    l1 <- nextLabel
    l2 <- nextLabel
    branch v l1 l2
    label l1
    x <- body
    goto exit
    label l2
    return $ x

-- | Compiles a single `for` statement and continues with changed environment.
compileFor :: Expr Pos -> Expr Pos -> Value -> Run a -> (a -> Run b) -> Run b
compileFor expr1 expr2 step body cont = do
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
        x <- localLabel "#break" l2 $ localLabel "#continue" l3 $ body
        goto l3 >> label l3
        vs3 <- forM (zip3 ts1 vs1 steps) $ \(t, v, s) -> binop "add" t v s
        forM (zip3 ts1 vs3 ps) $ \(t, v, p) -> store t v p
        goto l1
        label l2
        cont x
    where
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

-- | Outputs LLVM code for a function definition and initialization of its default arguments.
compileFunc :: Ident -> [FVar Pos] -> [FArg Pos] -> Type -> Maybe (Block Pos) -> [Type] -> Run Value
compileFunc id vars args1 rt block args2 = do
    (t, p) <- asks (M.! id)
    Function env set <- lift $ gets (M.! p)
    let as = map typeArg args1
    case S.member args2 set of
        True -> return $ p
        False -> local (const env) $ compileTypeVars args2 as $ do  -- environment is restored to the point of function definition
            lift $ modify (M.insert p (Function env (S.insert args2 set)))  -- function is marked as compiled with these types
            r <- retrieveType rt
            i <- case r of  -- if the return type is a tuple, the result is in the zeroth argument
                TTuple _ _ -> return $ 1
                otherwise -> return $ 0
            case S.null set of
                True -> do  -- default arguments are compiled only once, since their type is known
                    f <- functionName id
                    localScope f $ forM_ args1 $ compileDefaultArg
                False -> skip
            case block of
                Just b -> define t id $ compileArgs args1 i $ localType (Ident "#return") r $ do
                    l <- nextLabel
                    goto l >> label l
                    compileBlock b
                    case r of
                        TTuple _ _ -> retVoid
                        otherwise -> do
                            v <- defaultValue r
                            ret r v
                Nothing -> do
                    localScope "!global" $ external p t
                    skip
            return $ p
    where
        compileDefaultArg arg = case arg of
            ANoDefault _ _ _ -> skip
            ADefault _ t id' e -> do
                let p = argumentPointer id id'
                s <- strType t
                v <- defaultValue t
                writeTop $ [ p ++ " = global " ++ s ++ " " ++ v ]
                localScope "main" $ do
                    (_, v) <- compileExpr e
                    store t v p

-- | Outputs LLVM code for initialization of function arguments.
compileArgs :: [FArg Pos] -> Int -> Run a -> Run a
compileArgs args idx cont = case args of
    [] -> cont
    a:as -> compileArg a idx (compileArgs as (idx+1) cont)
    where
        compileArg arg idx cont = case arg of
            ANoDefault _ typ id -> do
                t <- retrieveType typ
                variable t id ("%" ++ show idx) cont
            ADefault _ typ id _ -> do
                t <- retrieveType typ
                variable t id ("%" ++ show idx) cont

-- | Adds type variables to the environment.
compileTypeVars :: [Type] -> [Type] -> Run a -> Run a
compileTypeVars as1 as2 cont = case (as1, as2) of
    ([], _) -> cont
    (t1:as1, t2:as2) -> compile t1 t2 $ compileTypeVars as1 as2 cont
    where
        compile t1 t2 cont = case (reduceType t1, reduceType t2) of
            (t1', t2'@(TVar _ id)) -> do
                if t1' == t2' then cont  -- to prevent looping
                else localType id t1 cont
            (TTuple _ ts1, TTuple _ ts2) -> compileTypeVars ts1 ts2 cont
            (TArray _ t1', TArray _ t2') -> compile t1' t2' cont
            (TFunc _ as1 r1, TFunc _ as2 r2) -> compileTypeVars as1 as2 (compile r1 r2 cont)
            otherwise -> cont


-- | Gets an identifier from the environment.
getIdent :: Ident -> Run (Maybe Result)
getIdent id = do
    r <- asks (M.lookup id)
    case r of
        Just (TFuncDef _ id [] as r b, _) -> compileFunc id [] as r (Just b) []
        Just (TFuncExt _ id as r, _) -> compileFunc id [] as r Nothing []
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
    EArrayCpr pos expr cprs -> do
        let c = "4"  -- initial capacity
        p1 <- alloca tInt
        store tInt c p1
        (t, _) <- temporary $ compileArrayCprs cprs $ compileExpr expr
        p2 <- initMemory (tArray t) "1"
        p3 <- gep (tArray t) p2 ["0"] [1]
        store tInt "0" p3
        p4 <- gep (tArray t) p2 ["0"] [0]
        p5 <- initMemory (tPtr t) c
        store (tPtr t) p5 p4
        compileArrayCprs cprs $ do
            (_, v1) <- compileExpr expr
            v2 <- load tInt p3
            v3 <- binop "add" tInt v2 "1"
            store tInt v3 p3
            v4 <- load tInt p1
            v5 <- binop "icmp sgt" tInt v3 v4
            l1 <- nextLabel
            l2 <- nextLabel
            branch v5 l1 l2
            label l1
            v6 <- binop "shl" tInt v4 "1"
            v7 <- sizeof (tPtr t) v6
            p6 <- load (tPtr t) p4
            p7 <- bitcast (tPtr t) (tPtr tChar) p6
            p8 <- call (tPtr tChar) "@realloc" [(tPtr tChar, p7), (tInt, v7)]
            p9 <- bitcast (tPtr tChar) (tPtr t) p8
            store (tPtr t) p9 p4
            store tInt v6 p1
            goto l2 >> label l2
            p10 <- load (tPtr t) p4
            gep (tPtr t) p10 [v2] [] >>= store t v1
        return $ (tArray t, p2)
    EVar _ _ -> compileRval expression
    EIndex _ _ _ -> compileRval expression
    ESlice pos expr slices -> do
        let s1:s2:s3:_ = slices ++ replicate 2 (SliceNone _pos)
        (v1, v1') <- case s1 of
            SliceExpr _ e -> do
                (_, v) <- compileExpr e
                return $ (v, "true")
            SliceNone _ -> return $ ("0", "false")
        (v2, v2') <- case s2 of
            SliceExpr _ e -> do
                (_, v) <- compileExpr e
                return $ (v, "true")
            SliceNone _ -> return $ ("0", "false")
        (_, v3) <- case s3 of
            SliceExpr _ e -> compileExpr e
            SliceNone _ -> return $ (tInt, "1")
        (t, p1) <- compileExpr expr
        t' <- case t of
            TArray _ t' -> return $ t'
            TString _ -> return $ tChar
        v4 <- gep t p1 ["0"] [1] >>= load tInt
        (_, f) <- compileExpr (EVar _pos (Ident "Array_prepareSlice"))
        let t2 = tTuple [tInt, tInt]
        v5 <- call t2 f [(tInt, v4), (tInt, v1), (tBool, v1'), (tInt, v2), (tBool, v2'), (tInt, v3)]
        v6 <- gep t2 v5 ["0"] [0] >>= load tInt
        v7 <- gep t2 v5 ["0"] [1] >>= load tInt
        p2 <- initArray t' [] [v7, v7]
        compileAssg t (eVar "source") p1 $ compileAssg t (eVar "result") p2 $ compileAssg tInt (eVar "c") v3 $ compileAssg tInt (eVar "j") v6 $ compileAssg tInt (eVar "d") v7 $ do
            b <- return $ SBlock _pos [
                SAssg _pos [EIndex _pos (eVar "result") (eVar "i"), EIndex _pos (eVar "source") (eVar "j")],
                SAssgAdd _pos (eVar "j") (eVar "c")]
            compileFor (eVar "i") (ERangeExcl _pos (eInt 0) (eVar "d")) "1" (compileBlock b) (const skip)
        return $ (t, p2)
    EAttr _ _ _ -> compileRval expression
    ECall _ expr args -> do
        (typ, func) <- case expr of
            EVar _ id -> do
                Just (t, p) <- getIdent id
                return $ (t, p)
            otherwise -> compileExpr expr
        (id, vars, args1, args2, rt) <- case typ of
            TFunc _ as r -> return $ (Ident "", [], as, [], r)
            TFuncDef _ id vs as r _ -> return $ (id, vs, map typeArg as, as, reduceType r)
            TFuncExt _ id as r -> return $ (id, [], map typeArg as, as, reduceType r)
        -- Build a map of arguments and their positions.
        let m = M.empty
        m <- case expr of
            EAttr pos e id -> do  -- if this is a method, the object will be passed as the first argument
                (t, v) <- compileExpr e
                case t of
                    TModule _ -> return $ m
                    otherwise -> return $ M.insert 0 (t, Left v) m
            otherwise -> return $ m
        m <- foldM' m (zip [(M.size m)..] args) $ \m (i, a) -> do
            (e, i) <- case a of
                APos _ e -> return $ (e, i)
                ANamed _ id e -> do
                    let Just (i', _) = getArgument args2 id
                    return $ (e, i')
            r <- case convertLambda _pos e of
                ELambda _ ids e' -> return $ (args1 !! i, Right (ids, e'))
                otherwise -> do
                    (t, v) <- compileExpr e
                    return $ (t, Left v)
            return $ M.insert i r m
        -- Extend the map using default arguments.
        m <- foldM' m (zip [0..] args2) $ \m (i, a) -> case (a, M.lookup i m) of
            (ADefault _ t id' _, Nothing) -> do
                t <- retrieveType t
                let p = argumentPointer id id'
                v <- load t p
                return $ M.insert i (t, Left v) m
            otherwise -> return $ m
        -- Call the function.
        compileTypeVars (map fst (M.elems m)) args1 $ do
            args4 <- forM (M.elems m) $ \r -> case r of
                (t, Left v) -> return $ (t, v)
                (t, Right (ids, e)) -> do
                    -- Compile lambda function.
                    let TFunc _ as r = t
                    n <- nextNumber
                    let id = Ident (".lambda" ++ show n)
                    f <- functionName id
                    s <- getScope
                    -- TODO: use compileFunc to get the returned type in a more concise way
                    i <- case r of  -- if the return type is a tuple, the result is in the zeroth argument
                        TTuple _ _ -> return $ 1
                        otherwise -> return $ 0
                    (r', p) <- localFunc id t $ localScope f $ compileArgs [ANoDefault _pos t' id' | (t', id') <- zip as ids] i $ do
                        l <- nextLabel
                        goto l >> label l
                        (r', v) <- compileExpr e
                        case r' of
                            TVoid _ -> retVoid
                            otherwise -> ret r' v
                        localScope s $ case r of
                            TVar _ id' -> localType id' r' $ define t id $ skip
                            otherwise -> define t id $ skip
                        (_, p) <- asks (M.! id)
                        return $ (r', p)
                    let t' = tFunc as r'
                    v <- load t' p
                    return $ (t', v)
            compileTypeVars (map fst args4) args1 $ do
                case typ of
                    TFuncDef _ id (_:_) _ _ b -> do
                        -- Compile generic function.
                        compileFunc id vars args2 rt (Just b) (map (reduceType.fst) args4)
                    otherwise -> return $ ""
                r <- retrieveType rt
                func <- case expr of
                    EVar _ id -> do
                        Just (t, p) <- getIdent id
                        p <- case vars of
                            [] -> return $ p
                            _:_ -> do
                                s <- strFVars vars
                                return $ p ++ s
                        load typ p
                    otherwise -> return $ func
                v <- call r func args4
                return $ (r, v)
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
    EBNot _ expr -> compileBinary "xor" (eInt (-1)) expr
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
                    compileArrayConcat tString v1 v2
                (TString _, TChar _, "add") -> do
                    (_, v3) <- compileMethod tChar (Ident "toString") [v2]
                    compileArrayConcat tString v1 v3
                (TChar _, TString _, "add") -> do
                    (_, v3) <- compileMethod tChar (Ident "toString") [v1]
                    compileArrayConcat tString v3 v2
                (TArray _ t1', TArray _ t2', "add") -> do
                    compileArrayConcat t1 v1 v2
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
        compileArrayConcat typ val1 val2 = do
            t' <- case typ of
                TString _ -> return $ tChar            
                TArray _ t' -> return $ t'
            p1 <- gep typ val1 ["0"] [0] >>= load (tPtr t')
            p2 <- gep typ val2 ["0"] [0] >>= load (tPtr t')
            v1 <- gep typ val1 ["0"] [1] >>= load tInt
            v2 <- gep typ val2 ["0"] [1] >>= load tInt
            v3 <- binop "add" tInt v1 v2
            p3 <- initArray t' [] [v3, v3]
            p4 <- gep typ p3 ["0"] [0] >>= load (tPtr t')
            p5 <- bitcast (tPtr t') (tPtr tChar) p4
            p6 <- bitcast (tPtr t') (tPtr tChar) p1
            v4 <- sizeof (tPtr t') v1
            call (tPtr tChar) "@memcpy" [(tPtr tChar, p5), (tPtr tChar, p6), (tInt, v4)]
            p7 <- gep (tPtr t') p4 [v1] []
            p8 <- bitcast (tPtr t') (tPtr tChar) p7
            p9 <- bitcast (tPtr t') (tPtr tChar) p2
            v5 <- sizeof (tPtr t') v2
            call (tPtr tChar) "@memcpy" [(tPtr tChar, p8), (tPtr tChar, p9), (tInt, v5)]
            return $ (typ, p3)
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
        compileArrayCprs cprs cont = case cprs of
            [] -> cont
            cpr:cprs -> compileArrayCpr cpr $ compileArrayCprs cprs cont
        compileArrayCpr cpr cont = case cpr of
            CprFor _ e1 e2 -> do
                compileFor e1 e2 "1" cont return
            CprForStep _ e1 e2 e3 -> do
                (_, v) <- compileExpr e3
                compileFor e1 e2 v cont return
            CprIf _ e -> do
                (_, l) <- asks (M.! (Ident "#continue"))
                x <- compileIf e cont l
                goto l
                return $ x
        compileCmp op typ val1 val2 = do
            (t, v1, v2) <- case typ of
                TString _ -> do
                    (_, v3) <- compileArrayCmp (tArray tChar) val1 val2
                    return $ (tInt, v3, "0")
                TArray _ _ -> do
                    (_, v3) <- compileArrayCmp typ val1 val2
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
        compileArrayCmp typ val1 val2 = do
            compileAssg typ (eVar "a1") val1 $ compileAssg typ (eVar "a2") val2 $ do
                compileExpr (ECall _pos (EVar _pos (Ident "Array_compare")) (map (APos _pos) [eVar "a1", eVar "a2"]))
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
    case t of
        TModule _ -> do
            return $ (t, p)
        otherwise -> do
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
        case t of
            TModule _ -> do
                (_, m) <- case e of
                    EVar _ id' -> asks (M.! id')
                Module env <- lift $ gets (M.! m)
                local (const env) $ getIdent id
            otherwise -> do
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
    TFunc _ as r <- retrieveType t
    p2 <- load t p1
    v <- call r p2 (zip as args)
    return $ (r, v)
