#!/bin/bash

set -e
dir="libgeotiff"

if [ ! -d "${dir}" ] ; then
    git clone https://github.com/OSGeo/libgeotiff.git "${dir}"
    cd "${dir}"
    git checkout "tags/1.5.1"
fi 