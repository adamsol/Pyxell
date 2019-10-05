grammar Pyxell;

program
  : stmt* EOF
  ;

stmt
  : simple_stmt ';'
  | compound_stmt
  ;

simple_stmt
  : 'skip' # StmtSkip
  | 'print' expr # StmtPrint
  | (ID '=')* expr # StmtAssg
  | ID op=('*' | '/' | '%' | '+' | '-') '=' expr # StmtAssgExpr
  ;

compound_stmt
  : 'if' expr block ('elif' expr block)* ('else' block)? # StmtIf
  | 'while' expr block # StmtWhile
  | 'until' expr block # StmtUntil
  ;

block
  : 'do' '{' stmt+ '}'
  ;

expr
  : atom # ExprAtom
  | '(' expr ')' # ExprParentheses
  | op=('+' | '-') expr # ExprUnaryOp
  | expr op=('*' | '/' | '%') expr # ExprBinaryOp
  | expr op=('+' | '-') expr # ExprBinaryOp
  | <assoc=right> expr op=('==' | '!=' | '<' | '<=' | '>' | '>=') expr # ExprCmp
  | op='not' expr # ExprUnaryOp
  | <assoc=right> expr op='and' expr # ExprLogicalOp
  | <assoc=right> expr op='or' expr # ExprLogicalOp
  ;

atom
  : INT # AtomInt
  | ('true' | 'false') # AtomBool
  | ID # AtomId
  ;

INT : DIGIT+ ;
ID : ID_START ID_CONT* ;

fragment DIGIT : [0-9] ;
fragment ID_START : [a-zA-Z_] ;
fragment ID_CONT : ID_START | DIGIT | [_'] ;

WS : [ \n\r\t]+ -> skip ;
ERR : . ;
