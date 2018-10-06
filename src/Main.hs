{-# OPTIONS_GHC -fno-warn-warnings-deprecations #-}

module Main where

import System.IO
import System.Environment
import System.Exit
import System.FilePath
import System.Process

import Control.Monad
import Control.Monad.Trans.Reader
import Control.Monad.Trans.State
import Control.Monad.Trans.Error
import qualified Data.Map as M

import AbsPyxell
import ParPyxell
import LayoutPyxell (resolveLayout)
import ErrM

import Checker
import CodeGen
import Compiler
import Libraries
import Utils


-- | Runs compilation and writes generated LLVM code to a file.
outputCode :: [CodeGen.Run CodeGen.Env] -> String -> Bool -> IO ()
outputCode units path main = do
    -- Compile sequentially all units, passing down the environment and output.
    (_, output) <- foldM (\((e, s), o) unit -> runStateT (runStateT (runReaderT unit e) s) o) ((M.empty, M.empty), M.empty) (initCompiler : units)
    output <- case main of
        True -> return $ M.adjust (\ls-> ["}", "\tret i64 0"] ++ ls ++ ["entry:", "define i64 @main() {"]) "main" output
        False -> return $ output
    -- Write concatenated output to the file.
    writeFile path (concat [unlines (reverse lines) ++ "\n" | lines <- M.elems output])


main :: IO ()
main = do
    args <- getArgs
    case args of
        [] -> hPutStrLn stderr $ "File path needed!"
        "-l":_ -> do
            outputCode [libBase] "lib/base.ll" False
        path:clangArgs -> do
            let file = fst $ splitExtension path
            let paths = ["lib/std.px", path]
            -- Type-check all files, passing down the environment.
            (_, units) <- foldM' (M.fromList [(Ident "#level", (tLabel, 0))], []) paths $ \(env, units) path -> do
                code <- readFile path
                case pProgram $ resolveLayout True $ myLexer code of
                    Bad err -> do
                        hPutStrLn stderr $ path ++ ": " ++ err
                        exitFailure
                        return $ (env, units)
                    Ok prog -> do
                        result <- runErrorT $ runReaderT (checkProgram prog) env
                        case result of
                            Left error -> do
                                hPutStr stderr $ path ++ error
                                exitFailure
                                return $ (env, units)
                            Right env' -> do
                                return $ (env', compileProgram prog : units)
            -- Compile all units to one LLVM file.
            outputCode (reverse units) (file ++ ".ll") True
            -- Generate executable file.
            readProcess "clang" ([file ++ ".ll", "lib/base.ll", "-o", file ++ ".exe", "-O2"] ++ clangArgs) ""
            return $ ()
