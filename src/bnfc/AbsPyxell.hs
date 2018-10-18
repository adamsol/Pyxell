

module AbsPyxell where

-- Haskell module generated by the BNF converter




newtype Ident = Ident String deriving (Eq, Ord, Show, Read)
data Program a = Program a [Stmt a]
  deriving (Eq, Ord, Show, Read)

instance Functor Program where
    fmap f x = case x of
        Program a stmts -> Program (f a) (map (fmap f) stmts)
data Stmt a
    = SProc a Ident [ArgF a] (Block a)
    | SFunc a Ident [ArgF a] (Type a) (Block a)
    | SProcExtern a Ident [ArgF a]
    | SFuncExtern a Ident [ArgF a] (Type a)
    | SRetVoid a
    | SRetExpr a (Expr a)
    | SSkip a
    | SPrint a (Expr a)
    | SPrintEmpty a
    | SAssg a [Expr a]
    | SAssgMul a (Expr a) (Expr a)
    | SAssgDiv a (Expr a) (Expr a)
    | SAssgMod a (Expr a) (Expr a)
    | SAssgAdd a (Expr a) (Expr a)
    | SAssgSub a (Expr a) (Expr a)
    | SIf a [Branch a] (Else a)
    | SWhile a (Expr a) (Block a)
    | SUntil a (Expr a) (Block a)
    | SFor a (Expr a) (Expr a) (Block a)
    | SForStep a (Expr a) (Expr a) (Expr a) (Block a)
    | SContinue a
    | SBreak a
  deriving (Eq, Ord, Show, Read)

instance Functor Stmt where
    fmap f x = case x of
        SProc a ident argfs block -> SProc (f a) ident (map (fmap f) argfs) (fmap f block)
        SFunc a ident argfs type_ block -> SFunc (f a) ident (map (fmap f) argfs) (fmap f type_) (fmap f block)
        SProcExtern a ident argfs -> SProcExtern (f a) ident (map (fmap f) argfs)
        SFuncExtern a ident argfs type_ -> SFuncExtern (f a) ident (map (fmap f) argfs) (fmap f type_)
        SRetVoid a -> SRetVoid (f a)
        SRetExpr a expr -> SRetExpr (f a) (fmap f expr)
        SSkip a -> SSkip (f a)
        SPrint a expr -> SPrint (f a) (fmap f expr)
        SPrintEmpty a -> SPrintEmpty (f a)
        SAssg a exprs -> SAssg (f a) (map (fmap f) exprs)
        SAssgMul a expr1 expr2 -> SAssgMul (f a) (fmap f expr1) (fmap f expr2)
        SAssgDiv a expr1 expr2 -> SAssgDiv (f a) (fmap f expr1) (fmap f expr2)
        SAssgMod a expr1 expr2 -> SAssgMod (f a) (fmap f expr1) (fmap f expr2)
        SAssgAdd a expr1 expr2 -> SAssgAdd (f a) (fmap f expr1) (fmap f expr2)
        SAssgSub a expr1 expr2 -> SAssgSub (f a) (fmap f expr1) (fmap f expr2)
        SIf a branchs else_ -> SIf (f a) (map (fmap f) branchs) (fmap f else_)
        SWhile a expr block -> SWhile (f a) (fmap f expr) (fmap f block)
        SUntil a expr block -> SUntil (f a) (fmap f expr) (fmap f block)
        SFor a expr1 expr2 block -> SFor (f a) (fmap f expr1) (fmap f expr2) (fmap f block)
        SForStep a expr1 expr2 expr3 block -> SForStep (f a) (fmap f expr1) (fmap f expr2) (fmap f expr3) (fmap f block)
        SContinue a -> SContinue (f a)
        SBreak a -> SBreak (f a)
data ArgF a
    = ANoDefault a (Type a) Ident | ADefault a (Type a) Ident (Expr a)
  deriving (Eq, Ord, Show, Read)

instance Functor ArgF where
    fmap f x = case x of
        ANoDefault a type_ ident -> ANoDefault (f a) (fmap f type_) ident
        ADefault a type_ ident expr -> ADefault (f a) (fmap f type_) ident (fmap f expr)
data Block a = SBlock a [Stmt a]
  deriving (Eq, Ord, Show, Read)

instance Functor Block where
    fmap f x = case x of
        SBlock a stmts -> SBlock (f a) (map (fmap f) stmts)
data Branch a = BElIf a (Expr a) (Block a)
  deriving (Eq, Ord, Show, Read)

instance Functor Branch where
    fmap f x = case x of
        BElIf a expr block -> BElIf (f a) (fmap f expr) (fmap f block)
data Else a = EElse a (Block a) | EEmpty a
  deriving (Eq, Ord, Show, Read)

instance Functor Else where
    fmap f x = case x of
        EElse a block -> EElse (f a) (fmap f block)
        EEmpty a -> EEmpty (f a)
data ArgC a = APos a (Expr a) | ANamed a Ident (Expr a)
  deriving (Eq, Ord, Show, Read)

instance Functor ArgC where
    fmap f x = case x of
        APos a expr -> APos (f a) (fmap f expr)
        ANamed a ident expr -> ANamed (f a) ident (fmap f expr)
data Cmp a
    = Cmp1 a (Expr a) (CmpOp a) (Expr a)
    | Cmp2 a (Expr a) (CmpOp a) (Cmp a)
  deriving (Eq, Ord, Show, Read)

instance Functor Cmp where
    fmap f x = case x of
        Cmp1 a expr1 cmpop expr2 -> Cmp1 (f a) (fmap f expr1) (fmap f cmpop) (fmap f expr2)
        Cmp2 a expr cmpop cmp -> Cmp2 (f a) (fmap f expr) (fmap f cmpop) (fmap f cmp)
data CmpOp a
    = CmpEQ a | CmpNE a | CmpLT a | CmpLE a | CmpGT a | CmpGE a
  deriving (Eq, Ord, Show, Read)

instance Functor CmpOp where
    fmap f x = case x of
        CmpEQ a -> CmpEQ (f a)
        CmpNE a -> CmpNE (f a)
        CmpLT a -> CmpLT (f a)
        CmpLE a -> CmpLE (f a)
        CmpGT a -> CmpGT (f a)
        CmpGE a -> CmpGE (f a)
data Expr a
    = EInt a Integer
    | ETrue a
    | EFalse a
    | EChar a Char
    | EString a String
    | EArray a [Expr a]
    | EVar a Ident
    | EElem a (Expr a) Integer
    | EIndex a (Expr a) (Expr a)
    | EAttr a (Expr a) Ident
    | ECall a (Expr a) [ArgC a]
    | EPow a (Expr a) (Expr a)
    | EMul a (Expr a) (Expr a)
    | EDiv a (Expr a) (Expr a)
    | EMod a (Expr a) (Expr a)
    | EAdd a (Expr a) (Expr a)
    | ESub a (Expr a) (Expr a)
    | ENeg a (Expr a)
    | ERangeIncl a (Expr a) (Expr a)
    | ERangeExcl a (Expr a) (Expr a)
    | ERangeInf a (Expr a)
    | ECmp a (Cmp a)
    | ENot a (Expr a)
    | EAnd a (Expr a) (Expr a)
    | EOr a (Expr a) (Expr a)
    | ETuple a [Expr a]
    | ECond a (Expr a) (Expr a) (Expr a)
    | ELambda a [Ident] (Expr a)
  deriving (Eq, Ord, Show, Read)

instance Functor Expr where
    fmap f x = case x of
        EInt a integer -> EInt (f a) integer
        ETrue a -> ETrue (f a)
        EFalse a -> EFalse (f a)
        EChar a char -> EChar (f a) char
        EString a string -> EString (f a) string
        EArray a exprs -> EArray (f a) (map (fmap f) exprs)
        EVar a ident -> EVar (f a) ident
        EElem a expr integer -> EElem (f a) (fmap f expr) integer
        EIndex a expr1 expr2 -> EIndex (f a) (fmap f expr1) (fmap f expr2)
        EAttr a expr ident -> EAttr (f a) (fmap f expr) ident
        ECall a expr argcs -> ECall (f a) (fmap f expr) (map (fmap f) argcs)
        EPow a expr1 expr2 -> EPow (f a) (fmap f expr1) (fmap f expr2)
        EMul a expr1 expr2 -> EMul (f a) (fmap f expr1) (fmap f expr2)
        EDiv a expr1 expr2 -> EDiv (f a) (fmap f expr1) (fmap f expr2)
        EMod a expr1 expr2 -> EMod (f a) (fmap f expr1) (fmap f expr2)
        EAdd a expr1 expr2 -> EAdd (f a) (fmap f expr1) (fmap f expr2)
        ESub a expr1 expr2 -> ESub (f a) (fmap f expr1) (fmap f expr2)
        ENeg a expr -> ENeg (f a) (fmap f expr)
        ERangeIncl a expr1 expr2 -> ERangeIncl (f a) (fmap f expr1) (fmap f expr2)
        ERangeExcl a expr1 expr2 -> ERangeExcl (f a) (fmap f expr1) (fmap f expr2)
        ERangeInf a expr -> ERangeInf (f a) (fmap f expr)
        ECmp a cmp -> ECmp (f a) (fmap f cmp)
        ENot a expr -> ENot (f a) (fmap f expr)
        EAnd a expr1 expr2 -> EAnd (f a) (fmap f expr1) (fmap f expr2)
        EOr a expr1 expr2 -> EOr (f a) (fmap f expr1) (fmap f expr2)
        ETuple a exprs -> ETuple (f a) (map (fmap f) exprs)
        ECond a expr1 expr2 expr3 -> ECond (f a) (fmap f expr1) (fmap f expr2) (fmap f expr3)
        ELambda a idents expr -> ELambda (f a) idents (fmap f expr)
data Type a
    = TPtr a (Type a)
    | TArr a Integer (Type a)
    | TDeref a (Type a)
    | TLabel a
    | TVoid a
    | TInt a
    | TBool a
    | TChar a
    | TObject a
    | TString a
    | TArray a (Type a)
    | TTuple a [Type a]
    | TArgN a (Type a) Ident
    | TArgD a (Type a) Ident String
    | TFunc a [Type a] (Type a)
  deriving (Eq, Ord, Show, Read)

instance Functor Type where
    fmap f x = case x of
        TPtr a type_ -> TPtr (f a) (fmap f type_)
        TArr a integer type_ -> TArr (f a) integer (fmap f type_)
        TDeref a type_ -> TDeref (f a) (fmap f type_)
        TLabel a -> TLabel (f a)
        TVoid a -> TVoid (f a)
        TInt a -> TInt (f a)
        TBool a -> TBool (f a)
        TChar a -> TChar (f a)
        TObject a -> TObject (f a)
        TString a -> TString (f a)
        TArray a type_ -> TArray (f a) (fmap f type_)
        TTuple a types -> TTuple (f a) (map (fmap f) types)
        TArgN a type_ ident -> TArgN (f a) (fmap f type_) ident
        TArgD a type_ ident string -> TArgD (f a) (fmap f type_) ident string
        TFunc a types type_ -> TFunc (f a) (map (fmap f) types) (fmap f type_)
