all: parser libs exe

parser:
	"$(MAKE)" parser -C src

libs:
	python pyxell.py --libs

exe:
	python -m PyInstaller --hidden-import=decorator --add-data "lib/;lib/" pyxell.py --noconfirm

clean:
	"$(MAKE)" clean -C src
	rm -f lib/*.ll lib/*.json
	rm -rf build/ dist/
