#!/bin/sh

echo "Setting up variables"

IMAGE_NAME="test_automation"
IMAGE_TAG="local"
CONTAINER_NAME="sid_test"
AWS_CREDS_SOURCE_PATH="/Users/$USER/.aws/"

echo "Pulling Container and copying AWS creds from the host"

docker rm ${CONTAINER_NAME} -f
docker pull ${IMAGE_NAME}:${IMAGE_TAG}
docker run -t -d --name ${CONTAINER_NAME} ${IMAGE_NAME}:${IMAGE_TAG}
docker cp ${AWS_CREDS_SOURCE_PATH} ${CONTAINER_NAME}:/root/.aws/

echo "Entering into Docker Container"

docker exec -it ${CONTAINER_NAME} bash