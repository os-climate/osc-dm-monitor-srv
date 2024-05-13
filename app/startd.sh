#!/bin/bash

#####
#
# startd.sh - Start the docker environment
#
# Author: Eric Broda, eric.broda@brodagroupsoftware.com, September 24, 2023
#
# Parameters:
#   N/A
#
#####

if [ -z ${ROOT_DIR+x} ] ; then
    echo "Environment variables have not been set.  Run 'source bin/environment.sh'"
    exit 1
fi

# Show the environment
$PROJECT_DIR/bin/show.sh

usage() {
    echo " "
    echo "Error: $1"
    echo "Usage: startd.sh"
    echo " "
    echo "Example: startd.sh"
    echo " "
}


export IMAGE_NAME="$PROJECT"
export HOSTNAME="$PROJECT"


echo "--- Docker Environment ---"
echo "IMAGE_NAME:   $IMAGE_NAME    <--- This is the docker image name"
echo "HOSTNAME:     $HOSTNAME      <--- This is the hostname running in docker"
echo " "

NETWORK_NAME="localnet"
docker network create $NETWORK_NAME

compose() {
  docker-compose -f $PROJECT_DIR/docker/docker-compose.yml up
}

decompose() {
  docker-compose -f $PROJECT_DIR/docker/docker-compose.yml down
}

compose;
decompose;