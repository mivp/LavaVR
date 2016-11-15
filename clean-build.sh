#!/bin/bash
cd LavaVu
make clean
cd ..

#Cave only
CMAKEFLAGS=""
if [ -d /cave ]; then 
  source /usr/share/Modules/3.2.10/init/bash
  module load cmake/3.5.2
  module load omegalib/13-c++11
  CMAKEFLAGS= -DCMAKE_CXX_FLAGS=-std=c++0x -DCMAKE_C_COMPILER=/usr/local/gcc/7.0.0/bin/gcc -DCMAKE_CXX_COMPILER=/usr/local/gcc/7.0.0/bin/gcc
fi

rm -rf CMakeFiles
rm CMakeCache.txt
cmake . ${CMAKEFLAGS}
make -j8 $@
