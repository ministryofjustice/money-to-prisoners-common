#############################################
#### SHARED MAKEFILE FOR MTP CLIENT APPS ####
#############################################

# mandatory parameters
ifeq ($(app),)
$(error The 'app' parameter is required)
endif
MTP_APP_PATH := mtp_$(subst -,_,$(app))

# default parameters, can be overridden when calling make
api_port ?= 8000
port ?= 8001
browsersync_port ?= 3001
browsersync_ui_port ?= 3031
django_settings ?= $(MTP_APP_PATH).settings
command_script ?= make
verbosity ?= 1

ifeq ($(command_script),run.sh)
override command_script := ./$(command_script)
endif

ifeq ($(shell [ $(verbosity) -gt 1 ] && echo true),true)
TASK_OUTPUT_REDIRECTION := &1
else
TASK_OUTPUT_REDIRECTION := /dev/null
endif

# functions
is_port_open = $(shell nc -z localhost $(1) >$(TASK_OUTPUT_REDIRECTION) 2>&1 && echo true)

# paths of folders, tools and assets
NODE_MODULES := node_modules
NODE_BIN := ./$(NODE_MODULES)/.bin

MTP_COMMON = $(NODE_MODULES)/money-to-prisoners-common
GOVUK_ELEMENTS = $(NODE_MODULES)/mojular-govuk-elements
MOJ_ELEMENTS = $(NODE_MODULES)/mojular-moj-elements

ASSETS_TARGET = $(MTP_APP_PATH)/assets
ASSETS_SOURCE = $(MTP_APP_PATH)/assets-src
TEMPLATES = $(MTP_APP_PATH)/templates

JS_PATH = $(ASSETS_TARGET)/scripts
ALL_JS := $(shell find -L $(ASSETS_SOURCE)/javascripts $(MTP_COMMON)/assets/javascripts -name \*.js)

CSS_PATH = $(ASSETS_TARGET)/stylesheets

SASS_DIRS = $(NODE_MODULES)/breakpoint-sass/stylesheets $(NODE_MODULES)/include-media/dist $(NODE_MODULES)/bourbon/app/assets/stylesheets $(NODE_MODULES)/susy/sass $(ASSETS_SOURCE)/stylesheets $(GOVUK_ELEMENTS)/sass $(MOJ_ELEMENTS)/sass $(MTP_COMMON)/assets/scss $(MTP_COMMON)/assets/scss/elements $(NODE_MODULES)

SASS_FILES := $(shell find -L $(SASS_DIRS) -name \*.scss)

IMAGE_FILES := $(shell find $(MTP_COMMON)/assets/images/* $(GOVUK_ELEMENTS)/images/* $(MTP_APP_PATH)/assets/images/* -type f 2>/dev/null)

SASS_LOAD_PATH := $(patsubst %,--include-path %, $(SASS_DIRS))

WATCHLIST := $(ASSETS_SOURCE) $(MTP_COMMON) $(GOVUK_ELEMENTS) $(MOJ_ELEMENTS) $(TEMPLATES)

SELENIUM := $(NODE_MODULES)/selenium-standalone/.selenium

#################
#### RECIPES ####
#################

# usage instructions
.PHONY: print_usage
print_usage:
	@echo "Usage: $(command_script) [start|watch|serve|update|build|clean|test]"
	@echo " - start [port=<port>]: start the application server on http://localhost:$(port)/"
	@echo " - watch [port=<port>]: start the application server and recompile the assets when they change"
	@echo " - serve [port=<port>]: start the browser-sync server on http://localhost:$(browsersync_port)/"
	@echo "   and recompile the assets when they change"
	@echo " - update: update node and python packages"
	@echo " - build: compile all the assets"
	@echo " - clean: delete compiled assets and node modules"
	@echo " - test [tests=<tests>]: run the python test suite"

# run the django dev server
.PHONY: start
start: build
	@venv/bin/python manage.py runserver 0:$(port)

# run the django dev server and recompile assets on change
.PHONY: watch
watch: build
export
watch:
	@$(MAKE) -f $(MAKEFILE_LIST) --jobs 2 start internal_watch watch_callback=build

# run the django dev server, recompile assets and reload browsers on change
.PHONY: serve
serve: build
export
serve:
	@$(MAKE) -f $(MAKEFILE_LIST) --jobs 3 start internal_browser_sync internal_watch watch_callback=internal_build_and_reload

# set an environment variable if api server is running
.PHONY: api_running
api_running:
ifeq ($(call is_port_open,$(api_port)), true)
export RUN_FUNCTIONAL_TESTS=true
endif

# run python tests
.PHONY: test
test: api_running
ifeq ($(RUN_FUNCTIONAL_TESTS), true)
	@echo Running all tests
else
	@echo Running non-functional tests only
endif
	@venv/bin/python manage.py test --verbosity=$(verbosity) $(tests)

# update python virtual environment
.PHONY: virtual_env
virtual_env: venv/bin/pip
	@echo Updating python packages
	@venv/bin/pip install -r requirements/dev.txt >$(TASK_OUTPUT_REDIRECTION)

# collect django static assets
.PHONY: static_assets
static_assets:
	@echo Collecting static Django assets
	@venv/bin/python manage.py collectstatic --noinput >$(TASK_OUTPUT_REDIRECTION)
	@echo Collecting images
	@rsync -ru --delete $(IMAGE_FILES) $(MTP_APP_PATH)/assets/images

# update node and python packages
.PHONY: update
update: virtual_env
	@echo Updating node modules
	@npm install >$(TASK_OUTPUT_REDIRECTION)  # force update rather than require $(NODE_MODULES) file target

# all the assets
.PHONY: build
build: $(NODE_MODULES) $(JS_PATH)/app.bundle.js $(CSS_PATH)/app.css $(CSS_PATH)/app-print.css virtual_env static_assets

# remove all the assets
.PHONY: clean
clean:
	@rm -rf $(ASSETS_TARGET) $(NODE_MODULES)

##########################
#### INTERNAL RECIPES ####
##########################

# load browser-sync
.PHONY: internal_browser_sync
internal_browser_sync:
	@$(NODE_BIN)/browser-sync start --host=localhost --port=$(browsersync_port) --proxy=localhost:$(port) --no-open --ui-port=$(browsersync_ui_port)

# monitor assets and recompile them when they change
.PHONY: internal_watch
internal_watch:
	@echo Monitoring changes
	@fswatch -l 1 -o $(WATCHLIST) | xargs -n1 -I {} /usr/bin/env bash -c '$(command_script) $(watch_callback)'

# monitor assets, recompile them and reload browsers when they change
.PHONY: internal_build_and_reload
internal_build_and_reload: build
	${NODE_BIN}/browser-sync reload --port=$(browsersync_port)

######################
#### FILE TARGETS ####
######################

$(JS_PATH)/app.bundle.js: $(ALL_JS)
	@echo Generating `basename $@`
	-@$(NODE_BIN)/jshint $<
	@$(NODE_BIN)/webpack >$(TASK_OUTPUT_REDIRECTION)

# Make the various css files (app, app-print) from their respective sources
$(CSS_PATH)/%.css: $(SASS_FILES)
	@echo Generating `basename $@`
	@$(NODE_BIN)/node-sass $(SASS_LOAD_PATH) $(ASSETS_SOURCE)/stylesheets/$*.scss $@ >$(TASK_OUTPUT_REDIRECTION) 2>&1

$(NODE_MODULES):
	@echo Installing node modules
	@npm install >$(TASK_OUTPUT_REDIRECTION)
	@echo "node_modules installed. Don't forget to link to local modules as needed (eg npm link money-to-prisoners-common)"

venv/bin/pip:
	@echo Creating python virtual environment
	@virtualenv -p python3 venv >$(TASK_OUTPUT_REDIRECTION)
	@venv/bin/pip install -U setuptools pip wheel ipython ipdb >$(TASK_OUTPUT_REDIRECTION)

$(SELENIUM):
	@echo Installing selenium binaries
	@$(NODE_BIN)/selenium-standalone install
