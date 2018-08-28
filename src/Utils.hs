{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}
{-# LANGUAGE FlexibleInstances #-}

module Utils where

import Data.List

import AbsPyxell hiding (Type)
import qualified AbsPyxell as Abs (Type)


-- | Representation of a position in the program's source code.
type Pos = Maybe (Int, Int)

-- | Alias for Type without passing Pos.
type Type = Abs.Type Pos

-- | Show instance for displaying types.
instance {-# OVERLAPS #-} Show Type where
    show typ = case typ of
        TVoid _ -> "Void"
        TInt _ -> "Int"
        TBool _ -> "Bool"
        TChar _ -> "Char"
        TObject _ -> "Object"
        TString _ -> "String"
        TArray _ t -> "[" ++ show t ++ "]"
        --TPower _ typ exp -> show typ ++ show exp
        TTuple _ types -> intercalate "*" (map show types)
        TFunc _ args ret -> "(" ++ intercalate "," (map show args) ++ ")->" ++ show ret

-- | Unification function. Returns a common supertype of given types.
unifyTypes :: Type -> Type -> Maybe Type
unifyTypes t1 t2 = do
    case (t1, t2) of
        (TVoid _, TVoid _) -> Just tInt
        (TInt _, TInt _) -> Just tInt
        (TBool _, TBool _) -> Just tBool
        (TChar _, TChar _) -> Just tChar
        --(TObject _, _) -> tObject
        --(_, TObject _) -> tObject
        (TString _, TString _) -> Just tString
        (TArray _ t1', TArray _ t2') -> fmap tArray (unifyTypes t1' t2')
        (TTuple _ ts1, TTuple _ ts2) ->
            if length ts1 == length ts2 then fmap tTuple (sequence (map (uncurry unifyTypes) (zip ts1 ts2)))
            else Nothing
        (TFunc _ as1 r1, TFunc _ as2 r2) ->
            if length as1 == length as2 then case (sequence (map (uncurry unifyTypes) (zip as1 as2)), (unifyTypes r1 r2)) of
                (Just as, Just r) -> Just (tFunc as r)
                otherwise -> Nothing
            else Nothing
        otherwise -> Nothing

-- | Try to reduce compound type to a simpler version (e.g. one-element tuple to the base type).
reduceType :: Type -> Type
reduceType t = do
    case t of
        TArray _ t' -> tArray (reduceType t')
        TTuple _ ts -> if length ts == 1 then reduceType (head ts) else tTuple (map reduceType ts)
        TFunc _ as r -> tFunc (map reduceType as) (reduceType r)
        otherwise -> t

-- | Helper functions for initializing types without a position.
tPtr = TPtr Nothing
tDeref = TDeref Nothing
tLabel = TLabel Nothing
tVoid = TVoid Nothing
tInt = TInt Nothing
tBool = TBool Nothing
tChar = TChar Nothing
tObject = TObject Nothing
tString = TString Nothing
tArray = TArray Nothing
tTuple = TTuple Nothing
tFunc = TFunc Nothing

-- | Shorter name for none position.
_pos = Nothing

-- | Gets name from an identifier.
fromIdent (Ident x) = x
