
PYTHON ?= python

ifeq ($(OS), Windows_NT)
	LIB_PATH = lib/;lib/
	VERSION_PATH = version.txt;.
else
	LIB_PATH = lib/:lib/
	VERSION_PATH = version.txt:.
endif

all: parser libs exe docs

parser:
	"$(MAKE)" parser -C src

libs:
	"$(PYTHON)" pyxell.py --libs

exe:
	"$(PYTHON)" -m PyInstaller --hidden-import=decorator --add-data "$(LIB_PATH)" --add-data "$(VERSION_PATH)" pyxell.py --noconfirm

.PHONY: docs
docs:
	"$(MAKE)" docs -C docs

clean:
	"$(MAKE)" clean -C src
	rm -f lib/*.ll lib/*.json
	rm -rf build/ dist/
	"$(MAKE)" clean -C docs
