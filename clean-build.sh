#!/bin/bash
cd LavaVu
make clean
cd ..
module load cmake/3.5.2
module load gcc/7.0.0
export OMEGA_HOME=/cave/omegalib/omegalib13.1-cxx11/
export Omegalib_DIR=/cave/omegalib/omegalib13.1-cxx11/build/
rm -rf CMakeFiles
rm CMakeCache.txt
cmake . -DCMAKE_CXX_FLAGS=-std=c++0x -DCMAKE_C_COMPILER=/usr/local/gcc/7.0.0/bin/gcc -DCMAKE_CXX_COMPILER=/usr/local/gcc/7.0.0/bin/gcc
#cmake .
make -j12 $@
