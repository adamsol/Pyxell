all:
	+$(MAKE) -C src

clean:
	+$(MAKE) clean -C src
	-rm -f pyxell.exe
