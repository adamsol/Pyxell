{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}
{-# LANGUAGE FlexibleInstances #-}

module Libraries where

import Control.Monad.Trans.Reader

import AbsPyxell

import CodeGen
import Utils


libBase :: Run Env
libBase = do
    write $ [ "",
        "@format.sw = internal constant [5 x i8] c\"%.*s\\00\"",
        "@format.sr = internal constant [7 x i8] c\"%1000s\\00\"",
        "@format.srl = internal constant [13 x i8] c\"%1000[^\\0A]%*c\\00\"",
        "@format.d = internal constant [5 x i8] c\"%lld\\00\"",
        "@format.c = internal constant [3 x i8] c\"%c\\00\"",
        "",
        "declare i64 @printf(i8*, ...)",
        "declare i64 @scanf(i8*, ...)",
        "declare i64 @strlen(i8*)",
        "" ]

    -- Char <-> Int (ASCII)
    define (tFunc [tChar] tInt) (Ident "ord") $ do
        v <- zext tChar tInt "%0"
        ret tInt v
    define (tFunc [tInt] tChar) (Ident "chr") $ do
        v <- trunc tInt tChar "%0"
        ret tChar v

    -- [Char] to String
    define (tFunc [tArray tChar] tString) (Ident "str") $ do
        p1 <- gep tString "%0" ["0"] [0] >>= load (tPtr tChar)
        v <- gep tString "%0" ["0"] [1] >>= load tInt
        p2 <- initArray tChar [] [v]
        p3 <- gep tString p2 ["0"] [0] >>= load (tPtr tChar)
        call (tPtr tChar) "@memcpy" [(tPtr tChar, p3), (tPtr tChar, p1), (tInt, v)]
        ret tString p2

    -- Standard output
    define (tFunc [tString] tVoid) (Ident "write") $ do
        p <- gep tString "%0" ["0"] [0] >>= load (tPtr tChar)
        v <- gep tString "%0" ["0"] [1] >>= load tInt
        format "sw" 5 >>= \f -> call tInt "(i8*, ...) @printf" [(tPtr tChar, f), (tInt, v), (tPtr tChar, p)]
        retVoid
    define (tFunc [tString] tVoid) (Ident "writeLine") $ do
        callVoid "@func.write" [(tString, "%0")]
        call tInt "@putchar" [(tChar, "10")]
        retVoid

    -- Standard input
    define (tFunc [] tString) (Ident "read") $ do
        p1 <- initArray tChar [] ["1001"]
        p2 <- gep tString p1 ["0"] [0] >>= load (tPtr tChar)
        format "sr" 7 >>= scanf tChar p2
        v <- call tInt "@strlen" [(tPtr tChar, p2)]
        gep tString p1 ["0"] [1] >>= store tInt v
        ret tString p1
    define (tFunc [] tString) (Ident "readLine") $ do
        p1 <- initArray tChar [] ["1001"]
        p2 <- gep tString p1 ["0"] [0] >>= load (tPtr tChar)
        format "srl" 13 >>= scanf tChar p2
        v <- call tInt "@strlen" [(tPtr tChar, p2)]
        gep tString p1 ["0"] [1] >>= store tInt v
        ret tString p1
    define (tFunc [] tInt) (Ident "readInt") $ do
        p <- alloca tInt
        format "d" 5 >>= scanf tInt p
        v <- load tInt p
        ret tInt v
    define (tFunc [] tChar) (Ident "readChar") $ do
        p <- alloca tChar
        format "c" 3 >>= scanf tChar p
        v <- load tChar p
        ret tChar v

    ask

    where
        format f n = gep (tPtr (tArr n tChar)) ("@format." ++ f) [] [0, 0]
        scanf t p f = call tInt "(i8*, ...) @scanf" [(tPtr tChar, f), (tPtr t, p)]
