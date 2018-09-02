all: grammar bin libs

grammar:
	+$(MAKE) grammar -C src
bin:
	+$(MAKE) bin -C src
libs:
	./pyxell -l

clean:
	+$(MAKE) clean -C src
	-rm -f pyxell pyxell.exe
