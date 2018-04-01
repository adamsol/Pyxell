{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}

module Main where

import System.IO
import System.Environment
import System.Exit
import System.FilePath
import System.Process

import Control.Monad
import Control.Monad.IO.Class
import Control.Monad.Trans.State
import Control.Monad.Trans.Reader
import Control.Monad.Trans.Writer
import Control.Monad.Trans.Error
import qualified Data.Map as M

import LexPyxell
import ParPyxell
import PrintPyxell
import AbsPyxell
import LayoutPyxell (resolveLayout)
import ErrM

import Checker
import Compiler


main :: IO ()
main = do
    args <- getArgs
    case args of
        [] -> hPutStrLn stderr $ "File path needed!"
        path:_ -> do
            let base = fst $ splitExtension path
            program <- readFile path
            case pProgram $ resolveLayout True $ myLexer program of
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
                            output <- execWriterT $ runStateT (runReaderT (compileProgram prog) M.empty) M.empty
                            writeFile (base ++ ".ll") output
                            readProcess "clang" [base ++ ".ll", "lib/runtime.ll", "-o", base ++ ".exe", "-O2"] ""
                            return $ ()
