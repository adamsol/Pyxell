grammar Pyxell;

program
  : (stmt ';')* EOF
  ;

block
  : '{' (stmt ';')+ '}'
  ;

stmt
  : 'use' name=ID ('only' only=id_list | 'hiding' hiding=id_list | 'as' as_=ID)? # StmtUse
  | 'skip' # StmtSkip
  | 'print' (expr ',')* expr? # StmtPrint
  | typ ID ('=' tuple_expr)? # StmtDecl
  | (tuple_expr '=')* tuple_expr # StmtAssg
  | expr op=('^' | '^^' | '/' | '//' | '%' | '*' | '&' | '+' | '-' | '??') '=' expr # StmtAssgExpr
  | s=('break' | 'continue') # StmtLoopControl
  | 'return' tuple_expr? # StmtReturn
  | 'yield' tuple_expr # StmtYield
  | 'if' expr 'do' block (';' 'elif' expr 'do' block)* (';' 'else' 'do' block)? # StmtIf
  | 'while' expr 'do' block # StmtWhile
  | 'until' expr 'do' block # StmtUntil
  | 'for' tuple_expr 'in' tuple_expr 'do' block # StmtFor
  | 'func' generator='*'? ID ('<' typevars=id_list '>')? args=func_args (ret=typ)? ('def' block | 'extern') # StmtFunc
  | 'class' ID ('(' typ ')')? 'def' '{' (class_member ';')+ '}' # StmtClass
  ;

func_arg
  : typ variadic='...'? ID (':' expr)? # FuncArg
  ;

func_args
  : '(' (func_arg ',')* func_arg? ')'
  ;

class_member
  : typ ID (':' tuple_expr)? # ClassField
  | 'func' generator='*'? ID args=func_args (ret=typ)? ('def' block | 'abstract') # ClassMethod
  | 'constructor' 'def' block # ClassConstructor
  | 'destructor' 'def' block # ClassDestructor
  ;

expr
  : atom # ExprAtom
  | '(' tuple_expr ')' # ExprParentheses
  | '[' (expr ',')* expr? ']' # ExprArray
  | '{' (expr ',')* expr? '}' # ExprSet
  | '{' (dict_item ',')* dict_item ','? '}' # ExprDict
  | '{' ':' '}' # ExprDict
  | '[' expr comprehension+ ']' # ExprArrayComprehension
  | '{' expr comprehension+ '}' # ExprSetComprehension
  | '{' expr ':' expr comprehension+ '}' # ExprDictComprehension
  | expr safe='?'? '.' ID # ExprAttr
  | expr safe='?'? '[' tuple_expr ']' # ExprIndex
  | expr '[' e1=expr? (':' e2=expr? (':' e3=expr?)?) ']' # ExprSlice
  | expr partial='@'? '(' (call_arg ',')* call_arg? ')' # ExprCall
  | expr op='!' # ExprUnaryOp
  | <assoc=right> expr op=('^' | '^^') expr # ExprBinaryOp
  | op=('+' | '-') expr # ExprUnaryOp
  | expr op='/' expr # ExprBinaryOp
  | expr op=('//' | '%' | '*' | '&') expr # ExprBinaryOp
  | expr op=('+' | '-') expr # ExprBinaryOp
  | expr op='%%' expr # ExprBinaryOp
  | <assoc=right> expr op='??' expr # ExprBinaryOp
  | expr dots=('..' | '...') expr # ExprRange
  | expr dots='...' # ExprRange
  | expr 'by' expr # ExprBy
  | '...' expr # ExprSpread
  | <assoc=right> expr op=('==' | '!=' | '<' | '<=' | '>' | '>=') expr # ExprCmp
  | expr not_='not'? 'in' expr # ExprIn
  | expr 'is' not_='not'? 'null' # ExprIsNull
  | op='not' expr # ExprUnaryOp
  | <assoc=right> expr op='and' expr # ExprLogicalOp
  | <assoc=right> expr op='or' expr # ExprLogicalOp
  | <assoc=right> expr '?' expr ':' expr # ExprCond
  | 'lambda' generator='*'? (ID ',')* ID? (':' expr | 'def' block) # ExprLambda
  ;

dict_item
  : expr ':' expr # DictPair
  | '...:' expr # DictSpread
  ;

tuple_expr
  : (expr ',')* expr # ExprTuple
  ;

interpolation_expr
  : tuple_expr EOF # ExprInterpolation
  ;

comprehension
  : 'for' tuple_expr 'in' tuple_expr # ComprehensionIteration
  | 'if' expr # ComprehensionPredicate
  ;

call_arg
  : (ID '=')? expr # CallArg
  ;

atom
  : (INT_DEC | INT_BIN | INT_OCT | INT_HEX) # AtomInt
  | RAT # AtomRat
  | FLOAT # AtomFloat
  | ('true' | 'false') # AtomBool
  | CHAR # AtomChar
  | STRING # AtomString
  | 'null' # AtomNull
  | 'this' # AtomThis
  | 'super' # AtomSuper
  | 'default' '(' typ ')' # AtomDefault
  | ID # AtomId
  ;

id_list
  : (ID ',')* ID # IdList
  ;

typ
  : ID # TypeName
  | '(' typ ')' # TypeParentheses
  | '[' typ ']' # TypeArray
  | '{' typ '}' # TypeSet
  | '{' typ ':' typ '}' # TypeDict
  | typ '?' # TypeNullable
  | <assoc=right> typ '*' typ # TypeTuple
  | <assoc=right> typ '->' typ # TypeFunc
  | '(' ')' '->' typ # TypeFunc0
  ;

INT_DEC : DIGIT NUMBER_DEC_CONT* ;
INT_BIN : '0b' NUMBER_BIN_CONT+ ;
INT_OCT : '0o' NUMBER_OCT_CONT+ ;
INT_HEX : '0x' NUMBER_HEX_CONT+ ;
RAT : DIGIT NUMBER_DEC_CONT* '.' NUMBER_DEC_CONT+ ;
FLOAT : DIGIT NUMBER_DEC_CONT* ('.' NUMBER_DEC_CONT+)? [eE] [-+]? NUMBER_DEC_CONT+ ;
CHAR : ['] (~[\\'] | ([\\] (['] | ESCAPE_CHAR))) ['] ;
STRING : ["] (~[\\"] | ([\\] (["] | ESCAPE_CHAR)))* ["] ;
ID : ID_START ID_CONT* ;

fragment DIGIT : [0-9] ;
fragment NUMBER_DEC_CONT : DIGIT | [_] ;
fragment NUMBER_BIN_CONT : [01_] ;
fragment NUMBER_OCT_CONT : [0-7_] ;
fragment NUMBER_HEX_CONT : [0-9a-fA-F_] ;
fragment ESCAPE_CHAR : [\\abfnrt] | 'x' [0-9a-fA-F]+ ;
fragment ID_START : [a-zA-Z_] ;
fragment ID_CONT : ID_START | DIGIT | ['] ;

WS : [ \n\r]+ -> skip ;
ERR : . ;
