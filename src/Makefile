all: parser

parser:
	java -jar antlr*.jar Pyxell.g4 -visitor -no-listener -Dlanguage=Python3 -o antlr

clean:
	rm -rf antlr/
