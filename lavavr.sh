#!/bin/bash
DIR=$(pwd)
echo $DIR

LV=$(which LavaVR)
echo $LV
LVDIR=$(dirname "${LV}")
echo ${LVDIR}
cd ${LVDIR}

file="init.script"
if [ -f "$file" ]
then
	echo "$file found."
  orun -s init.py -x "os.chdir('${DIR}'); queueCommand('lv.file(\"init.script\")')"
else
	echo "$file not found."
  orun -s init.py -x "os.chdir('${DIR}'); print os.getcwd(); queueCommand(':r init.py')"
fi
