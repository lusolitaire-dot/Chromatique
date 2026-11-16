.PHONY: all build clean test
ARCH ?= native
JOBS ?= 2
ifeq ($(shell uname -s),Darwin)
COMP ?= clang
else
COMP ?= gcc
endif

all: build

build:
	mkdir -p bin
	$(MAKE) -C src -j$(JOBS) build ARCH=$(ARCH) COMP=$(COMP) EXE=../bin/chromatique-v4.1.0 EXTRACXXFLAGS=-DNNUE_EMBEDDING_OFF

clean:
	$(MAKE) -C src objclean
	rm -f bin/chromatique-v4.1.0

test:
	python3 -m unittest discover -s tests -v
