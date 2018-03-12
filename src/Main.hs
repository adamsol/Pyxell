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


main :: IO ()
main = do
    args <- getArgs
    case args of
        [] -> hPutStrLn stderr $ "ERROR\nFile path needed!"
        path:_ -> do
            let base = fst $ splitExtension path
            program <- readFile path
            case pProgram $ resolveLayout True $ myLexer program of
                Bad err -> do
                    hPutStrLn stderr $ "ERROR\n" ++ path ++ ": " ++ err
                    exitFailure
                Ok prog -> do
                    result <- runErrorT $ runReaderT (checkProgram prog) M.empty
                    case result of
                        Left error -> do
                            hPutStrLn stderr $ "ERROR\n" ++ path ++ error
                            exitFailure
                        Right () -> do
                            hPutStrLn stderr $ "OK"
