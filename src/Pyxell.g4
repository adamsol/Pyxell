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
  | 'print' tuple_expr? # StmtPrint
  | (lvalue '=')* tuple_expr # StmtAssg
  | expr op=('^' | '*' | '/' | '%' | '+' | '-' | '<<' | '>>' | '&' | '$' | '|') '=' expr # StmtAssgExpr
  | s=('break' | 'continue') # StmtLoopControl
  ;

lvalue
  : expr (',' expr)*
  ;

compound_stmt
  : 'if' expr block ('elif' expr block)* ('else' block)? # StmtIf
  | 'while' expr block # StmtWhile
  | 'until' expr block # StmtUntil
  | 'for' tuple_expr 'in' tuple_expr ('step' step=tuple_expr)? block # StmtFor
  ;

block
  : 'do' '{' stmt+ '}'
  ;

tuple_expr
  : (expr ',')* expr # ExprTuple
  ;

expr
  : atom # ExprAtom
  | '(' tuple_expr ')' # ExprParentheses
  | expr '[' expr ']' # ExprIndex
  | expr '.' ID # ExprAttr
  | <assoc=right> expr op='^' expr # ExprBinaryOp
  | op=('+' | '-' | '~') expr # ExprUnaryOp
  | expr op=('*' | '/' | '%') expr # ExprBinaryOp
  | expr op=('+' | '-') expr # ExprBinaryOp
  | expr op=('<<' | '>>') expr # ExprBinaryOp
  | expr op='&' expr # ExprBinaryOp
  | expr op='$' expr # ExprBinaryOp
  | expr op='|' expr # ExprBinaryOp
  | expr dots='..' expr # ExprRange
  | expr dots='...' expr # ExprRange
  | expr dots='...' # ExprRange
  | <assoc=right> expr op=('==' | '!=' | '<' | '<=' | '>' | '>=') expr # ExprCmp
  | op='not' expr # ExprUnaryOp
  | <assoc=right> expr op='and' expr # ExprLogicalOp
  | <assoc=right> expr op='or' expr # ExprLogicalOp
  | <assoc=right> expr '?' expr ':' expr # ExprCond
  ;

atom
  : INT # AtomInt
  | ('true' | 'false') # AtomBool
  | CHAR # AtomChar
  | STRING # AtomString
  | '[' (expr ',')* expr? ']' # AtomArray
  | ID # AtomId
  ;

INT : DIGIT+ ;
CHAR : '\'' (~[\\'] | ('\\' ['\\nt]))* '\'' ;
STRING : '"' (~[\\"] | ('\\' ["\\nt]))* '"' ;
ID : ID_START ID_CONT* ;

fragment DIGIT : [0-9] ;
fragment ID_START : [a-zA-Z_] ;
fragment ID_CONT : ID_START | DIGIT | [_'] ;

WS : [ \n\r\t]+ -> skip ;
ERR : . ;
