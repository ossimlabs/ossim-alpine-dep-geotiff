#!/bin/bash

cd libgeotiff/libgeotiff
./autogen.sh
./configure --prefix=/usr/local --enable-shared --disable-static
make -j 8 install
make clean
