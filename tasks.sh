#!/usr/bin/env bash

# This script runs the application in various ways depending on the params
# passed. It's normally run from the makefile

APP_PATH=./$1
APP_PORT=$2
shift
shift

IMAGES_SRC_DIR=./assets/images
IMAGES_DST_DIR=../../${APP_PATH}/assets/images

NODE_MODULES=./node_modules
NODE_BIN=${NODE_MODULES}/.bin

# kill all processes spawned by this script in the
# background when it stops, in particular django
# restarts
function clean_up {
  echo "Killing all spawned processes."
  kill -- -$(ps -o pgid= $PID | grep -o "[ 0-9]*")
}

# Activate and run the django application
function start {
  source venv/bin/activate > /dev/null
  pip install -r requirements/dev.txt > /dev/null
  ./manage.py runserver 0.0.0.0:${APP_PORT}
}

case "$1" in
  start)
    # just run normally
    start
    ;;
  watch)
    # run normally but monitor assets and recompile
    # them when they change
    trap clean_up INT
    start & PID=$!
    shift
    fswatch -o $@ | xargs  -n1 -I{} sh -c 'echo "---- Change detected ----"; ./run.sh build'
    ;;
  serve)
    # as above but also run browser-sync for dynamic
    # browser reload
    trap clean_up INT
    echo Starting Django dev server
    start & PID=$!
    echo Starting Browser-Sync
    ${NODE_BIN}/browser-sync start --host=localhost --port=3000 --proxy=localhost:${APP_PORT} --no-open --ui-port=3001 &
    shift
    echo "Watching changes"
    fswatch -o $@ | xargs -n1 -I{} sh -c 'echo "---- Change detected ----"; ./run.sh build; ${NODE_BIN}/browser-sync reload'
    ;;
  test*)
    RUN_FUNCTIONAL_TESTS=1 ./manage.py test
    ;;
  *)
    echo "Usage: $0 [start|watch|serve|test-headless] <args>"
    echo " - $0 start: just start the application server"
    echo " - $0 watch <list of asset directories to monitor>: start the "
    echo "   application server and recompile the assets if they are changed"
    echo " - $0 serve <list of asset directories to monitor>: start the "
    echo "   browser-sync server and recompile the assets if they are changed"
    echo " - $0 test: run the test suite"
    exit 1
esac
