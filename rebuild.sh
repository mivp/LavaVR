#!/bin/bash
#Cave only
if [ -d /cave ]; then 
  module load LavaVR/1.2.0
fi

cd LavaVu
make TIFF=1 -j12 $@
cd ..

make -j4 $@
