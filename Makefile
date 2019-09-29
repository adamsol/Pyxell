all: parser libs

parser:
	+$(MAKE) parser -C src
libs:
	./pyxell.py -l

clean:
	+$(MAKE) clean -C src
