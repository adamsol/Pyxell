; ModuleID = ""
target triple = "unknown-unknown-unknown"
target datalayout = ""

@"format" = constant [5 x i8] [i8 37, i8 108, i8 108, i8 100, i8 0]
@"format.1" = constant [4 x i8] [i8 37, i8 108, i8 103, i8 0]
@"format.2" = constant [6 x i8] [i8 37, i8 46, i8 49, i8 53, i8 103, i8 0]
@"format.3" = constant [7 x i8] [i8 37, i8 46, i8 48, i8 102, i8 46, i8 48, i8 0]
@"format.4" = constant [5 x i8] [i8 116, i8 114, i8 117, i8 101, i8 0]
@"format.5" = constant [6 x i8] [i8 102, i8 97, i8 108, i8 115, i8 101, i8 0]
@"format.6" = constant [3 x i8] [i8 37, i8 99, i8 0]
@"format.7" = constant [7 x i8] [i8 37, i8 49, i8 48, i8 50, i8 51, i8 115, i8 0]
@"format.8" = constant [13 x i8] [i8 37, i8 49, i8 48, i8 50, i8 51, i8 91, i8 94, i8 10, i8 93, i8 37, i8 42, i8 99, i8 0]
@"format.9" = constant [5 x i8] [i8 37, i8 46, i8 42, i8 115, i8 0]
declare void @"free"(i8* %".1") 

declare i8* @"malloc"(i64 %".1") 

declare void @"memcpy"(i8* %".1", i8* %".2", i64 %".3") 

declare i64 @"printf"(i8* %".1", ...) 

declare void @"putchar"(i8 %".1") 

declare i64 @"scanf"(i8* %".1", ...) 

declare i64 @"sprintf"(i8* %".1", i8* %".2", ...) 

declare i64 @"sscanf"(i8* %".1", i8* %".2", ...) 

declare i64 @"strlen"(i8* %".1", ...) 

declare i8* @"strncpy"(i8* %".1", i8* %".2", i64 %".3") 

declare double @"exp"(double %".1") 

declare double @"log"(double %".1") 

declare double @"log10"(double %".1") 

declare double @"pow"(double %".1", double %".2") 

declare double @"sqrt"(double %".1") 

declare double @"cos"(double %".1") 

declare double @"sin"(double %".1") 

declare double @"tan"(double %".1") 

declare double @"acos"(double %".1") 

declare double @"asin"(double %".1") 

declare double @"atan"(double %".1") 

declare double @"atan2"(double %".1", double %".2") 

declare double @"fabs"(double %".1") 

declare double @"ceil"(double %".1") 

declare double @"floor"(double %".1") 

declare double @"trunc"(double %".1") 

declare i64 @"time"(i64* %".1") 

define {i8*, i64}* @"def.CharArray_asString"({i8*, i64}* %".1") 
{
entry:
  ret {i8*, i64}* %".1"
}

@"f.CharArray_asString" = global {i8*, i64}* ({i8*, i64}*)* @"def.CharArray_asString"
define {i8*, i64}* @"def.String_toArray"({i8*, i64}* %".1") 
{
entry:
  %".3" = getelementptr {i8*, i64}, {i8*, i64}* %".1", i64 0, i32 1
  %".4" = load i64, i64* %".3"
  %".5" = getelementptr i8, i8* null, i64 %".4"
  %".6" = ptrtoint i8* %".5" to i64
  %".7" = call i8* @"malloc"(i64 %".6")
  %".8" = getelementptr {i8*, i64}, {i8*, i64}* null, i64 1
  %".9" = ptrtoint {i8*, i64}* %".8" to i64
  %".10" = call i8* @"malloc"(i64 %".9")
  %".11" = bitcast i8* %".10" to {i8*, i64}*
  %".12" = getelementptr {i8*, i64}, {i8*, i64}* %".11", i64 0, i32 0
  store i8* %".7", i8** %".12"
  %".14" = getelementptr {i8*, i64}, {i8*, i64}* %".11", i64 0, i32 1
  store i64 %".4", i64* %".14"
  %".16" = getelementptr {i8*, i64}, {i8*, i64}* %".11", i64 0, i32 0
  %".17" = load i8*, i8** %".16"
  %".18" = getelementptr {i8*, i64}, {i8*, i64}* %".1", i64 0, i32 0
  %".19" = load i8*, i8** %".18"
  call void @"memcpy"(i8* %".17", i8* %".19", i64 %".4")
  ret {i8*, i64}* %".11"
}

@"f.String_toArray" = global {i8*, i64}* ({i8*, i64}*)* @"def.String_toArray"
define void @"def.write"({i8*, i64}* %".1") 
{
entry:
  %".3" = getelementptr [5 x i8], [5 x i8]* @"format.9", i64 0, i64 0
  %".4" = getelementptr {i8*, i64}, {i8*, i64}* %".1", i64 0, i32 1
  %".5" = load i64, i64* %".4"
  %".6" = getelementptr {i8*, i64}, {i8*, i64}* %".1", i64 0, i32 0
  %".7" = load i8*, i8** %".6"
  %".8" = call i64 (i8*, ...) @"printf"(i8* %".3", i64 %".5", i8* %".7")
  ret void
}

@"f.write" = global void ({i8*, i64}*)* @"def.write"
define void @"def.writeLine"({i8*, i64}* %".1") 
{
entry:
  %".3" = getelementptr [5 x i8], [5 x i8]* @"format.9", i64 0, i64 0
  %".4" = getelementptr {i8*, i64}, {i8*, i64}* %".1", i64 0, i32 1
  %".5" = load i64, i64* %".4"
  %".6" = getelementptr {i8*, i64}, {i8*, i64}* %".1", i64 0, i32 0
  %".7" = load i8*, i8** %".6"
  %".8" = call i64 (i8*, ...) @"printf"(i8* %".3", i64 %".5", i8* %".7")
  call void @"putchar"(i8 10)
  ret void
}

@"f.writeLine" = global void ({i8*, i64}*)* @"def.writeLine"
define void @"def.writeInt"(i64 %".1") 
{
entry:
  %".3" = getelementptr [5 x i8], [5 x i8]* @"format", i64 0, i64 0
  %".4" = call i64 (i8*, ...) @"printf"(i8* %".3", i64 %".1")
  ret void
}

@"f.writeInt" = global void (i64)* @"def.writeInt"
define void @"def.writeFloat"(double %".1") 
{
entry:
  %".3" = call double @"fabs"(double %".1")
  %".4" = fcmp olt double %".3", 0x430c6bf526340000
  %".5" = call double @"floor"(double %".1")
  %".6" = fcmp oeq double %".1", %".5"
  %".7" = and i1 %".4", %".6"
  br i1 %".7", label %"entry.if", label %"entry.else"
entry.if:
  %".9" = getelementptr [7 x i8], [7 x i8]* @"format.3", i64 0, i64 0
  %".10" = call i64 (i8*, ...) @"printf"(i8* %".9", double %".1")
  br label %"entry.endif"
entry.else:
  %".12" = getelementptr [6 x i8], [6 x i8]* @"format.2", i64 0, i64 0
  %".13" = call i64 (i8*, ...) @"printf"(i8* %".12", double %".1")
  br label %"entry.endif"
entry.endif:
  ret void
}

@"f.writeFloat" = global void (double)* @"def.writeFloat"
define void @"def.writeBool"(i1 %".1") 
{
entry:
  %".3" = getelementptr [5 x i8], [5 x i8]* @"format.4", i64 0, i64 0
  %".4" = getelementptr [6 x i8], [6 x i8]* @"format.5", i64 0, i64 0
  %".5" = select i1 %".1", i8* %".3", i8* %".4"
  %".6" = call i64 (i8*, ...) @"printf"(i8* %".5")
  ret void
}

@"f.writeBool" = global void (i1)* @"def.writeBool"
define void @"def.writeChar"(i8 %".1") 
{
entry:
  %".3" = getelementptr [3 x i8], [3 x i8]* @"format.6", i64 0, i64 0
  %".4" = call i64 (i8*, ...) @"printf"(i8* %".3", i8 %".1")
  ret void
}

@"f.writeChar" = global void (i8)* @"def.writeChar"
define {i8*, i64}* @"def.read"() 
{
entry:
  %".2" = getelementptr i8, i8* null, i64 1024
  %".3" = ptrtoint i8* %".2" to i64
  %".4" = call i8* @"malloc"(i64 %".3")
  %".5" = getelementptr {i8*, i64}, {i8*, i64}* null, i64 1
  %".6" = ptrtoint {i8*, i64}* %".5" to i64
  %".7" = call i8* @"malloc"(i64 %".6")
  %".8" = bitcast i8* %".7" to {i8*, i64}*
  %".9" = getelementptr {i8*, i64}, {i8*, i64}* %".8", i64 0, i32 0
  store i8* %".4", i8** %".9"
  %".11" = getelementptr {i8*, i64}, {i8*, i64}* %".8", i64 0, i32 1
  store i64 1024, i64* %".11"
  %".13" = getelementptr {i8*, i64}, {i8*, i64}* %".8", i64 0, i32 0
  %".14" = load i8*, i8** %".13"
  %".15" = getelementptr [7 x i8], [7 x i8]* @"format.7", i64 0, i64 0
  %".16" = call i64 (i8*, ...) @"scanf"(i8* %".15", i8* %".14")
  %".17" = call i64 (i8*, ...) @"strlen"(i8* %".14")
  %".18" = getelementptr {i8*, i64}, {i8*, i64}* %".8", i64 0, i32 1
  store i64 %".17", i64* %".18"
  ret {i8*, i64}* %".8"
}

@"f.read" = global {i8*, i64}* ()* @"def.read"
define {i8*, i64}* @"def.readLine"() 
{
entry:
  %".2" = getelementptr i8, i8* null, i64 1024
  %".3" = ptrtoint i8* %".2" to i64
  %".4" = call i8* @"malloc"(i64 %".3")
  %".5" = getelementptr {i8*, i64}, {i8*, i64}* null, i64 1
  %".6" = ptrtoint {i8*, i64}* %".5" to i64
  %".7" = call i8* @"malloc"(i64 %".6")
  %".8" = bitcast i8* %".7" to {i8*, i64}*
  %".9" = getelementptr {i8*, i64}, {i8*, i64}* %".8", i64 0, i32 0
  store i8* %".4", i8** %".9"
  %".11" = getelementptr {i8*, i64}, {i8*, i64}* %".8", i64 0, i32 1
  store i64 1024, i64* %".11"
  %".13" = getelementptr {i8*, i64}, {i8*, i64}* %".8", i64 0, i32 0
  %".14" = load i8*, i8** %".13"
  %".15" = getelementptr [13 x i8], [13 x i8]* @"format.8", i64 0, i64 0
  %".16" = call i64 (i8*, ...) @"scanf"(i8* %".15", i8* %".14")
  %".17" = call i64 (i8*, ...) @"strlen"(i8* %".14")
  %".18" = getelementptr {i8*, i64}, {i8*, i64}* %".8", i64 0, i32 1
  store i64 %".17", i64* %".18"
  ret {i8*, i64}* %".8"
}

@"f.readLine" = global {i8*, i64}* ()* @"def.readLine"
define i64 @"def.readInt"() 
{
entry:
  %".2" = alloca i64
  %".3" = getelementptr [5 x i8], [5 x i8]* @"format", i64 0, i64 0
  %".4" = bitcast i64* %".2" to i8*
  %".5" = call i64 (i8*, ...) @"scanf"(i8* %".3", i8* %".4")
  %".6" = load i64, i64* %".2"
  ret i64 %".6"
}

@"f.readInt" = global i64 ()* @"def.readInt"
define double @"def.readFloat"() 
{
entry:
  %".2" = alloca double
  %".3" = getelementptr [4 x i8], [4 x i8]* @"format.1", i64 0, i64 0
  %".4" = bitcast double* %".2" to i8*
  %".5" = call i64 (i8*, ...) @"scanf"(i8* %".3", i8* %".4")
  %".6" = load double, double* %".2"
  ret double %".6"
}

@"f.readFloat" = global double ()* @"def.readFloat"
define i8 @"def.readChar"() 
{
entry:
  %".2" = alloca i8
  %".3" = getelementptr [3 x i8], [3 x i8]* @"format.6", i64 0, i64 0
  %".4" = call i64 (i8*, ...) @"scanf"(i8* %".3", i8* %".2")
  %".5" = load i8, i8* %".2"
  ret i8 %".5"
}

@"f.readChar" = global i8 ()* @"def.readChar"
define double @"def.Int_toFloat"(i64 %".1") 
{
entry:
  %".3" = sitofp i64 %".1" to double
  ret double %".3"
}

@"f.Int_toFloat" = global double (i64)* @"def.Int_toFloat"
define i64 @"def.Float_toInt"(double %".1") 
{
entry:
  %".3" = fptosi double %".1" to i64
  ret i64 %".3"
}

@"f.Float_toInt" = global i64 (double)* @"def.Float_toInt"
define {i8*, i64}* @"def.Int_toString"(i64 %".1") 
{
entry:
  %".3" = getelementptr i8, i8* null, i64 21
  %".4" = ptrtoint i8* %".3" to i64
  %".5" = call i8* @"malloc"(i64 %".4")
  %".6" = getelementptr {i8*, i64}, {i8*, i64}* null, i64 1
  %".7" = ptrtoint {i8*, i64}* %".6" to i64
  %".8" = call i8* @"malloc"(i64 %".7")
  %".9" = bitcast i8* %".8" to {i8*, i64}*
  %".10" = getelementptr {i8*, i64}, {i8*, i64}* %".9", i64 0, i32 0
  store i8* %".5", i8** %".10"
  %".12" = getelementptr {i8*, i64}, {i8*, i64}* %".9", i64 0, i32 1
  store i64 21, i64* %".12"
  %".14" = getelementptr {i8*, i64}, {i8*, i64}* %".9", i64 0, i32 0
  %".15" = load i8*, i8** %".14"
  %".16" = getelementptr [5 x i8], [5 x i8]* @"format", i64 0, i64 0
  %".17" = call i64 (i8*, i8*, ...) @"sprintf"(i8* %".15", i8* %".16", i64 %".1")
  %".18" = call i64 (i8*, ...) @"strlen"(i8* %".15")
  %".19" = getelementptr {i8*, i64}, {i8*, i64}* %".9", i64 0, i32 1
  store i64 %".18", i64* %".19"
  ret {i8*, i64}* %".9"
}

@"f.Int_toString" = global {i8*, i64}* (i64)* @"def.Int_toString"
define {i8*, i64}* @"def.Float_toString"(double %".1") 
{
entry:
  %".3" = getelementptr i8, i8* null, i64 25
  %".4" = ptrtoint i8* %".3" to i64
  %".5" = call i8* @"malloc"(i64 %".4")
  %".6" = getelementptr {i8*, i64}, {i8*, i64}* null, i64 1
  %".7" = ptrtoint {i8*, i64}* %".6" to i64
  %".8" = call i8* @"malloc"(i64 %".7")
  %".9" = bitcast i8* %".8" to {i8*, i64}*
  %".10" = getelementptr {i8*, i64}, {i8*, i64}* %".9", i64 0, i32 0
  store i8* %".5", i8** %".10"
  %".12" = getelementptr {i8*, i64}, {i8*, i64}* %".9", i64 0, i32 1
  store i64 25, i64* %".12"
  %".14" = getelementptr {i8*, i64}, {i8*, i64}* %".9", i64 0, i32 0
  %".15" = load i8*, i8** %".14"
  %".16" = call double @"fabs"(double %".1")
  %".17" = fcmp olt double %".16", 0x430c6bf526340000
  %".18" = call double @"floor"(double %".1")
  %".19" = fcmp oeq double %".1", %".18"
  %".20" = and i1 %".17", %".19"
  br i1 %".20", label %"entry.if", label %"entry.else"
entry.if:
  %".22" = getelementptr [7 x i8], [7 x i8]* @"format.3", i64 0, i64 0
  %".23" = call i64 (i8*, i8*, ...) @"sprintf"(i8* %".15", i8* %".22", double %".1")
  br label %"entry.endif"
entry.else:
  %".25" = getelementptr [6 x i8], [6 x i8]* @"format.2", i64 0, i64 0
  %".26" = call i64 (i8*, i8*, ...) @"sprintf"(i8* %".15", i8* %".25", double %".1")
  br label %"entry.endif"
entry.endif:
  %".28" = call i64 (i8*, ...) @"strlen"(i8* %".15")
  %".29" = getelementptr {i8*, i64}, {i8*, i64}* %".9", i64 0, i32 1
  store i64 %".28", i64* %".29"
  ret {i8*, i64}* %".9"
}

@"f.Float_toString" = global {i8*, i64}* (double)* @"def.Float_toString"
define i64 @"def.String_toInt"({i8*, i64}* %".1") 
{
entry:
  %".3" = getelementptr {i8*, i64}, {i8*, i64}* %".1", i64 0, i32 1
  %".4" = load i64, i64* %".3"
  %".5" = add i64 %".4", 1
  %".6" = call i8* @"malloc"(i64 %".5")
  %".7" = getelementptr {i8*, i64}, {i8*, i64}* %".1", i64 0, i32 0
  %".8" = load i8*, i8** %".7"
  %".9" = call i8* @"strncpy"(i8* %".6", i8* %".8", i64 %".4")
  %".10" = getelementptr i8, i8* %".6", i64 %".4"
  store i8 0, i8* %".10"
  %".12" = alloca i64
  %".13" = getelementptr [5 x i8], [5 x i8]* @"format", i64 0, i64 0
  %".14" = bitcast i64* %".12" to i8*
  %".15" = call i64 (i8*, i8*, ...) @"sscanf"(i8* %".6", i8* %".13", i8* %".14")
  call void @"free"(i8* %".6")
  %".17" = load i64, i64* %".12"
  ret i64 %".17"
}

@"f.String_toInt" = global i64 ({i8*, i64}*)* @"def.String_toInt"
define double @"def.String_toFloat"({i8*, i64}* %".1") 
{
entry:
  %".3" = getelementptr {i8*, i64}, {i8*, i64}* %".1", i64 0, i32 1
  %".4" = load i64, i64* %".3"
  %".5" = add i64 %".4", 1
  %".6" = call i8* @"malloc"(i64 %".5")
  %".7" = getelementptr {i8*, i64}, {i8*, i64}* %".1", i64 0, i32 0
  %".8" = load i8*, i8** %".7"
  %".9" = call i8* @"strncpy"(i8* %".6", i8* %".8", i64 %".4")
  %".10" = getelementptr i8, i8* %".6", i64 %".4"
  store i8 0, i8* %".10"
  %".12" = alloca double
  %".13" = getelementptr [4 x i8], [4 x i8]* @"format.1", i64 0, i64 0
  %".14" = bitcast double* %".12" to i8*
  %".15" = call i64 (i8*, i8*, ...) @"sscanf"(i8* %".6", i8* %".13", i8* %".14")
  call void @"free"(i8* %".6")
  %".17" = load double, double* %".12"
  ret double %".17"
}

@"f.String_toFloat" = global double ({i8*, i64}*)* @"def.String_toFloat"
@"f.Float_pow" = global double (double, double)* @"pow"
@"f.exp" = global double (double)* @"exp"
@"f.log" = global double (double)* @"log"
@"f.log10" = global double (double)* @"log10"
@"f.sqrt" = global double (double)* @"sqrt"
@"f.cos" = global double (double)* @"cos"
@"f.sin" = global double (double)* @"sin"
@"f.tan" = global double (double)* @"tan"
@"f.acos" = global double (double)* @"acos"
@"f.asin" = global double (double)* @"asin"
@"f.atan" = global double (double)* @"atan"
@"f.atan2" = global double (double, double)* @"atan2"
@"f.ceil" = global double (double)* @"ceil"
@"f.floor" = global double (double)* @"floor"
@"f.trunc" = global double (double)* @"trunc"
define i64 @"def.time"(double %".1") 
{
entry:
  %".3" = call i64 @"time"(i64* null)
  ret i64 %".3"
}

@"f.time" = global i64 (double)* @"def.time"
@"rand_state" = global i64 0
define void @"def.seed"(i64 %".1") 
{
entry:
  store i64 %".1", i64* @"rand_state"
  ret void
}

@"f.seed" = global void (i64)* @"def.seed"
define i64 @"def.rand"() 
{
entry:
  %".2" = load i64, i64* @"rand_state"
  %".3" = mul i64 1103515245, %".2"
  %".4" = add i64 %".3", 12345
  %".5" = srem i64 %".4", 2147483648
  store i64 %".5", i64* @"rand_state"
  %".7" = ashr i64 %".5", 16
  %".8" = and i64 %".7", 32767
  ret i64 %".8"
}

@"f.rand" = global i64 ()* @"def.rand"