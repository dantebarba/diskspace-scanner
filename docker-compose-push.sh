#!/bin/sh
export BUILD_VERSION=$(git describe --tags --dirty --always)
docker-compose $@;
echo dantebarba/diskspacescanner:{$BUILD_VERSION,latest} | xargs -n 1 docker push