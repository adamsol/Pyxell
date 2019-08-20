all: grammar bin

grammar:
	+$(MAKE) -C bnfc

bin:
	ghc --make Main.hs -i./bnfc/ -o ../pyxell \
	    -XFlexibleInstances -XFlexibleContexts -XLambdaCase \
	    -fwarn-unused-imports -fno-warn-warnings-deprecations

clean:
	+$(MAKE) clean -C bnfc
