all: grammar bin

grammar:
	+$(MAKE) -C bnfc
bin:
	ghc --make -fwarn-unused-imports Main.hs -i./bnfc/ -o ../pyxell

clean:
	+$(MAKE) clean -C bnfc
