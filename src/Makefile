all: parser

parser: Pyxell.g4
	java -jar antlr*.jar Pyxell.g4 -visitor -no-listener -Dlanguage=Python3 -o parser

clean:
	rm -rf parser/
