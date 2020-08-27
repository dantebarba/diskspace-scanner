#!/bin/sh
docker build --pull --build-arg BUILD_VERSION=$(git describe --tags --dirty --always) --rm -f "Dockerfile" -t dantebarba/diskspacescanner:$@ "."