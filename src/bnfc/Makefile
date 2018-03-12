all:
	bnfc --functor ../Pyxell.cf
	happy -gca ParPyxell.y
	alex -g LexPyxell.x

clean:
	-rm -f *.log *.aux *.hi *.o *.dvi

distclean: clean
	-rm -f DocPyxell.* LexPyxell.* ParPyxell.* LayoutPyxell.* SkelPyxell.* PrintPyxell.* TestPyxell.* AbsPyxell.* TestPyxell ErrM.* SharedString.* ComposOp.* Pyxell.dtd XMLPyxell.* Makefile*
	

