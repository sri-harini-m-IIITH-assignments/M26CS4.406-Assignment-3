#!/usr/bin/env bash
set -e
mkdir -p data
[ -f data/sift-128-euclidean.hdf5 ] || curl -L -o data/sift-128-euclidean.hdf5 http://ann-benchmarks.com/sift-128-euclidean.hdf5
[ -f data/glove-100-angular.hdf5 ]  || curl -L -o data/glove-100-angular.hdf5  http://ann-benchmarks.com/glove-100-angular.hdf5