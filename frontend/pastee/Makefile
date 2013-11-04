DART = dart
PUB = pub

ifeq ($(DEBUG), 1)
  FLAGS += -c
endif

out: build.dart
	$(DART) build.dart

out/pubspec.yaml: pubspec.yaml
	ln -s ../$< out/$<

.PHONY: build
build:
	$(PUB) build

serve: out out/pubspec.yaml
	cd out && $(PUB) serve

.PHONY: clean
clean:
	rm -rf out build

all: build
.DEFAULT_GOAL := all
