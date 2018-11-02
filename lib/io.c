
#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>

void _io() {
    int n;
    char s[0];
    scanf("%d", &n);
    printf("%d", 0);
    sscanf(s, "%d", &n);
    sprintf(s, "%d", 0);
}
