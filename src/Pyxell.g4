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
  ;

compound_stmt
  : 'if' expr block ('elif' expr block)* ('else' block)? # StmtIf
  ;

block
  : 'do' '{' stmt+ '}'
  ;

expr
  : expr op=('*' | '/' | '%') expr # ExprBinaryOp
  | expr op=('+' | '-') expr # ExprBinaryOp
  | op=('+' | '-') expr # ExprUnaryOp
  | '(' expr ')' # ExprParentheses
  | atom # ExprAtom
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

WS: [ \n\r\t]+ -> skip;
