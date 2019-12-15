all: parser

parser:
	"$(MAKE)" parser -C src

clean:
	"$(MAKE)" clean -C src
