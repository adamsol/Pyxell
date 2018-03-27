
@dnl = internal constant [4 x i8] c"%d\0A\00"

declare i32 @printf(i8*, ...)
declare i32 @puts(i8*)

declare i8* @malloc(i64)
declare i64 @strlen(i8*)
declare i8* @strncpy(i8*, i8*, i64)


define void @printInt(i32 %x) {
    %t0 = getelementptr [4 x i8], [4 x i8]* @dnl, i32 0, i32 0
    call i32 (i8*, ...) @printf(i8* %t0, i32 %x)
    ret void
}

define void @printString(i8* %s) {
    call i32 @puts(i8* %s)
	ret void
}

define i8* @concatStrings(i8*, i8*) {
    %3 = alloca i8*, align 8
    %4 = alloca i8*, align 8
    %5 = alloca i32, align 4
    %6 = alloca i32, align 4
    %7 = alloca i8*, align 8
    store i8* %0, i8** %3, align 8
    store i8* %1, i8** %4, align 8
    %8 = load i8*, i8** %3, align 8
    %9 = call i64 @strlen(i8* %8)
    %10 = trunc i64 %9 to i32
    store i32 %10, i32* %5, align 4
    %11 = load i8*, i8** %4, align 8
    %12 = call i64 @strlen(i8* %11)
    %13 = add i64 %12, 1
    %14 = trunc i64 %13 to i32
    store i32 %14, i32* %6, align 4
    %15 = load i32, i32* %5, align 4
    %16 = load i32, i32* %6, align 4
    %17 = add nsw i32 %15, %16
    %18 = sext i32 %17 to i64
    %19 = call noalias i8* @malloc(i64 %18)
    store i8* %19, i8** %7, align 8
    %20 = load i8*, i8** %7, align 8
    %21 = load i8*, i8** %3, align 8
    %22 = load i32, i32* %5, align 4
    %23 = sext i32 %22 to i64
    %24 = call i8* @strncpy(i8* %20, i8* %21, i64 %23)
    %25 = load i8*, i8** %7, align 8
    %26 = load i32, i32* %5, align 4
    %27 = sext i32 %26 to i64
    %28 = getelementptr inbounds i8, i8* %25, i64 %27
    %29 = load i8*, i8** %4, align 8
    %30 = load i32, i32* %6, align 4
    %31 = sext i32 %30 to i64
    %32 = call i8* @strncpy(i8* %28, i8* %29, i64 %31)
    %33 = load i8*, i8** %7, align 8
    ret i8* %33
}
