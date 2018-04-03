
@d = internal constant [5 x i8] c"%lld\00"
@bt = internal constant [5 x i8] c"true\00"
@bf = internal constant [6 x i8] c"false\00"
@s = internal constant [3 x i8] c"%s\00"

declare i32 @printf(i8*, ...)
declare i32 @putchar(i8)

declare i8* @malloc(i64)
declare i64 @strlen(i8*)
declare i8* @strncpy(i8*, i8*, i64)


define void @printInt(i64 %x) {
    %d = getelementptr [5 x i8], [5 x i8]* @d, i32 0, i32 0
    call i32 (i8*, ...) @printf(i8* %d, i64 %x)
    ret void
}

define void @printBool(i1 %x) {
    %bt = getelementptr [5 x i8], [5 x i8]* @bt, i32 0, i32 0
    %bf = getelementptr [6 x i8], [6 x i8]* @bf, i32 0, i32 0
    %b = select i1 %x, i8* %bt, i8* %bf
    call i32 (i8*, ...) @printf(i8* %b)
    ret void
}

define void @printChar(i8 %x) {
    call i32 @putchar(i8 %x)
    ret void
}

define void @printString(i8* %x) {
    %s = getelementptr [3 x i8], [3 x i8]* @s, i32 0, i32 0
    call i32 (i8*, ...) @printf(i8* %s, i8* %x)
    ret void
}

define void @printSpace() {
    call i32 @putchar(i8 32)
    ret void
}

define void @printLn() {
    call i32 @putchar(i8 10)
    ret void
}


define i8* @concatStrings(i8*, i8*) {
    %3 = call i64 @strlen(i8* %0)
    %4 = call i64 @strlen(i8* %1)
    %5 = add i64 %4, 1
    %6 = add i64 %5, %3
    %7 = call i8* @malloc(i64 %6)
    %8 = call i8* @strncpy(i8* %7, i8* %0, i64 %3)
    %9 = getelementptr inbounds i8, i8* %7, i64 %3
    %10 = call i8* @strncpy(i8* %9, i8* %1, i64 %5)
    ret i8* %7
}
