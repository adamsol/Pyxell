
@d = internal constant [5 x i8] c"%lld\00"
@bt = internal constant [5 x i8] c"true\00"
@bf = internal constant [6 x i8] c"false\00"
@s = internal constant [3 x i8] c"%s\00"

declare i32 @printf(i8*, ...)
declare i32 @putchar(i8)


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
