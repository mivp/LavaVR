#!/bin/bash
DIR=$(pwd)
LV=$(which LavaVR.sh)
LVDIR=$(dirname "${LV}")
echo "Found LavaVR in ${LVDIR}"
cd ${LVDIR}

#Cave only
if [ -d /cave ]; then 
  #/cave/sabi.js/scripts/GL-highperformance
  export PATH=/cave/dev/LavaVR/::${PATH}
  source /usr/share/Modules/3.2.10/init/bash
  module unload omegalib
  module load omegalib/13-c++11
fi

CMD=orun
#CMD=gdb --args orun

#Run a python script or a lavavu script by extension
function run
{
  file=$1
  DIR=$2
  echo "Running ${file} from ${DIR}"
  file_ext=${file##*.}
  if [ ${file_ext} = "script" ]
  then
    echo "os.chdir('${DIR}'); lv.file('${file}')"
    ${CMD} -s LavaVR.py -x "os.chdir('${DIR}'); lv.file('${file}')"
  else
    echo "os.chdir('${DIR}'); exec(open('${file}').read(), globals())"
    ${CMD} -s LavaVR.py -x "os.chdir('${DIR}'); exec(open('${file}').read(), globals())"
    #orun -s LavaVR.py -x "os.chdir('${DIR}'); queueCommand(':r ${file}');"
  fi
}

#Use first command line arg or init.script / init.py
file=${1:-init.py}
path="${DIR}/$file"
echo $path
if [ -f "$path" ]
then
  run ${file} ${DIR}
else
  run init.script ${DIR}
fi

