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


-- | Outputs LLVM code for all statements in the program.
compileProgram :: Program Pos -> Run ()
compileProgram prog = case prog of
    Program _ stmts -> do
        write $ [ "",
            "declare i8* @malloc(i64)", "declare i8* @memcpy(i8*, i8*, i64)",
            "declare i64 @putchar(i8)",
            "" ]
        lift $ modify (M.insert "$number" (Number 0))
        define (tFunc [] tInt) "@main" $ do
            compileStmts stmts skip
            ret tInt "0"

-- | Outputs LLVM code for a block of statements.
compileBlock :: Block Pos -> Run ()
compileBlock block = case block of
    SBlock _ stmts -> compileStmts stmts skip

-- | Outputs LLVM code for a bunch of statements and runs the continuation.
compileStmts :: [Stmt Pos] -> Run () -> Run ()
compileStmts stmts cont = case stmts of
    [] -> cont
    s:ss -> compileStmt s (compileStmts ss cont)

-- | Outputs LLVM code for a single statement and runs the continuation.
compileStmt :: Stmt Pos -> Run () -> Run ()
compileStmt stmt cont = case stmt of
    SProc _ (Ident f) args block -> do
        compileFunc f args tVoid (Just block) cont
    SFunc _ (Ident f) args rt block -> do
        compileFunc f args rt (Just block) cont
    SProcExtern _ (Ident f) args -> do
        compileFunc f args tVoid Nothing cont
    SFuncExtern _ (Ident f) args rt -> do
        compileFunc f args rt Nothing cont
    SRetVoid _ -> do
        ret tVoid ""
    SRetExpr _ expr -> do
        (t, v) <- compileExpr expr
        ret t v
    SSkip _ -> do
        cont
    SPrint _  expr -> do
        (t, v) <- compileExpr expr
        compilePrint t v
        callVoid "@writeLn" []
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
        compileStmt (SAssg _pos [expr1, EMul _pos expr1 expr2]) cont
    SAssgDiv pos expr1 expr2 -> do
        compileStmt (SAssg _pos [expr1, EDiv _pos expr1 expr2]) cont
    SAssgMod pos expr1 expr2 -> do
        compileStmt (SAssg _pos [expr1, EMod _pos expr1 expr2]) cont
    SAssgAdd pos expr1 expr2 -> do
        compileStmt (SAssg _pos [expr1, EAdd _pos expr1 expr2]) cont
    SAssgSub pos expr1 expr2 -> do
        compileStmt (SAssg _pos [expr1, ESub _pos expr1 expr2]) cont
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
        local (M.insert "#break" (tLabel, l3)) $ local (M.insert "#continue" (tLabel, l1)) $ compileBlock block
        goto l1
        label l3
        cont
    SUntil _ expr block -> do
        [l1, l2] <- sequence (replicate 2 nextLabel)
        goto l1 >> label l1
        local (M.insert "#break" (tLabel, l2)) $ local (M.insert "#continue" (tLabel, l1)) $ compileBlock block
        (_, v) <- compileExpr expr
        branch v l2 l1
        label l2
        cont
    SFor _ expr1 expr2 block -> case expr2 of
        ERangeIncl _ e1 e2 -> do
            compileStmt (SFor _pos expr1 (ERangeInclStep _pos e1 e2 (EInt _pos 1)) block) cont
        ERangeExcl _ e1 e2 -> do
            compileStmt (SFor _pos expr1 (ERangeExclStep _pos e1 e2 (EInt _pos 1)) block) cont
        ERangeInclStep _ e1 e2 e3 -> do
            [(t, v1), (_, v2), (_, v3)] <- mapM compileExpr [e1, e2, e3]
            v4 <- binop "icmp sgt" t v3 "0"
            let cmp v = do
                v5 <- binop "icmp sle" t v v2
                v6 <- binop "icmp sge" t v v2
                select v4 tBool v5 v6
            compileFor t t expr1 v1 v2 v3 cmp return block cont
        ERangeExclStep _ e1 e2 e3 -> do
            [(t, v1), (_, v2), (_, v3)] <- mapM compileExpr [e1, e2, e3]
            v4 <- binop "icmp sgt" t v3 "0"
            let cmp v = do
                v5 <- binop "icmp slt" t v v2
                v6 <- binop "icmp sgt" t v v2
                select v4 tBool v5 v6
            compileFor t t expr1 v1 v2 v3 cmp return block cont
        otherwise -> do
            (t, v1) <- compileExpr expr2
            t' <- case t of
                TString _ -> return $ tChar
                TArray _ t' -> return $ t'
            v2 <- gep t v1 ["0"] [0] >>= load (tPtr t')
            v3 <- gep t v1 ["0"] [1] >>= load tInt
            let cmp v = binop "icmp slt" tInt v v3
            let get v = gep (tPtr t') v2 [v] [] >>= load t'
            compileFor tInt t' expr1 "0" v3 "1" cmp get block cont
    SBreak _ -> do
        (_, l) <- asks (M.! "#break")
        goto l
    SContinue _ -> do
        (_, l) <- asks (M.! "#continue")
        goto l
    where
        compileFunc name args rt block cont = do
            let as = map (\(ANoDef _ t _) -> reduceType t) args
            let r = reduceType rt
            let t = tFunc as r
            s <- getScope
            let f = do
                if block == Nothing then "@" ++ name
                else (if s /= "@main" then s else "@") ++ "." ++ [if c == '\'' then '-' else c | c <- name]
            p <- global t f
            local (M.insert name (t, p)) $ do
                case block of
                    Just b -> define t f $ compileArgs args 0 $ local (M.insert "#return" (r, "")) $ do
                        l <- nextLabel
                        goto l >> label l
                        compileBlock b
                        ret r (defaultValue r)
                    Nothing -> scope "!global" $ do
                        write $ [ "declare " ++ strType r ++ " " ++ f ++ "(" ++ intercalate ", " (map strType as) ++ ")" ]
                cont
        compileArgs args i cont = case args of
             [] -> cont
             a:as -> compileArg a i (compileArgs as (i+1) cont)
        compileArg arg i cont = case arg of
            ANoDef pos typ id -> do
                declare (reduceType typ) id ("%" ++ show i) cont
        compilePrint typ val = case typ of
            TTuple _ ts -> do
                forM_ (zip [0..] ts) $ \(i, t') -> do
                    v <- gep typ val ["0"] [i] >>= load t'
                    compilePrint t' v
                    if i == length ts - 1 then skip
                    else call tInt "@putchar" [(tChar, "32")] >> skip
            otherwise -> do
                (_, v) <- compileMethod typ "toString" [val]
                callVoid "@write" [(tString, v)]
        compileAssgs rs typ val cont = case rs of
            [] -> cont
            (t, e, i):rs -> do
                v <- gep typ val ["0"] [i] >>= load t
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
                    declare typ id val cont
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
        compileFor typ1 typ2 var start end step cmp get block cont = do
            p <- alloca typ1
            store typ1 start p
            [l1, l2, l3, l4] <- sequence (replicate 4 nextLabel)
            compileAssg typ2 var "" $ do
                goto l1 >> label l1
                v1 <- load typ1 p
                v2 <- cmp v1
                branch v2 l2 l3
                label l2
                v3 <- get v1
                compileAssg typ2 var v3 skip
                local (M.insert "#break" (tLabel, l3)) $ local (M.insert "#continue" (tLabel, l4)) $ compileBlock block
                goto l4 >> label l4
                v4 <- binop "add" typ1 v1 step
                store typ1 v4 p
                goto l1
                label l3
                cont


-- | Outputs LLVM code that evaluates a given expression. Returns type and name of the result.
compileExpr :: Expr Pos -> Run Result
compileExpr expr =
    case expr of
        EInt _ n -> return $ (tInt, show n)
        ETrue _ -> return $ (tBool, "true")
        EFalse _ -> return $ (tBool, "false")
        EChar _ c -> return $ (tChar, show (ord c))
        EString _ s -> do
            let (txts, tags) = interpolateString (read s)
            if length txts == 1 then initString (txts !! 0)
            else do
                (_, p1) <- initArray tString [] (replicate 2 (show (length txts * 2 - 1)))
                p2 <- gep (tArray tString) p1 ["0"] [0] >>= load (tPtr tString)
                forM (zip3 txts tags [0..]) $ \(txt, tag, i) -> do
                    p3 <- gep (tPtr tString) p2 [show (2*i)] []
                    (_, p4) <- initString txt
                    store tString p4 p3
                    if tag == "" then skip
                    else do
                        p5 <- gep (tPtr tString) p2 [show (2*i+1)] []
                        (_, v) <- case pExpr $ resolveLayout False $ myLexer tag of
                            Ok expr -> do
                                (t, v) <- compileExpr expr
                                compileMethod t "toString" [v]
                        store tString v p5
                (_, p7) <- initString ""
                compileMethod (tArray tString) "join" [p1, p7]
        EArray _ es -> do
            rs <- mapM compileExpr es
            case rs of
                [] -> initArray tObject [] []
                r:_ -> initArray (fst r) (map snd rs) []
        EVar _ _ -> compileRval expr
        EElem _ e n -> do
            (t, p) <- compileExpr e
            let i = fromInteger n
            case t of
                TTuple _ ts -> do
                    v <- gep t p ["0"] [i] >>= load (ts !! i)
                    return $ (ts !! i, v)
        EIndex _ _ _ -> compileRval expr
        EAttr _ _ _ -> compileRval expr
        ECall _ e es -> do
            (TFunc _ args ret, f) <- compileExpr e
            es <- case e of
                EAttr _ e' _ -> return $ e':es
                otherwise -> return $ es
            as <- forM (zip args es) $ \(t, e) -> compileExpr e
            v <- call ret f as
            return $ (ret, v)
        EMul _ e1 e2 -> compileBinary "mul" e1 e2
        EDiv _ e1 e2 -> compileBinary "sdiv" e1 e2
        EMod _ e1 e2 -> do
            (t, v1) <- compileExpr e1
            (t, v2) <- compileExpr e2
            v3 <- binop "srem" t v1 v2
            v4 <- binop "add" t v3 v2
            v5 <- binop "xor" t v1 v2
            v6 <- binop "icmp slt" t v5 "0"
            v7 <- select v6 t v4 v3
            return $ (t, v7)
        EAdd _ e1 e2 -> compileBinary "add" e1 e2
        ESub _ e1 e2 -> compileBinary "sub" e1 e2
        ENeg _ e -> compileBinary "sub" (EInt _pos 0) e
        ECmp _ cmp -> case cmp of
            Cmp1 _ e1 op e2 -> do
                (t, v1) <- compileExpr e1
                (t, v2) <- compileExpr e2
                v <- case op of
                    CmpEQ _ -> compileCmp "eq" t v1 v2
                    CmpNE _ -> compileCmp "ne" t v1 v2
                    CmpLT _ -> compileCmp "lt" t v1 v2
                    CmpLE _ -> compileCmp "le" t v1 v2
                    CmpGT _ -> compileCmp "gt" t v1 v2
                    CmpGE _ -> compileCmp "ge" t v1 v2
                return $ (tBool, v)
            Cmp2 _ e1 op cmp -> do
                e2 <- case cmp of
                    Cmp1 pos e2 _ _ -> return $ e2
                    Cmp2 pos e2 _ _ -> return $ e2
                compileExpr (EAnd _pos (ECmp _pos (Cmp1 _pos e1 op e2)) (ECmp _pos cmp))
        ENot _ e -> compileBinary "xor" (ETrue _pos) e
        EAnd _ e1 e2 -> do
            l <- nextLabel
            v <- compileAnd e1 e2 [] l
            return $ (tBool, v)
        EOr _ e1 e2 -> do
            l <- nextLabel
            v <- compileOr e1 e2 [] l
            return $ (tBool, v)
        ETuple _ es -> do
            rs <- mapM compileExpr es
            case rs of
                r:[] -> return $ r
                otherwise -> do
                    let t = tTuple (map fst rs)
                    p <- alloca (tDeref t)
                    mapM (compileTupleElem t p) (zipWith (\r i -> (fst r, snd r, i)) rs [0..])
                    return $ (t, p)
    where
        compileBinary op e1 e2 = do
            (t1, v1) <- compileExpr e1
            (t2, v2) <- compileExpr e2
            (t, v) <- case (t1, t2) of
                (TString _, TString _) -> do
                    p1 <- gep tString v1 ["0"] [0] >>= load (tPtr tChar)
                    p2 <- gep tString v2 ["0"] [0] >>= load (tPtr tChar)
                    v3 <- gep tString v1 ["0"] [1] >>= load tInt
                    v4 <- gep tString v2 ["0"] [1] >>= load tInt
                    v5 <- binop "add" tInt v3 v4
                    (_, p3) <- initArray tChar [] [v5, v5]
                    p4 <- gep tString p3 ["0"] [0] >>= load (tPtr tChar)
                    call (tPtr tChar) "@memcpy" [(tPtr tChar, p4), (tPtr tChar, p1), (tInt, v3)]
                    p5 <- gep (tPtr tChar) p4 [v3] []
                    call (tPtr tChar) "@memcpy" [(tPtr tChar, p5), (tPtr tChar, p2), (tInt, v4)]
                    return (tString, p3)
                (TString _, TInt _) -> do
                    p <- compileArrayMul tChar v1 v2
                    return $ (tString, p)
                (TInt _, TString _) -> do
                    compileBinary op e2 e1
                (TArray _ t', TInt _) -> do
                    p <- compileArrayMul t' v1 v2
                    return $ (t1, p)
                (TInt _, TArray _ _) -> do
                    compileBinary op e2 e1
                otherwise -> do
                    v3 <- binop op t1 v1 v2
                    return $ (t1, v3)
            return $ (t, v)
        compileArrayMul t' v1 v2 = do
            p1 <- gep (tArray t') v1 ["0"] [0] >>= load (tPtr t')
            v3 <- gep (tArray t') v1 ["0"] [1] >>= load tInt
            v4 <- binop "mul" tInt v3 v2
            (_, p2) <- initArray t' [] [v4, v4]
            p3 <- gep (tArray t') p2 ["0"] [0] >>= load (tPtr t')
            p4 <- alloca tInt
            p5 <- alloca tInt
            [l1, l2, l3, l4, l5, l6] <- sequence (replicate 6 nextLabel)
            store tInt "0" p4
            goto l1 >> label l1
            v5 <- load tInt p4
            v6 <- binop "icmp slt" tInt v5 v3
            branch v6 l2 l3
            label l2
            v7 <- gep (tPtr t') p1 [v5] [] >>= load t'
            do
                store tInt v5 p5
                goto l4 >> label l4
                v8 <- load tInt p5
                v9 <- binop "icmp slt" tInt v8 v4
                branch v9 l5 l6
                label l5
                gep (tPtr t') p3 [v8] [] >>= store t' v7
                v10 <- binop "add" tInt v8 v3
                store tInt v10 p5
                goto l4
                label l6
            v11 <- binop "add" tInt v5 "1"
            store tInt v11 p4
            goto l1
            label l3
            return $ p2
        compileCmp op t v1 v2 = do
            (t, v1, v2) <- case t of
                TString _ -> do
                    (_, v3) <- compileMethod tString "compare" [v1, v2]
                    return $ (tInt, v3, "0")
                otherwise -> return $ (t, v1, v2)
            case (op, t) of
                (_, TTuple _ ts) -> do
                    lt <- nextLabel
                    lf <- nextLabel
                    compileTupleCmp op t v1 v2 0 lt lf
                ("eq", _) -> binop ("icmp " ++ op) t v1 v2
                ("ne", _) -> binop ("icmp " ++ op) t v1 v2
                (_, TBool _) -> binop ("icmp u" ++ op) t v1 v2
                otherwise -> binop ("icmp s" ++ op) t v1 v2
        compileTupleCmp op t v1 v2 i lt lf = do
            t' <- case t of
                TTuple _ ts -> return $ ts !! i
            v1' <- gep t v1 ["0"] [i] >>= load t'
            v2' <- gep t v2 ["0"] [i] >>= load t'
            v3 <- compileCmp op t' v1' v2'
            case t of
                TTuple _ ts -> do
                    if i == length ts - 1 then do
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
                                v4 <- compileCmp "eq" t' v1' v2'
                                l2 <- nextLabel
                                branch v4 l2 lf
                                label l2
                        compileTupleCmp op t v1 v2 (i+1) lt lf
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
        compileTupleElem typ ptr (t, v, i) = do
            gep typ ptr ["0"] [i] >>= store t v

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
compileAttr :: Type -> String -> Ident -> Run (Maybe Result)
compileAttr typ val (Ident attr) = do
    case typ of
        -- TODO: toString() for other types
        TInt _ -> case attr of
            "toString" -> getIdent (Ident "Int_toString")
        TBool _ -> case attr of
            "toString" -> getIdent (Ident "Bool_toString")
        TChar _ -> case attr of
            "toString" -> getIdent (Ident "Char_toString")
        TString _ -> case attr of
            "length" -> getAttr (tArray tChar) val tInt 1
            "toString" -> getIdent (Ident "String_toString")
            "toInt" -> getIdent (Ident "String_toInt")
            "compare" -> getIdent (Ident "String_compare")
        TArray _ t' -> case (t', attr) of
            (_, "length") -> getAttr typ val tInt 1
            (TChar _, "join") -> getIdent (Ident "CharArray_join")
            (TString _, "join") -> getIdent (Ident "StringArray_join")
    where
        getAttr typ1 obj typ2 idx = do
            p <- gep typ1 obj ["0"] [idx]
            return $ Just (typ2, p)

-- | Outputs LLVM code that calls a method with given arguments. Returns type and name of the result.
compileMethod :: Type -> String -> [String] -> Run Result
compileMethod typ func args = do
    Just (t, p1) <- compileAttr typ "" (Ident func)
    let TFunc _ as r = t
    p2 <- load t p1
    v <- call r p2 (zip as args)
    return $ (r, v)
