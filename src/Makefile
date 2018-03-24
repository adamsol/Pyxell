all: grammar code

grammar:
	+$(MAKE) -C bnfc
code:
	ghc --make Main.hs -i./bnfc/ -o ../pyxell

clean:
	+$(MAKE) clean -C bnfc
