# Output directory meant for serving.
BUILD_DIR = _build

# Google Closure tools.
#
# Path to the Closure compiler .jar file.
# http://closure-compiler.googlecode.com/files/compiler-latest.zip
CLOSURE_JAR = src/third_party/closure.jar
# Path to closurebuilder.py tool within the Closure respository.
BUILDER = src/third_party/closure-library/closure/bin/build/closurebuilder.py
# Flags to pass to the closurebuilder.py tool and the Closure compiler.
BUILDER_FLAGS = \
  --root=$(BUILD_DIR)/js/app \
  --root=$(BUILD_DIR)/js/third_party \
  --namespace="pastee.main" \
  --compiler_jar=$(CLOSURE_JAR) \
  -o compiled \
  -f --compilation_level=ADVANCED_OPTIMIZATIONS
# Path to depswriter.py.
DEPSWRITER = src/third_party/closure-library/closure/bin/build/depswriter.py

# TypeScript compiler path and flags.
TSC = tsc
TSC_FLAGS = --declaration --sourcemap

# JavaScript dependencies.
JS_THIRD_PARTY_DEPS = \
  src/third_party/sjcl.js \
  src/third_party/closure-library/closure/goog/base.js

paste_SRC = src/paste.ts
paste_OUT = $(BUILD_DIR)/js/app/paste.js
paste_DECL = $(BUILD_DIR)/js/app/paste.d.ts
paste_IDEPS = builddir

main_SRC = src/main.ts
main_OUT = $(BUILD_DIR)/js/app/main.js
main_DEPS = $(paste_DECL)
main_IDEPS = $(paste_OUT) builddir

deps_SRC =
deps_OUT = $(BUILD_DIR)/js/deps.js
deps_DEPS = $(paste_OUT) $(main_OUT)
deps_IDEPS = builddir

app_min_SRC =
app_min_OUT = $(BUILD_DIR)/js/app.min.js
app_min_DEPS = $(paste_OUT) $(main_OUT)
app_min_IDEPS = builddir

$(paste_OUT): $(paste_SRC) $(paste_DEPS) | $(paste_IDEPS)
	$(TSC) $(TSC_FLAGS) --out $@ $^

$(main_OUT): $(main_SRC) $(main_DEPS) | $(main_IDEPS)
	$(TSC) $(TSC_FLAGS) --out $@ $^

$(app_min_OUT): $(app_min_SRC) $(app_min_DEPS) | $(app_min_IDEPS)
	$(BUILDER) $(BUILDER_FLAGS) > $@

$(deps_OUT): $(deps_SRC) $(deps_DEPS) | $(deps_IDEPS)
	$(DEPSWRITER) --root_with_prefix="$(BUILD_DIR)/js/app ../app" > $@

# Generic rules below.
builddir:
	mkdir -p $(BUILD_DIR)/js/app
	mkdir -p $(BUILD_DIR)/js/third_party
	rsync -a static/* $(BUILD_DIR)
	rsync -a $(JS_THIRD_PARTY_DEPS) $(BUILD_DIR)/js/third_party/

# With just `make' or `make default', build the unminified app.
default: $(deps_OUT)
.DEFAULT_GOAL := default

# With `make all', build the minified app.
all: $(app_min_OUT)

clean:
	rm -rf $(BUILD_DIR)
