#!/bin/bash

# Build the docker image

mkdir -p /var/tmp/backup_manager_inttest
mkdir -p /var/tmp/backup_manager_inttest/ssh-keys
ssh-keygen -q -t rsa -N '' -f /var/tmp/backup_manager_inttest/ssh-keys/id_rsa <<<y 2>&1 >/dev/null

