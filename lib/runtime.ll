
@d = internal constant [3 x i8] c"%d\00"
@bt = internal constant [5 x i8] c"true\00"
@bf = internal constant [6 x i8] c"false\00"
@s = internal constant [3 x i8] c"%s\00"

declare i32 @printf(i8*, ...)
declare i32 @putchar(i32)

declare i8* @malloc(i64)
declare i64 @strlen(i8*)
declare i8* @strncpy(i8*, i8*, i64)


define void @printInt(i32 %x) {
    %d = getelementptr [3 x i8], [3 x i8]* @d, i32 0, i32 0
    call i32 (i8*, ...) @printf(i8* %d, i32 %x)
    ret void
}

define void @printBool(i1 %x) {
    %bt = getelementptr [5 x i8], [5 x i8]* @bt, i32 0, i32 0
    %bf = getelementptr [6 x i8], [6 x i8]* @bf, i32 0, i32 0
    %b = select i1 %x, i8* %bt, i8* %bf
    call i32 (i8*, ...) @printf(i8* %b)
    ret void
}

define void @printString(i8* %x) {
    %s = getelementptr [3 x i8], [3 x i8]* @s, i32 0, i32 0
    call i32 (i8*, ...) @printf(i8* %s, i8* %x)
    ret void
}

define void @printSpace() {
    call i32 @putchar(i32 32)
    ret void
}

define void @printLn() {
    call i32 @putchar(i32 10)
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
