#!/bin/bash

# Build the docker image

mkdir -p /var/tmp/backup_manager_inttest
mkdir -p /var/tmp/backup_manager_inttest/ssh-keys
ssh-keygen -q -t rsa -N '' -f /var/tmp/backup_manager_inttest/ssh-keys/id_rsa <<<y 2>&1 >/dev/null



#!/usr/bin/env bash

RUN_UNIT_TESTS=0
RUN_INTEGRATION_TESTS=0
NO_VENV=0
TEST_NAMES=""

while (( "$#" )); do
    case "$1" in
        --unit-test|-u)
            RUN_UNIT_TESTS=1
            shift 1
            ;;
        --integration-test|-i)
            RUN_INTEGRATION_TESTS=1
            shift 1
            ;;
        --test-names|-k)
            TEST_NAMES="-k $2"
            shift 2
            ;;
        --no-venv|-n)
            NO_VENV=1
            shift 1
            ;;
        *)
            echo "Unexpected option: $1"
            exit 1
            ;;
    esac
done

# Default to running all tests if none are specified
if [[ $RUN_UNIT_TESTS == 0 && $RUN_INTEGRATION_TESTS == 0 ]]; then
    RUN_UNIT_TESTS=1
    RUN_INTEGRATION_TESTS=1
fi

#########################################################################
# This script is used to setup and run the application integration tests.
# Just run it and it will tell you if you are missing something
#########################################################################

if [[ -z $DEVPI_INDEX_URL ]]; then
    DEVPI_INDEX_URL=http://devpi.tools.quasar.nadops.net/root/release
    export DEVPI_INDEX_URL=$DEVPI_INDEX_URL
    read -r -d '' USAGE <<EOM
=================================================================
DEVPI_INDEX_URL is defaulting the the following URL:

$DEVPI_INDEX_URL

If you want to use a different DevPI index the you must export
DEVPI_INDEX_URL and point it to the index you want to
use to pull down packages for this test. During development, the
right choice is usually:

export DEVPI_INDEX_URL=http://devpi.tools.quasar.nadops.net/$USER/dev
=================================================================
EOM
    echo "$USAGE"
fi

set -e
set -u

function trace() {
  echo "==================================================="
  echo "$1"
  echo "==================================================="
}

APP_NAME=unzipper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR=/tmp/$USER/virtualenv/${APP_NAME}_integration_test

# You can skip creating a new virtual env if you want to just run in an existing one.
# If you use this option, it is up to you to ensure the virtual env is setup right
if [[ $NO_VENV == 0 ]]; then
  # Create and activate a clean new virtual environment to run the test
  trace "Recreating test virtual environment, $TEST_DIR"
  rm -rf $TEST_DIR
  $(which python3.8) -m venv --clear $TEST_DIR
  source $TEST_DIR/bin/activate
  pip install --index $DEVPI_INDEX_URL -U setuptools pip wheel coverage

  # Install the prerequisite dependencies needed to run the test. The test
  # itself might install additional packages, as needed. These are only
  # the packages needed by the integration test code itself.

  trace "Installing application and dependencies into test virtual environment"
  (cd $SCRIPT_DIR && pip install --disable-pip-version-check --index $DEVPI_INDEX_URL .)
fi

APPEND=""

if [[ $RUN_UNIT_TESTS == 1 ]]; then
  # Run the unit tests first
  APPEND="--append"
  trace "Running unit tests"
  (cd $SCRIPT_DIR && coverage run -m unittest discover -s ${APP_NAME}/tests $TEST_NAMES)
fi

if [[ $RUN_INTEGRATION_TESTS == 1 ]]; then
  # Install application and run the integration test
  (cd $SCRIPT_DIR && coverage run ${APPEND} -m unittest discover --failfast --pattern integration_test.py $TEST_NAMES)
fi

coverage report ${APP_NAME}/*.py
~                                   
