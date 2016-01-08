NODE_MODULES = ./node_modules
MTP_COMMON = $(NODE_MODULES)/money-to-prisoners-common
GOVUK_ELEMENTS = $(NODE_MODULES)/mojular-govuk-elements
MOJ_ELEMENTS = $(NODE_MODULES)/mojular-moj-elements
RUN_TASK = $(MTP_COMMON)/tasks.sh
NODE_BIN = $(NODE_MODULES)/.bin

MTP_APP_PATH = mtp_$(subst -,_,$(app))

ASSETS_TARGET = ./$(MTP_APP_PATH)/assets
ASSETS_SOURCE = ./$(MTP_APP_PATH)/assets-src
TEMPLATES = ./$(MTP_APP_PATH)/templates

JS_PATH = $(ASSETS_TARGET)/scripts
ALL_JS := $(shell find -L $(ASSETS_SOURCE)/javascripts $(MTP_COMMON)/assets/javascripts -name \*.js)

CSS_PATH = $(ASSETS_TARGET)/stylesheets

SASS_DIRS = $(NODE_MODULES)/breakpoint-sass/stylesheets $(NODE_MODULES)/include-media/dist $(NODE_MODULES)/bourbon/app/assets/stylesheets $(NODE_MODULES)/susy/sass $(ASSETS_SOURCE)/stylesheets $(GOVUK_ELEMENTS)/sass $(MOJ_ELEMENTS)/sass $(MTP_COMMON)/assets/scss $(MTP_COMMON)/assets/scss/elements $(NODE_MODULES)

SASS_FILES := $(shell find -L $(SASS_DIRS) -name \*.scss)

IMAGE_FILES := $(MTP_COMMON)/assets/images/* $(GOVUK_ELEMENTS)/images/*

SASS_LOAD_PATH := $(patsubst %,--include-path %, $(SASS_DIRS))

WATCHLIST := $(ASSETS_SOURCE) $(MTP_COMMON) $(GOVUK_ELEMENTS) $(MOJ_ELEMENTS) $(TEMPLATES)

SELENIUM = $(NODE_MODULES)/selenium-standalone/.selenium

#################
#### RECIPES ####
#################

# all the assets
.PHONY: build
build: node_modules $(JS_PATH)/app.bundle.js $(CSS_PATH)/app.css $(CSS_PATH)/app-print.css ./$(MTP_APP_PATH)/assets/images

# remove all the assets
.PHONY: clean
clean:
	rm -rf $(ASSETS_TARGET) $(NODE_MODULES)

# monitor assets and recompile them when they change
.PHONY: watch
watch:
	@echo Monitoring changes
	@fswatch -l 1 -o $(WATCHLIST) | xargs -n1 -I {} /usr/bin/env bash -c './run.sh $(watch_callback)'

######################
#### FILE TARGETS ####
######################

$(JS_PATH)/app.bundle.js: $(ALL_JS)
	@echo Generating `basename $@`
	-@$(NODE_BIN)/jshint $<
	@$(NODE_BIN)/webpack > /dev/null

# Make the various css files (app, app-print) from their respective sources
$(CSS_PATH)/%.css: $(SASS_FILES)
	@echo Generating `basename $@`
	@$(NODE_BIN)/node-sass $(SASS_LOAD_PATH) $(ASSETS_SOURCE)/stylesheets/$*.scss $@ > /dev/null 2>&1

node_modules:
	@echo Installing node modules
	npm install
	@echo "node_modules installed. Don't forget to link to local modules as needed (eg npm link money-to-prisoners-common)"

$(MTP_APP_PATH)/assets/images: $(IMAGE_FILES)
	@echo Collecting images
	@mkdir -p $@
	@cp $(IMAGE_FILES) ./$(MTP_APP_PATH)/assets/images

$(SELENIUM):
	@echo Installing selenium binaries
	@$(NODE_BIN)/selenium-standalone install
