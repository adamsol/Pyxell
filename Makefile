all: parser exe

parser:
	"$(MAKE)" parser -C src

exe:
	python -m PyInstaller --add-data "lib/;lib/" pyxell.py --noconfirm

clean:
	"$(MAKE)" clean -C src
	rm -rf build/ dist/
