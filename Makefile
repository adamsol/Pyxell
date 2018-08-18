all:
	+$(MAKE) -C src
grammar:
	+$(MAKE) grammar -C src
code:
	+$(MAKE) code -C src

clean:
	+$(MAKE) clean -C src
	-rm -f pyxell pyxell.exe
