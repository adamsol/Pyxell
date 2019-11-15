grammar Pyxell;

program
  : stmt* EOF
  ;

stmt
  : simple_stmt ';'
  | compound_stmt
  ;

simple_stmt
  : 'use' name=ID ('only' only=id_list | 'hiding' hiding=id_list | 'as' as_=ID)? # StmtUse
  | 'skip' # StmtSkip
  | 'print' tuple_expr? # StmtPrint
  | typ ID ('=' tuple_expr)? # StmtDecl
  | (lvalue '=')* tuple_expr # StmtAssg
  | expr op=('^' | '*' | '/' | '%' | '+' | '-' | '<<' | '>>' | '&' | '$' | '|' | '??') '=' expr # StmtAssgExpr
  | s=('break' | 'continue') # StmtLoopControl
  | 'return' tuple_expr? # StmtReturn
  ;

lvalue
  : expr (',' expr)*
  ;

compound_stmt
  : 'if' expr 'do' block ('elif' expr 'do' block)* ('else' 'do' block)? # StmtIf
  | 'while' expr 'do' block # StmtWhile
  | 'until' expr 'do' block # StmtUntil
  | 'for' tuple_expr 'in' tuple_expr ('step' tuple_expr)? 'do' block # StmtFor
  | 'func' ID '(' (func_arg ',')* func_arg? ')' (ret=typ)? ('def' block | 'extern' ';') # StmtFunc
  ;

func_arg
  : typ ID (':' expr)? # FuncArg
  ;

block
  : '{' stmt+ '}'
  ;

expr
  : atom # ExprAtom
  | '(' tuple_expr ')' # ExprParentheses
  | '[' (expr ',')* expr? ']' # ExprArray
  | '[' expr comprehension+ ']' # ExprArrayComprehension
  | expr safe='?'? '[' tuple_expr ']' # ExprIndex
  | expr '[' e1=expr? (':' e2=expr? (':' e3=expr?)?) ']' # ExprSlice
  | expr safe='?'? '.' ID # ExprAttr
  | expr '(' (call_arg ',')* call_arg? ')' # ExprCall
  | expr op='!' # ExprUnaryOp
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
  | expr op=('is' | 'isn\'t') expr # ExprIs
  | <assoc=right> expr op=('==' | '!=' | '<' | '<=' | '>' | '>=') expr # ExprCmp
  | op='not' expr # ExprUnaryOp
  | <assoc=right> expr op='and' expr # ExprLogicalOp
  | <assoc=right> expr op='or' expr # ExprLogicalOp
  | <assoc=right> expr op='??' expr # ExprBinaryOp
  | <assoc=right> expr '?' expr ':' expr # ExprCond
  | 'lambda' (ID ',')* ID? '->' expr # ExprLambda
  ;

tuple_expr
  : (expr ',')* expr # ExprTuple
  ;

interpolation_expr
  : tuple_expr EOF # ExprInterpolation
  ;

comprehension
  : 'for' tuple_expr 'in' tuple_expr ('step' tuple_expr)? # ComprehensionGenerator
  | 'if' expr # ComprehensionFilter
  ;

call_arg
  : (ID '=')? expr # CallArg
  ;

atom
  : INT # AtomInt
  | FLOAT # AtomFloat
  | ('true' | 'false') # AtomBool
  | CHAR # AtomChar
  | STRING # AtomString
  | 'null' # AtomNull
  | ID # AtomId
  ;

id_list
  : (ID ',')* ID
  ;

typ
  : ('Void' | 'Int' | 'Float' | 'Bool' | 'Char' | 'String') # TypePrimitive
  | '(' typ ')' # TypeParentheses
  | '[' typ ']' # TypeArray
  | typ '?' # TypeNullable
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

COMMENT : '--' ~[\r\n\f]* -> skip ;
WS : [ \n\r\t]+ -> skip ;
ERR : . ;
