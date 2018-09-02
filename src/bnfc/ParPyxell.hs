{-# OPTIONS_GHC -w #-}
{-# OPTIONS -XMagicHash -XBangPatterns -XTypeSynonymInstances -XFlexibleInstances -cpp #-}
#if __GLASGOW_HASKELL__ >= 710
{-# OPTIONS_GHC -XPartialTypeSignatures #-}
#endif
{-# OPTIONS_GHC -fno-warn-incomplete-patterns -fno-warn-overlapping-patterns #-}
module ParPyxell where
import AbsPyxell
import LexPyxell
import ErrM
import qualified Data.Array as Happy_Data_Array
import qualified Data.Bits as Bits
import qualified GHC.Exts as Happy_GHC_Exts
import Control.Applicative(Applicative(..))
import Control.Monad (ap)

-- parser produced by Happy Version 1.19.8

newtype HappyAbsSyn  = HappyAbsSyn HappyAny
#if __GLASGOW_HASKELL__ >= 607
type HappyAny = Happy_GHC_Exts.Any
#else
type HappyAny = forall a . a
#endif
happyIn34 :: ((Maybe (Int, Int), Ident)) -> (HappyAbsSyn )
happyIn34 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn34 #-}
happyOut34 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Ident))
happyOut34 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut34 #-}
happyIn35 :: ((Maybe (Int, Int), Integer)) -> (HappyAbsSyn )
happyIn35 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn35 #-}
happyOut35 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Integer))
happyOut35 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut35 #-}
happyIn36 :: ((Maybe (Int, Int), Char)) -> (HappyAbsSyn )
happyIn36 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn36 #-}
happyOut36 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Char))
happyOut36 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut36 #-}
happyIn37 :: ((Maybe (Int, Int), String)) -> (HappyAbsSyn )
happyIn37 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn37 #-}
happyOut37 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), String))
happyOut37 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut37 #-}
happyIn38 :: ((Maybe (Int, Int), Program (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn38 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn38 #-}
happyOut38 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Program (Maybe (Int, Int))))
happyOut38 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut38 #-}
happyIn39 :: ((Maybe (Int, Int), [Stmt (Maybe (Int, Int))])) -> (HappyAbsSyn )
happyIn39 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn39 #-}
happyOut39 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), [Stmt (Maybe (Int, Int))]))
happyOut39 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut39 #-}
happyIn40 :: ((Maybe (Int, Int), Stmt (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn40 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn40 #-}
happyOut40 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Stmt (Maybe (Int, Int))))
happyOut40 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut40 #-}
happyIn41 :: ((Maybe (Int, Int), Arg (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn41 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn41 #-}
happyOut41 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Arg (Maybe (Int, Int))))
happyOut41 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut41 #-}
happyIn42 :: ((Maybe (Int, Int), [Arg (Maybe (Int, Int))])) -> (HappyAbsSyn )
happyIn42 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn42 #-}
happyOut42 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), [Arg (Maybe (Int, Int))]))
happyOut42 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut42 #-}
happyIn43 :: ((Maybe (Int, Int), Block (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn43 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn43 #-}
happyOut43 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Block (Maybe (Int, Int))))
happyOut43 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut43 #-}
happyIn44 :: ((Maybe (Int, Int), [Expr (Maybe (Int, Int))])) -> (HappyAbsSyn )
happyIn44 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn44 #-}
happyOut44 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), [Expr (Maybe (Int, Int))]))
happyOut44 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut44 #-}
happyIn45 :: ((Maybe (Int, Int), Branch (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn45 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn45 #-}
happyOut45 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Branch (Maybe (Int, Int))))
happyOut45 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut45 #-}
happyIn46 :: ((Maybe (Int, Int), [Branch (Maybe (Int, Int))])) -> (HappyAbsSyn )
happyIn46 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn46 #-}
happyOut46 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), [Branch (Maybe (Int, Int))]))
happyOut46 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut46 #-}
happyIn47 :: ((Maybe (Int, Int), Else (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn47 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn47 #-}
happyOut47 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Else (Maybe (Int, Int))))
happyOut47 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut47 #-}
happyIn48 :: ((Maybe (Int, Int), Expr (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn48 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn48 #-}
happyOut48 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Expr (Maybe (Int, Int))))
happyOut48 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut48 #-}
happyIn49 :: ((Maybe (Int, Int), [Expr (Maybe (Int, Int))])) -> (HappyAbsSyn )
happyIn49 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn49 #-}
happyOut49 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), [Expr (Maybe (Int, Int))]))
happyOut49 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut49 #-}
happyIn50 :: ((Maybe (Int, Int), Expr (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn50 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn50 #-}
happyOut50 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Expr (Maybe (Int, Int))))
happyOut50 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut50 #-}
happyIn51 :: ((Maybe (Int, Int), Expr (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn51 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn51 #-}
happyOut51 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Expr (Maybe (Int, Int))))
happyOut51 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut51 #-}
happyIn52 :: ((Maybe (Int, Int), Expr (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn52 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn52 #-}
happyOut52 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Expr (Maybe (Int, Int))))
happyOut52 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut52 #-}
happyIn53 :: ((Maybe (Int, Int), Expr (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn53 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn53 #-}
happyOut53 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Expr (Maybe (Int, Int))))
happyOut53 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut53 #-}
happyIn54 :: ((Maybe (Int, Int), Cmp (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn54 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn54 #-}
happyOut54 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Cmp (Maybe (Int, Int))))
happyOut54 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut54 #-}
happyIn55 :: ((Maybe (Int, Int), CmpOp (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn55 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn55 #-}
happyOut55 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), CmpOp (Maybe (Int, Int))))
happyOut55 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut55 #-}
happyIn56 :: ((Maybe (Int, Int), Expr (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn56 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn56 #-}
happyOut56 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Expr (Maybe (Int, Int))))
happyOut56 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut56 #-}
happyIn57 :: ((Maybe (Int, Int), Expr (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn57 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn57 #-}
happyOut57 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Expr (Maybe (Int, Int))))
happyOut57 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut57 #-}
happyIn58 :: ((Maybe (Int, Int), Expr (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn58 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn58 #-}
happyOut58 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Expr (Maybe (Int, Int))))
happyOut58 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut58 #-}
happyIn59 :: ((Maybe (Int, Int), [Expr (Maybe (Int, Int))])) -> (HappyAbsSyn )
happyIn59 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn59 #-}
happyOut59 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), [Expr (Maybe (Int, Int))]))
happyOut59 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut59 #-}
happyIn60 :: ((Maybe (Int, Int), Expr (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn60 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn60 #-}
happyOut60 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Expr (Maybe (Int, Int))))
happyOut60 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut60 #-}
happyIn61 :: ((Maybe (Int, Int), Expr (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn61 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn61 #-}
happyOut61 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Expr (Maybe (Int, Int))))
happyOut61 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut61 #-}
happyIn62 :: ((Maybe (Int, Int), Type (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn62 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn62 #-}
happyOut62 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Type (Maybe (Int, Int))))
happyOut62 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut62 #-}
happyIn63 :: ((Maybe (Int, Int), Type (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn63 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn63 #-}
happyOut63 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Type (Maybe (Int, Int))))
happyOut63 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut63 #-}
happyIn64 :: ((Maybe (Int, Int), [Type (Maybe (Int, Int))])) -> (HappyAbsSyn )
happyIn64 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn64 #-}
happyOut64 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), [Type (Maybe (Int, Int))]))
happyOut64 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut64 #-}
happyIn65 :: ((Maybe (Int, Int), [Type (Maybe (Int, Int))])) -> (HappyAbsSyn )
happyIn65 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn65 #-}
happyOut65 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), [Type (Maybe (Int, Int))]))
happyOut65 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut65 #-}
happyIn66 :: ((Maybe (Int, Int), Type (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn66 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn66 #-}
happyOut66 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Type (Maybe (Int, Int))))
happyOut66 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut66 #-}
happyIn67 :: ((Maybe (Int, Int), Type (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn67 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn67 #-}
happyOut67 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Type (Maybe (Int, Int))))
happyOut67 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut67 #-}
happyIn68 :: ((Maybe (Int, Int), Type (Maybe (Int, Int)))) -> (HappyAbsSyn )
happyIn68 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyIn68 #-}
happyOut68 :: (HappyAbsSyn ) -> ((Maybe (Int, Int), Type (Maybe (Int, Int))))
happyOut68 x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOut68 #-}
happyInTok :: (Token) -> (HappyAbsSyn )
happyInTok x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyInTok #-}
happyOutTok :: (HappyAbsSyn ) -> (Token)
happyOutTok x = Happy_GHC_Exts.unsafeCoerce# x
{-# INLINE happyOutTok #-}


happyExpList :: HappyAddr
happyExpList = HappyA# "\x00\x00\x00\x00\x00\x00\x00\x00\x40\x20\x00\x00\x90\xc1\xeb\xf3\x00\x00\x00\x00\x00\x00\x00\x00\x80\x40\x00\x00\x20\x83\xd7\xe7\x01\x00\x00\x00\x00\x00\x00\x00\x00\x81\x00\x00\x40\x06\xaf\xcf\x03\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\xf7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\xee\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x08\x00\x00\x04\x10\x42\x3c\x00\x00\x00\x00\x00\x00\x00\x00\x20\x10\x00\x00\x08\x20\x84\x78\x00\x00\x00\x00\x00\x00\x00\x00\x40\x20\x00\x00\x10\x40\x08\xf1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x40\x00\x01\xc4\x03\x00\x00\x00\x00\x00\x00\x00\x00\x02\x01\x00\x80\x00\x42\x88\x07\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x01\x04\x10\x0f\x00\x00\x00\x00\x00\x00\x00\x00\x08\x04\x00\x00\x02\x08\x20\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x10\x08\x00\x00\x04\x10\x40\x3c\x00\x00\x00\x00\x00\x00\x00\x00\x20\x10\x00\x00\x08\x20\x84\x78\x00\x00\x00\x00\x00\x00\x00\x00\x40\x20\x00\x00\x10\x40\x00\xf1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x81\x00\x00\x40\x00\x21\xc4\x03\x00\x00\x00\x00\x00\x00\x00\x00\x02\x01\x00\x80\x00\x42\x88\x07\x00\x00\x00\x00\x00\x00\x00\x00\x04\x02\x00\x00\x01\x84\x10\x0f\x00\x00\x00\x00\x00\x00\x00\x00\x08\x04\x00\x00\x02\x08\x21\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x10\x08\x00\x00\x04\x10\x42\x3c\x00\x00\x00\x00\x00\x00\x00\x00\x20\x10\x00\x00\x08\x20\x84\x78\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\xe0\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\xc0\x3d\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x80\x7b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\xf7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\xee\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\xdc\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\xb8\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\xf7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x80\x7b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x10\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x22\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x89\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe0\x0e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x04\x00\x00\x02\x08\x21\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x04\x10\x40\x3c\x00\x00\x00\x00\x00\x00\x00\x00\x20\x10\x00\x00\x08\x20\x84\x78\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x40\x00\x00\x20\x80\x10\xe2\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe0\x0e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x11\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x80\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x40\x00\x00\x20\x83\xd7\xe7\x01\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x4a\x10\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x01\x00\x80\x00\x42\x88\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x08\x04\x00\x00\x02\x08\x21\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x10\x08\x00\x00\x04\x10\x42\x3c\x00\x00\x00\x00\x00\x00\x00\x00\x20\x10\x00\x00\x08\x20\x84\x78\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x40\x00\x00\x20\x80\x10\xe2\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x08\x00\x00\x64\xf0\xfa\x3c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x04\x00\x00\x02\x08\x21\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x10\x08\x00\x00\x04\x10\x42\x3c\x00\x00\x00\x00\x00\x00\x00\x00\x20\x10\x00\x00\x08\x20\x84\x78\x00\x00\x00\x00\x00\x00\x00\x00\x40\x20\x00\x00\x10\x40\x08\xf1\x00\x00\x00\x00\x00\x00\x00\x00\x80\x40\x00\x00\x20\x80\x10\xe2\x01\x00\x00\x00\x00\x00\x00\x00\x00\x81\x00\x00\x40\x00\x21\xc4\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\xee\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x20\x10\x00\x00\x08\x20\x84\x78\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x80\x40\x00\x00\x20\x80\x10\xe2\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x01\x00\x80\x00\x42\x88\x07\x00\x00\x00\x00\x00\x00\x00\x00\x04\x02\x00\x00\x01\x84\x10\x0f\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x02\x08\x20\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x04\x10\x40\x3c\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x08\x20\x80\x78\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x10\x40\x00\xf1\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x20\x80\x00\xe2\x01\x00\x00\x00\x00\x00\x00\x00\x00\x81\x00\x00\x40\x00\x01\xc4\x03\x00\x00\x00\x00\x00\x00\x00\x00\x02\x01\x00\x80\x00\x42\x88\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x44\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x20\x00\x00\x10\x40\x08\xf1\x00\x00\x00\x00\x00\x00\x00\x00\x80\x40\x00\x00\x20\x80\x10\xe2\x01\x00\x00\x00\x00\x00\x00\x00\x00\x81\x00\x00\x40\x00\x01\xc4\x03\x00\x00\x00\x00\x00\x00\x00\x00\x02\x01\x00\x80\x00\x02\x88\x07\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\xee\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\xdc\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\xb8\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x89\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x12\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb8\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x88\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x01\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x02\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x04\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x08\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x02\x00\x00\x01\x84\x10\x0f\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\xdc\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x08\x00\x00\x04\x10\x40\x3c\x00\x00\x00\x00\x00\x00\x00\x00\x20\x10\x00\x00\x08\x20\x80\x78\x00\x00\x00\x00\x00\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x48\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\xf7\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"#

{-# NOINLINE happyExpListPerState #-}
happyExpListPerState st =
    token_strs_expected
  where token_strs = ["error","%dummy","%start_pProgram_internal","%start_pListStmt_internal","%start_pStmt_internal","%start_pArg_internal","%start_pListArg_internal","%start_pBlock_internal","%start_pListExpr_internal","%start_pBranch_internal","%start_pListBranch_internal","%start_pElse_internal","%start_pExpr9_internal","%start_pListExpr2_internal","%start_pExpr8_internal","%start_pExpr7_internal","%start_pExpr6_internal","%start_pExpr5_internal","%start_pCmp_internal","%start_pCmpOp_internal","%start_pExpr4_internal","%start_pExpr3_internal","%start_pExpr1_internal","%start_pListExpr3_internal","%start_pExpr_internal","%start_pExpr2_internal","%start_pType4_internal","%start_pType2_internal","%start_pListType3_internal","%start_pListType2_internal","%start_pType1_internal","%start_pType_internal","%start_pType3_internal","Ident","Integer","Char","String","Program","ListStmt","Stmt","Arg","ListArg","Block","ListExpr","Branch","ListBranch","Else","Expr9","ListExpr2","Expr8","Expr7","Expr6","Expr5","Cmp","CmpOp","Expr4","Expr3","Expr1","ListExpr3","Expr","Expr2","Type4","Type2","ListType3","ListType2","Type1","Type","Type3","'%'","'%='","'('","')'","'*'","'*='","'+'","'+='","','","'-'","'-='","'->'","'.'","'..'","'...'","'/'","'/='","';'","'<'","'<='","'<>'","'='","'=='","'>'","'>='","'Bool'","'Char'","'Int'","'Label'","'Object'","'String'","'Void'","'['","']'","'and'","'break'","'continue'","'def'","'do'","'elif'","'else'","'extern'","'false'","'for'","'func'","'if'","'in'","'not'","'or'","'print'","'return'","'skip'","'true'","'while'","'{'","'}'","L_ident","L_integ","L_charac","L_quoted","%eof"]
        bit_start = st * 129
        bit_end = (st + 1) * 129
        read_bit = readArrayBit happyExpList
        bits = map read_bit [bit_start..bit_end - 1]
        bits_indexed = zip bits [0..128]
        token_strs_expected = concatMap f bits_indexed
        f (False, _) = []
        f (True, nr) = [token_strs !! nr]

happyActOffsets :: HappyAddr
happyActOffsets = HappyA# "\x18\x00\x18\x00\x18\x00\x0d\x00\x0d\x00\xcc\xff\x2e\x00\x2e\x00\x2e\x00\xe1\xff\x6b\x00\x2e\x00\x6b\x00\x37\x00\x37\x00\x2e\x00\x37\x00\x9f\x00\x2e\x00\x2e\x00\x2e\x00\x2e\x00\x2e\x00\x2e\x00\x0d\x00\x0d\x00\x0d\x00\x0d\x00\x0d\x00\x0d\x00\x0d\x00\xd4\xff\x00\x00\x00\x00\xdb\xff\x0d\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0d\x00\x8e\x00\x00\x00\x24\x00\x00\x00\xdd\xff\x58\x00\xdd\xff\x36\x00\xe4\xff\xe4\xff\x42\x00\x0c\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x13\x00\x0e\x00\x15\x00\x9f\x00\x2d\x00\x00\x00\x29\x00\x00\x00\x22\x00\x2e\x00\x6b\x00\x2e\x00\x00\x00\x2e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x22\x00\x00\x00\x57\x00\x28\x00\x28\x00\x28\x00\x28\x00\x28\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x9f\x00\x28\x00\x28\x00\x28\x00\xfa\xff\x01\x00\x28\x00\x62\x00\x05\x00\x32\x00\x4d\x00\x67\x00\x56\x00\x74\x00\x5c\x00\x5c\x00\x69\x00\x66\x00\x18\x00\x81\x00\x6f\x00\x78\x00\x88\x00\x88\x00\x00\x00\x5e\x03\x00\x00\x00\x00\x2e\x00\x96\x00\x2e\x00\x2e\x00\x2e\x00\x00\x00\x2e\x00\x9d\x00\xcc\x00\xa4\x00\x00\x00\x18\x00\xbb\x00\x00\x00\x00\x00\x7f\x00\xe2\x00\xbc\x00\x2e\x00\x2e\x00\x2e\x00\x2e\x00\x2e\x00\x2e\x00\x00\x00\x0d\x00\xbe\x00\xc2\x00\x2e\x00\xc2\x00\x2e\x00\xfc\xff\x2e\x00\x2e\x00\x6b\x00\x6b\x00\x6b\x00\x6b\x00\x6b\x00\x63\x00\x2e\x00\x00\x00\xd8\x00\x0e\x00\xf7\x00\x2e\x00\x2e\x00\x63\x00\x63\x00\x0d\x00\x0d\x00\x0d\x00\xdb\x00\xfa\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x72\x00\x86\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x9f\x00\x00\x00\x0e\x00\x0e\x00\x13\x00\x13\x00\x13\x00\x00\x00\xdd\x00\x00\x00\x00\x00\xfd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x2e\x00\x0d\x00\x00\x00\xd0\x00\x00\x00\x00\x00\x11\x01\xeb\x00\x00\x00\x00\x00\x63\x00\x63\x00\xbf\x00\xbf\x00\xdf\x00\x8f\x00\x09\x00\xdf\x00\x00\x00\x00\x00\x00\x00\xdf\x00\x00\x00\x00\x00\x00\x00"#

happyGotoOffsets :: HappyAddr
happyGotoOffsets = HappyA# "\xba\x00\xd6\x00\x2a\x01\xf2\x01\x2e\x01\x10\x01\x9a\x01\xb6\x01\x46\x01\x0a\x01\x69\x01\x76\x03\x80\x03\x8a\x04\x85\x04\x4f\x04\x6b\x04\x05\x01\x75\x00\x26\x04\x5a\x03\x02\x04\xee\x01\xe6\x03\xff\x00\x39\x00\x5f\x00\xd2\x02\xb6\x02\x46\x02\xfb\xff\x00\x00\x00\x00\x00\x00\x00\x00\x62\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x7e\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0a\x02\x9c\x03\x92\x03\x00\x00\x64\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf2\x00\x00\x00\x00\x00\x23\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x26\x02\x2f\x01\x62\x01\x42\x02\x5e\x02\x00\x00\x7a\x02\x00\x00\x00\x00\x00\x00\x00\x00\x0e\x01\x00\x00\x00\x00\x00\x00\x21\x01\x00\x00\x00\x00\x96\x02\xb2\x02\xce\x02\xea\x02\x06\x03\xd2\x01\x00\x00\x9e\x01\x00\x00\x28\x01\x7e\x01\x29\x01\xae\x03\xa1\x00\x22\x03\xca\x03\x85\x01\x2d\x02\x49\x02\xb8\x03\xd4\x03\x80\x04\x0c\x04\x00\x00\x00\x00\x00\x00\x00\x00\x30\x04\x48\x04\x9c\x04\xa0\x04\xc1\x00\xee\x02\xa5\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3e\x03\xd6\x01\x00\x00\x30\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa4\x04\xb6\x04\x00\x00\x00\x00\x36\x01\x9a\x02\x00\x00\x4a\x01\x00\x00\x00\x00\x00\x00\x4c\x01\x00\x00\x00\x00\x00\x00"#

happyAdjustOffset :: Happy_GHC_Exts.Int# -> Happy_GHC_Exts.Int#
happyAdjustOffset off = off

happyDefActions :: HappyAddr
happyDefActions = HappyA# "\xdb\xff\xdb\xff\x00\x00\x00\x00\xc4\xff\x00\x00\x00\x00\x00\x00\xbd\xff\xb9\xff\x00\x00\xac\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe0\xff\x76\xff\x00\x00\x00\x00\x85\xff\x84\xff\x86\xff\x83\xff\x82\xff\x87\xff\x00\x00\x78\xff\x7f\xff\x00\x00\x77\xff\x00\x00\x7d\xff\x00\x00\x7b\xff\x00\x00\x00\x00\x7d\xff\x00\x00\x00\x00\xb2\xff\xb8\xff\xb5\xff\xb4\xff\xa6\xff\xa2\xff\x9d\xff\x9a\xff\x90\xff\x9c\xff\x8e\xff\x88\xff\x00\x00\x00\x00\x00\x00\xac\xff\xb6\xff\x00\x00\xb7\xff\xdf\xff\xde\xff\xdd\xff\x88\xff\x89\xff\x8d\xff\x00\x00\x8c\xff\x8b\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x95\xff\x94\xff\x96\xff\x97\xff\x93\xff\x92\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xab\xff\x00\x00\x00\x00\x00\x00\xbc\xff\x00\x00\x00\x00\x00\x00\x00\x00\xc0\xff\x00\x00\xdb\xff\xc3\xff\x00\x00\x00\x00\x00\x00\x00\x00\xd0\xff\xc0\xff\xc6\xff\xc7\xff\x00\x00\x00\x00\xbd\xff\x00\x00\xd4\xff\xd2\xff\x00\x00\x00\x00\xda\xff\x00\x00\xdc\xff\xdb\xff\x00\x00\xd3\xff\xd1\xff\xb9\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc5\xff\xc4\xff\x00\x00\x00\x00\xbd\xff\x00\x00\xac\xff\x00\x00\x00\x00\xac\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x9b\xff\x00\x00\xa3\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\xff\x81\xff\x79\xff\x7a\xff\x7c\xff\xa0\xff\xa1\xff\x91\xff\x8f\xff\xad\xff\xb3\xff\x8a\xff\x99\xff\x98\xff\xa4\xff\xa5\xff\xa8\xff\xa9\xff\xa7\xff\xaa\xff\x00\x00\xaf\xff\xb1\xff\x00\x00\xba\xff\xbb\xff\xbe\xff\xc1\xff\xc2\xff\xbf\xff\xce\xff\xcb\xff\xcc\xff\xcf\xff\xcd\xff\x00\x00\xc4\xff\xca\xff\x00\x00\xd9\xff\xc9\xff\x00\x00\x00\x00\xae\xff\xb0\xff\x00\x00\x00\x00\x9e\xff\x9f\xff\x00\x00\x00\x00\x00\x00\x00\x00\xd6\xff\xc8\xff\xd8\xff\x00\x00\xd5\xff\xd7\xff"#

happyCheck :: HappyAddr
happyCheck = HappyA# "\xff\xff\x07\x00\x01\x00\x37\x00\x0a\x00\x02\x00\x05\x00\x04\x00\x03\x00\x06\x00\x29\x00\x08\x00\x09\x00\x39\x00\x0b\x00\x01\x00\x03\x00\x10\x00\x0d\x00\x05\x00\x11\x00\x12\x00\x03\x00\x1c\x00\x3d\x00\x16\x00\x3d\x00\x03\x00\x07\x00\x22\x00\x10\x00\x0a\x00\x0d\x00\x3d\x00\x0a\x00\x0e\x00\x0f\x00\x22\x00\x21\x00\x1a\x00\x1b\x00\x1c\x00\x27\x00\x1e\x00\x1f\x00\x20\x00\x21\x00\x26\x00\x0c\x00\x03\x00\x2f\x00\x2a\x00\x21\x00\x39\x00\x3a\x00\x3d\x00\x0a\x00\x21\x00\x03\x00\x38\x00\x24\x00\x25\x00\x3d\x00\x09\x00\x3d\x00\x0a\x00\x3d\x00\x2b\x00\x2c\x00\x2d\x00\x2e\x00\x05\x00\x30\x00\x3d\x00\x32\x00\x33\x00\x34\x00\x35\x00\x36\x00\x21\x00\x23\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\x1c\x00\x1d\x00\x1e\x00\x21\x00\x2b\x00\x31\x00\x22\x00\x04\x00\x05\x00\x30\x00\x3d\x00\x09\x00\x09\x00\x2b\x00\x35\x00\x0c\x00\x3d\x00\x03\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\x09\x00\x35\x00\x0a\x00\x03\x00\x3d\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\x27\x00\x00\x00\x01\x00\x02\x00\x03\x00\x07\x00\x22\x00\x1c\x00\x0a\x00\x1e\x00\x26\x00\x16\x00\x0e\x00\x22\x00\x2a\x00\x0e\x00\x21\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x09\x00\x16\x00\x21\x00\x07\x00\x2b\x00\x28\x00\x0a\x00\x39\x00\x03\x00\x3d\x00\x0e\x00\x3d\x00\x2b\x00\x09\x00\x35\x00\x3d\x00\x0c\x00\x27\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\x35\x00\x00\x00\x01\x00\x3d\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\x29\x00\x1a\x00\x1b\x00\x1c\x00\x3d\x00\x1e\x00\x1f\x00\x20\x00\x21\x00\x39\x00\x13\x00\x14\x00\x15\x00\x26\x00\x17\x00\x18\x00\x19\x00\x2a\x00\x00\x00\x01\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06\x00\x1c\x00\x1d\x00\x1e\x00\x0a\x00\x3d\x00\x07\x00\x22\x00\x0e\x00\x0a\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x39\x00\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x3d\x00\x05\x00\x06\x00\x1c\x00\x12\x00\x1e\x00\x0a\x00\x3d\x00\x27\x00\x22\x00\x0e\x00\x03\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x2f\x00\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x38\x00\x05\x00\x06\x00\x37\x00\x22\x00\x04\x00\x0a\x00\x22\x00\x04\x00\x22\x00\x0e\x00\x04\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x37\x00\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x27\x00\x05\x00\x06\x00\x04\x00\x37\x00\x0d\x00\x0a\x00\x09\x00\x15\x00\x1c\x00\x0e\x00\x15\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x00\x00\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x0d\x00\x00\x00\x06\x00\x09\x00\x09\x00\x15\x00\x0a\x00\x07\x00\x08\x00\xff\xff\x0e\x00\x09\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x09\x00\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x1c\x00\x1d\x00\x1e\x00\x1f\x00\x20\x00\x21\x00\x22\x00\x0b\x00\x0c\x00\x09\x00\x0e\x00\x09\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\x0b\x00\x0c\x00\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x0e\x00\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\x0b\x00\x0c\x00\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x0e\x00\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x0a\x00\x07\x00\x08\x00\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x1c\x00\x1d\x00\x1e\x00\x1f\x00\x20\x00\x21\x00\x22\x00\x0b\x00\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x0a\x00\x07\x00\x08\x00\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x1c\x00\x1d\x00\x1e\x00\x1f\x00\x20\x00\x21\x00\x22\x00\x07\x00\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x1c\x00\x1d\x00\x1e\x00\x1f\x00\x20\x00\x21\x00\x22\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x0e\x00\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x0e\x00\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x1c\x00\x1d\x00\x1e\x00\x1f\x00\x20\x00\x21\x00\x22\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x1c\x00\x1d\x00\x1e\x00\x1f\x00\x20\x00\x21\x00\x22\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x1c\x00\x1d\x00\x1e\x00\x1f\x00\x20\x00\x21\x00\x22\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x1c\x00\x1d\x00\x1e\x00\x1f\x00\x20\x00\x21\x00\x22\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x1c\x00\x1d\x00\x1e\x00\x1f\x00\x20\x00\xff\xff\x22\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x1c\x00\x1d\x00\x1e\x00\x1f\x00\xff\xff\xff\xff\x22\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\x1c\x00\x1d\x00\x1e\x00\x1f\x00\xff\xff\xff\xff\x22\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x18\x00\x19\x00\x1a\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\x02\x00\xff\xff\xff\xff\xff\xff\x06\x00\xff\xff\x08\x00\xff\xff\x0e\x00\x0b\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x11\x00\x16\x00\x17\x00\x18\x00\x19\x00\x16\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\x0e\x00\x0f\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x0e\x00\xff\xff\x10\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\x0e\x00\x0f\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x0e\x00\xff\xff\x10\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\x0e\x00\x0f\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x0e\x00\xff\xff\x10\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\x0e\x00\x0f\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x0e\x00\xff\xff\x10\x00\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\xff\xff\xff\xff\xff\xff\x1b\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x0e\x00\x19\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\xff\xff\x19\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\xff\xff\x16\x00\x17\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x0e\x00\x16\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\xff\xff\x14\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\x00\x00\x01\x00\x02\x00\x03\x00\x0e\x00\xff\xff\x10\x00\x11\x00\x12\x00\x0e\x00\x14\x00\x10\x00\x11\x00\x12\x00\x0e\x00\xff\xff\x10\x00\x11\x00\x00\x00\x01\x00\x02\x00\x03\x00\x00\x00\x01\x00\x02\x00\x03\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\x0e\x00\xff\xff\x10\x00\x11\x00\x0e\x00\xff\xff\x10\x00\x11\x00\x00\x00\x01\x00\x02\x00\x03\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x0e\x00\xff\xff\x10\x00\x11\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"#

happyTable :: HappyAddr
happyTable = HappyA# "\x00\x00\xa1\x00\x9e\x00\x72\x00\xa2\x00\x88\xff\x9f\x00\x88\xff\x9a\x00\x88\xff\x6a\x00\x88\xff\xa4\x00\x21\x00\x88\xff\x9e\x00\x24\x00\xa0\x00\x9b\x00\x9f\x00\x88\xff\x88\xff\x9a\x00\x21\x00\xff\xff\x88\xff\xff\xff\x46\x00\xa1\x00\x22\x00\xa0\x00\xa2\x00\x9b\x00\xff\xff\x47\x00\xab\x00\xac\x00\x88\xff\x9c\x00\x25\x00\x26\x00\x27\x00\x88\xff\x28\x00\x29\x00\x2a\x00\x2b\x00\xea\x00\xaf\x00\x46\x00\x88\xff\xeb\x00\x9c\x00\x21\x00\x4c\x00\xff\xff\x47\x00\x48\x00\x46\x00\x88\xff\x7a\x00\x7b\x00\xff\xff\xae\x00\x88\xff\x47\x00\xff\xff\x49\x00\x7c\x00\x7d\x00\x7e\x00\xad\x00\x4a\x00\xff\xff\x7f\x00\x80\x00\x81\x00\x4b\x00\x82\x00\x48\x00\xaa\x00\x21\x00\x4c\x00\x4d\x00\x4e\x00\x21\x00\x36\x00\x2c\x00\x48\x00\x49\x00\xa9\x00\x30\x00\x7d\xff\xad\x00\x4a\x00\xff\xff\xa4\x00\x7d\xff\x49\x00\x4b\x00\x7d\xff\xff\xff\x46\x00\x21\x00\x4c\x00\x4d\x00\x4e\x00\x9d\x00\x4b\x00\x47\x00\x46\x00\xff\xff\x21\x00\x4c\x00\x4d\x00\x4e\x00\x99\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\xa1\x00\x7d\xff\x21\x00\xa2\x00\x34\x00\x7d\xff\x93\x00\xe0\x00\x35\x00\x7d\xff\x3c\x00\x48\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x95\x00\x57\x00\x48\x00\xa1\x00\x49\x00\x98\x00\xa2\x00\x7d\xff\x24\x00\xff\xff\xdf\x00\x7d\xff\x49\x00\xae\x00\x4b\x00\xff\xff\x7b\xff\x97\x00\x21\x00\x4c\x00\x4d\x00\x4e\x00\x4b\x00\xc6\x00\xc7\x00\xff\xff\x21\x00\x4c\x00\x4d\x00\x4e\x00\x6a\x00\x25\x00\x26\x00\x27\x00\xff\xff\x28\x00\x29\x00\x2a\x00\x2b\x00\x21\x00\x5a\x00\x5b\x00\x5c\x00\xe6\x00\x5d\x00\x5e\x00\x5f\x00\xe7\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x84\x00\x85\x00\x83\x00\x21\x00\xb3\x00\x2c\x00\x77\x00\xff\xff\xa1\x00\x30\x00\x3c\x00\xa2\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x21\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x78\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\xff\xff\x82\x00\x83\x00\x21\x00\x87\x00\xb5\x00\x77\x00\xff\xff\xd8\x00\x35\x00\x3c\x00\xd6\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\xd5\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x78\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\xcd\x00\x95\x00\x83\x00\x72\x00\xbc\x00\xbb\x00\x77\x00\xb3\x00\xb2\x00\xde\x00\x3c\x00\xdd\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x72\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x78\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\xe3\x00\xd8\x00\x83\x00\xe4\x00\x72\x00\x68\x00\x77\x00\x70\x00\x58\x00\x37\x00\x3c\x00\xa2\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x93\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x78\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\xd6\x00\x8b\x00\x76\x00\xcb\x00\xc9\x00\xa2\x00\x77\x00\x72\x00\x73\x00\x00\x00\x3c\x00\xd9\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\xe7\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x78\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x21\x00\x2b\x00\x2c\x00\x2d\x00\x2e\x00\x74\x00\x30\x00\x6a\x00\x6b\x00\xe8\x00\x3c\x00\xeb\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x6c\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x6a\x00\x8a\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x67\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x6c\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x6a\x00\xca\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\xc3\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x6c\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x6e\x00\x72\x00\xcd\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x6f\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x21\x00\x2b\x00\x2c\x00\x2d\x00\x2e\x00\x74\x00\x30\x00\x6d\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x6c\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xce\x00\x72\x00\xda\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x6f\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x21\x00\x2b\x00\x2c\x00\x2d\x00\x2e\x00\x74\x00\x30\x00\x75\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x51\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x21\x00\x2b\x00\x2c\x00\x2d\x00\x2e\x00\x74\x00\x30\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\xa7\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\xc2\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x8c\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\xc1\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x89\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x21\x00\x2b\x00\x2c\x00\x2d\x00\x2e\x00\x2f\x00\x30\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x88\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x21\x00\x2b\x00\x2c\x00\x2d\x00\x2e\x00\xb0\x00\x30\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\x87\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x21\x00\x2b\x00\x2c\x00\x2d\x00\x2e\x00\xaf\x00\x30\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\xd3\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x21\x00\x2b\x00\x2c\x00\x2d\x00\x2e\x00\xe4\x00\x30\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\xd2\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x21\x00\x2b\x00\x2c\x00\x2d\x00\x31\x00\x00\x00\x30\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\xd1\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x21\x00\x32\x00\x2c\x00\x33\x00\x00\x00\x00\x00\x30\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\xd0\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x21\x00\x32\x00\x2c\x00\xb4\x00\x00\x00\x00\x00\x30\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\xcf\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\xc5\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x4e\x00\x4f\x00\x50\x00\xdb\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x8e\x00\x00\x00\x00\x00\x00\x00\x8f\x00\x00\x00\x90\x00\x00\x00\x3c\x00\x91\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x92\x00\x42\x00\x4e\x00\x55\x00\x50\x00\x93\x00\x52\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\x65\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x43\x00\x3c\x00\x00\x00\x64\x00\x66\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\xa5\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x43\x00\x3c\x00\x00\x00\xa6\x00\x66\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\xc8\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x43\x00\x3c\x00\x00\x00\xc0\x00\x66\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\xc4\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x43\x00\x3c\x00\x00\x00\xbf\x00\x66\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x43\x00\x00\x00\x00\x00\x00\x00\x44\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x53\x00\x3c\x00\x54\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x53\x00\x00\x00\xbc\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\x56\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x00\x00\x42\x00\xb9\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\x40\x00\x41\x00\x3c\x00\xb8\x00\x3d\x00\x3e\x00\x3f\x00\x61\x00\x41\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x3f\x00\xa4\x00\x41\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\x5f\x00\x00\x00\x60\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x3c\x00\x00\x00\x3d\x00\x3e\x00\xbd\x00\x3c\x00\xbe\x00\x3d\x00\x3e\x00\x62\x00\x3c\x00\x00\x00\x3d\x00\x63\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\xb7\x00\x3c\x00\x00\x00\x3d\x00\xb6\x00\x3c\x00\x00\x00\x3d\x00\xe1\x00\x38\x00\x39\x00\x3a\x00\x3b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3c\x00\x00\x00\x3d\x00\xe0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"#

happyReduceArr = Happy_Data_Array.array (31, 137) [
	(31 , happyReduce_31),
	(32 , happyReduce_32),
	(33 , happyReduce_33),
	(34 , happyReduce_34),
	(35 , happyReduce_35),
	(36 , happyReduce_36),
	(37 , happyReduce_37),
	(38 , happyReduce_38),
	(39 , happyReduce_39),
	(40 , happyReduce_40),
	(41 , happyReduce_41),
	(42 , happyReduce_42),
	(43 , happyReduce_43),
	(44 , happyReduce_44),
	(45 , happyReduce_45),
	(46 , happyReduce_46),
	(47 , happyReduce_47),
	(48 , happyReduce_48),
	(49 , happyReduce_49),
	(50 , happyReduce_50),
	(51 , happyReduce_51),
	(52 , happyReduce_52),
	(53 , happyReduce_53),
	(54 , happyReduce_54),
	(55 , happyReduce_55),
	(56 , happyReduce_56),
	(57 , happyReduce_57),
	(58 , happyReduce_58),
	(59 , happyReduce_59),
	(60 , happyReduce_60),
	(61 , happyReduce_61),
	(62 , happyReduce_62),
	(63 , happyReduce_63),
	(64 , happyReduce_64),
	(65 , happyReduce_65),
	(66 , happyReduce_66),
	(67 , happyReduce_67),
	(68 , happyReduce_68),
	(69 , happyReduce_69),
	(70 , happyReduce_70),
	(71 , happyReduce_71),
	(72 , happyReduce_72),
	(73 , happyReduce_73),
	(74 , happyReduce_74),
	(75 , happyReduce_75),
	(76 , happyReduce_76),
	(77 , happyReduce_77),
	(78 , happyReduce_78),
	(79 , happyReduce_79),
	(80 , happyReduce_80),
	(81 , happyReduce_81),
	(82 , happyReduce_82),
	(83 , happyReduce_83),
	(84 , happyReduce_84),
	(85 , happyReduce_85),
	(86 , happyReduce_86),
	(87 , happyReduce_87),
	(88 , happyReduce_88),
	(89 , happyReduce_89),
	(90 , happyReduce_90),
	(91 , happyReduce_91),
	(92 , happyReduce_92),
	(93 , happyReduce_93),
	(94 , happyReduce_94),
	(95 , happyReduce_95),
	(96 , happyReduce_96),
	(97 , happyReduce_97),
	(98 , happyReduce_98),
	(99 , happyReduce_99),
	(100 , happyReduce_100),
	(101 , happyReduce_101),
	(102 , happyReduce_102),
	(103 , happyReduce_103),
	(104 , happyReduce_104),
	(105 , happyReduce_105),
	(106 , happyReduce_106),
	(107 , happyReduce_107),
	(108 , happyReduce_108),
	(109 , happyReduce_109),
	(110 , happyReduce_110),
	(111 , happyReduce_111),
	(112 , happyReduce_112),
	(113 , happyReduce_113),
	(114 , happyReduce_114),
	(115 , happyReduce_115),
	(116 , happyReduce_116),
	(117 , happyReduce_117),
	(118 , happyReduce_118),
	(119 , happyReduce_119),
	(120 , happyReduce_120),
	(121 , happyReduce_121),
	(122 , happyReduce_122),
	(123 , happyReduce_123),
	(124 , happyReduce_124),
	(125 , happyReduce_125),
	(126 , happyReduce_126),
	(127 , happyReduce_127),
	(128 , happyReduce_128),
	(129 , happyReduce_129),
	(130 , happyReduce_130),
	(131 , happyReduce_131),
	(132 , happyReduce_132),
	(133 , happyReduce_133),
	(134 , happyReduce_134),
	(135 , happyReduce_135),
	(136 , happyReduce_136),
	(137 , happyReduce_137)
	]

happy_n_terms = 62 :: Int
happy_n_nonterms = 35 :: Int

happyReduce_31 = happySpecReduce_1  0# happyReduction_31
happyReduction_31 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn34
		 ((Just (tokenLineCol happy_var_1), Ident (prToken happy_var_1))
	)}

happyReduce_32 = happySpecReduce_1  1# happyReduction_32
happyReduction_32 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn35
		 ((Just (tokenLineCol happy_var_1), read (prToken happy_var_1))
	)}

happyReduce_33 = happySpecReduce_1  2# happyReduction_33
happyReduction_33 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn36
		 ((Just (tokenLineCol happy_var_1), read (prToken happy_var_1))
	)}

happyReduce_34 = happySpecReduce_1  3# happyReduction_34
happyReduction_34 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn37
		 ((Just (tokenLineCol happy_var_1), prToken happy_var_1)
	)}

happyReduce_35 = happySpecReduce_1  4# happyReduction_35
happyReduction_35 happy_x_1
	 =  case happyOut39 happy_x_1 of { happy_var_1 -> 
	happyIn38
		 ((fst happy_var_1, AbsPyxell.Program (fst happy_var_1)(snd happy_var_1))
	)}

happyReduce_36 = happySpecReduce_0  5# happyReduction_36
happyReduction_36  =  happyIn39
		 ((Nothing, [])
	)

happyReduce_37 = happySpecReduce_1  5# happyReduction_37
happyReduction_37 happy_x_1
	 =  case happyOut40 happy_x_1 of { happy_var_1 -> 
	happyIn39
		 ((fst happy_var_1, (:[]) (snd happy_var_1))
	)}

happyReduce_38 = happySpecReduce_3  5# happyReduction_38
happyReduction_38 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut40 happy_x_1 of { happy_var_1 -> 
	case happyOut39 happy_x_3 of { happy_var_3 -> 
	happyIn39
		 ((fst happy_var_1, (:) (snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_39 = happyReduce 7# 6# happyReduction_39
happyReduction_39 (happy_x_7 `HappyStk`
	happy_x_6 `HappyStk`
	happy_x_5 `HappyStk`
	happy_x_4 `HappyStk`
	happy_x_3 `HappyStk`
	happy_x_2 `HappyStk`
	happy_x_1 `HappyStk`
	happyRest)
	 = case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut34 happy_x_2 of { happy_var_2 -> 
	case happyOut42 happy_x_4 of { happy_var_4 -> 
	case happyOut43 happy_x_7 of { happy_var_7 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SProc (Just (tokenLineCol happy_var_1)) (snd happy_var_2)(snd happy_var_4)(snd happy_var_7))
	) `HappyStk` happyRest}}}}

happyReduce_40 = happyReduce 8# 6# happyReduction_40
happyReduction_40 (happy_x_8 `HappyStk`
	happy_x_7 `HappyStk`
	happy_x_6 `HappyStk`
	happy_x_5 `HappyStk`
	happy_x_4 `HappyStk`
	happy_x_3 `HappyStk`
	happy_x_2 `HappyStk`
	happy_x_1 `HappyStk`
	happyRest)
	 = case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut34 happy_x_2 of { happy_var_2 -> 
	case happyOut42 happy_x_4 of { happy_var_4 -> 
	case happyOut67 happy_x_6 of { happy_var_6 -> 
	case happyOut43 happy_x_8 of { happy_var_8 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SFunc (Just (tokenLineCol happy_var_1)) (snd happy_var_2)(snd happy_var_4)(snd happy_var_6)(snd happy_var_8))
	) `HappyStk` happyRest}}}}}

happyReduce_41 = happyReduce 6# 6# happyReduction_41
happyReduction_41 (happy_x_6 `HappyStk`
	happy_x_5 `HappyStk`
	happy_x_4 `HappyStk`
	happy_x_3 `HappyStk`
	happy_x_2 `HappyStk`
	happy_x_1 `HappyStk`
	happyRest)
	 = case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut34 happy_x_2 of { happy_var_2 -> 
	case happyOut42 happy_x_4 of { happy_var_4 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SProcExtern (Just (tokenLineCol happy_var_1)) (snd happy_var_2)(snd happy_var_4))
	) `HappyStk` happyRest}}}

happyReduce_42 = happyReduce 7# 6# happyReduction_42
happyReduction_42 (happy_x_7 `HappyStk`
	happy_x_6 `HappyStk`
	happy_x_5 `HappyStk`
	happy_x_4 `HappyStk`
	happy_x_3 `HappyStk`
	happy_x_2 `HappyStk`
	happy_x_1 `HappyStk`
	happyRest)
	 = case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut34 happy_x_2 of { happy_var_2 -> 
	case happyOut42 happy_x_4 of { happy_var_4 -> 
	case happyOut67 happy_x_6 of { happy_var_6 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SFuncExtern (Just (tokenLineCol happy_var_1)) (snd happy_var_2)(snd happy_var_4)(snd happy_var_6))
	) `HappyStk` happyRest}}}}

happyReduce_43 = happySpecReduce_1  6# happyReduction_43
happyReduction_43 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SRetVoid (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_44 = happySpecReduce_2  6# happyReduction_44
happyReduction_44 happy_x_2
	happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut60 happy_x_2 of { happy_var_2 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SRetExpr (Just (tokenLineCol happy_var_1)) (snd happy_var_2))
	)}}

happyReduce_45 = happySpecReduce_1  6# happyReduction_45
happyReduction_45 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SSkip (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_46 = happySpecReduce_2  6# happyReduction_46
happyReduction_46 happy_x_2
	happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut60 happy_x_2 of { happy_var_2 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SPrint (Just (tokenLineCol happy_var_1)) (snd happy_var_2))
	)}}

happyReduce_47 = happySpecReduce_1  6# happyReduction_47
happyReduction_47 happy_x_1
	 =  case happyOut44 happy_x_1 of { happy_var_1 -> 
	happyIn40
		 ((fst happy_var_1, AbsPyxell.SAssg (fst happy_var_1)(snd happy_var_1))
	)}

happyReduce_48 = happySpecReduce_3  6# happyReduction_48
happyReduction_48 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut60 happy_x_1 of { happy_var_1 -> 
	case happyOut60 happy_x_3 of { happy_var_3 -> 
	happyIn40
		 ((fst happy_var_1, AbsPyxell.SAssgMul (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_49 = happySpecReduce_3  6# happyReduction_49
happyReduction_49 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut60 happy_x_1 of { happy_var_1 -> 
	case happyOut60 happy_x_3 of { happy_var_3 -> 
	happyIn40
		 ((fst happy_var_1, AbsPyxell.SAssgDiv (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_50 = happySpecReduce_3  6# happyReduction_50
happyReduction_50 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut60 happy_x_1 of { happy_var_1 -> 
	case happyOut60 happy_x_3 of { happy_var_3 -> 
	happyIn40
		 ((fst happy_var_1, AbsPyxell.SAssgMod (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_51 = happySpecReduce_3  6# happyReduction_51
happyReduction_51 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut60 happy_x_1 of { happy_var_1 -> 
	case happyOut60 happy_x_3 of { happy_var_3 -> 
	happyIn40
		 ((fst happy_var_1, AbsPyxell.SAssgAdd (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_52 = happySpecReduce_3  6# happyReduction_52
happyReduction_52 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut60 happy_x_1 of { happy_var_1 -> 
	case happyOut60 happy_x_3 of { happy_var_3 -> 
	happyIn40
		 ((fst happy_var_1, AbsPyxell.SAssgSub (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_53 = happySpecReduce_3  6# happyReduction_53
happyReduction_53 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut46 happy_x_2 of { happy_var_2 -> 
	case happyOut47 happy_x_3 of { happy_var_3 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SIf (Just (tokenLineCol happy_var_1)) (snd happy_var_2)(snd happy_var_3))
	)}}}

happyReduce_54 = happyReduce 4# 6# happyReduction_54
happyReduction_54 (happy_x_4 `HappyStk`
	happy_x_3 `HappyStk`
	happy_x_2 `HappyStk`
	happy_x_1 `HappyStk`
	happyRest)
	 = case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut60 happy_x_2 of { happy_var_2 -> 
	case happyOut43 happy_x_4 of { happy_var_4 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SWhile (Just (tokenLineCol happy_var_1)) (snd happy_var_2)(snd happy_var_4))
	) `HappyStk` happyRest}}}

happyReduce_55 = happyReduce 6# 6# happyReduction_55
happyReduction_55 (happy_x_6 `HappyStk`
	happy_x_5 `HappyStk`
	happy_x_4 `HappyStk`
	happy_x_3 `HappyStk`
	happy_x_2 `HappyStk`
	happy_x_1 `HappyStk`
	happyRest)
	 = case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut60 happy_x_2 of { happy_var_2 -> 
	case happyOut60 happy_x_4 of { happy_var_4 -> 
	case happyOut43 happy_x_6 of { happy_var_6 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SFor (Just (tokenLineCol happy_var_1)) (snd happy_var_2)(snd happy_var_4)(snd happy_var_6))
	) `HappyStk` happyRest}}}}

happyReduce_56 = happySpecReduce_1  6# happyReduction_56
happyReduction_56 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SContinue (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_57 = happySpecReduce_1  6# happyReduction_57
happyReduction_57 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn40
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SBreak (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_58 = happySpecReduce_2  7# happyReduction_58
happyReduction_58 happy_x_2
	happy_x_1
	 =  case happyOut67 happy_x_1 of { happy_var_1 -> 
	case happyOut34 happy_x_2 of { happy_var_2 -> 
	happyIn41
		 ((fst happy_var_1, AbsPyxell.ANoDef (fst happy_var_1)(snd happy_var_1)(snd happy_var_2))
	)}}

happyReduce_59 = happySpecReduce_0  8# happyReduction_59
happyReduction_59  =  happyIn42
		 ((Nothing, [])
	)

happyReduce_60 = happySpecReduce_1  8# happyReduction_60
happyReduction_60 happy_x_1
	 =  case happyOut41 happy_x_1 of { happy_var_1 -> 
	happyIn42
		 ((fst happy_var_1, (:[]) (snd happy_var_1))
	)}

happyReduce_61 = happySpecReduce_3  8# happyReduction_61
happyReduction_61 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut41 happy_x_1 of { happy_var_1 -> 
	case happyOut42 happy_x_3 of { happy_var_3 -> 
	happyIn42
		 ((fst happy_var_1, (:) (snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_62 = happySpecReduce_3  9# happyReduction_62
happyReduction_62 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut39 happy_x_2 of { happy_var_2 -> 
	happyIn43
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.SBlock (Just (tokenLineCol happy_var_1)) (snd happy_var_2))
	)}}

happyReduce_63 = happySpecReduce_1  10# happyReduction_63
happyReduction_63 happy_x_1
	 =  case happyOut60 happy_x_1 of { happy_var_1 -> 
	happyIn44
		 ((fst happy_var_1, (:[]) (snd happy_var_1))
	)}

happyReduce_64 = happySpecReduce_3  10# happyReduction_64
happyReduction_64 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut60 happy_x_1 of { happy_var_1 -> 
	case happyOut44 happy_x_3 of { happy_var_3 -> 
	happyIn44
		 ((fst happy_var_1, (:) (snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_65 = happySpecReduce_3  11# happyReduction_65
happyReduction_65 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut60 happy_x_1 of { happy_var_1 -> 
	case happyOut43 happy_x_3 of { happy_var_3 -> 
	happyIn45
		 ((fst happy_var_1, AbsPyxell.BElIf (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_66 = happySpecReduce_0  12# happyReduction_66
happyReduction_66  =  happyIn46
		 ((Nothing, [])
	)

happyReduce_67 = happySpecReduce_1  12# happyReduction_67
happyReduction_67 happy_x_1
	 =  case happyOut45 happy_x_1 of { happy_var_1 -> 
	happyIn46
		 ((fst happy_var_1, (:[]) (snd happy_var_1))
	)}

happyReduce_68 = happySpecReduce_3  12# happyReduction_68
happyReduction_68 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut45 happy_x_1 of { happy_var_1 -> 
	case happyOut46 happy_x_3 of { happy_var_3 -> 
	happyIn46
		 ((fst happy_var_1, (:) (snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_69 = happySpecReduce_3  13# happyReduction_69
happyReduction_69 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut43 happy_x_3 of { happy_var_3 -> 
	happyIn47
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.EElse (Just (tokenLineCol happy_var_1)) (snd happy_var_3))
	)}}

happyReduce_70 = happySpecReduce_0  13# happyReduction_70
happyReduction_70  =  happyIn47
		 ((Nothing, AbsPyxell.EEmpty Nothing)
	)

happyReduce_71 = happySpecReduce_1  14# happyReduction_71
happyReduction_71 happy_x_1
	 =  case happyOut35 happy_x_1 of { happy_var_1 -> 
	happyIn48
		 ((fst happy_var_1, AbsPyxell.EInt (fst happy_var_1)(snd happy_var_1))
	)}

happyReduce_72 = happySpecReduce_1  14# happyReduction_72
happyReduction_72 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn48
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.ETrue (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_73 = happySpecReduce_1  14# happyReduction_73
happyReduction_73 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn48
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.EFalse (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_74 = happySpecReduce_1  14# happyReduction_74
happyReduction_74 happy_x_1
	 =  case happyOut36 happy_x_1 of { happy_var_1 -> 
	happyIn48
		 ((fst happy_var_1, AbsPyxell.EChar (fst happy_var_1)(snd happy_var_1))
	)}

happyReduce_75 = happySpecReduce_1  14# happyReduction_75
happyReduction_75 happy_x_1
	 =  case happyOut37 happy_x_1 of { happy_var_1 -> 
	happyIn48
		 ((fst happy_var_1, AbsPyxell.EString (fst happy_var_1)(snd happy_var_1))
	)}

happyReduce_76 = happySpecReduce_3  14# happyReduction_76
happyReduction_76 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut49 happy_x_2 of { happy_var_2 -> 
	happyIn48
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.EArray (Just (tokenLineCol happy_var_1)) (snd happy_var_2))
	)}}

happyReduce_77 = happySpecReduce_1  14# happyReduction_77
happyReduction_77 happy_x_1
	 =  case happyOut34 happy_x_1 of { happy_var_1 -> 
	happyIn48
		 ((fst happy_var_1, AbsPyxell.EVar (fst happy_var_1)(snd happy_var_1))
	)}

happyReduce_78 = happySpecReduce_3  14# happyReduction_78
happyReduction_78 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut48 happy_x_1 of { happy_var_1 -> 
	case happyOut35 happy_x_3 of { happy_var_3 -> 
	happyIn48
		 ((fst happy_var_1, AbsPyxell.EElem (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_79 = happyReduce 4# 14# happyReduction_79
happyReduction_79 (happy_x_4 `HappyStk`
	happy_x_3 `HappyStk`
	happy_x_2 `HappyStk`
	happy_x_1 `HappyStk`
	happyRest)
	 = case happyOut48 happy_x_1 of { happy_var_1 -> 
	case happyOut60 happy_x_3 of { happy_var_3 -> 
	happyIn48
		 ((fst happy_var_1, AbsPyxell.EIndex (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	) `HappyStk` happyRest}}

happyReduce_80 = happySpecReduce_3  14# happyReduction_80
happyReduction_80 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut48 happy_x_1 of { happy_var_1 -> 
	case happyOut34 happy_x_3 of { happy_var_3 -> 
	happyIn48
		 ((fst happy_var_1, AbsPyxell.EAttr (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_81 = happyReduce 4# 14# happyReduction_81
happyReduction_81 (happy_x_4 `HappyStk`
	happy_x_3 `HappyStk`
	happy_x_2 `HappyStk`
	happy_x_1 `HappyStk`
	happyRest)
	 = case happyOut48 happy_x_1 of { happy_var_1 -> 
	case happyOut49 happy_x_3 of { happy_var_3 -> 
	happyIn48
		 ((fst happy_var_1, AbsPyxell.ECall (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	) `HappyStk` happyRest}}

happyReduce_82 = happySpecReduce_3  14# happyReduction_82
happyReduction_82 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut60 happy_x_2 of { happy_var_2 -> 
	happyIn48
		 ((Just (tokenLineCol happy_var_1), snd happy_var_2)
	)}}

happyReduce_83 = happySpecReduce_0  15# happyReduction_83
happyReduction_83  =  happyIn49
		 ((Nothing, [])
	)

happyReduce_84 = happySpecReduce_1  15# happyReduction_84
happyReduction_84 happy_x_1
	 =  case happyOut61 happy_x_1 of { happy_var_1 -> 
	happyIn49
		 ((fst happy_var_1, (:[]) (snd happy_var_1))
	)}

happyReduce_85 = happySpecReduce_3  15# happyReduction_85
happyReduction_85 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut61 happy_x_1 of { happy_var_1 -> 
	case happyOut49 happy_x_3 of { happy_var_3 -> 
	happyIn49
		 ((fst happy_var_1, (:) (snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_86 = happySpecReduce_3  16# happyReduction_86
happyReduction_86 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut50 happy_x_1 of { happy_var_1 -> 
	case happyOut48 happy_x_3 of { happy_var_3 -> 
	happyIn50
		 ((fst happy_var_1, AbsPyxell.EMul (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_87 = happySpecReduce_3  16# happyReduction_87
happyReduction_87 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut50 happy_x_1 of { happy_var_1 -> 
	case happyOut48 happy_x_3 of { happy_var_3 -> 
	happyIn50
		 ((fst happy_var_1, AbsPyxell.EDiv (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_88 = happySpecReduce_3  16# happyReduction_88
happyReduction_88 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut50 happy_x_1 of { happy_var_1 -> 
	case happyOut48 happy_x_3 of { happy_var_3 -> 
	happyIn50
		 ((fst happy_var_1, AbsPyxell.EMod (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_89 = happySpecReduce_1  16# happyReduction_89
happyReduction_89 happy_x_1
	 =  case happyOut48 happy_x_1 of { happy_var_1 -> 
	happyIn50
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_90 = happySpecReduce_3  17# happyReduction_90
happyReduction_90 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut51 happy_x_1 of { happy_var_1 -> 
	case happyOut50 happy_x_3 of { happy_var_3 -> 
	happyIn51
		 ((fst happy_var_1, AbsPyxell.EAdd (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_91 = happySpecReduce_3  17# happyReduction_91
happyReduction_91 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut51 happy_x_1 of { happy_var_1 -> 
	case happyOut50 happy_x_3 of { happy_var_3 -> 
	happyIn51
		 ((fst happy_var_1, AbsPyxell.ESub (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_92 = happySpecReduce_2  17# happyReduction_92
happyReduction_92 happy_x_2
	happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut50 happy_x_2 of { happy_var_2 -> 
	happyIn51
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.ENeg (Just (tokenLineCol happy_var_1)) (snd happy_var_2))
	)}}

happyReduce_93 = happySpecReduce_1  17# happyReduction_93
happyReduction_93 happy_x_1
	 =  case happyOut50 happy_x_1 of { happy_var_1 -> 
	happyIn51
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_94 = happySpecReduce_3  18# happyReduction_94
happyReduction_94 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut51 happy_x_1 of { happy_var_1 -> 
	case happyOut51 happy_x_3 of { happy_var_3 -> 
	happyIn52
		 ((fst happy_var_1, AbsPyxell.ERangeIncl (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_95 = happySpecReduce_3  18# happyReduction_95
happyReduction_95 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut51 happy_x_1 of { happy_var_1 -> 
	case happyOut51 happy_x_3 of { happy_var_3 -> 
	happyIn52
		 ((fst happy_var_1, AbsPyxell.ERangeExcl (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_96 = happyReduce 5# 18# happyReduction_96
happyReduction_96 (happy_x_5 `HappyStk`
	happy_x_4 `HappyStk`
	happy_x_3 `HappyStk`
	happy_x_2 `HappyStk`
	happy_x_1 `HappyStk`
	happyRest)
	 = case happyOut51 happy_x_1 of { happy_var_1 -> 
	case happyOut51 happy_x_3 of { happy_var_3 -> 
	case happyOut51 happy_x_5 of { happy_var_5 -> 
	happyIn52
		 ((fst happy_var_1, AbsPyxell.ERangeInclStep (fst happy_var_1)(snd happy_var_1)(snd happy_var_3)(snd happy_var_5))
	) `HappyStk` happyRest}}}

happyReduce_97 = happyReduce 5# 18# happyReduction_97
happyReduction_97 (happy_x_5 `HappyStk`
	happy_x_4 `HappyStk`
	happy_x_3 `HappyStk`
	happy_x_2 `HappyStk`
	happy_x_1 `HappyStk`
	happyRest)
	 = case happyOut51 happy_x_1 of { happy_var_1 -> 
	case happyOut51 happy_x_3 of { happy_var_3 -> 
	case happyOut51 happy_x_5 of { happy_var_5 -> 
	happyIn52
		 ((fst happy_var_1, AbsPyxell.ERangeExclStep (fst happy_var_1)(snd happy_var_1)(snd happy_var_3)(snd happy_var_5))
	) `HappyStk` happyRest}}}

happyReduce_98 = happySpecReduce_1  18# happyReduction_98
happyReduction_98 happy_x_1
	 =  case happyOut51 happy_x_1 of { happy_var_1 -> 
	happyIn52
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_99 = happySpecReduce_1  19# happyReduction_99
happyReduction_99 happy_x_1
	 =  case happyOut54 happy_x_1 of { happy_var_1 -> 
	happyIn53
		 ((fst happy_var_1, AbsPyxell.ECmp (fst happy_var_1)(snd happy_var_1))
	)}

happyReduce_100 = happySpecReduce_2  19# happyReduction_100
happyReduction_100 happy_x_2
	happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut53 happy_x_2 of { happy_var_2 -> 
	happyIn53
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.ENot (Just (tokenLineCol happy_var_1)) (snd happy_var_2))
	)}}

happyReduce_101 = happySpecReduce_1  19# happyReduction_101
happyReduction_101 happy_x_1
	 =  case happyOut52 happy_x_1 of { happy_var_1 -> 
	happyIn53
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_102 = happySpecReduce_3  20# happyReduction_102
happyReduction_102 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut52 happy_x_1 of { happy_var_1 -> 
	case happyOut55 happy_x_2 of { happy_var_2 -> 
	case happyOut52 happy_x_3 of { happy_var_3 -> 
	happyIn54
		 ((fst happy_var_1, AbsPyxell.Cmp1 (fst happy_var_1)(snd happy_var_1)(snd happy_var_2)(snd happy_var_3))
	)}}}

happyReduce_103 = happySpecReduce_3  20# happyReduction_103
happyReduction_103 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut52 happy_x_1 of { happy_var_1 -> 
	case happyOut55 happy_x_2 of { happy_var_2 -> 
	case happyOut54 happy_x_3 of { happy_var_3 -> 
	happyIn54
		 ((fst happy_var_1, AbsPyxell.Cmp2 (fst happy_var_1)(snd happy_var_1)(snd happy_var_2)(snd happy_var_3))
	)}}}

happyReduce_104 = happySpecReduce_1  21# happyReduction_104
happyReduction_104 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn55
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.CmpEQ (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_105 = happySpecReduce_1  21# happyReduction_105
happyReduction_105 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn55
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.CmpNE (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_106 = happySpecReduce_1  21# happyReduction_106
happyReduction_106 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn55
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.CmpLT (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_107 = happySpecReduce_1  21# happyReduction_107
happyReduction_107 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn55
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.CmpLE (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_108 = happySpecReduce_1  21# happyReduction_108
happyReduction_108 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn55
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.CmpGT (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_109 = happySpecReduce_1  21# happyReduction_109
happyReduction_109 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn55
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.CmpGE (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_110 = happySpecReduce_3  22# happyReduction_110
happyReduction_110 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut53 happy_x_1 of { happy_var_1 -> 
	case happyOut56 happy_x_3 of { happy_var_3 -> 
	happyIn56
		 ((fst happy_var_1, AbsPyxell.EAnd (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_111 = happySpecReduce_1  22# happyReduction_111
happyReduction_111 happy_x_1
	 =  case happyOut53 happy_x_1 of { happy_var_1 -> 
	happyIn56
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_112 = happySpecReduce_3  23# happyReduction_112
happyReduction_112 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut56 happy_x_1 of { happy_var_1 -> 
	case happyOut57 happy_x_3 of { happy_var_3 -> 
	happyIn57
		 ((fst happy_var_1, AbsPyxell.EOr (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_113 = happySpecReduce_1  23# happyReduction_113
happyReduction_113 happy_x_1
	 =  case happyOut56 happy_x_1 of { happy_var_1 -> 
	happyIn57
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_114 = happySpecReduce_1  24# happyReduction_114
happyReduction_114 happy_x_1
	 =  case happyOut59 happy_x_1 of { happy_var_1 -> 
	happyIn58
		 ((fst happy_var_1, AbsPyxell.ETuple (fst happy_var_1)(snd happy_var_1))
	)}

happyReduce_115 = happySpecReduce_1  24# happyReduction_115
happyReduction_115 happy_x_1
	 =  case happyOut61 happy_x_1 of { happy_var_1 -> 
	happyIn58
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_116 = happySpecReduce_1  25# happyReduction_116
happyReduction_116 happy_x_1
	 =  case happyOut57 happy_x_1 of { happy_var_1 -> 
	happyIn59
		 ((fst happy_var_1, (:[]) (snd happy_var_1))
	)}

happyReduce_117 = happySpecReduce_3  25# happyReduction_117
happyReduction_117 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut57 happy_x_1 of { happy_var_1 -> 
	case happyOut59 happy_x_3 of { happy_var_3 -> 
	happyIn59
		 ((fst happy_var_1, (:) (snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_118 = happySpecReduce_1  26# happyReduction_118
happyReduction_118 happy_x_1
	 =  case happyOut58 happy_x_1 of { happy_var_1 -> 
	happyIn60
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_119 = happySpecReduce_1  27# happyReduction_119
happyReduction_119 happy_x_1
	 =  case happyOut57 happy_x_1 of { happy_var_1 -> 
	happyIn61
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_120 = happySpecReduce_1  28# happyReduction_120
happyReduction_120 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn62
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.TVoid (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_121 = happySpecReduce_1  28# happyReduction_121
happyReduction_121 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn62
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.TInt (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_122 = happySpecReduce_1  28# happyReduction_122
happyReduction_122 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn62
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.TBool (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_123 = happySpecReduce_1  28# happyReduction_123
happyReduction_123 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn62
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.TChar (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_124 = happySpecReduce_1  28# happyReduction_124
happyReduction_124 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn62
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.TObject (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_125 = happySpecReduce_1  28# happyReduction_125
happyReduction_125 happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	happyIn62
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.TString (Just (tokenLineCol happy_var_1)))
	)}

happyReduce_126 = happySpecReduce_3  28# happyReduction_126
happyReduction_126 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut67 happy_x_2 of { happy_var_2 -> 
	happyIn62
		 ((Just (tokenLineCol happy_var_1), AbsPyxell.TArray (Just (tokenLineCol happy_var_1)) (snd happy_var_2))
	)}}

happyReduce_127 = happySpecReduce_3  28# happyReduction_127
happyReduction_127 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOutTok happy_x_1 of { happy_var_1 -> 
	case happyOut67 happy_x_2 of { happy_var_2 -> 
	happyIn62
		 ((Just (tokenLineCol happy_var_1), snd happy_var_2)
	)}}

happyReduce_128 = happySpecReduce_1  29# happyReduction_128
happyReduction_128 happy_x_1
	 =  case happyOut64 happy_x_1 of { happy_var_1 -> 
	happyIn63
		 ((fst happy_var_1, AbsPyxell.TTuple (fst happy_var_1)(snd happy_var_1))
	)}

happyReduce_129 = happySpecReduce_1  29# happyReduction_129
happyReduction_129 happy_x_1
	 =  case happyOut68 happy_x_1 of { happy_var_1 -> 
	happyIn63
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_130 = happySpecReduce_1  30# happyReduction_130
happyReduction_130 happy_x_1
	 =  case happyOut68 happy_x_1 of { happy_var_1 -> 
	happyIn64
		 ((fst happy_var_1, (:[]) (snd happy_var_1))
	)}

happyReduce_131 = happySpecReduce_3  30# happyReduction_131
happyReduction_131 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut68 happy_x_1 of { happy_var_1 -> 
	case happyOut64 happy_x_3 of { happy_var_3 -> 
	happyIn64
		 ((fst happy_var_1, (:) (snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_132 = happySpecReduce_1  31# happyReduction_132
happyReduction_132 happy_x_1
	 =  case happyOut63 happy_x_1 of { happy_var_1 -> 
	happyIn65
		 ((fst happy_var_1, (:[]) (snd happy_var_1))
	)}

happyReduce_133 = happySpecReduce_3  31# happyReduction_133
happyReduction_133 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut63 happy_x_1 of { happy_var_1 -> 
	case happyOut65 happy_x_3 of { happy_var_3 -> 
	happyIn65
		 ((fst happy_var_1, (:) (snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_134 = happySpecReduce_3  32# happyReduction_134
happyReduction_134 happy_x_3
	happy_x_2
	happy_x_1
	 =  case happyOut65 happy_x_1 of { happy_var_1 -> 
	case happyOut63 happy_x_3 of { happy_var_3 -> 
	happyIn66
		 ((fst happy_var_1, AbsPyxell.TFunc (fst happy_var_1)(snd happy_var_1)(snd happy_var_3))
	)}}

happyReduce_135 = happySpecReduce_1  32# happyReduction_135
happyReduction_135 happy_x_1
	 =  case happyOut63 happy_x_1 of { happy_var_1 -> 
	happyIn66
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_136 = happySpecReduce_1  33# happyReduction_136
happyReduction_136 happy_x_1
	 =  case happyOut66 happy_x_1 of { happy_var_1 -> 
	happyIn67
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyReduce_137 = happySpecReduce_1  34# happyReduction_137
happyReduction_137 happy_x_1
	 =  case happyOut62 happy_x_1 of { happy_var_1 -> 
	happyIn68
		 ((fst happy_var_1, snd happy_var_1)
	)}

happyNewToken action sts stk [] =
	happyDoAction 61# notHappyAtAll action sts stk []

happyNewToken action sts stk (tk:tks) =
	let cont i = happyDoAction i tk action sts stk tks in
	case tk of {
	PT _ (TS _ 1) -> cont 1#;
	PT _ (TS _ 2) -> cont 2#;
	PT _ (TS _ 3) -> cont 3#;
	PT _ (TS _ 4) -> cont 4#;
	PT _ (TS _ 5) -> cont 5#;
	PT _ (TS _ 6) -> cont 6#;
	PT _ (TS _ 7) -> cont 7#;
	PT _ (TS _ 8) -> cont 8#;
	PT _ (TS _ 9) -> cont 9#;
	PT _ (TS _ 10) -> cont 10#;
	PT _ (TS _ 11) -> cont 11#;
	PT _ (TS _ 12) -> cont 12#;
	PT _ (TS _ 13) -> cont 13#;
	PT _ (TS _ 14) -> cont 14#;
	PT _ (TS _ 15) -> cont 15#;
	PT _ (TS _ 16) -> cont 16#;
	PT _ (TS _ 17) -> cont 17#;
	PT _ (TS _ 18) -> cont 18#;
	PT _ (TS _ 19) -> cont 19#;
	PT _ (TS _ 20) -> cont 20#;
	PT _ (TS _ 21) -> cont 21#;
	PT _ (TS _ 22) -> cont 22#;
	PT _ (TS _ 23) -> cont 23#;
	PT _ (TS _ 24) -> cont 24#;
	PT _ (TS _ 25) -> cont 25#;
	PT _ (TS _ 26) -> cont 26#;
	PT _ (TS _ 27) -> cont 27#;
	PT _ (TS _ 28) -> cont 28#;
	PT _ (TS _ 29) -> cont 29#;
	PT _ (TS _ 30) -> cont 30#;
	PT _ (TS _ 31) -> cont 31#;
	PT _ (TS _ 32) -> cont 32#;
	PT _ (TS _ 33) -> cont 33#;
	PT _ (TS _ 34) -> cont 34#;
	PT _ (TS _ 35) -> cont 35#;
	PT _ (TS _ 36) -> cont 36#;
	PT _ (TS _ 37) -> cont 37#;
	PT _ (TS _ 38) -> cont 38#;
	PT _ (TS _ 39) -> cont 39#;
	PT _ (TS _ 40) -> cont 40#;
	PT _ (TS _ 41) -> cont 41#;
	PT _ (TS _ 42) -> cont 42#;
	PT _ (TS _ 43) -> cont 43#;
	PT _ (TS _ 44) -> cont 44#;
	PT _ (TS _ 45) -> cont 45#;
	PT _ (TS _ 46) -> cont 46#;
	PT _ (TS _ 47) -> cont 47#;
	PT _ (TS _ 48) -> cont 48#;
	PT _ (TS _ 49) -> cont 49#;
	PT _ (TS _ 50) -> cont 50#;
	PT _ (TS _ 51) -> cont 51#;
	PT _ (TS _ 52) -> cont 52#;
	PT _ (TS _ 53) -> cont 53#;
	PT _ (TS _ 54) -> cont 54#;
	PT _ (TS _ 55) -> cont 55#;
	PT _ (TS _ 56) -> cont 56#;
	PT _ (TV _) -> cont 57#;
	PT _ (TI _) -> cont 58#;
	PT _ (TC _) -> cont 59#;
	PT _ (TL _) -> cont 60#;
	_ -> happyError' ((tk:tks), [])
	}

happyError_ explist 61# tk tks = happyError' (tks, explist)
happyError_ explist _ tk tks = happyError' ((tk:tks), explist)

happyThen :: () => Err a -> (a -> Err b) -> Err b
happyThen = (thenM)
happyReturn :: () => a -> Err a
happyReturn = (returnM)
happyThen1 m k tks = (thenM) m (\a -> k a tks)
happyReturn1 :: () => a -> b -> Err a
happyReturn1 = \a tks -> (returnM) a
happyError' :: () => ([(Token)], [String]) -> Err a
happyError' = (\(tokens, _) -> happyError tokens)
pProgram_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 0# tks) (\x -> happyReturn (happyOut38 x))

pListStmt_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 1# tks) (\x -> happyReturn (happyOut39 x))

pStmt_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 2# tks) (\x -> happyReturn (happyOut40 x))

pArg_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 3# tks) (\x -> happyReturn (happyOut41 x))

pListArg_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 4# tks) (\x -> happyReturn (happyOut42 x))

pBlock_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 5# tks) (\x -> happyReturn (happyOut43 x))

pListExpr_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 6# tks) (\x -> happyReturn (happyOut44 x))

pBranch_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 7# tks) (\x -> happyReturn (happyOut45 x))

pListBranch_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 8# tks) (\x -> happyReturn (happyOut46 x))

pElse_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 9# tks) (\x -> happyReturn (happyOut47 x))

pExpr9_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 10# tks) (\x -> happyReturn (happyOut48 x))

pListExpr2_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 11# tks) (\x -> happyReturn (happyOut49 x))

pExpr8_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 12# tks) (\x -> happyReturn (happyOut50 x))

pExpr7_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 13# tks) (\x -> happyReturn (happyOut51 x))

pExpr6_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 14# tks) (\x -> happyReturn (happyOut52 x))

pExpr5_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 15# tks) (\x -> happyReturn (happyOut53 x))

pCmp_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 16# tks) (\x -> happyReturn (happyOut54 x))

pCmpOp_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 17# tks) (\x -> happyReturn (happyOut55 x))

pExpr4_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 18# tks) (\x -> happyReturn (happyOut56 x))

pExpr3_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 19# tks) (\x -> happyReturn (happyOut57 x))

pExpr1_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 20# tks) (\x -> happyReturn (happyOut58 x))

pListExpr3_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 21# tks) (\x -> happyReturn (happyOut59 x))

pExpr_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 22# tks) (\x -> happyReturn (happyOut60 x))

pExpr2_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 23# tks) (\x -> happyReturn (happyOut61 x))

pType4_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 24# tks) (\x -> happyReturn (happyOut62 x))

pType2_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 25# tks) (\x -> happyReturn (happyOut63 x))

pListType3_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 26# tks) (\x -> happyReturn (happyOut64 x))

pListType2_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 27# tks) (\x -> happyReturn (happyOut65 x))

pType1_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 28# tks) (\x -> happyReturn (happyOut66 x))

pType_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 29# tks) (\x -> happyReturn (happyOut67 x))

pType3_internal tks = happySomeParser where
 happySomeParser = happyThen (happyParse 30# tks) (\x -> happyReturn (happyOut68 x))

happySeq = happyDontSeq


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
pStmt = (>>= return . snd) . pStmt_internal
pArg = (>>= return . snd) . pArg_internal
pListArg = (>>= return . snd) . pListArg_internal
pBlock = (>>= return . snd) . pBlock_internal
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
pListType2 = (>>= return . snd) . pListType2_internal
pType1 = (>>= return . snd) . pType1_internal
pType = (>>= return . snd) . pType_internal
pType3 = (>>= return . snd) . pType3_internal
{-# LINE 1 "templates\GenericTemplate.hs" #-}
{-# LINE 1 "templates\\GenericTemplate.hs" #-}
{-# LINE 1 "<built-in>" #-}
{-# LINE 1 "<command-line>" #-}
{-# LINE 11 "<command-line>" #-}
{-# LINE 1 "D:\\GitHub\\haskell-platform\\build\\ghc-bindist\\local\\lib/include\\ghcversion.h" #-}















{-# LINE 11 "<command-line>" #-}
{-# LINE 1 "C:\\Users\\randy\\AppData\\Local\\Temp\\ghc10356_0\\ghc_2.h" #-}




























































































































































{-# LINE 11 "<command-line>" #-}
{-# LINE 1 "templates\\GenericTemplate.hs" #-}
-- Id: GenericTemplate.hs,v 1.26 2005/01/14 14:47:22 simonmar Exp 













-- Do not remove this comment. Required to fix CPP parsing when using GCC and a clang-compiled alex.
#if __GLASGOW_HASKELL__ > 706
#define LT(n,m) ((Happy_GHC_Exts.tagToEnum# (n Happy_GHC_Exts.<# m)) :: Bool)
#define GTE(n,m) ((Happy_GHC_Exts.tagToEnum# (n Happy_GHC_Exts.>=# m)) :: Bool)
#define EQ(n,m) ((Happy_GHC_Exts.tagToEnum# (n Happy_GHC_Exts.==# m)) :: Bool)
#else
#define LT(n,m) (n Happy_GHC_Exts.<# m)
#define GTE(n,m) (n Happy_GHC_Exts.>=# m)
#define EQ(n,m) (n Happy_GHC_Exts.==# m)
#endif
{-# LINE 43 "templates\\GenericTemplate.hs" #-}

data Happy_IntList = HappyCons Happy_GHC_Exts.Int# Happy_IntList







{-# LINE 65 "templates\\GenericTemplate.hs" #-}

{-# LINE 75 "templates\\GenericTemplate.hs" #-}

{-# LINE 84 "templates\\GenericTemplate.hs" #-}

infixr 9 `HappyStk`
data HappyStk a = HappyStk a (HappyStk a)

-----------------------------------------------------------------------------
-- starting the parse

happyParse start_state = happyNewToken start_state notHappyAtAll notHappyAtAll

-----------------------------------------------------------------------------
-- Accepting the parse

-- If the current token is 0#, it means we've just accepted a partial
-- parse (a %partial parser).  We must ignore the saved token on the top of
-- the stack in this case.
happyAccept 0# tk st sts (_ `HappyStk` ans `HappyStk` _) =
        happyReturn1 ans
happyAccept j tk st sts (HappyStk ans _) = 
        (happyTcHack j (happyTcHack st)) (happyReturn1 ans)

-----------------------------------------------------------------------------
-- Arrays only: do the next action



happyDoAction i tk st
        = {- nothing -}


          case action of
                0#           -> {- nothing -}
                                     happyFail (happyExpListPerState ((Happy_GHC_Exts.I# (st)) :: Int)) i tk st
                -1#          -> {- nothing -}
                                     happyAccept i tk st
                n | LT(n,(0# :: Happy_GHC_Exts.Int#)) -> {- nothing -}

                                                   (happyReduceArr Happy_Data_Array.! rule) i tk st
                                                   where rule = (Happy_GHC_Exts.I# ((Happy_GHC_Exts.negateInt# ((n Happy_GHC_Exts.+# (1# :: Happy_GHC_Exts.Int#))))))
                n                 -> {- nothing -}


                                     happyShift new_state i tk st
                                     where new_state = (n Happy_GHC_Exts.-# (1# :: Happy_GHC_Exts.Int#))
   where off    = happyAdjustOffset (indexShortOffAddr happyActOffsets st)
         off_i  = (off Happy_GHC_Exts.+#  i)
         check  = if GTE(off_i,(0# :: Happy_GHC_Exts.Int#))
                  then EQ(indexShortOffAddr happyCheck off_i, i)
                  else False
         action
          | check     = indexShortOffAddr happyTable off_i
          | otherwise = indexShortOffAddr happyDefActions st




indexShortOffAddr (HappyA# arr) off =
        Happy_GHC_Exts.narrow16Int# i
  where
        i = Happy_GHC_Exts.word2Int# (Happy_GHC_Exts.or# (Happy_GHC_Exts.uncheckedShiftL# high 8#) low)
        high = Happy_GHC_Exts.int2Word# (Happy_GHC_Exts.ord# (Happy_GHC_Exts.indexCharOffAddr# arr (off' Happy_GHC_Exts.+# 1#)))
        low  = Happy_GHC_Exts.int2Word# (Happy_GHC_Exts.ord# (Happy_GHC_Exts.indexCharOffAddr# arr off'))
        off' = off Happy_GHC_Exts.*# 2#




{-# INLINE happyLt #-}
happyLt x y = LT(x,y)


readArrayBit arr bit =
    Bits.testBit (Happy_GHC_Exts.I# (indexShortOffAddr arr ((unbox_int bit) `Happy_GHC_Exts.iShiftRA#` 4#))) (bit `mod` 16)
  where unbox_int (Happy_GHC_Exts.I# x) = x






data HappyAddr = HappyA# Happy_GHC_Exts.Addr#


-----------------------------------------------------------------------------
-- HappyState data type (not arrays)

{-# LINE 180 "templates\\GenericTemplate.hs" #-}

-----------------------------------------------------------------------------
-- Shifting a token

happyShift new_state 0# tk st sts stk@(x `HappyStk` _) =
     let i = (case Happy_GHC_Exts.unsafeCoerce# x of { (Happy_GHC_Exts.I# (i)) -> i }) in
--     trace "shifting the error token" $
     happyDoAction i tk new_state (HappyCons (st) (sts)) (stk)

happyShift new_state i tk st sts stk =
     happyNewToken new_state (HappyCons (st) (sts)) ((happyInTok (tk))`HappyStk`stk)

-- happyReduce is specialised for the common cases.

happySpecReduce_0 i fn 0# tk st sts stk
     = happyFail [] 0# tk st sts stk
happySpecReduce_0 nt fn j tk st@((action)) sts stk
     = happyGoto nt j tk st (HappyCons (st) (sts)) (fn `HappyStk` stk)

happySpecReduce_1 i fn 0# tk st sts stk
     = happyFail [] 0# tk st sts stk
happySpecReduce_1 nt fn j tk _ sts@((HappyCons (st@(action)) (_))) (v1`HappyStk`stk')
     = let r = fn v1 in
       happySeq r (happyGoto nt j tk st sts (r `HappyStk` stk'))

happySpecReduce_2 i fn 0# tk st sts stk
     = happyFail [] 0# tk st sts stk
happySpecReduce_2 nt fn j tk _ (HappyCons (_) (sts@((HappyCons (st@(action)) (_))))) (v1`HappyStk`v2`HappyStk`stk')
     = let r = fn v1 v2 in
       happySeq r (happyGoto nt j tk st sts (r `HappyStk` stk'))

happySpecReduce_3 i fn 0# tk st sts stk
     = happyFail [] 0# tk st sts stk
happySpecReduce_3 nt fn j tk _ (HappyCons (_) ((HappyCons (_) (sts@((HappyCons (st@(action)) (_))))))) (v1`HappyStk`v2`HappyStk`v3`HappyStk`stk')
     = let r = fn v1 v2 v3 in
       happySeq r (happyGoto nt j tk st sts (r `HappyStk` stk'))

happyReduce k i fn 0# tk st sts stk
     = happyFail [] 0# tk st sts stk
happyReduce k nt fn j tk st sts stk
     = case happyDrop (k Happy_GHC_Exts.-# (1# :: Happy_GHC_Exts.Int#)) sts of
         sts1@((HappyCons (st1@(action)) (_))) ->
                let r = fn stk in  -- it doesn't hurt to always seq here...
                happyDoSeq r (happyGoto nt j tk st1 sts1 r)

happyMonadReduce k nt fn 0# tk st sts stk
     = happyFail [] 0# tk st sts stk
happyMonadReduce k nt fn j tk st sts stk =
      case happyDrop k (HappyCons (st) (sts)) of
        sts1@((HappyCons (st1@(action)) (_))) ->
          let drop_stk = happyDropStk k stk in
          happyThen1 (fn stk tk) (\r -> happyGoto nt j tk st1 sts1 (r `HappyStk` drop_stk))

happyMonad2Reduce k nt fn 0# tk st sts stk
     = happyFail [] 0# tk st sts stk
happyMonad2Reduce k nt fn j tk st sts stk =
      case happyDrop k (HappyCons (st) (sts)) of
        sts1@((HappyCons (st1@(action)) (_))) ->
         let drop_stk = happyDropStk k stk

             off = happyAdjustOffset (indexShortOffAddr happyGotoOffsets st1)
             off_i = (off Happy_GHC_Exts.+#  nt)
             new_state = indexShortOffAddr happyTable off_i




          in
          happyThen1 (fn stk tk) (\r -> happyNewToken new_state sts1 (r `HappyStk` drop_stk))

happyDrop 0# l = l
happyDrop n (HappyCons (_) (t)) = happyDrop (n Happy_GHC_Exts.-# (1# :: Happy_GHC_Exts.Int#)) t

happyDropStk 0# l = l
happyDropStk n (x `HappyStk` xs) = happyDropStk (n Happy_GHC_Exts.-# (1#::Happy_GHC_Exts.Int#)) xs

-----------------------------------------------------------------------------
-- Moving to a new state after a reduction


happyGoto nt j tk st = 
   {- nothing -}
   happyDoAction j tk new_state
   where off = happyAdjustOffset (indexShortOffAddr happyGotoOffsets st)
         off_i = (off Happy_GHC_Exts.+#  nt)
         new_state = indexShortOffAddr happyTable off_i




-----------------------------------------------------------------------------
-- Error recovery (0# is the error token)

-- parse error if we are in recovery and we fail again
happyFail explist 0# tk old_st _ stk@(x `HappyStk` _) =
     let i = (case Happy_GHC_Exts.unsafeCoerce# x of { (Happy_GHC_Exts.I# (i)) -> i }) in
--      trace "failing" $ 
        happyError_ explist i tk

{-  We don't need state discarding for our restricted implementation of
    "error".  In fact, it can cause some bogus parses, so I've disabled it
    for now --SDM

-- discard a state
happyFail  0# tk old_st (HappyCons ((action)) (sts)) 
                                                (saved_tok `HappyStk` _ `HappyStk` stk) =
--      trace ("discarding state, depth " ++ show (length stk))  $
        happyDoAction 0# tk action sts ((saved_tok`HappyStk`stk))
-}

-- Enter error recovery: generate an error token,
--                       save the old token and carry on.
happyFail explist i tk (action) sts stk =
--      trace "entering error recovery" $
        happyDoAction 0# tk action sts ( (Happy_GHC_Exts.unsafeCoerce# (Happy_GHC_Exts.I# (i))) `HappyStk` stk)

-- Internal happy errors:

notHappyAtAll :: a
notHappyAtAll = error "Internal Happy error\n"

-----------------------------------------------------------------------------
-- Hack to get the typechecker to accept our action functions


happyTcHack :: Happy_GHC_Exts.Int# -> a -> a
happyTcHack x y = y
{-# INLINE happyTcHack #-}


-----------------------------------------------------------------------------
-- Seq-ing.  If the --strict flag is given, then Happy emits 
--      happySeq = happyDoSeq
-- otherwise it emits
--      happySeq = happyDontSeq

happyDoSeq, happyDontSeq :: a -> b -> b
happyDoSeq   a b = a `seq` b
happyDontSeq a b = b

-----------------------------------------------------------------------------
-- Don't inline any functions from the template.  GHC has a nasty habit
-- of deciding to inline happyGoto everywhere, which increases the size of
-- the generated parser quite a bit.


{-# NOINLINE happyDoAction #-}
{-# NOINLINE happyTable #-}
{-# NOINLINE happyCheck #-}
{-# NOINLINE happyActOffsets #-}
{-# NOINLINE happyGotoOffsets #-}
{-# NOINLINE happyDefActions #-}

{-# NOINLINE happyShift #-}
{-# NOINLINE happySpecReduce_0 #-}
{-# NOINLINE happySpecReduce_1 #-}
{-# NOINLINE happySpecReduce_2 #-}
{-# NOINLINE happySpecReduce_3 #-}
{-# NOINLINE happyReduce #-}
{-# NOINLINE happyMonadReduce #-}
{-# NOINLINE happyGoto #-}
{-# NOINLINE happyFail #-}

-- end of Happy Template.
