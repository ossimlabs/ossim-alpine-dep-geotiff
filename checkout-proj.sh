#!/bin/bash

set -e
dir="PROJ"

if [ ! -d "${dir}" ] ; then
    git clone https://github.com/OSGeo/PROJ.git "${dir}"
    cd "${dir}"
    git checkout "tags/6.2.0"
    mkdir -p build
fi
