#!/bin/bash
DIR=$(pwd)
LV=$(which LavaVR.sh)
LVDIR=$(dirname "${LV}")
echo "Found LavaVR in ${LVDIR}"
cd ${LVDIR}

#Cave only
if [ -d /cave ]; then 
  /cave/sabi.js/scripts/GL-highperformance
  export PATH=/cave/dev/LavaVR/::${PATH}
  source /usr/share/Modules/3.2.10/init/bash
  module unload omegalib
  module load omegalib/13-c++11
fi

file="${DIR}/init.script"
if [ -f "$file" ]
then
  echo "Running init.script from ${DIR}"
  orun -s LavaVR.py -x "print os.getcwd(); os.chdir('${DIR}'); queueCommand('lv.file(\"init.script\")')"
else
  echo "Running init.py from ${DIR}"
  orun -s LavaVR.py -x "print os.getcwd(); os.chdir('${DIR}'); queueCommand(':r init.py')"
fi

