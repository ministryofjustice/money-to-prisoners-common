#!/usr/bin/env bash

# This script runs the application in various ways depending on the params
# passed.

NODE_MODULES=./node_modules
NODE_BIN=${NODE_MODULES}/.bin

print_usage() {
  TASKS_COMMAND=`basename $0`
  echo "Usage: ${TASKS_COMMAND} [start|watch|serve|clean|build] <args>"
  echo " - start <port>: start the application server on http://localhost:${DEFAULT_PORT}/ or <port>"
  echo " - watch <port>: start the application server and recompile the assets when they change"
  echo " - serve <port>: start the browser-sync server and recompile the assets when they change"
  echo " - build: compile all the assets"
  echo " - clean: delete compiled assets and node modules"
  echo " - test: run the test suite"
}

make_venv() {
  [ -f venv/bin/activate ] || {
    virtualenv venv > /dev/null
  }
}

activate_venv() {
  . venv/bin/activate
}

update_venv() {
  make_venv
  activate_venv
  pip install -U setuptools pip wheel ipython ipdb > /dev/null
  pip install -r requirements/dev.txt > /dev/null
}

choose_django_settings() {
  [ -z ${DJANGO_SETTINGS_MODULE} ] && {
    DJANGO_SETTINGS_MODULE=${DEFAULT_DJANGO_SETTINGS_MODULE}
  }
}

choose_ports() {
  PORT=$1
  [ -z ${PORT} ] && {
    PORT=${DEFAULT_PORT}
  }
  [ -z ${BROWSERSYNC_PORT} ] && {
    BROWSERSYNC_PORT=${DEFAULT_BROWSERSYNC_PORT}
  }
  [ -z ${BROWSERSYNC_UI_PORT} ] && {
    BROWSERSYNC_UI_PORT=${DEFAULT_BROWSERSYNC_UI_PORT}
  }
}

is_port_open() {
  nc -z localhost $1-$1 > /dev/null 2>&1
}

make_command() {
  MAKE_TASK=$1
  shift
  make -f ${SHARED_MAKEFILE} ${MAKE_TASK} app=${APP} $@
}

manage_command() {
  ./manage.py $@
}

clean_up() {
  # kill all processes spawned by this script in the
  # background when it stops, in particular django
  # restarts
  echo "Killing all spawned processes."
  kill `ps -o pgid= ${SERVER_PID} | grep -o "[ 0-9]*"`
}

start() {
  # Activate and run the django application
  echo "Starting Django dev server"
  update_venv
  choose_django_settings
  manage_command collectstatic --noinput > /dev/null
  build
  manage_command runserver 0:${PORT}
}

watch() {
  # Activate and run the django application, building
  # assets when a change is detected
  trap clean_up INT
  start & SERVER_PID=$!
  make_command watch watch_callback=build
}

serve() {
  # Activate and run the django application, building
  # assets and reloading browsers when a change is detected
  trap clean_up INT
  start & SERVER_PID=$!
  echo "Starting Browser-Sync"
  ${NODE_BIN}/browser-sync start --host=localhost --port=${BROWSERSYNC_PORT} --proxy=localhost:${PORT} --no-open --ui-port=${BROWSERSYNC_UI_PORT} &
  make_command watch watch_callback=build_and_reload__${BROWSERSYNC_PORT}
}

tests() {
  update_venv
  choose_django_settings
  echo "Running the test suite"
  is_port_open 8000 && {
    export RUN_FUNCTIONAL_TESTS=1
  } || {
    unset RUN_FUNCTIONAL_TESTS
  }
  manage_command test $@
}

build() {
  echo "Building..."
  make_command build $@
}

clean() {
  echo "Cleaning..."
  make_command clean $@
}

main() {
  load_defaults

  ACTION=$1
  shift

  case ${ACTION} in
    start)
      # just run normally
      choose_ports $1
      start
      ;;
    watch)
      # run normally but monitor assets and recompile
      # them when they change
      choose_ports $1
      watch
      ;;
    serve)
      # as above but also run browser-sync for dynamic
      # browser reload
      choose_ports $1
      serve
      ;;
    test)
      # run python-based tests
      tests $@
      ;;
    build)
      # compile static assets
      build $@
      ;;
    build_and_reload__*)
      # called internally to also reload browser-sync
      build $@
      ${NODE_BIN}/browser-sync reload --port=${ACTION:18}
      ;;
    clean)
      # delete compiled assets
      clean $@
      ;;
    *)
      print_usage
      exit 1
      ;;
  esac
  exit 0
}
