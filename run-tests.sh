#!/bin/bash

###############################################################################
# Wrapper script for setting up and running backup_manager tests
#
# name:     run-tests.sh
# author:   Ryan Chapin
#
################################################################################
#
#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  export_env_vars
#   DESCRIPTION:  Will export all of the required environmental varibles to run
#                 the tests
#    PARAMETERS:  None
#       RETURNS:  void
#-------------------------------------------------------------------------------
function export_env_vars {
  set -e

  local override_env_vars=$1
  if [ "$override_env_vars" != "0" ]
  then
    if [ ! -f "$override_env_vars" ]
    then
      printf "ERROR! OVERRIDE_ENV_VARS_PATH, -e argument, pointed to a non-existant file\n\n" >&2
      usage
      #
      # We don't just exit here, because we may be sourcing this script and it would
      # then close the current terminal without giving the user an opportunity to
      # see the error message.  If we were not passed in a path to a valid file for
      # the required env vars, we just fall through and exit without doing anything
      # else.
      #
    fi
    echo "Sourcing required env vars script $OVERRIDE_ENV_VARS_PATH"
    source $OVERRIDE_ENV_VARS_PATH
  fi

  # ------------------------------------------------------------------------------
  # Sane defaults.  Can be overriden by first specifying the variable you want to
  # change as an environmental variable in the calling shell.

  export BACKUPMGRINTTEST_TEST_HOST=${BACKUPMGRINTTEST_TEST_HOST:-localhost}

  # Parent directory for all of the integration test files and directories
  export BACKUPMGRINTTEST_PARENT_DIR=${BACKUPMGRINTTEST_PARENT_DIR:-/var/tmp/backup_manager-integration-test}
  export BACKUPMGRINTTEST_CONFIG_DIR=${BACKUPMGRINTTEST_CONFIG_DIR:-$BACKUPMGRINTTEST_PARENT_DIR/config}
  export BACKUPMGRINTTEST_CONFIG_FILE=${BACKUPMGRINTTEST_CONFIG_FILE:-backup_manager.yaml}
  export BACKUPMGRINTTEST_LOCK_DIR=${BACKUPMGRINTTEST_LOCK_DIR:-$BACKUPMGRINTTEST_PARENT_DIR/lock}
  export BACKUPMGRINTTEST_PID_DIR=${BACKUPMGRINTTEST_PID_DIR:-$BACKUPMGRINTTEST_PARENT_DIR/pid}
  export BACKUPMGRINTTEST_TEST_DATA_DIR=${BACKUPMGRINTTEST_TEST_DATA_DIR:-$BACKUPMGRINTTEST_PARENT_DIR/test_data}
  export BACKUPMGRINTTEST_DOCKER_DIR=${BACKUPMGRINTTEST_DOCKER_DIR:-$BACKUPMGRINTTEST_PARENT_DIR/docker}
  export BACKUPMGRINTTEST_SSH_IDENTITY_FILE=${BACKUPMGRINTTEST_SSH_IDENTITY_FILE:-$BACKUPMGRINTTEST_DOCKER_DIR/id_rsa}
  export BACKUPMGRINTTEST_SSH_IDENTITY_FILE_PUB=${BACKUPMGRINTTEST_SSH_IDENTITY_FILE_PUB:-${BACKUPMGRINTTEST_SSH_IDENTITY_FILE}.pub}
  export BACKUPMGRINTTEST_VIRTENV_DIR=${BACKUPMGRINTTEST_VIRTENV_DIR:-$BACKUPMGRINTTEST_PARENT_DIR/virtenv}
  export BACKUPMGRINTTEST_CONTAINER_NAME=${BACKUPMGRINTTEST_CONTAINER_NAME:-backup_manager_inttest}
  export BACKUPMGRINTTEST_IMAGE_NAME=${BACKUPMGRINTTEST_IMAGE_NAME:-backup_manager_inttest}
  export BACKUPMGRINTTEST_CONTAINER_PORT=${BACKUPMGRINTTEST_CONTAINER_PORT:-22222}

  # For each of the tests, we only want the BackupManager to run one time and
  # not wait for a pre-determined time to run.
  export BACKUPMGRINTTEST_RUNONCE=${BACKUPMGRINTTEST_RUNONCE:-1}

  # It doesn't really matter what this password is. We just need something
  # with which we can ssh/rsync to the container to execute the tests
  export BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD=${BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD:-password123}
  export BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD_FILE=${BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD_FILE:-$BACKUPMGRINTTEST_PARENT_DIR/test-container-root-passwd.txt}

  export BACKUPMGRINTTEST_WHICH_PATH=${BACKUPMGRINTTEST_WHICH_PATH:-/usr/bin/which}

  set +e
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  which_linux_distro
#   DESCRIPTION:  Returns the enum/name of the linux distro on which we are
#                 running the tests
#-------------------------------------------------------------------------------
function which_linux_distro {
  local retval=""

  if [ -f "/etc/debian_version" ]; then
    retval="debian"
  fi
  # TODO add RHEL

  echo $retval
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  install_dependencies
#   DESCRIPTION:  Installs required packages to setup and run the tests.
#-------------------------------------------------------------------------------
function install_dependencies {
  distro=$(which_linux_distro)
  case $distro in

    debian)
      ssh root@localhost apt-get install -y netcat-traditional rsync sshpass
      ;;

    redhat)
      # TODO
      echo "redhat"
      ;;

    *)
      echo -n "unknown"
      ;;

  esac
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  build_docker_test_image
#   DESCRIPTION:  Builds the docker image which we will use to run the tests.
#-------------------------------------------------------------------------------
function build_docker_test_image {
  local start_dir=$(pwd)

  # Generate an ssh key to be added to the docker image when we build it.
  ssh-keygen -q -t rsa -N '' -f $BACKUPMGRINTTEST_SSH_IDENTITY_FILE <<<y 2>&1 >/dev/null

  # Copy the docker file to the "build" dir and build the docker image
  cp backupmanager/integration_tests/docker/Dockerfile $BACKUPMGRINTTEST_DOCKER_DIR
  cd $BACKUPMGRINTTEST_DOCKER_DIR
  docker build --build-arg root_passwd=$BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD -t $BACKUPMGRINTTEST_IMAGE_NAME .

  # Write out the password to a text file
  echo "$BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD" > $BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD_FILE

  cd $start_dir
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  start_docker_container
#   DESCRIPTION:  Start the docker container which we will use to run the tests.
#-------------------------------------------------------------------------------
function start_docker_container {

  # Fire up the docker container
  docker run --rm -d --name $BACKUPMGRINTTEST_CONTAINER_NAME -p ${BACKUPMGRINTTEST_CONTAINER_PORT}:22 $BACKUPMGRINTTEST_IMAGE_NAME

  # Because we are likely going to run this multiple times and idempotency is
  # king, we want to ensure that we do not already have a set of keys for
  # this docker container.
  ssh-keygen -f "/home/rchapin/.ssh/known_hosts" -R "[localhost]:$BACKUPMGRINTTEST_CONTAINER_PORT"

  # ssh to the docker container automatically accepting the host keys
  ssh -p $BACKUPMGRINTTEST_CONTAINER_PORT -i $BACKUPMGRINTTEST_SSH_IDENTITY_FILE -o StrictHostKeyChecking=no root@localhost hostname
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  configure_firewall
#   DESCRIPTION:  Configures the firewall on the test machine if it is already
#                 installed and enabled.  If not, it is a noop.
#-------------------------------------------------------------------------------
function configure_firewall {
  distro=$(which_linux_distro)
  case $distro in

    debian)
      if dpkg --get-selections | grep ufw 2>&1 > /dev/null     
      then
        # Check to see if it is active
        if ! ssh root@localhost ufw status | grep inactive > /dev/null
        then
          echo "Adding ${BACKUPMGRINTTEST_CONTAINER_PORT} to ufw firewall"
          ssh root@localhost ufw allow ${BACKUPMGRINTTEST_CONTAINER_PORT}/tcp
        fi
      fi
      ;;

    redhat)
      echo "redhat"
      ;;

    *)
      echo -n "unknown"
      ;;

  esac
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  create_virtenv
#   DESCRIPTION:  Create the virtual environment and install the application.
#-------------------------------------------------------------------------------
function create_virtenv {
  $(which python3.7) -mvenv $BACKUPMGRINTTEST_VIRTENV_DIR
  source $BACKUPMGRINTTEST_VIRTENV_DIR/bin/activate
  pip install -U setuptools pip coverage
  pip install .
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  setup
#   DESCRIPTION:  Cleans and creates the required test dirs based on the env
#                 vars already defined.
#-------------------------------------------------------------------------------
function setup {
  # First run teardown to remove anything left behind
  teardown

  echo "Setting up test environment"
  # Now create the directory structure needed for the tests.
  dirs=(
    "$BACKUPMGRINTTEST_PARENT_DIR"
    "$BACKUPMGRINTTEST_CONFIG_DIR"
    "$BACKUPMGRINTTEST_DOCKER_DIR"
  ) 
  for dir in "${dirs[@]}"
  do
    mkdir -p $dir
  done

  install_dependencies 
  configure_firewall
  build_docker_test_image
  start_docker_container
  create_virtenv
  echo "Test environment setup complete"
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  teardown
#   DESCRIPTION:  Cleans up the required test dirs based on the env vars already
#                 defined.
#-------------------------------------------------------------------------------
function teardown {
  echo "Tearing down test environment"
  echo "Deleting test dirs"
  rm -rf $BACKUPMGRINTTEST_PARENT_DIR

  # It is possible that there is no container or images in existence, but we
  # will stop any running container and delete the image to ensure a clean
  # slate.
  echo "Stopping docker container and deleting test image"
  set +e
  docker stop $BACKUPMGRINTTEST_CONTAINER_NAME 2> /dev/null
  docker rmi $BACKUPMGRINTTEST_IMAGE_NAME 2> /dev/null
  set -e

  echo "Test environment clean-up complete" 
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  run_tests
#   DESCRIPTION:  Runs both the unit and integration tests.
#    PARAMETERS:  None
#       RETURNS:  void
#-------------------------------------------------------------------------------

function run_tests {
  set -e
  source $BACKUPMGRINTTEST_VIRTENV_DIR/bin/activate

  # Run the unit tests
  echo "======================================================================="
  echo "Running the unit tests"
  coverage run -m unittest discover -s backupmanager/tests # add -k $test_name 

  if [ "$OMIT_INTEGRATION_TESTS" -ne 1 ]
  then
    echo "======================================================================="
    echo "Running the integration tests"
    coverage run --append -m unittest discover -s backupmanager/integration_tests --failfast # add -k $test_name
  fi

  coverage report backupmanager/*.py
  set +e
}

################################################################################
# USAGE:

function usage {
   cat << EOF
Usage: run-tests.sh [OPTIONS]

Options:

  -e OVERRIDE_ENV_VARS_PATH
     Path to the file that contains the any overriding env vars.

  -i OMIT_INTEGRATION_TESTS
     Ommit running the integration tests and just run the unit tests.

  -l LEAVE
     Do not clean any existing environment previously setup.  By default the
     environment is cleaned and re-installed with each invocation of this
     script.

  -t TEARDOWN
     Teardown the test environment on the configured test host

  --setup-only Only run the setup without running the tests.

  --export-env-vars-only
    Only export the require environmental variables for the test, overriding
    the defaults with those env vars defined in the -e file, but do not run the
    test.  To achieve this goal, you must source this script instead of running
    it as an executable script.

    Example:

    $ source ./run-tests.sh -e /path/to/required-env-vars.sh --export-env-vars-only

    Alternatively, you can omit the -e arg to use the defaults.

  -h HELP
     Outputs this basic usage information.
EOF
}

################################################################################
#
# Here we define variables to store the input from the command line arguments as
# well as define the default values.
#
HELP=0
LEAVE=0
TEARDOWN=0
TEARDOWN_ONLY=0
SETUP_ONLY=0
EXPORT_ENV_VARS_ONLY=0
OVERRIDE_ENV_VARS_PATH=0
OMIT_INTEGRATION_TESTS=0

PARSED_OPTIONS=`getopt -o hltie: -l export-env-vars-only,setup-only,teardown-only -- "$@"`

# Check to see if the getopts command failed
if [ $? -ne 0 ];
then
   echo "Failed to parse arguments"
   exit 1
fi

eval set -- "$PARSED_OPTIONS"

# Loop through all of the options with a case statement
while true; do
   case "$1" in
      -h)
         HELP=1
         shift
         ;;

      -e)
         OVERRIDE_ENV_VARS_PATH=$2
         shift 2
         ;;

      -i)
         OMIT_INTEGRATION_TESTS=1
         shift
         ;;

      -l)
         LEAVE=1
         shift
         ;;

      -t)
         TEARDOWN=1
         shift
         ;;


      --export-env-vars-only)
         EXPORT_ENV_VARS_ONLY=1
         shift
         ;;

      --setup-only)
         SETUP_ONLY=1
         shift
         ;;

      --teardown-only)
         TEARDOWN_ONLY=1
         shift
         ;;


      --)
         shift
         break
         ;;
   esac
done

if [ "$HELP" -eq 1 ];
then
   usage
   exit
fi

################################################################################

export_env_vars $OVERRIDE_ENV_VARS_PATH
run_script_dir=$(cd $(dirname $0) && pwd)

if [ "$EXPORT_ENV_VARS_ONLY" -eq 1 ]
then
  #
  # Check to make sure that the user actually sourced this script otherwise we
  # can give them a warning so that they won't be confused when they do not
  # see any of the expected env vars.
  #
  current_dirname=`dirname "$0"`
  if [[ "$current_dirname" != *"/bin"* ]]
  then
    cat << EOF

!!!!! WARNING !!!!!
You are trying to just export the env vars, however, it seems as though you did not source this script, but were attempting to execute it.
EOF
    usage
  fi

else
  #
  # If we are to do more than export env vars, continue processing
  #
  if [ "$TEARDOWN_ONLY" -eq 1 ]
  then
    teardown
    exit
  fi

  if [ "$SETUP_ONLY" -eq 1 ]
  then
    setup
    exit
  fi

  if [ "$LEAVE" -eq 0 ]
  then
    # We are to run setup which will clean any existing test environment
    setup
  fi

  time run_tests

  if [ "$TEARDOWN" -eq 1 ]
  then
    #
    # We should teardown the test setup environment
    #
    teardown
  fi
fi

