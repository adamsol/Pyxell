
@s = internal constant [3 x i8] c"%s\00"

declare i8* @malloc(i64)
declare i8* @memcpy(i8*, i8*, i64)
declare i8* @strcpy(i8*, i8*)
declare i64 @strcmp(i8*, i8*)
declare i64 @putchar(i8)
declare i64 @printf(i8*, i8*)


define i8 @chr(i64) {
entry:
	%t2 = trunc i64 %0 to i8
	ret i8 %t2
}

define i64 @ord(i8) {
entry:
	%t1 = zext i8 %0 to i64
	ret i64 %t1
}

define {i8*, i64}* @str({i8*, i64}*) {
entry:
	%t3 = getelementptr inbounds {i8*, i64}, {i8*, i64}* %0, i64 0, i32 0
	%t4 = load i8*, i8** %t3
	%t5 = getelementptr inbounds {i8*, i64}, {i8*, i64}* %0, i64 0, i32 1
	%t6 = load i64, i64* %t5
	%t7 = add i64 %t6, 1
	%t8 = getelementptr inbounds {i8*, i64}, {i8*, i64}* null, i64 1
	%t9 = ptrtoint {i8*, i64}* %t8 to i64
	%t10 = call i8* @malloc(i64 %t9)
	%t11 = bitcast i8* %t10 to {i8*, i64}*
	%t12 = getelementptr inbounds i8, i8* null, i64 %t7
	%t13 = ptrtoint i8* %t12 to i64
	%t14 = call i8* @malloc(i64 %t13)
	%t15 = bitcast i8* %t14 to i8*
	%t16 = getelementptr inbounds {i8*, i64}, {i8*, i64}* %t11, i64 0, i32 0
	store i8* %t15, i8** %t16
	%t17 = getelementptr inbounds {i8*, i64}, {i8*, i64}* %t11, i64 0, i32 1
	store i64 %t6, i64* %t17
	%t18 = getelementptr inbounds {i8*, i64}, {i8*, i64}* %t11, i64 0, i32 0
	%t19 = load i8*, i8** %t18
	%t20 = call i8* @memcpy(i8* %t19, i8* %t4, i64 %t6)
	%t21 = getelementptr inbounds i8, i8* %t19, i64 %t6
	store i8 0, i8* %t21
	ret {i8*, i64}* %t11
}

define void @write({i8*, i64}*) {
entry:
	%t22 = getelementptr inbounds {i8*, i64}, {i8*, i64}* %0, i64 0, i32 0
	%t23 = load i8*, i8** %t22
	%s = getelementptr [3 x i8], [3 x i8]* @s, i32 0, i32 0
	%t24 = call i64 @printf(i8* %s, i8* %t23)
	ret void 
}

define void @writeLn() {
entry:
	%t25 = call i64 @putchar(i8 10)
	ret void 
}
