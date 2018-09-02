{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}

module Main where

import System.IO
import System.Environment
import System.Exit
import System.FilePath
import System.Process

import Control.Monad.Trans.Reader
import Control.Monad.Trans.Error
import Data.List
import qualified Data.Map as M

import ParPyxell
import LayoutPyxell (resolveLayout)
import ErrM

import Checker
import CodeGen
import Compiler
import Libraries


main :: IO ()
main = do
    args <- getArgs
    case args of
        [] -> hPutStrLn stderr $ "File path needed!"
        "-l":_ -> do
            outputCode libInternal "lib/runtime.ll"
        path:_ -> do
            let base = fst $ splitExtension path
            code <- readFile path
            lib <- readFile "lib/std.px"
            case pProgram $ resolveLayout True $ myLexer (intercalate "\n" [lib, code]) of
                Bad err -> do
                    hPutStrLn stderr $ path ++ ": " ++ err
                    exitFailure
                Ok prog -> do
                    result <- runErrorT $ runReaderT (checkProgram prog) M.empty
                    case result of
                        Left error -> do
                            hPutStr stderr $ path ++ error
                            exitFailure
                        Right () -> do
                            outputCode (compileProgram prog) (base ++ ".ll")
                            readProcess "clang" [base ++ ".ll", "lib/runtime.ll", "-o", base ++ ".exe", "-O2"] ""
                            return $ ()
