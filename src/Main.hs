{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}

module Main where

import System.IO
import System.Environment
import System.Exit
import System.FilePath
import System.Process

import Control.Monad.Trans.Reader
import Control.Monad.Trans.Error
import qualified Data.Map as M

import ParPyxell
import LayoutPyxell (resolveLayout)
import ErrM

import Checker
import CodeGen
import Compiler
import Libraries
import Utils


type Env = M.Map String Type

-- | Type-checks Pyxell code and optionally compiles to an executable file.
run :: String -> [String] -> Env -> Bool -> Bool -> IO Env
run path libs env compile exe = do
    let base = fst $ splitExtension path
    code <- readFile path
    case pProgram $ resolveLayout True $ myLexer code of
        Bad err -> do
            hPutStrLn stderr $ path ++ ": " ++ err
            exitFailure
            return $ M.empty
        Ok prog -> do
            result <- runErrorT $ runReaderT (checkProgram prog env) M.empty
            case result of
                Left error -> do
                    hPutStr stderr $ path ++ error
                    exitFailure
                    return $ M.empty
                Right env' -> do
                    if compile then do
                        outputCode (compileProgram prog env exe) (base ++ ".ll")
                        if exe then readProcess "clang" ([base ++ ".ll"] ++ libs ++ [ "-o", base ++ ".exe", "-O2"]) ""
                        else return $ ""
                    else return $ ""
                    return $ env'

main :: IO ()
main = do
    args <- getArgs
    case args of
        [] -> hPutStrLn stderr $ "File path needed!"
        "-l":_ -> do
            outputCode libBase "lib/base.ll"
            run "lib/std.px" ["lib/base.ll"] M.empty True False
            return $ ()
        path:_ -> do
            env <- run "lib/std.px" ["lib/base.ll"] M.empty False False
            run path ["lib/base.ll", "lib/std.ll"] env True True
            return $ ()
