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
  | typ ID ('=' tuple_expr)? # StmtDecl
  | (lvalue '=')* tuple_expr # StmtAssg
  | expr op=('^' | '*' | '/' | '%' | '+' | '-' | '<<' | '>>' | '&' | '$' | '|') '=' expr # StmtAssgExpr
  | s=('break' | 'continue') # StmtLoopControl
  | 'return' tuple_expr? # StmtReturn
  ;

lvalue
  : expr (',' expr)*
  ;

compound_stmt
  : 'if' expr do_block ('elif' expr do_block)* ('else' do_block)? # StmtIf
  | 'while' expr do_block # StmtWhile
  | 'until' expr do_block # StmtUntil
  | 'for' tuple_expr 'in' tuple_expr ('step' step=tuple_expr)? do_block # StmtFor
  | 'func' ID '(' (arg ',')* arg? ')' ret=typ? def_block # StmtFunc
  ;

arg
  : typ ID
  ;

do_block
  : 'do' '{' stmt+ '}'
  ;

def_block
  : 'def' '{' stmt+ '}'
  ;

tuple_expr
  : (expr ',')* expr # ExprTuple
  ;

expr
  : atom # ExprAtom
  | '(' tuple_expr ')' # ExprParentheses
  | expr '[' expr ']' # ExprIndex
  | expr '.' ID # ExprAttr
  | expr '(' (expr ',')* expr? ')' # ExprCall
  | <assoc=right> expr op='^' expr # ExprBinaryOp
  | op=('+' | '-' | '~') expr # ExprUnaryOp
  | expr op=('*' | '/' | '%') expr # ExprBinaryOp
  | expr op=('+' | '-') expr # ExprBinaryOp
  | expr op=('<<' | '>>') expr # ExprBinaryOp
  | expr op='&' expr # ExprBinaryOp
  | expr op='$' expr # ExprBinaryOp
  | expr op='|' expr # ExprBinaryOp
  | expr dots=('..' | '...') expr # ExprRange
  | expr dots='...' # ExprRange
  | <assoc=right> expr op=('==' | '!=' | '<' | '<=' | '>' | '>=') expr # ExprCmp
  | op='not' expr # ExprUnaryOp
  | <assoc=right> expr op='and' expr # ExprLogicalOp
  | <assoc=right> expr op='or' expr # ExprLogicalOp
  | <assoc=right> expr '?' expr ':' expr # ExprCond
  ;

atom
  : INT # AtomInt
  | FLOAT # AtomFloat
  | ('true' | 'false') # AtomBool
  | CHAR # AtomChar
  | STRING # AtomString
  | '[' (expr ',')* expr? ']' # AtomArray
  | ID # AtomId
  ;

typ
  : 'Void' # TypePrimitive
  | 'Int' # TypePrimitive
  | 'Float' # TypePrimitive
  | 'Bool' # TypePrimitive
  | 'Char' # TypePrimitive
  | 'String' # TypePrimitive
  | '(' typ ')' # TypeParentheses
  | '[' typ ']' # TypeArray
  | <assoc=right> typ '*' typ # TypeTuple
  | <assoc=right> typ '->' typ # TypeFunc
  | '->' typ # TypeFunc0
  ;

INT : DIGIT+ ;
FLOAT : DIGIT+ '.' DIGIT+ ('e' '-'? DIGIT+)? ;
CHAR : '\'' (~[\\'] | ('\\' ['\\nt]))* '\'' ;
STRING : '"' (~[\\"] | ('\\' ["\\nt]))* '"' ;
ID : ID_START ID_CONT* ;

fragment DIGIT : [0-9] ;
fragment ID_START : [a-zA-Z_] ;
fragment ID_CONT : ID_START | DIGIT | [_'] ;

WS : [ \n\r\t]+ -> skip ;
ERR : . ;
