#!/bin/bash
DIR=$(pwd)
LV=$(which LavaVR.sh)
LVDIR=$(dirname "${LV}")
echo "Found LavaVR in ${LVDIR}"
echo "Running ${1} from ${DIR}"

#Kill existing
orun -K

#Cave only
if [ -d /cave ]; then 
  #/cave/sabi.js/scripts/GL-highperformance
  #/cave/sabi.js/scripts/GL-highquality
  export PATH=/cave/dev/LavaVR/:${PATH}
  source /usr/share/Modules/3.2.10/init/bash
  module unload omegalib
  module load omegalib/13-c++11
fi

#Ensure correct LavaVu module gets loaded
export PYTHONPATH=${LVDIR}/LavaVu:${PYTHONPATH}

CMD=orun
#CMD="gdb --args orun"

#Use first command line arg
#echo ${CMD} -s ${LVDIR}/LavaVR.py -x "loadScript('${DIR}/${1}')"
${CMD} -s ${LVDIR}/LavaVR.py -x "loadScript('${DIR}/${1}')"

