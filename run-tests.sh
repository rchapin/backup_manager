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
  export BACKUPMGRINTTEST_SSH_DIR=${BACKUPMGRINTTEST_SSH_DIR:-$BACKUPMGRINTTEST_PARENT_DIR/ssh}
  export BACKUPMGRINTTEST_SSH_IDENTITY_FILE=${BACKUPMGRINTTEST_SSH_IDENTITY_FILE:-$BACKUPMGRINTTEST_SSH_DIR/id_rsa}
  export BACKUPMGRINTTEST_SSH_IDENTITY_FILE_PUB=${BACKUPMGRINTTEST_SSH_IDENTITY_FILE_PUB:-${BACKUPMGRINTTEST_SSH_IDENTITY_FILE}.pub}
  export BACKUPMGRINTTEST_VIRTENV_DIR=${BACKUPMGRINTTEST_VIRTENV_DIR:-$BACKUPMGRINTTEST_PARENT_DIR/virtenv}
  export BACKUPMGRINTTEST_CONTAINER_NAME=${BACKUPMGRINTTEST_CONTAINER_NAME:-backup_manager_inttest}
  export BACKUPMGRINTTEST_IMAGE_NAME=${BACKUPMGRINTTEST_IMAGE_NAME:-backup_manager_inttest}
  export BACKUPMGRINTTEST_CONTAINER_PORT=${BACKUPMGRINTTEST_CONTAINER_PORT:-22222}

  # It doesn't really matter what this password is. We just need something
  # with which we can ssh/rsync to the container to execute the tests
  export BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD=${BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD:-password123}
  export BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD_FILE=${BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD_FILE:-$BACKUPMGRINTTEST_CONFIG_DIR/test-container-root-passwd.txt}

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
      ssh root@localhost apt-get install -y sshpass
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
#          NAME:  setup
#   DESCRIPTION:  Cleans and creates the required test dirs based on the env
#                 vars already defined.
#-------------------------------------------------------------------------------
function setup {
  # First run teardown to remove anything left behind
  teardown
  install_dependencies 
  configure_firewall

  # Now create the directory structure needed for the tests.
  dirs=(
    "$BACKUPMGRINTTEST_PARENT_DIR"
    "$BACKUPMGRINTTEST_CONFIG_DIR"
    "$BACKUPMGRINTTEST_SSH_DIR"
  ) 
  for dir in "${dirs[@]}"
  do
    mkdir -p $dir
  done

  # Create the virtual environment and install the application
  $(which python3.7) -mvenv $BACKUPMGRINTTEST_VIRTENV_DIR
  source $BACKUPMGRINTTEST_VIRTENV_DIR/bin/activate
  pip install -U setuptools pip
  pip install .

  start_dir=$(pwd)
  # Build the docker image
  cd backupmanager/lib/integration_tests/docker/
  docker build --build-arg root_passwd=$BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD -t $BACKUPMGRINTTEST_IMAGE_NAME .

  # Fire up the docker container
  docker run --rm -d --name $BACKUPMGRINTTEST_CONTAINER_NAME -p ${BACKUPMGRINTTEST_CONTAINER_PORT}:22 $BACKUPMGRINTTEST_IMAGE_NAME
  cd $start_dir

  # Set the correct permissions for the ssh dir
  chmod 700 $BACKUPMGRINTTEST_SSH_DIR

  # Generate an ssh key to be added to the coand add it to the docker container
  ssh-keygen -q -t rsa -N '' -f $BACKUPMGRINTTEST_SSH_IDENTITY_FILE <<<y 2>&1 >/dev/null
  chmod 600 $BACKUPMGRINTTEST_SSH_DIR/*

  # Because we are likely going to run this multiple times and idempotency is
  # king, we want to ensure that we do not already have a set of keys for
  # this docker container.
  ssh-keygen -f "/home/rchapin/.ssh/known_hosts" -R "[localhost]:$BACKUPMGRINTTEST_CONTAINER_PORT"

  # Generate a file that contains the root password for the docker container so
  # that we can use sshpass to non-interactively ssh to the docker container to
  # install our ssh key.
  echo "$BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD" > $BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD_FILE
  sshpass -f $BACKUPMGRINTTEST_CONTAINER_ROOT_PASSWD_FILE ssh-copy-id -i $BACKUPMGRINTTEST_SSH_IDENTITY_FILE_PUB -p $BACKUPMGRINTTEST_CONTAINER_PORT -o StrictHostKeyChecking=no root@localhost

  # ssh to the docker container automatically accepting the host keys
  ssh -p $BACKUPMGRINTTEST_CONTAINER_PORT -i $BACKUPMGRINTTEST_SSH_IDENTITY_FILE -o StrictHostKeyChecking=no root@localhost hostname

  # Copy the log4.properties and logging.properties files into the config dir so
  # that we can provide the paths to them in the command to start the JVM.
  #
  # Figure out the path to the resources dir
  # resources_dir=$(dirname $0)
  # resources_dir=$(cd $resources_dir && pwd)
  # cp $resources_dir/$BACKUPMGRINTTEST_LOG4JFILE $BACKUPMGRINTTEST_LOG4JPATH

  # Substitute specific vars in the logging.properties file and write it to the
  # specified test location
  # envsubst '${BACKUPMGRINTTEST_LOG_DIR}' <${resources_dir}/$BACKUPMGRINTTEST_LOGGING_PROPERTIES_FILE > $BACKUPMGRINTTEST_LOGGING_PROPERTIES_PATH
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  teardown
#   DESCRIPTION:  Cleans up the required test dirs based on the env vars already
#                 defined.
#-------------------------------------------------------------------------------
function teardown {
  rm -rf $BACKUPMGRINTTEST_PARENT_DIR

  # It is possible that there is no container or images in existence, but we
  # we will stop any running container and delete the image
  set +e
  docker stop $BACKUPMGRINTTEST_CONTAINER_NAME 2> /dev/null
  docker rmi $BACKUPMGRINTTEST_IMAGE_NAME 2> /dev/null
  set -e

  echo "Test dirs and docker clean-up complete" 
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  run_tests
#   DESCRIPTION:  Runs both the unit and integration tests.
#    PARAMETERS:  None
#       RETURNS:  void
#-------------------------------------------------------------------------------

function run_tests {
  set -e
  #
  # Run the unit tests
  # 
#   CMD="mvn"
# 
#   if [ "$UNIT_TEST_TO_RUN" != 0 ]
#   then
#     CMD="$CMD -Dtest=$UNIT_TEST_TO_RUN"
#   fi
# 
#   CMD="$CMD test -P dev"
#   echo "CMD = $CMD"
#   eval $CMD
#   if [ "$?" != 0 ]
#   then
#     echo "Unit tests failed" >&2
#     exit 1
#   fi
# 
#   #
#   # Run the integration tests
#   #
#   CMD=""
# 
#   if [ "$DEBUG" == 1 ]
#   then
#     CMD="mvnDebug -DforkCount=0"
#   else
#     CMD="mvn"
#   fi
# 
#   if [ "$INTEGRATION_TEST_TO_RUN" != 0 ]
#   then
#     CMD="$CMD -Dit.test=$INTEGRATION_TEST_TO_RUN"
#   fi
# 
#   CMD=$(cat << EOF
# $CMD verify -P integration-test
# -Dlog4j.configurationFile="file:$BACKUPMGRINTTEST_LOG4JPATH"
# -Djava.util.logging.config.file=$BACKUPMGRINTTEST_LOGGING_PROPERTIES_PATH
# -Dlog.file.path=$BACKUPMGRINTTEST_LOG_DIR
# EOF
# )
# 
#   eval $CMD
  set +e
}

################################################################################
# USAGE:

function usage {
   cat << EOF
Usage: run-tests.sh [OPTIONS]

Options:

  -e OVERRIDE_ENV_VARS_PATH
       path to the file that contains the any overriding env vars.

  -i INTEGRATION_TEST_TO_RUN
       Specific integration test to run, must be specify class and test in quoted
       argument as follows:
         "MyIntegrationTestClass#testName"

       You can also run all of the test methods in a given class by passing in
       a pattern that matches everything, or a subset of the tests.  The
       following will run ALL of the anotated test methods in the class:
         "MyIntegrationTestClass#*"

       The following will only run the test cases with the string "Fails" in
       the name of the method:
         "MyIntegrationTestClass#*Fails*"

  -u UNIT_TEST_TO_RUN
       Specific unit test to run, must be specify class and test in quoted
       argument as follows:
         "MyUnitTestClass#testName"

  -l LEAVE
       do not clean any existing environment previously setup.  By default the
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
SETUP_ONLY=0
EXPORT_ENV_VARS_ONLY=0
OVERRIDE_ENV_VARS_PATH=0
INTEGRATION_TEST_TO_RUN=0
UNIT_TEST_TO_RUN=0

PARSED_OPTIONS=`getopt -o hlte:i:u: -l export-env-vars-only,setup-only -- "$@"`

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

      -i)
         INTEGRATION_TEST_TO_RUN=$2
         shift 2
         ;;

      -u)
         UNIT_TEST_TO_RUN=$2
         shift 2
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

      -e)
         OVERRIDE_ENV_VARS_PATH=$2
         shift 2
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
  if [ "$TEARDOWN" -eq 1 ]
  then
    teardown
    exit
  fi

  setup
  echo "Test environment setup complete"

  if [ "$SETUP_ONLY" -ne 1 ]
  then
    time run_tests
  fi

  if [ "$LEAVE" -ne 0 ]
  then
    #
    # We should teardown the test setup environment
    #
    teardown
    echo "Test environment clean-up complete"
  fi
fi

