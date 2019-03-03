
module CodeGen where

import Control.Monad.Identity
import Control.Monad.Trans.Class
import Control.Monad.Trans.State hiding (State)
import Control.Monad.Trans.Reader
import Data.Char
import Data.List
import qualified Data.Map as M

import AbsPyxell hiding (Type)

import Utils


-- | Utility types for LLVM registers.
type Value = String
type Result = (Type, Value)

-- | Compiler environment and state.
type Env = M.Map Ident Result
data StateItem = Number Int | Label Value | Function Env
type State = M.Map Value StateItem

-- | LLVM code for each scope (function or global).
type Output = M.Map String [String]

-- | Main compiler monad: Reader for identifier environment, State to store some useful values and the output LLVM code.
type Run r = ReaderT Env (StateT State (StateT Output IO)) r


-- | Does nothing.
skip :: Run ()
skip = do
    return $ ()

-- | Outputs several lines of LLVM code in the current scope.
write :: [String] -> Run ()
write lines = do
    s <- getScope
    lift $ lift $ modify (M.insertWith (++) (s ++ "-2") (reverse lines))

-- | Outputs several lines of LLVM code at the top of the current scope.
writeTop :: [String] -> Run ()
writeTop lines = do
    s <- getScope
    lift $ lift $ modify (M.insertWith (++) (s ++ "-1") (reverse lines))

-- | Adds an indent to given lines.
indent :: [String] -> [String]
indent lines = map ('\t':) lines


-- | Inserts a label into the map and continues with changed environment.
localLabel :: String -> Value -> Run a -> Run a
localLabel name lbl cont = do
    local (M.insert (Ident name) (tVoid, lbl)) cont

-- | Inserts a type into the map and continues with changed environment.
localType :: Ident -> Type -> Run a -> Run a
localType id typ cont = do
    local (M.insert id (typ, "")) $ cont

-- | Inserts a variable into the map and continues with changed environment.
localVar :: Ident -> Type -> Value -> Run a -> Run a
localVar id typ val cont = do
    local (M.insert id (typ, val)) cont

-- | Inserts a function into the map and saves environment for later compilation.
localFunction :: Ident -> Type -> Run a -> Run a
localFunction id typ cont = do
    f <- functionName id
    let p = "@f" ++ f
    localVar id typ p $ do
        env <- ask
        lift $ modify (M.insert p (Function env))
        cont

-- | Runs continuation in a given scope (function).
localScope :: Value -> Run a -> Run a
localScope name cont = do
    localLabel "#scope" name cont

-- | Returns name of the current scope (function).
getScope :: Run Value
getScope = do
    r <- asks (M.lookup (Ident "#scope"))
    case r of
        Just (_, name) -> return $ name
        Nothing -> return $ "!global"


-- | LLVM string representation for a given type.
strType :: Type -> String
strType typ = case reduceType typ of
    TPtr _ t -> strType t ++ "*"
    TArr _ n t -> "[" ++ show n ++ " x " ++ strType t ++ "]"
    TDeref _ t -> init (strType t)
    TVoid _ -> "void"
    TInt _ -> "i64"
    TFloat _ -> "double"
    TBool _ -> "i1"
    TChar _ -> "i8"
    TString _ -> strType (tArray tChar)
    TArray _ t -> "{" ++ strType t ++ "*, i64}*"
    TTuple _ ts -> "{" ++ intercalate ", " (map strType ts) ++ "}*"
    TFunc _ as r -> case r of
        TTuple _ _ -> strType (tFunc (r:as) tVoid)
        otherwise -> (strType.reduceType) r ++ " (" ++ intercalate ", " (map (strType.reduceType) as) ++ ")*"

-- | Returns a default value for a given type.
-- | This function is for LLVM code and only serves its internal requirements.
-- | Returned values are not to be relied upon.
defaultValue :: Type -> Value
defaultValue typ = case reduceType typ of
    TVoid _ -> ""
    TInt _ -> "42"
    TFloat _ -> "6.0"
    TBool _ -> "true"
    TChar _ -> show (ord '$')
    otherwise -> "null"

-- | Casts value to a given type.
castValue :: Type -> Value -> Type -> Run Value
castValue typ1 val typ2 = case (typ1, typ2) of
    (TInt _, TFloat _) -> sitofp val
    otherwise -> return $ val

-- | Casts given values to a common type.
unifyValues :: Type -> Value -> Type -> Value -> Run (Type, Value, Value)
unifyValues typ1 val1 typ2 val2 = do
    t <- case (typ1, typ2) of
        (TInt _, TFloat _) -> return $ typ2
        otherwise -> return $ typ1
    v1 <- castValue typ1 val1 t
    v2 <- castValue typ2 val2 t
    return $ (t, v1, v2)


-- | Returns an unused index for temporary names.
nextNumber :: Run Int
nextNumber = do
    Number n <- lift $ gets (M.! "$number")
    lift $ modify (M.insert "$number" (Number (n+1)))
    return $ n+1

-- | Returns an unused register name in the form: '%t\d+'.
nextTemp :: Run Value
nextTemp = do
    n <- nextNumber
    return $ "%t" ++ show n

-- | Returns an unused variable name in the form: '@g\d+'.
nextGlobal :: Run Value
nextGlobal = do
    n <- nextNumber
    return $ "@g" ++ show n

-- | Returns an unused constant name in the form: '@c\d+'.
nextConst :: Run Value
nextConst = do
    n <- nextNumber
    return $ "@c" ++ show n

-- | Returns an unused label name in the form: 'L\d+'.
nextLabel :: Run Value
nextLabel = do
    n <- nextNumber
    return $ "L" ++ show n

-- | Starts new LLVM label with a given name.
label :: Value -> Run ()
label lbl = do
    write $ [ lbl ++ ":" ]
    s <- getScope
    lift $ modify (M.insert ("$label-" ++ s) (Label lbl))

-- | Returns name of the currently active label.
getLabel :: Run Value
getLabel = do
    s <- getScope
    Label l <- lift $ gets (M.! ("$label-" ++ s))
    return $ l

-- | Returns unique function name to use in LLVM code.
functionName :: Ident -> Run Value
functionName id = do
    s <- getScope
    let f = (if s !! 0 == '.' then s else "") ++ "." ++ escapeName id
    return $ f

-- | Returns a special identifier for function's argument in the environment.
argumentPointer :: Ident -> Ident -> Value
argumentPointer f a = "@g." ++ escapeName f ++ "." ++ escapeName a


-- | Outputs a function declaration.
declare :: Type -> Value -> Run ()
declare (TFunc _ args rt) name = do
    localScope "!global" $ write $ [ "declare " ++ strType rt ++ " " ++ name ++ "(" ++ intercalate ", " (map strType args) ++ ")" ]

-- | Outputs new function definition with given body.
define :: Type -> Ident -> Run () -> Run ()
define typ id body = do
    let (TFunc _ args rt) = typ
    f <- functionName id
    localScope f $ do
        (as, r) <- case rt of
            TTuple _ _ -> return $ (rt : args, tVoid)
            otherwise -> return $ (args, rt)
        writeTop $ [
            "@f" ++ f ++ " = global " ++ strType typ ++ " @func" ++ f,
            "define " ++ strType r ++ " @func" ++ f ++ "(" ++ intercalate ", " (map strType as) ++ ") {",
            "entry:" ]
        lift $ modify (M.insert ("$label-" ++ f) (Label "entry"))
        body
        write $ [ "}", "" ]

-- | Outputs LLVM 'br' command with a single goal.
goto :: Value -> Run ()
goto lbl = do
    write $ indent [ "br label %" ++ lbl ]

-- | Outputs LLVM 'br' command with two goals depending on a given value.
branch :: Value -> Value -> Value -> Run ()
branch val lbl1 lbl2 = do
    write $ indent [ "br i1 " ++ val ++ ", label %" ++ lbl1 ++ ", label %" ++ lbl2 ]

-- | Outputs LLVM 'alloca' command.
alloca :: Type -> Run Value
alloca typ = do
    p <- nextTemp
    writeTop $ indent [ p ++ " = alloca " ++ strType typ ]
    return $ p

-- | Outputs LLVM 'global' command.
global :: Type -> Value -> Run Value
global typ val = do
    g <- nextGlobal
    writeTop $ [ g ++ " = global " ++ strType typ ++ " " ++ val ]
    return $ g

-- | Outputs LLVM constant command.
constant :: Type -> Value -> Run Value
constant typ val = do
    c <- nextConst
    writeTop $ [ c ++ " = constant " ++ strType typ ++ " " ++ val ]
    return $ c

-- | Outputs LLVM 'external global' command.
external :: Value -> Type -> Run Value
external name typ = do
    writeTop $ [ name ++ " = external global " ++ strType typ ]
    return $ name

-- | Outputs LLVM 'store' command.
store :: Type -> Value -> Value -> Run ()
store typ val ptr = do
    if val == "" then skip
    else write $ indent [ "store " ++ strType typ ++ " " ++ val ++ ", " ++ strType typ ++ "* " ++ ptr ]

-- | Outputs LLVM 'load' command.
load :: Type -> Value -> Run Value
load typ ptr = do
    v <- nextTemp
    write $ indent [ v ++ " = load " ++ strType typ ++ ", " ++ strType typ ++ "* " ++ ptr ]
    return $ v

-- | Allocates a new identifier, outputs corresponding LLVM code, and runs continuation with changed environment.
variable :: Type -> Ident -> Value -> Run a -> Run a
variable typ id val cont = do
    s <- getScope
    p <- case s of
        "main" -> localScope "!global" $ global typ (defaultValue typ)
        otherwise -> alloca typ
    store typ val p
    localVar id typ p cont

-- | Outputs LLVM 'getelementptr' command with given indices.
gep :: Type -> Value -> [Value] -> [Int] -> Run Value
gep typ val inds1 inds2 = do
    p <- nextTemp
    write $ indent [ p ++ " = getelementptr inbounds " ++ strType (tDeref typ) ++ ", " ++ strType typ ++ " " ++ val ++ intercalate "" [", i64 " ++ i | i <- inds1] ++ intercalate "" [", i32 " ++ show i | i <- inds2] ]
    return $ p

-- | Outputs LLVM 'bitcast' command.
bitcast :: Type -> Type -> Value -> Run Value
bitcast typ1 typ2 ptr = do
    p <- nextTemp
    write $ indent [ p ++ " = bitcast " ++ strType typ1 ++ " " ++ ptr ++ " to " ++ strType typ2 ]
    return $ p

-- | Outputs LLVM 'ptrtoint' command.
ptrtoint :: Type -> Value -> Run Value
ptrtoint typ ptr = do
    v <- nextTemp
    write $ indent [ v ++ " = ptrtoint " ++ strType typ ++ " " ++ ptr ++ " to i64" ]
    return $ v

-- | Outputs LLVM 'sitofp' command to convert from Int to Float.
sitofp :: Value -> Run Value
sitofp val = do
    v <- nextTemp
    write $ indent [ v ++ " = sitofp " ++ strType tInt ++ " " ++ val ++ " to " ++ strType tFloat ]
    return $ v

-- | Outputs LLVM 'fptosi' command to convert from Float to Int.
fptosi :: Value -> Run Value
fptosi val = do
    v <- nextTemp
    write $ indent [ v ++ " = fptosi " ++ strType tFloat ++ " " ++ val ++ " to " ++ strType tInt ]
    return $ v

-- | Outputs LLVM 'trunc' command.
trunc :: Type -> Type -> Value -> Run Value
trunc typ1 typ2 val = do
    v <- nextTemp
    write $ indent [ v ++ " = trunc " ++ strType typ1 ++ " " ++ val ++ " to " ++ strType typ2 ]
    return $ v

-- | Outputs LLVM 'zext' command.
zext :: Type -> Type -> Value -> Run Value
zext typ1 typ2 val = do
    v <- nextTemp
    write $ indent [ v ++ " = zext " ++ strType typ1 ++ " " ++ val ++ " to " ++ strType typ2 ]
    return $ v

-- | Outputs LLVM 'select' instruction for given values.
select :: String -> Type -> Value -> Value -> Run Value
select val typ opt1 opt2 = do
    v <- nextTemp
    write $ indent [ v ++ " = select i1 " ++ val ++ ", " ++ strType typ ++ " " ++ opt1 ++ ", " ++ strType typ ++ " " ++ opt2 ]
    return $ v

-- | Outputs LLVM 'phi' instruction for given values and label names.
phi :: [(Value, Value)] -> Run Value
phi opts = do
    v <- nextTemp
    write $ indent [ v ++ " = phi i1 " ++ (intercalate ", " ["[" ++ v ++ ", %" ++ l ++ "]" | (v, l) <- opts]) ]
    return $ v

-- | Outputs LLVM binary operation instruction.
binop :: String -> Type -> Value -> Value -> Run Value
binop op typ val1 val2 = do
    v <- nextTemp
    write $ indent [ v ++ " = " ++ op ++ " " ++ strType typ ++ " " ++ val1 ++ ", " ++ val2 ]
    return $ v

-- | Outputs LLVM function 'call' instruction.
call :: Type -> Value -> [Result] -> Run Value
call rt name args = do
    v <- nextTemp
    c <- case rt of
        TVoid _ -> return $ "call "
        TTuple _ _ -> return $ "call "
        otherwise -> return $ v ++ " = call "
    case rt of
        TTuple _ _ -> do
            p <- alloca (tDeref rt)
            write $ indent [ c ++ "void " ++ name ++ "(" ++ intercalate ", " [strType t ++ " " ++ v | (t, v) <- (rt, p) : args] ++ ")" ]
            return $ p
        otherwise -> do
            write $ indent [ c ++ strType rt ++ " " ++ name ++ "(" ++ intercalate ", " [strType t ++ " " ++ v | (t, v) <- args] ++ ")" ]
            return $ v

-- | Outputs LLVM function 'call' with void return type.
callVoid :: Value -> [Result] -> Run ()
callVoid name args = do
    call tVoid name args
    skip

-- | Outputs LLVM 'ret' instruction.
ret :: Type -> Value -> Run ()
ret typ val = case typ of
    TTuple _ _ -> do
        p1 <- bitcast typ (tPtr tChar) "%0"
        p2 <- bitcast typ (tPtr tChar) val
        v <- sizeof typ "1"
        call (tPtr tChar) "@memcpy" [(tPtr tChar, p1), (tPtr tChar, p2), (tInt, v)]
        retVoid
    otherwise -> do
        write $ indent [ "ret " ++ strType typ ++ " " ++ val ]

-- | Outputs LLVM 'ret void' instruction.
retVoid :: Run ()
retVoid = do
    ret tVoid ""


-- | Outputs LLVM code to calculate memory size of an array of objects of a given type.
sizeof :: Type -> Value -> Run Value
sizeof typ len = do
    gep typ "null" [len] [] >>= ptrtoint typ

-- | Outputs LLVM code to allocate memory for objects of a given type.
initMemory :: Type -> Value -> Run Value
initMemory typ len = do
    v <- sizeof typ len
    call (tPtr tChar) "@malloc" [(tInt, v)] >>= bitcast (tPtr tChar) typ

-- | Outputs LLVM code for tuple initialization.
initTuple :: [Result] -> Run Value
initTuple rs = do
    let t = tTuple (map fst rs)
    p <- alloca (tDeref t)
    forM (zipWith (\r i -> (fst r, snd r, i)) rs [0..]) $ \(t', v', i) -> do
        gep t p ["0"] [i] >>= store t' v'
    return $ p

-- | Outputs LLVM code for string initialization.
initString :: String -> Run Value
initString str = do
    let l = length str
    let t = (tArr (toInteger l) tChar)
    c <- localScope "!global" $ constant t ("[" ++ intercalate ", " [strType tChar ++ " " ++ show (ord c) | c <- str] ++ "]")
    p1 <- initMemory tString "1"
    p2 <- gep (tPtr t) c ["0"] [0]
    gep tString p1 ["0"] [0] >>= store (tPtr tChar) p2
    gep tString p1 ["0"] [1] >>= store tInt (show l)
    return $ p1

-- | Outputs LLVM code for array initialization.
-- |   'lens' is an array of two optional values:
-- |   - length which will be saved in the .length attribute,
-- |   - size of allocated memory.
-- |   Any omitted value will default to the length of 'vals'.
initArray :: Type -> [Value] -> [Value] -> Run Value
initArray typ vals lens = do
    let t1 = tArray typ
    let t2 = tPtr typ
    let len1:len2:_ = lens ++ replicate 2 (show (length vals))
    p1 <- initMemory t1 "1"
    p2 <- initMemory t2 len2
    gep t1 p1 ["0"] [0] >>= store t2 p2
    gep t1 p1 ["0"] [1] >>= store tInt len1
    forM (zip [0..] vals) (\(i, v) -> gep t2 p2 [show i] [] >>= store typ v)
    return $ p1
