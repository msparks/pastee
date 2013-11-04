DART2JS = dart2js

ifeq ($(DEBUG), 1)
  FLAGS += -c
endif

BINARIES = pastee.dart.js

%.dart.js: %.dart
	$(DART2JS) $(FLAGS) -o$@ $<

clean:
	rm -f *.dart.*

all: $(BINARIES)
.DEFAULT_GOAL := $(BINARIES)
