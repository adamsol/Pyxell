grammar Pyxell;

program
  : stmt* EOF
  ;

stmt
  : 'print' expr ';' # StmtPrint
  | ID '=' expr ';' # StmtAssg
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
  | ID # AtomId
  ;

INT : DIGIT+ ;
ID : ID_START ID_CONT* ;

fragment DIGIT : [0-9] ;
fragment ID_START : [a-zA-Z_] ;
fragment ID_CONT : ID_START | DIGIT | [_'] ;

WS: [ \n\r\t]+ -> skip;
