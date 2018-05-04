-- This Happy file was machine-generated by the BNF converter
{
{-# OPTIONS_GHC -fno-warn-incomplete-patterns -fno-warn-overlapping-patterns #-}
module ParPyxell where
import AbsPyxell
import LexPyxell
import ErrM

}

-- no lexer declaration
%monad { Err } { thenM } { returnM }
%tokentype {Token}
%name pProgram_internal Program
%name pListStmt_internal ListStmt
%name pBlock_internal Block
%name pStmt_internal Stmt
%name pListExpr_internal ListExpr
%name pBranch_internal Branch
%name pListBranch_internal ListBranch
%name pElse_internal Else
%name pExpr9_internal Expr9
%name pListExpr2_internal ListExpr2
%name pExpr8_internal Expr8
%name pExpr7_internal Expr7
%name pExpr6_internal Expr6
%name pExpr5_internal Expr5
%name pCmp_internal Cmp
%name pCmpOp_internal CmpOp
%name pExpr4_internal Expr4
%name pExpr3_internal Expr3
%name pExpr1_internal Expr1
%name pListExpr3_internal ListExpr3
%name pExpr_internal Expr
%name pExpr2_internal Expr2
%name pType4_internal Type4
%name pType2_internal Type2
%name pListType3_internal ListType3
%name pType_internal Type
%name pType1_internal Type1
%name pType3_internal Type3
%token
  '%' { PT _ (TS _ 1) }
  '%=' { PT _ (TS _ 2) }
  '(' { PT _ (TS _ 3) }
  ')' { PT _ (TS _ 4) }
  '*' { PT _ (TS _ 5) }
  '*=' { PT _ (TS _ 6) }
  '+' { PT _ (TS _ 7) }
  '+=' { PT _ (TS _ 8) }
  ',' { PT _ (TS _ 9) }
  '-' { PT _ (TS _ 10) }
  '-=' { PT _ (TS _ 11) }
  '.' { PT _ (TS _ 12) }
  '..' { PT _ (TS _ 13) }
  '...' { PT _ (TS _ 14) }
  '/' { PT _ (TS _ 15) }
  '/=' { PT _ (TS _ 16) }
  ';' { PT _ (TS _ 17) }
  '<' { PT _ (TS _ 18) }
  '<=' { PT _ (TS _ 19) }
  '<>' { PT _ (TS _ 20) }
  '=' { PT _ (TS _ 21) }
  '==' { PT _ (TS _ 22) }
  '>' { PT _ (TS _ 23) }
  '>=' { PT _ (TS _ 24) }
  'Bool' { PT _ (TS _ 25) }
  'Char' { PT _ (TS _ 26) }
  'Int' { PT _ (TS _ 27) }
  'Label' { PT _ (TS _ 28) }
  'Object' { PT _ (TS _ 29) }
  'String' { PT _ (TS _ 30) }
  'Void' { PT _ (TS _ 31) }
  '[' { PT _ (TS _ 32) }
  ']' { PT _ (TS _ 33) }
  'and' { PT _ (TS _ 34) }
  'break' { PT _ (TS _ 35) }
  'continue' { PT _ (TS _ 36) }
  'do' { PT _ (TS _ 37) }
  'elif' { PT _ (TS _ 38) }
  'else' { PT _ (TS _ 39) }
  'false' { PT _ (TS _ 40) }
  'for' { PT _ (TS _ 41) }
  'if' { PT _ (TS _ 42) }
  'in' { PT _ (TS _ 43) }
  'not' { PT _ (TS _ 44) }
  'or' { PT _ (TS _ 45) }
  'print' { PT _ (TS _ 46) }
  'skip' { PT _ (TS _ 47) }
  'true' { PT _ (TS _ 48) }
  'while' { PT _ (TS _ 49) }
  '{' { PT _ (TS _ 50) }
  '}' { PT _ (TS _ 51) }

  L_integ {PT _ (TI _)}
  L_charac {PT _ (TC _)}
  L_quoted {PT _ (TL _)}
  L_ident {PT _ (TV _)}

%%

Integer :: {
  (Maybe (Int, Int), Integer)
}
: L_integ {
  (Just (tokenLineCol $1), read (prToken $1)) 
}

Char :: {
  (Maybe (Int, Int), Char)
}
: L_charac {
  (Just (tokenLineCol $1), read (prToken $1)) 
}

String :: {
  (Maybe (Int, Int), String)
}
: L_quoted {
  (Just (tokenLineCol $1), prToken $1)
}

Ident :: {
  (Maybe (Int, Int), Ident)
}
: L_ident {
  (Just (tokenLineCol $1), Ident (prToken $1)) 
}

Program :: {
  (Maybe (Int, Int), Program (Maybe (Int, Int)))
}
: ListStmt {
  (fst $1, AbsPyxell.Program (fst $1)(snd $1)) 
}

ListStmt :: {
  (Maybe (Int, Int), [Stmt (Maybe (Int, Int))]) 
}
: {
  (Nothing, [])
}
| Stmt {
  (fst $1, (:[]) (snd $1)) 
}
| Stmt ';' ListStmt {
  (fst $1, (:) (snd $1)(snd $3)) 
}

Block :: {
  (Maybe (Int, Int), Block (Maybe (Int, Int)))
}
: '{' ListStmt '}' {
  (Just (tokenLineCol $1), AbsPyxell.SBlock (Just (tokenLineCol $1)) (snd $2)) 
}

Stmt :: {
  (Maybe (Int, Int), Stmt (Maybe (Int, Int)))
}
: 'skip' {
  (Just (tokenLineCol $1), AbsPyxell.SSkip (Just (tokenLineCol $1)))
}
| 'print' Expr {
  (Just (tokenLineCol $1), AbsPyxell.SPrint (Just (tokenLineCol $1)) (snd $2)) 
}
| ListExpr {
  (fst $1, AbsPyxell.SAssg (fst $1)(snd $1)) 
}
| Expr '*=' Expr {
  (fst $1, AbsPyxell.SAssgMul (fst $1)(snd $1)(snd $3)) 
}
| Expr '/=' Expr {
  (fst $1, AbsPyxell.SAssgDiv (fst $1)(snd $1)(snd $3)) 
}
| Expr '%=' Expr {
  (fst $1, AbsPyxell.SAssgMod (fst $1)(snd $1)(snd $3)) 
}
| Expr '+=' Expr {
  (fst $1, AbsPyxell.SAssgAdd (fst $1)(snd $1)(snd $3)) 
}
| Expr '-=' Expr {
  (fst $1, AbsPyxell.SAssgSub (fst $1)(snd $1)(snd $3)) 
}
| 'if' ListBranch Else {
  (Just (tokenLineCol $1), AbsPyxell.SIf (Just (tokenLineCol $1)) (snd $2)(snd $3)) 
}
| 'while' Expr 'do' Block {
  (Just (tokenLineCol $1), AbsPyxell.SWhile (Just (tokenLineCol $1)) (snd $2)(snd $4)) 
}
| 'for' Expr 'in' Expr 'do' Block {
  (Just (tokenLineCol $1), AbsPyxell.SFor (Just (tokenLineCol $1)) (snd $2)(snd $4)(snd $6)) 
}
| 'continue' {
  (Just (tokenLineCol $1), AbsPyxell.SContinue (Just (tokenLineCol $1)))
}
| 'break' {
  (Just (tokenLineCol $1), AbsPyxell.SBreak (Just (tokenLineCol $1)))
}

ListExpr :: {
  (Maybe (Int, Int), [Expr (Maybe (Int, Int))]) 
}
: Expr {
  (fst $1, (:[]) (snd $1)) 
}
| Expr '=' ListExpr {
  (fst $1, (:) (snd $1)(snd $3)) 
}

Branch :: {
  (Maybe (Int, Int), Branch (Maybe (Int, Int)))
}
: Expr 'do' Block {
  (fst $1, AbsPyxell.BElIf (fst $1)(snd $1)(snd $3)) 
}

ListBranch :: {
  (Maybe (Int, Int), [Branch (Maybe (Int, Int))]) 
}
: {
  (Nothing, [])
}
| Branch {
  (fst $1, (:[]) (snd $1)) 
}
| Branch 'elif' ListBranch {
  (fst $1, (:) (snd $1)(snd $3)) 
}

Else :: {
  (Maybe (Int, Int), Else (Maybe (Int, Int)))
}
: 'else' 'do' Block {
  (Just (tokenLineCol $1), AbsPyxell.EElse (Just (tokenLineCol $1)) (snd $3)) 
}
| {
  (Nothing, AbsPyxell.EEmpty Nothing)
}

Expr9 :: {
  (Maybe (Int, Int), Expr (Maybe (Int, Int)))
}
: Integer {
  (fst $1, AbsPyxell.EInt (fst $1)(snd $1)) 
}
| 'true' {
  (Just (tokenLineCol $1), AbsPyxell.ETrue (Just (tokenLineCol $1)))
}
| 'false' {
  (Just (tokenLineCol $1), AbsPyxell.EFalse (Just (tokenLineCol $1)))
}
| Char {
  (fst $1, AbsPyxell.EChar (fst $1)(snd $1)) 
}
| String {
  (fst $1, AbsPyxell.EString (fst $1)(snd $1)) 
}
| '[' ListExpr2 ']' {
  (Just (tokenLineCol $1), AbsPyxell.EArray (Just (tokenLineCol $1)) (snd $2)) 
}
| Ident {
  (fst $1, AbsPyxell.EVar (fst $1)(snd $1)) 
}
| Expr9 '.' Integer {
  (fst $1, AbsPyxell.EElem (fst $1)(snd $1)(snd $3)) 
}
| Expr9 '[' Expr ']' {
  (fst $1, AbsPyxell.EIndex (fst $1)(snd $1)(snd $3)) 
}
| Expr9 '.' Ident {
  (fst $1, AbsPyxell.EAttr (fst $1)(snd $1)(snd $3)) 
}
| '(' Expr ')' {
  (Just (tokenLineCol $1), snd $2)
}

ListExpr2 :: {
  (Maybe (Int, Int), [Expr (Maybe (Int, Int))]) 
}
: {
  (Nothing, [])
}
| Expr2 {
  (fst $1, (:[]) (snd $1)) 
}
| Expr2 ',' ListExpr2 {
  (fst $1, (:) (snd $1)(snd $3)) 
}

Expr8 :: {
  (Maybe (Int, Int), Expr (Maybe (Int, Int)))
}
: Expr8 '*' Expr9 {
  (fst $1, AbsPyxell.EMul (fst $1)(snd $1)(snd $3)) 
}
| Expr8 '/' Expr9 {
  (fst $1, AbsPyxell.EDiv (fst $1)(snd $1)(snd $3)) 
}
| Expr8 '%' Expr9 {
  (fst $1, AbsPyxell.EMod (fst $1)(snd $1)(snd $3)) 
}
| Expr9 {
  (fst $1, snd $1)
}

Expr7 :: {
  (Maybe (Int, Int), Expr (Maybe (Int, Int)))
}
: Expr7 '+' Expr8 {
  (fst $1, AbsPyxell.EAdd (fst $1)(snd $1)(snd $3)) 
}
| Expr7 '-' Expr8 {
  (fst $1, AbsPyxell.ESub (fst $1)(snd $1)(snd $3)) 
}
| '-' Expr8 {
  (Just (tokenLineCol $1), AbsPyxell.ENeg (Just (tokenLineCol $1)) (snd $2)) 
}
| Expr8 {
  (fst $1, snd $1)
}

Expr6 :: {
  (Maybe (Int, Int), Expr (Maybe (Int, Int)))
}
: Expr7 '..' Expr7 {
  (fst $1, AbsPyxell.ERangeIncl (fst $1)(snd $1)(snd $3)) 
}
| Expr7 '...' Expr7 {
  (fst $1, AbsPyxell.ERangeExcl (fst $1)(snd $1)(snd $3)) 
}
| Expr7 '..' Expr7 '..' Expr7 {
  (fst $1, AbsPyxell.ERangeInclStep (fst $1)(snd $1)(snd $3)(snd $5)) 
}
| Expr7 '...' Expr7 '..' Expr7 {
  (fst $1, AbsPyxell.ERangeExclStep (fst $1)(snd $1)(snd $3)(snd $5)) 
}
| Expr7 {
  (fst $1, snd $1)
}

Expr5 :: {
  (Maybe (Int, Int), Expr (Maybe (Int, Int)))
}
: Cmp {
  (fst $1, AbsPyxell.ECmp (fst $1)(snd $1)) 
}
| 'not' Expr5 {
  (Just (tokenLineCol $1), AbsPyxell.ENot (Just (tokenLineCol $1)) (snd $2)) 
}
| Expr6 {
  (fst $1, snd $1)
}

Cmp :: {
  (Maybe (Int, Int), Cmp (Maybe (Int, Int)))
}
: Expr6 CmpOp Expr6 {
  (fst $1, AbsPyxell.Cmp1 (fst $1)(snd $1)(snd $2)(snd $3)) 
}
| Expr6 CmpOp Cmp {
  (fst $1, AbsPyxell.Cmp2 (fst $1)(snd $1)(snd $2)(snd $3)) 
}

CmpOp :: {
  (Maybe (Int, Int), CmpOp (Maybe (Int, Int)))
}
: '==' {
  (Just (tokenLineCol $1), AbsPyxell.CmpEQ (Just (tokenLineCol $1)))
}
| '<>' {
  (Just (tokenLineCol $1), AbsPyxell.CmpNE (Just (tokenLineCol $1)))
}
| '<' {
  (Just (tokenLineCol $1), AbsPyxell.CmpLT (Just (tokenLineCol $1)))
}
| '<=' {
  (Just (tokenLineCol $1), AbsPyxell.CmpLE (Just (tokenLineCol $1)))
}
| '>' {
  (Just (tokenLineCol $1), AbsPyxell.CmpGT (Just (tokenLineCol $1)))
}
| '>=' {
  (Just (tokenLineCol $1), AbsPyxell.CmpGE (Just (tokenLineCol $1)))
}

Expr4 :: {
  (Maybe (Int, Int), Expr (Maybe (Int, Int)))
}
: Expr5 'and' Expr4 {
  (fst $1, AbsPyxell.EAnd (fst $1)(snd $1)(snd $3)) 
}
| Expr5 {
  (fst $1, snd $1)
}

Expr3 :: {
  (Maybe (Int, Int), Expr (Maybe (Int, Int)))
}
: Expr4 'or' Expr3 {
  (fst $1, AbsPyxell.EOr (fst $1)(snd $1)(snd $3)) 
}
| Expr4 {
  (fst $1, snd $1)
}

Expr1 :: {
  (Maybe (Int, Int), Expr (Maybe (Int, Int)))
}
: ListExpr3 {
  (fst $1, AbsPyxell.ETuple (fst $1)(snd $1)) 
}
| Expr2 {
  (fst $1, snd $1)
}

ListExpr3 :: {
  (Maybe (Int, Int), [Expr (Maybe (Int, Int))]) 
}
: Expr3 {
  (fst $1, (:[]) (snd $1)) 
}
| Expr3 ',' ListExpr3 {
  (fst $1, (:) (snd $1)(snd $3)) 
}

Expr :: {
  (Maybe (Int, Int), Expr (Maybe (Int, Int)))
}
: Expr1 {
  (fst $1, snd $1)
}

Expr2 :: {
  (Maybe (Int, Int), Expr (Maybe (Int, Int)))
}
: Expr3 {
  (fst $1, snd $1)
}

Type4 :: {
  (Maybe (Int, Int), Type (Maybe (Int, Int)))
}
: 'Int' {
  (Just (tokenLineCol $1), AbsPyxell.TInt (Just (tokenLineCol $1)))
}
| 'Bool' {
  (Just (tokenLineCol $1), AbsPyxell.TBool (Just (tokenLineCol $1)))
}
| 'Char' {
  (Just (tokenLineCol $1), AbsPyxell.TChar (Just (tokenLineCol $1)))
}
| 'Object' {
  (Just (tokenLineCol $1), AbsPyxell.TObject (Just (tokenLineCol $1)))
}
| 'String' {
  (Just (tokenLineCol $1), AbsPyxell.TString (Just (tokenLineCol $1)))
}
| '[' Type ']' {
  (Just (tokenLineCol $1), AbsPyxell.TArray (Just (tokenLineCol $1)) (snd $2)) 
}
| '(' Type ')' {
  (Just (tokenLineCol $1), snd $2)
}

Type2 :: {
  (Maybe (Int, Int), Type (Maybe (Int, Int)))
}
: ListType3 {
  (fst $1, AbsPyxell.TTuple (fst $1)(snd $1)) 
}
| Type3 {
  (fst $1, snd $1)
}

ListType3 :: {
  (Maybe (Int, Int), [Type (Maybe (Int, Int))]) 
}
: Type3 {
  (fst $1, (:[]) (snd $1)) 
}
| Type3 '*' ListType3 {
  (fst $1, (:) (snd $1)(snd $3)) 
}

Type :: {
  (Maybe (Int, Int), Type (Maybe (Int, Int)))
}
: Type1 {
  (fst $1, snd $1)
}

Type1 :: {
  (Maybe (Int, Int), Type (Maybe (Int, Int)))
}
: Type2 {
  (fst $1, snd $1)
}

Type3 :: {
  (Maybe (Int, Int), Type (Maybe (Int, Int)))
}
: Type4 {
  (fst $1, snd $1)
}

{

returnM :: a -> Err a
returnM = return

thenM :: Err a -> (a -> Err b) -> Err b
thenM = (>>=)

happyError :: [Token] -> Err a
happyError ts =
  Bad $ "syntax error at " ++ tokenPos ts ++ 
  case ts of
    [] -> []
    [Err _] -> " due to lexer error"
    t:_ -> " before `" ++ id(prToken t) ++ "'"

myLexer = tokens

pProgram = (>>= return . snd) . pProgram_internal
pListStmt = (>>= return . snd) . pListStmt_internal
pBlock = (>>= return . snd) . pBlock_internal
pStmt = (>>= return . snd) . pStmt_internal
pListExpr = (>>= return . snd) . pListExpr_internal
pBranch = (>>= return . snd) . pBranch_internal
pListBranch = (>>= return . snd) . pListBranch_internal
pElse = (>>= return . snd) . pElse_internal
pExpr9 = (>>= return . snd) . pExpr9_internal
pListExpr2 = (>>= return . snd) . pListExpr2_internal
pExpr8 = (>>= return . snd) . pExpr8_internal
pExpr7 = (>>= return . snd) . pExpr7_internal
pExpr6 = (>>= return . snd) . pExpr6_internal
pExpr5 = (>>= return . snd) . pExpr5_internal
pCmp = (>>= return . snd) . pCmp_internal
pCmpOp = (>>= return . snd) . pCmpOp_internal
pExpr4 = (>>= return . snd) . pExpr4_internal
pExpr3 = (>>= return . snd) . pExpr3_internal
pExpr1 = (>>= return . snd) . pExpr1_internal
pListExpr3 = (>>= return . snd) . pListExpr3_internal
pExpr = (>>= return . snd) . pExpr_internal
pExpr2 = (>>= return . snd) . pExpr2_internal
pType4 = (>>= return . snd) . pType4_internal
pType2 = (>>= return . snd) . pType2_internal
pListType3 = (>>= return . snd) . pListType3_internal
pType = (>>= return . snd) . pType_internal
pType1 = (>>= return . snd) . pType1_internal
pType3 = (>>= return . snd) . pType3_internal
}

