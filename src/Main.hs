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
    -- Compile sequentially all units, passing down the environment, state and output.
    (_, output) <- foldM (\((e, s), o) unit -> runStateT (runStateT (runReaderT unit e) s) o) ((M.empty, M.empty), M.empty) (initCompiler : units)
    output <- case main of
        True -> return $ M.insert "main-4" ["}", "\tret i64 0"] (M.insert "main-0" ["entry:", "define i64 @main() {"] output)
        False -> return $ output
    -- Write concatenated output to the file.
    writeFile path (concat [unlines (reverse lines) | lines <- M.elems output])


main :: IO ()
main = do
    abspath <- getExecutablePath >>= return . takeDirectory
    args <- getArgs
    case args of
        [] -> hPutStrLn stderr $ "File path needed!"
        "-l":_ -> do
            outputCode [libBase] (abspath </> "lib/base.ll") False
            outputCode [libMath] (abspath </> "lib/math.ll") False
            readProcess "clang" [abspath </> "lib/io.c", "-S", "-emit-llvm", "-o", abspath </> "lib/io.ll"] ""
            return $ ()
        path:clangArgs -> do
            let file = fst $ splitExtension path
            let paths = [("std", abspath </> "lib/std.px"), ("math", abspath </> "lib/math.px"), ("main", path)]
            -- Type-check all files, passing down the environment.
            (_, units) <- foldM' (M.fromList [(Ident "#level", (tVoid, Level 0))], []) paths $ \(env, units) (name, path) -> do
                code <- readFile path
                case pProgram $ resolveLayout True $ myLexer code of
                    Bad err -> do
                        hPutStrLn stderr $ path ++ ": " ++ err
                        exitFailure
                        return $ (env, units)
                    Ok prog -> do
                        result <- runErrorT $ runReaderT (checkProgram prog name) env
                        case result of
                            Left error -> do
                                hPutStr stderr $ path ++ error
                                exitFailure
                                return $ (env, units)
                            Right env' -> do
                                return $ (env', compileProgram prog name : units)
            -- Compile all units to one LLVM file.
            outputCode (reverse units) (file ++ ".ll") True
            -- Generate executable file.
            readProcess "clang" ([file ++ ".ll", abspath </> "lib/io.ll", abspath </> "lib/base.ll", abspath </> "lib/math.ll", "-o", file ++ ".exe", "-O2"] ++ clangArgs) ""
            return $ ()
