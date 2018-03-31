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
        TInt _ -> "Int"
        TBool _ -> "Bool"
        TString _ -> "String"
        --TPower _ typ exp -> show typ ++ show exp
        TTuple _ types -> intercalate "*" $ map show types
        --TFunc _ typ1 typ2 -> show typ1 ++ "->" ++ show typ2

-- | Helper functions for initializing types without a position.
tDeref = TDeref Nothing
tInt = TInt Nothing
tBool = TBool Nothing
tString = TString Nothing
tTuple = TTuple Nothing

-- | Shorter name for none position.
_pos = Nothing