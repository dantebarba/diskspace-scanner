#!/bin/sh
./build.sh $@
docker push dantebarba/diskspacescanner:$@