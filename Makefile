
PYTHON ?= python

ifeq ($(OS), Windows_NT)
	LIB_PATH = lib/;lib/
	VERSION_PATH = version.txt;.
else
	LIB_PATH = lib/:lib/
	VERSION_PATH = version.txt:.
endif

all: exe docs

exe:
	"$(PYTHON)" -m PyInstaller --hidden-import=decorator --add-data "$(LIB_PATH)" --add-data "$(VERSION_PATH)" pyxell.py --noconfirm

.PHONY: docs
docs:
	"$(MAKE)" docs -C docs

clean:
	rm -rf build/ dist/
	"$(MAKE)" clean -C docs
