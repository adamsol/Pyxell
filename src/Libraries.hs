
module Libraries where

import Control.Monad.Trans.Reader

import AbsPyxell

import CodeGen
import Utils


libBase :: Run Env
libBase = do
    write $ [
        "@format.sw = internal constant [5 x i8] c\"%.*s\\00\"",
        "@format.sr = internal constant [7 x i8] c\"%1000s\\00\"",
        "@format.srl = internal constant [13 x i8] c\"%1000[^\\0A]%*c\\00\"",
        "@format.d = internal constant [5 x i8] c\"%lld\\00\"",
        "@format.fw = internal constant [6 x i8] c\"%.15g\\00\"",
        "@format.fr = internal constant [4 x i8] c\"%lg\\00\"",
        "@format.bt = internal constant [5 x i8] c\"true\\00\"",
        "@format.bf = internal constant [6 x i8] c\"false\\00\"",
        "@format.c = internal constant [3 x i8] c\"%c\\00\"",
        "",
        "declare i64 @printf(i8*, ...)",
        "declare i64 @scanf(i8*, ...)",
        "declare i64 @sprintf(i8*, i8*, ...)",
        "declare i64 @sscanf(i8*, i8*, ...)",
        "declare i64 @strlen(i8*)",
        "declare i8* @strncpy(i8*, i8*, i64)",
        "declare void @free(i8*)",
        "" ]

    -- Char <-> Int (ASCII)
    define (tFunc [tChar] tInt) (Ident "ord") $ do
        v <- zext tChar tInt "%0"
        ret tInt v
    define (tFunc [tInt] tChar) (Ident "chr") $ do
        v <- trunc tInt tChar "%0"
        ret tChar v

    -- [Char] <-> String
    define (tFunc [tArray tChar] tString) (Ident "CharArray_asString") $ do
        ret tString "%0"
    define (tFunc [tString] (tArray tChar)) (Ident "String_toArray") $ do
        p1 <- gep tString "%0" ["0"] [0] >>= load (tPtr tChar)
        v <- gep tString "%0" ["0"] [1] >>= load tInt
        p2 <- initArray tChar [] [v]
        p3 <- gep tString p2 ["0"] [0] >>= load (tPtr tChar)
        call (tPtr tChar) "@memcpy" [(tPtr tChar, p3), (tPtr tChar, p1), (tInt, v)]
        ret (tArray tChar) p2

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
    define (tFunc [tInt] tVoid) (Ident "writeInt") $ do
        format "d" 5 >>= \f -> call tInt "(i8*, ...) @printf" [(tPtr tChar, f), (tInt, "%0")]
        retVoid
    define (tFunc [tFloat] tVoid) (Ident "writeFloat") $ do
        format "fw" 6 >>= \f -> call tInt "(i8*, ...) @printf" [(tPtr tChar, f), (tFloat, "%0")]
        retVoid
    define (tFunc [tBool] tVoid) (Ident "writeBool") $ do
        f1 <- format "bt" 5
        f2 <- format "bf" 6
        f <- select "%0" (tPtr tChar) f1 f2
        call tInt "(i8*, ...) @printf" [(tPtr tChar, f)]
        retVoid
    define (tFunc [tChar] tVoid) (Ident "writeChar") $ do
        format "c" 3 >>= \f -> call tInt "(i8*, ...) @printf" [(tPtr tChar, f), (tChar, "%0")]
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
        load tInt p >>= ret tInt
    define (tFunc [] tChar) (Ident "readChar") $ do
        p <- alloca tChar
        format "c" 3 >>= scanf tChar p
        load tChar p >>= ret tChar

    -- Conversions to/from string
    define (tFunc [tInt] tString) (Ident "Int_toString") $ do
        p1 <- initArray tChar [] ["21"]
        p2 <- gep tString p1 ["0"] [0] >>= load (tPtr tChar)
        format "d" 5 >>= sprintf tInt p2
        v <- call tInt "@strlen" [(tPtr tChar, p2)]
        gep tString p1 ["0"] [1] >>= store tInt v
        ret tString p1
    define (tFunc [tFloat, tInt] tString) (Ident "Float_toString") $ do
        p1 <- initArray tChar [] ["25"]
        p2 <- gep tString p1 ["0"] [0] >>= load (tPtr tChar)
        format "fw" 6 >>= sprintf tFloat p2
        v <- call tInt "@strlen" [(tPtr tChar, p2)]
        gep tString p1 ["0"] [1] >>= store tInt v
        ret tString p1
    define (tFunc [tString] tInt) (Ident "String_toInt") $ do
        p1 <- alloca tInt
        p2 <- gep tString "%0" ["0"] [0] >>= load (tPtr tChar)
        -- sscanf needs a null-terminated string, so we have to copy it and append \0
        v1 <- gep tString "%0" ["0"] [1] >>= load tInt
        v2 <- binop "add" tInt v1 "1"
        p3 <- call (tPtr tChar) "@malloc" [(tInt, v2)]
        call (tPtr tChar) "@strncpy" [(tPtr tChar, p3), (tPtr tChar, p2), (tInt, v1)]
        gep (tPtr tChar) p3 [v1] [] >>= store tChar "0"
        format "d" 5 >>= sscanf tInt p1 p3
        callVoid "@free" [(tPtr tChar, p3)]
        load tInt p1 >>= ret tInt
    define (tFunc [tString] tFloat) (Ident "String_toFloat") $ do
        p1 <- alloca tFloat
        p2 <- gep tString "%0" ["0"] [0] >>= load (tPtr tChar)
        -- sscanf needs a null-terminated string, so we have to copy it and append \0
        v1 <- gep tString "%0" ["0"] [1] >>= load tInt
        v2 <- binop "add" tInt v1 "1"
        p3 <- call (tPtr tChar) "@malloc" [(tInt, v2)]
        call (tPtr tChar) "@strncpy" [(tPtr tChar, p3), (tPtr tChar, p2), (tInt, v1)]
        gep (tPtr tChar) p3 [v1] [] >>= store tChar "0"
        format "fr" 4 >>= sscanf tFloat p1 p3
        callVoid "@free" [(tPtr tChar, p3)]
        load tFloat p1 >>= ret tFloat

    -- Numeric conversions
    define (tFunc [tInt] tFloat) (Ident "Int_toFloat") $ do
        sitofp "%0" >>= ret tFloat
    define (tFunc [tFloat] tInt) (Ident "Float_toInt") $ do
        fptosi "%0" >>= ret tInt

    ask

    where
        format f n = gep (tPtr (tArr n tChar)) ("@format." ++ f) [] [0, 0]
        scanf t s f = call tInt "(i8*, ...) @scanf" [(tPtr tChar, f), (tPtr t, s)]
        sprintf t s f = call tInt "(i8*, i8*, ...) @sprintf" [(tPtr tChar, s), (tPtr tChar, f), (t, "%0")]
        sscanf t p s f = call tInt "(i8*, i8*, ...) @sscanf" [(tPtr tChar, s), (tPtr tChar, f), (tPtr t, p)]


libMath :: Run Env
libMath = do
    write $ [
        "declare double @exp(double)",
        "declare double @log(double)",
        "declare double @log10(double)",
        "declare double @pow(double, double)",
        "declare double @sqrt(double)",
        "",
        "declare double @cos(double)",
        "declare double @sin(double)",
        "declare double @tan(double)",
        "",
        "declare double @acos(double)",
        "declare double @asin(double)",
        "declare double @atan(double)",
        "declare double @atan2(double, double)",
        "",
        "declare double @floor(double)",
        "declare double @ceil(double)",
        "declare double @trunc(double)",
        "" ]

    define (tFunc [tFloat] tFloat) (Ident "exp") $ do
        call tFloat "@exp" [(tFloat, "%0")] >>= ret tFloat
    define (tFunc [tFloat] tFloat) (Ident "log") $ do
        call tFloat "@log" [(tFloat, "%0")] >>= ret tFloat
    define (tFunc [tFloat] tFloat) (Ident "log10") $ do
        call tFloat "@log10" [(tFloat, "%0")] >>= ret tFloat
    define (tFunc [tFloat, tFloat] tFloat) (Ident "Float_pow") $ do
        call tFloat "@pow" [(tFloat, "%0"), (tFloat, "%1")] >>= ret tFloat
    define (tFunc [tFloat] tFloat) (Ident "sqrt") $ do
        call tFloat "@sqrt" [(tFloat, "%0")] >>= ret tFloat

    define (tFunc [tFloat] tFloat) (Ident "cos") $ do
        call tFloat "@cos" [(tFloat, "%0")] >>= ret tFloat
    define (tFunc [tFloat] tFloat) (Ident "sin") $ do
        call tFloat "@sin" [(tFloat, "%0")] >>= ret tFloat
    define (tFunc [tFloat] tFloat) (Ident "tan") $ do
        call tFloat "@tan" [(tFloat, "%0")] >>= ret tFloat

    define (tFunc [tFloat] tFloat) (Ident "acos") $ do
        call tFloat "@acos" [(tFloat, "%0")] >>= ret tFloat
    define (tFunc [tFloat] tFloat) (Ident "asin") $ do
        call tFloat "@asin" [(tFloat, "%0")] >>= ret tFloat
    define (tFunc [tFloat] tFloat) (Ident "atan") $ do
        call tFloat "@atan" [(tFloat, "%0")] >>= ret tFloat
    define (tFunc [tFloat, tFloat] tFloat) (Ident "atan2") $ do
        call tFloat "@atan2" [(tFloat, "%0"), (tFloat, "%1")] >>= ret tFloat

    define (tFunc [tFloat] tFloat) (Ident "floor") $ do
        call tFloat "@floor" [(tFloat, "%0")] >>= ret tFloat
    define (tFunc [tFloat] tFloat) (Ident "ceil") $ do
        call tFloat "@ceil" [(tFloat, "%0")] >>= ret tFloat
    define (tFunc [tFloat] tFloat) (Ident "trunc") $ do
        call tFloat "@trunc" [(tFloat, "%0")] >>= ret tFloat

    ask


libTime :: Run Env
libTime = do
    write $ [
        "declare i64 @time(i64*)",
        "" ]

    define (tFunc [] tInt) (Ident "time") $ do
        call tInt "@time" [(tPtr tInt, "null")] >>= ret tInt

    ask


libRandom :: Run Env
libRandom = do
    write $ [
        "declare void @srand(i64)",
        "declare i64 @rand()",
        "" ]

    define (tFunc [tInt] tVoid) (Ident "seed") $ do
        callVoid "@srand" [(tInt, "%0")] >> retVoid

    define (tFunc [] tInt) (Ident "rand") $ do
        call tInt "@rand" [] >>= ret tInt

    ask
