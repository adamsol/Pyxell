all:
	+$(MAKE) -C bnfc
	ghc --make Main.hs -i./bnfc/ -o ../pyxell

clean:
	+$(MAKE) clean -C bnfc
