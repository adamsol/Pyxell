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
        "@s = internal constant [5 x i8] c\"%.*s\\00\"",
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
        write $ indent [ "%s = getelementptr [5 x i8], [5 x i8]* @s, i32 0, i32 0" ]
        call tInt "@printf" [(tPtr tChar, "%s"), (tInt, v), (tPtr tChar, p)]
        ret tVoid ""

    ask
