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
webdriver ?= phantomjs
accessibility_tests ?= false
django_settings ?= $(MTP_APP_PATH).settings
python_requirements ?= requirements/dev.txt
verbosity ?= 1

GOVUK_TEMPLATE_VERSION=0.17.3
GOVUK_TEMPLATE_TGZ = https://github.com/alphagov/govuk_template/releases/download/v${GOVUK_TEMPLATE_VERSION}/django_govuk_template-$(GOVUK_TEMPLATE_VERSION).tgz

ifeq ($(shell [ $(verbosity) -gt 1 ] && echo true),true)
TASK_OUTPUT_REDIRECTION := &1
PYTHON_WARNINGS := "-W default"
else ifeq ($(shell [ $(verbosity) -eq 0 ] && echo true),true)
TASK_OUTPUT_REDIRECTION := /dev/null
PYTHON_WARNINGS := "-W ignore"
else
TASK_OUTPUT_REDIRECTION := /dev/null
PYTHON_WARNINGS := "-W once"
endif

# functions
is_port_open = $(shell nc -z $(1) $(2) >/dev/null 2>&1 && echo true)

# paths of folders, tools and assets
NODE_MODULES := node_modules
NODE_BIN := ./$(NODE_MODULES)/.bin

VIRTUAL_ENV_DIR=venv
MTP_COMMON_PY = $(PYTHON_LIBS)/mtp_common
MTP_COMMON = $(NODE_MODULES)/money-to-prisoners-common
GOVUK_ELEMENTS_SASS = $(NODE_MODULES)/govuk-elements-sass/public/sass
GOVUK_FRONTEND_TOOLKIT = $(NODE_MODULES)/govuk_frontend_toolkit
GOVUK_FRONTEND_TOOLKIT_SASS = $(GOVUK_FRONTEND_TOOLKIT)/stylesheets

ASSETS_TARGET = $(MTP_APP_PATH)/assets
ASSETS_SOURCE = $(MTP_APP_PATH)/assets-src
TEMPLATES = $(MTP_APP_PATH)/templates

JS_PATH = $(ASSETS_TARGET)/javascripts
ALL_JS := $(shell find -L $(ASSETS_SOURCE)/javascripts $(MTP_COMMON)/assets/javascripts -name \*.js 2> /dev/null)

CSS_PATH = $(ASSETS_TARGET)/stylesheets

SASS_DIRS = $(NODE_MODULES)/breakpoint-sass/stylesheets $(NODE_MODULES)/include-media/dist $(NODE_MODULES)/bourbon/app/assets/stylesheets $(NODE_MODULES)/susy/sass $(ASSETS_SOURCE)/stylesheets $(MTP_COMMON)/assets/scss $(NODE_MODULES) $(GOVUK_ELEMENTS_SASS) $(GOVUK_FRONTEND_TOOLKIT_SASS)

SASS_FILES := $(shell find -L $(SASS_DIRS) -name \*.scss 2>/dev/null)

IMAGE_PATH = $(ASSETS_TARGET)/images

IMAGE_FILES := $(shell find $(GOVUK_FRONTEND_TOOLKIT)/images $(MTP_APP_PATH)/assets-src/static/images -type f 2>/dev/null)

SASS_LOAD_PATH := $(patsubst %,--include-path %, $(SASS_DIRS))

WATCHLIST := $(ASSETS_SOURCE) $(MTP_COMMON_PY)/assets $(MTP_COMMON_PY)/static $(MTP_COMMON_PY)/templates $(GOVUK_ELEMENTS_SASS) $(MOJ_ELEMENTS) $(TEMPLATES)

SELENIUM := $(NODE_MODULES)/selenium-standalone/.selenium

#################
#### RECIPES ####
#################

# usage instructions
.PHONY: help
help:
	@echo "Usage: make [start|watch|serve|docker|update|build|clean|test]"
	@echo " - start [port=<port>]: start the application server on http://localhost:$(port)/"
	@echo " - watch [port=<port>]: start the application server and recompile the assets when they change"
	@echo " - serve [port=<port>]: start the browser-sync server on http://localhost:$(browsersync_port)/"
	@echo "   and recompile the assets when they change"
	@echo " - docker: build and run using Docker locally"
	@echo " - update: update node and python packages"
	@echo " - build: compile all the assets"
	@echo " - clean: delete compiled assets and node modules"
	@echo " - test [tests=<tests>]: run the python test suite"
	@echo "        [webdriver=<phantomjs|firefox|chrome>] can be added to run functional tests in a specific driver"
	@echo "        [accessibility_tests=true] can be added to run accessibility tests"
	@echo ""
	@echo "[verbosity=<0|1|2|3>] can be added to any task"

# run the django dev server
.PHONY: start
start: build
	@$(VIRTUAL_ENV_DIR)/bin/python $(PYTHON_WARNINGS) manage.py runserver 0:$(port) --verbosity=$(verbosity)

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

# build and run using docker locally
.PHONY: docker
docker: .host_machine_ip
	@docker-compose build
	@echo "Starting MTP $(app) in Docker on http://$(HOST_MACHINE_IP):$(port)/ in test mode"
	@docker-compose up

# run uwsgi, this is the entry point for docker running remotely
uwsgi: $(VIRTUAL_ENV_DIR)/bin/uwsgi collect_static_assets
	@echo "Starting MTP $(app) in uWSGI"
	@$(VIRTUAL_ENV_DIR)/bin/uwsgi --ini conf/uwsgi/$(subst -,_,$(app)).ini

# run python tests
.PHONY: test
test: $(SELENIUM) .api_running virtual_env assets
ifdef RUN_FUNCTIONAL_TESTS
	@echo Running all tests
else
	@echo Running non-functional tests only
endif
	@$(VIRTUAL_ENV_DIR)/bin/python $(PYTHON_WARNINGS) manage.py test --verbosity=$(verbosity) $(tests)

# update python virtual environment
.PHONY: virtual_env
virtual_env: $(VIRTUAL_ENV_DIR)/bin/pip3
	@echo Updating python packages
	@$(VIRTUAL_ENV_DIR)/bin/pip3 install -U setuptools pip wheel ipython ipdb >$(TASK_OUTPUT_REDIRECTION)
	@$(VIRTUAL_ENV_DIR)/bin/pip3 install -r $(python_requirements) >$(TASK_OUTPUT_REDIRECTION)

# migrate the db
# NB: client apps do not have databases
.PHONY: migrate_db
migrate_db: $(VIRTUAL_ENV_DIR)/bin/python
	@$(VIRTUAL_ENV_DIR)/bin/python manage.py migrate --verbosity=$(verbosity) --noinput >$(TASK_OUTPUT_REDIRECTION)

.PHONY: generate_screenshots
generate_screenshots:
	@echo Generating screenshots
	@mkdir -p $(IMAGE_PATH)/screenshots
	@$(VIRTUAL_ENV_DIR)/bin/python manage.py takescreenshots

.PHONY: retrieve_govuk_templates
retrieve_govuk_templates:
	@echo Retrieving GOV.UK stylesheets
	@curl -Ls $(GOVUK_TEMPLATE_TGZ) | tar xzf - ./govuk_template && \
	  cp -r govuk_template/static/* $(ASSETS_TARGET) && \
	  mkdir -p $(ASSETS_TARGET)/templates && \
	  cp -r govuk_template/templates/govuk_template $(ASSETS_TARGET)/templates && \
	  rm -rf govuk_template

# collect static images and templates
.PHONY: collect_static_assets
collect_static_assets:
	@echo Collecting static assets
	@echo Copying images
	@rsync -ru --delete $(IMAGE_FILES) $(MTP_APP_PATH)/assets/images >$(TASK_OUTPUT_REDIRECTION)
	@$(VIRTUAL_ENV_DIR)/bin/python manage.py collectstatic --verbosity=$(verbosity) --noinput >$(TASK_OUTPUT_REDIRECTION)

# compile translation messages
.PHONY: makemessages
makemessages:
	@echo Compiling translation strings
	@cd $(MTP_APP_PATH) && ../$(VIRTUAL_ENV_DIR)/bin/python ../manage.py compilemessages --verbosity=$(verbosity) >$(TASK_OUTPUT_REDIRECTION)

# update node and python packages
.PHONY: update
update: virtual_env
	@echo Updating node modules
	@npm set progress=false
	@npm install >$(TASK_OUTPUT_REDIRECTION)  # force update rather than require $(NODE_MODULES) file target

# all the assets
.PHONY: build
build: virtual_env assets retrieve_govuk_templates generate_screenshots collect_static_assets makemessages

.PHONY: assets
assets: $(JS_PATH)/app.bundle.js $(CSS_PATH)/app.css $(CSS_PATH)/app-ie6.css $(CSS_PATH)/app-ie7.css $(CSS_PATH)/app-ie8.css $(CSS_PATH)/app-print.css

# remove all the assets
.PHONY: clean
clean:
	@rm -r $(VIRTUAL_ENV_DIR) $(NODE_MODULES) static $(ASSETS_TARGET)

##########################
#### INTERNAL RECIPES ####
##########################

# load browser-sync
.PHONY: internal_browser_sync
internal_browser_sync: assets
	@$(NODE_BIN)/browser-sync start --host=localhost --port=$(browsersync_port) --proxy=localhost:$(port) --no-open --ui-port=$(browsersync_ui_port)

# monitor assets and recompile them when they change
.PHONY: internal_watch
internal_watch:
	@echo Monitoring changes
	@fswatch -l 1 -o $(WATCHLIST) | xargs -n1 -I {} $(MAKE) -f $(MAKEFILE_LIST) $(watch_callback)

# monitor assets, recompile them and reload browsers when they change
.PHONY: internal_build_and_reload
internal_build_and_reload: assets
	@$(NODE_BIN)/browser-sync reload --port=$(browsersync_port)

# set an environment variable if api server is running
.PHONY: .api_running
.api_running:
ifeq ($(call is_port_open,localhost,$(api_port)),true)
export RUN_FUNCTIONAL_TESTS=true
export WEBDRIVER=$(webdriver)
ifeq ($(accessibility_tests),true)
export RUN_ACCESSIBILITY_TESTS=true
endif
endif

# determine host machine ip, could be running via docker machine
.PHONY: .host_machine_ip
.host_machine_ip: .docker_machine
HOST_MACHINE_IP := $(strip $(shell docker-machine ip default 2>/dev/null))
ifeq ($(HOST_MACHINE_IP),)
HOST_MACHINE_IP := localhost
else
ifneq ($(call is_port_open,$(HOST_MACHINE_IP),$(api_port)), true)
HOST_MACHINE_IP := localhost
endif
endif
export HOST_MACHINE_IP

# connect to docker-machine if necessary
.PHONY: .docker_machine
.docker_machine:
ifneq ($(strip $(shell which docker-machine)),)
	@[ `docker-machine status default` = "Running" ] && echo 'Machine "default" is already running.' || docker-machine start default
	$(eval DOCKER_MACHINE_ENV := $(shell docker-machine env default))
	$(eval export DOCKER_MACHINE_NAME := $(shell echo '$(DOCKER_MACHINE_ENV)' | sed 's/.*DOCKER_MACHINE_NAME="\([^"]*\)".*/\1/'))
	$(eval export DOCKER_HOST := $(shell echo '$(DOCKER_MACHINE_ENV)' | sed 's/.*DOCKER_HOST="\([^"]*\)".*/\1/'))
	$(eval export DOCKER_CERT_PATH := $(shell echo '$(DOCKER_MACHINE_ENV)' | sed 's/.*DOCKER_CERT_PATH="\([^"]*\)".*/\1/'))
	$(eval export DOCKER_TLS_VERIFY := $(shell echo '$(DOCKER_MACHINE_ENV)' | sed 's/.*DOCKER_TLS_VERIFY="\([^"]*\)".*/\1/'))
endif

######################
#### FILE TARGETS ####
######################

OS = $(shell uname)
ifeq ($(OS),Darwin)
  alert = osascript -e 'display notification "$@" with title "Error compiling asset"'
else
  alert = echo Error compiling asset $@
endif

$(JS_PATH)/app.bundle.js: $(ALL_JS)
	@echo Generating `basename $@` $(UNAME)
	$(NODE_BIN)/jshint -c $(MTP_COMMON_PY)/.jshintrc $(ALL_JS) || $(call alert)
	$(NODE_BIN)/webpack --bail >$(TASK_OUTPUT_REDIRECTION) || $(call alert)

# Make the various css files (app, app-print) from their respective sources
$(CSS_PATH)/%.css: $(SASS_FILES)
	@echo Generating `basename $@`
	@$(NODE_BIN)/node-sass $(SASS_LOAD_PATH) $(ASSETS_SOURCE)/stylesheets/$*.scss $@ >$(TASK_OUTPUT_REDIRECTION) 2>&1 || $(call alert)

$(VIRTUAL_ENV_DIR)/bin/python, $(VIRTUAL_ENV_DIR)/bin/pip3:
	@echo Creating python virtual environment
	@virtualenv -p python3 $(VIRTUAL_ENV_DIR) >$(TASK_OUTPUT_REDIRECTION)

$(VIRTUAL_ENV_DIR)/bin/uwsgi: $(VIRTUAL_ENV_DIR)/bin/pip3
	@$(VIRTUAL_ENV_DIR)/bin/pip3 install uWSGI

$(SELENIUM):
	@echo Installing selenium binaries
	@$(NODE_BIN)/selenium-standalone install
