
module CodeGen where

import Control.Monad.Identity
import Control.Monad.Trans.Class
import Control.Monad.Trans.State
import Control.Monad.Trans.Reader
import Data.Char
import Data.List
import qualified Data.Map as M

import AbsPyxell hiding (Type)

import Utils


-- | Type and name of LLVM register(s).
type Result = (Type, String)

-- | Identifier environment.
type Env = M.Map String Result

-- | State item (for storing different data).
data StateItem = Number Int | Label String

-- | LLVM code for each scope (function or global).
type Output = M.Map String [String]

-- | Compiler monad: Reader for identifier environment, State to store some useful values and the output LLVM code.
type Run r = ReaderT (M.Map String Result) (StateT (M.Map String StateItem) (StateT Output IO)) r


-- | Does nothing.
skip :: Run ()
skip = do
    return $ ()

-- | Runs compilation in a given scope (function).
scope :: String -> Run a -> Run a
scope name cont = do
    local (M.insert "#scope" (tVoid, name)) cont

-- | Returns name of the current scope (function).
getScope :: Run String
getScope = do
    r <- asks (M.lookup "#scope")
    case r of
        Just (_, name) -> return $ name
        Nothing -> return $ "!global"

-- | Outputs several lines of LLVM code.
write :: [String] -> Run ()
write lines = do
    s <- getScope
    lift $ lift $ modify (M.insertWith (++) s (reverse lines))

-- | Adds an indent to given lines.
indent :: [String] -> [String]
indent lines = map ('\t':) lines

-- | Gets an identifier from the environment.
getIdent :: Ident -> Run (Maybe Result)
getIdent (Ident x) = asks (M.lookup x)


-- | LLVM string representation for a given type.
strType :: Type -> String
strType typ = case reduceType typ of
    TPtr _ t -> strType t ++ "*"
    TArr _ n t -> "[" ++ show n ++ " x " ++ strType t ++ "]"
    TDeref _ t -> init (strType t)
    TVoid _ -> "void"
    TInt _ -> "i64"
    TBool _ -> "i1"
    TChar _ -> "i8"
    TObject _ -> "i8*"
    TString _ -> strType (tArray tChar)
    TArray _ t -> "{" ++ strType t ++ "*, i64}*"
    TTuple _ ts -> "{" ++ intercalate ", " (map strType ts) ++ "}*"
    TFunc _ as r -> (strType.reduceType) r ++ " (" ++ intercalate ", " (map (strType.reduceType) as) ++ ")*"
    TArgN _ t' -> strType t'
    TArgD _ t' _ -> strType t'

-- | Returns a default value for a given type.
-- | This function is for LLVM code and only serves its internal requirements.
-- | Returned values are not to be relied upon.
defaultValue :: Type -> String
defaultValue typ = case typ of
    TVoid _ -> ""
    TInt _ -> "42"
    TBool _ -> "true"
    TChar _ -> show (ord '$')
    otherwise -> "null"

-- | Returns an unused index for temporary names.
nextNumber :: Run Int
nextNumber = do
    Number n <- lift $ gets (M.! "$number")
    lift $ modify (M.insert "$number" (Number (n+1)))
    return $ n+1

-- | Returns an unused register name in the form: '%t\d+'.
nextTemp :: Run String
nextTemp = do
    n <- nextNumber
    return $ "%t" ++ show n

-- | Returns an unused variable name in the form: '@g\d+'.
nextGlobal :: Run String
nextGlobal = do
    n <- nextNumber
    return $ "@g" ++ show n

-- | Returns an unused constant name in the form: '@c\d+'.
nextConst :: Run String
nextConst = do
    n <- nextNumber
    return $ "@c" ++ show n

-- | Returns an unused label name in the form: 'L\d+'.
nextLabel :: Run String
nextLabel = do
    n <- nextNumber
    return $ "L" ++ show n

-- | Starts new LLVM label with a given name.
label :: String -> Run ()
label lbl = do
    write $ [ lbl ++ ":" ]
    s <- getScope
    lift $ modify (M.insert ("$label-" ++ s)  (Label lbl))

-- | Returns name of the currently active label.
getLabel :: Run String
getLabel = do
    s <- getScope
    Label l <- lift $ gets (M.! ("$label-" ++ s))
    return $ l

-- | Outputs a function declaration.
declare :: Type -> String -> Run ()
declare (TFunc _ args rt) name = do
    scope "!global" $ write $ [ "declare " ++ strType rt ++ " " ++ name ++ "(" ++ intercalate ", " (map strType args) ++ ")" ]

-- | Outputs new function definition with given body.
define :: Type -> String -> Run () -> Run ()
define typ name body = do
    let (TFunc _ args rt) = typ
    s <- getScope
    let f = (if s !! 0 == '.' then s else "") ++ "." ++ escapeName name
    scope f $ do
        write $ [
            "@f" ++ f ++ " = global " ++ strType typ ++ " @func" ++ f,
            "define " ++ strType rt ++ " @func" ++ f ++ "(" ++ intercalate ", " (map strType args) ++ ") {",
            "entry:" ]
        lift $ modify (M.insert ("$label-" ++ f) (Label "entry"))
        body
        write $ [ "}" ]

-- | Outputs LLVM 'br' command with a single goal.
goto :: String -> Run ()
goto lbl = do
    write $ indent [ "br label %" ++ lbl ]

-- | Outputs LLVM 'br' command with two goals depending on a given value.
branch :: String -> String -> String -> Run ()
branch val lbl1 lbl2 = do
    write $ indent [ "br i1 " ++ val ++ ", label %" ++ lbl1 ++ ", label %" ++ lbl2 ]

-- | Outputs LLVM 'alloca' command.
alloca :: Type -> Run String
alloca typ = do
    p <- nextTemp
    write $ indent [ p ++ " = alloca " ++ strType typ ]
    return $ p

-- | Outputs LLVM 'global' command.
global :: Type -> String -> Run String
global typ val = do
    g <- nextGlobal
    write $ [ g ++ " = global " ++ strType typ ++ " " ++ val ]
    return $ g

-- | Outputs LLVM constant command.
constant :: Type -> String -> Run String
constant typ val = do
    c <- nextConst
    write $ [ c ++ " = constant " ++ strType typ ++ " " ++ val ]
    return $ c

-- | Outputs LLVM 'external global' command.
external :: String -> Type -> Run String
external name typ = do
    write $ [ name ++ " = external global " ++ strType typ ]
    return $ name

-- | Outputs LLVM 'store' command.
store :: Type -> String -> String -> Run ()
store typ val ptr = do
    if val == "" then skip
    else write $ indent [ "store " ++ strType typ ++ " " ++ val ++ ", " ++ strType typ ++ "* " ++ ptr ]

-- | Outputs LLVM 'load' command.
load :: Type -> String -> Run String
load typ ptr = do
    v <- nextTemp
    write $ indent [ v ++ " = load " ++ strType typ ++ ", " ++ strType typ ++ "* " ++ ptr ]
    return $ v

-- | Allocates a new identifier, outputs corresponding LLVM code, and runs continuation with changed environment.
variable :: Type -> Ident -> String -> Run a -> Run a
variable typ (Ident x) val cont = do
    s <- getScope
    p <- case s of
        "main" -> scope "!global" $ global typ (defaultValue typ)
        otherwise -> alloca typ
    store typ val p
    local (M.insert x (typ, p)) cont

-- | Outputs LLVM 'getelementptr' command with given indices.
gep :: Type -> String -> [String] -> [Int] -> Run String
gep typ val inds1 inds2 = do
    p <- nextTemp
    write $ indent [ p ++ " = getelementptr inbounds " ++ strType (tDeref typ) ++ ", " ++ strType typ ++ " " ++ val ++ intercalate "" [", i64 " ++ i | i <- inds1] ++ intercalate "" [", i32 " ++ show i | i <- inds2] ]
    return $ p

-- | Outputs LLVM 'bitcast' command.
bitcast :: Type -> Type -> String -> Run String
bitcast typ1 typ2 ptr = do
    p <- nextTemp
    write $ indent [ p ++ " = bitcast " ++ strType typ1 ++ " " ++ ptr ++ " to " ++ strType typ2 ]
    return $ p

-- | Outputs LLVM 'ptrtoint' command.
ptrtoint :: Type -> String -> Run String
ptrtoint typ ptr = do
    v <- nextTemp
    write $ indent [ v ++ " = ptrtoint " ++ strType typ ++ " " ++ ptr ++ " to i64" ]
    return $ v

-- | Outputs LLVM 'trunc' command.
trunc :: Type -> Type -> String -> Run String
trunc typ1 typ2 val = do
    v <- nextTemp
    write $ indent [ v ++ " = trunc " ++ strType typ1 ++ " " ++ val ++ " to " ++ strType typ2 ]
    return $ v

-- | Outputs LLVM 'zext' command.
zext :: Type -> Type -> String -> Run String
zext typ1 typ2 val = do
    v <- nextTemp
    write $ indent [ v ++ " = zext " ++ strType typ1 ++ " " ++ val ++ " to " ++ strType typ2 ]
    return $ v

-- | Outputs LLVM 'select' instruction for given values.
select :: String -> Type -> String -> String -> Run String
select val typ opt1 opt2 = do
    v <- nextTemp
    write $ indent [ v ++ " = select i1 " ++ val ++ ", " ++ strType typ ++ " " ++ opt1 ++ ", " ++ strType typ ++ " " ++ opt2 ]
    return $ v

-- | Outputs LLVM 'phi' instruction for given values and label names.
phi :: [(String, String)] -> Run String
phi opts = do
    v <- nextTemp
    write $ indent [ v ++ " = phi i1 " ++ (intercalate ", " ["[" ++ v ++ ", %" ++ l ++ "]" | (v, l) <- opts]) ]
    return $ v

-- | Outputs LLVM binary operation instruction.
binop :: String -> Type -> String -> String -> Run String
binop op typ val1 val2 = do
    v <- nextTemp
    write $ indent [ v ++ " = " ++ op ++ " " ++ strType typ ++ " " ++ val1 ++ ", " ++ val2 ]
    return $ v

-- | Outputs LLVM function 'call' instruction.
call :: Type -> String -> [Result] -> Run String
call rt name args = do
    v <- nextTemp
    c <- case rt of
        TVoid _ -> return $ "call "
        otherwise -> return $ v ++ " = call "
    write $ indent [ c ++ strType rt ++ " " ++ name ++ "(" ++ intercalate ", " [strType t ++ " " ++ v | (t, v) <- args] ++ ")" ]
    return $ v

-- | Outputs LLVM function 'call' with void return type.
callVoid :: String -> [Result] -> Run ()
callVoid name args = do
    call tVoid name args
    skip

-- | Outputs LLVM 'ret' instruction.
ret :: Type -> String -> Run ()
ret typ val = do
    write $ indent [ "ret " ++ strType typ ++ " " ++ val ]


-- | Outputs LLVM code for string initialization.
initString :: String -> Run Result
initString s = do
    let l = length s
    let t = (tArr (toInteger l) tChar)
    c <- scope "!global" $ constant t ("[" ++ intercalate ", " [strType tChar ++ " " ++ show (ord c) | c <- s] ++ "]")
    v <- gep tString "null" ["1"] [] >>= ptrtoint tString
    p1 <- call (tPtr tChar) "@malloc" [(tInt, v)] >>= bitcast (tPtr tChar) tString
    p2 <- gep (tPtr t) c ["0"] [0]
    gep tString p1 ["0"] [0] >>= store (tPtr tChar) p2
    gep tString p1 ["0"] [1] >>= store tInt (show l)
    return $ (tString, p1)

-- | Outputs LLVM code for array initialization.
-- |   'lens' is an array of two optional values:
-- |   - length which will be saved in the .length attribute,
-- |   - size of allocated memory.
-- |   Any omitted value will default to the length of 'vals'.
initArray :: Type -> [String] -> [String] -> Run Result
initArray typ vals lens = do
    let t1 = tArray typ
    let t2 = tPtr typ
    let len1:len2:_ = lens ++ replicate 2 (show (length vals))
    v1 <- gep t1 "null" ["1"] [] >>= ptrtoint t1
    p1 <- call (tPtr tChar) "@malloc" [(tInt, v1)] >>= bitcast (tPtr tChar) t1
    v2 <- gep t2 "null" [len2] [] >>= ptrtoint t2
    p2 <- call (tPtr tChar) "@malloc" [(tInt, v2)] >>= bitcast (tPtr tChar) t2
    gep t1 p1 ["0"] [0] >>= store t2 p2
    gep t1 p1 ["0"] [1] >>= store tInt len1
    forM (zip [0..] vals) (\(i, v) -> gep t2 p2 [show i] [] >>= store typ v)
    return $ (t1, p1)
