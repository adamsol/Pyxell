{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}
{-# LANGUAGE FlexibleInstances #-}

module Libraries where

import Control.Monad.Trans.Class
import Control.Monad.Trans.State
import qualified Data.Map as M

import CodeGen
import Utils


libInternal :: Run ()
libInternal = do
    write $ [ "",
        "@s = internal constant [3 x i8] c\"%s\\00\"",
        "",
        "declare i8* @malloc(i64)", "declare i8* @memcpy(i8*, i8*, i64)",
        "declare i8* @strcpy(i8*, i8*)", "declare i64 @strcmp(i8*, i8*)",
        "declare i64 @putchar(i8)", "declare i64 @printf(i8*, i8*)",
        "" ]
    lift $ modify (M.insert "$number" (Number 0))

    -- Char <-> Int (ASCII)
    define (tFunc [tChar] tInt) "@ord" $ do
        v <- zext tChar tInt "%0"
        ret tInt v
    define (tFunc [tInt] tChar) "@chr" $ do
        v <- trunc tInt tChar "%0"
        ret tChar v

    -- [Char] to String
    define (tFunc [tArray tChar] tString) "@str" $ do
        p1 <- gep tString "%0" ["0"] [0] >>= load (tPtr tChar)
        v1 <- gep tString "%0" ["0"] [1] >>= load tInt
        v2 <- binop "add" tInt v1 "1"
        (_, p2) <- initArray tChar [] [v1, v2]
        p3 <- gep tString p2 ["0"] [0] >>= load (tPtr tChar)
        call (tPtr tChar) "@memcpy" [(tPtr tChar, p3), (tPtr tChar, p1), (tInt, v1)]
        gep (tPtr tChar) p3 [v1] [] >>= store tChar "0"
        ret tString p2

    -- Standard output
    define (tFunc [tString] tVoid) "@write" $ do
        p <- gep tString "%0" ["0"] [0] >>= load (tPtr tChar)
        write $ indent [ "%s = getelementptr [3 x i8], [3 x i8]* @s, i32 0, i32 0" ]
        call tInt "@printf" [(tPtr tChar, "%s"), (tPtr tChar, p)]
        ret tVoid ""
    define (tFunc [] tVoid) "@writeLn" $ do
        call tInt "@putchar" [(tChar, "10")]
        ret tVoid ""
