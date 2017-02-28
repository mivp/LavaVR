#######################################
# init.py : LavaVu OmegaLib init script
#######################################
import LavaVu.lavavu as lavavu
import LavaVR
from omega import *
from euclid import *
import urllib2
import glob, os

cmds = []
mnulabels = dict()
objmnu = None
filemnu = None
animate = 0
saveAnimate = 7 # 10 fps
time = 0

#LavaVu functions
_lvu = None
#TODO: Check: Is this deprecated? Can't we just use _lvu.queueCommands()
def _sendCommand(cmd):
  global lv
  if not isMaster():
    return
  _lvu.commands(cmd)
  #url = 'http://localhost:8080/command=' + urllib2.quote(cmd)
  #urllib2.urlopen(url)

def _addCommand(cmd):
  global cmds
  if not isMaster():
    return
  cmds = [cmd] + cmds

objectMenu = dict()
def _toggleObject(name):
  if not isMaster():
    return

  global objectMenu
  #Check state (this has already been switched so shows current state)
  if objectMenu[name].getButton().isChecked():
    _sendCommand('show "' + name + '"');
  else:
    _sendCommand('hide "' + name + '"');

def _setPointSize(sizeLevel):
  global mnulabels
  _sendCommand('scale points ' + str(sizeLevel))
  mnulabels["Point Size"].setText("Point Size: " + str(sizeLevel))

transp = 0.0
def _setTransparency(val):
  global mnulabels, transp
  trval = (10 - val) / 10.0
  if trval <= 0.01: trval = 0.01
  trans = float("{0:.1f}".format(trval))
  if trans != transp:
    #_sendCommand('alpha ' + str(trans))
    _addCommand('alpha ' + str(trans))
    mnulabels["Transparency"].setText("Transparency: " + str(trans))
    transp = trans

def _setFrameRate(val):
  global animate
  animate = val

def _addMenuItem(menu, label, call, checked=None):
  #Adds menu item, checkable optional
  mi = menu.addButton(label, call)
  if not checked == None:
    mi.getButton().setCheckable(True)
    mi.getButton().setChecked(checked)
  return mi

def _addSlider(menu, label, call, ticks, value):
  global mnulabels
  l = menu.addLabel(label)
  mnulabels[label] = l
  ss = menu.addSlider(ticks, call)
  ss.getSlider().setValue(value)
  ss.getWidget().setWidth(200)

def _addCommandMenuItem(menu, label, command):
  #Adds a menu item to issue a command to the control server
  return _addMenuItem(menu, label, "_sendCommand('"  + command + "')")

def _addObjectMenuItem(name=None, state=False):
  global objectMenu, objmnu
  #Clear?
  if name == None:
      c = objmnu.getContainer()
      for name in objectMenu:
          c.removeChild(objectMenu[name].getWidget())
      return
  #Adds a toggle menu item to hide/show object
  mitem = objmnu.addButton(name, "_toggleObject('"  + name + "')")
  mitem.getButton().setCheckable(True)
  mitem.getButton().setChecked(state)
  objectMenu[name] = mitem

def _addFileMenuItem(filename):
  #Adds menu item to run a script
  global filemnu
  mitem = filemnu.addButton(filename, "_sendCommand('file "  + filename + "')")

def _populateFileMenu():
  #Clear first
  global filemnu
  c = filemnu.getContainer()
  for idx in range(c.getNumChildren()):
    item = c.getChildByIndex(idx)
    c.removeChild(item)
  #Populate the files menu with any json files (TODO: *.py, *.script?)
  for file in glob.glob("*.json"):
      _addFileMenuItem(file)

def onUpdate(frame, t, dt):
  global animate, cmds, mnulabels, time
  if animate > 0:
    elapsed = t - time
    fps = (10.0 - animate) * 4.0
    spf = 1.0 / fps
    #print "fps %f spf %f elapsed %f" % (fps, spf, elapsed)
    if elapsed > spf:
      _sendCommand("next")
      mnulabels["Animate"].setText("Animate: " + str(int(round(1.0 / elapsed))) + "fps")
      time = t

  if frame % 10 == 0:
    while len(cmds):
      _sendCommand(cmds.pop())

def onEvent():
  global animate, saveAnimate
  if not isMaster():
    return

  e = getEvent()
  type = e.getServiceType()

  # If we want to check multiple controllers or other tracked objects,
  # we could also check the sourceID of the event
  sourceID = e.getSourceId()

  # Check to make sure the event we're checking is a Wand event
  if type == ServiceType.Wand:
    #Turn animate on/off
    if(e.isButtonDown( EventFlags.ButtonUp )): # D-Pad up
      if animate:
        saveAnimate = animate
        _setFrameRate(0)
      else:
        _setFrameRate(saveAnimate)

#LavaVu menu
mm = MenuManager.createAndInitialize()
menu = mm.getMainMenu()

#Monash menu
try:
    import MonashMenu
    MonashMenu.addMonashMenu(menu)
except:
    pass

objmnu = menu.addSubMenu("Objects")
objmnu.addLabel("Toggle Objects")
filemnu = menu.addSubMenu("Files")
filemnu.addLabel("Load files")
_addMenuItem(menu, "Save State", "_lvr.saveState()")
_addSlider(menu, "Point Size", "_setPointSize(%value%)", 50, 1)
_addCommandMenuItem(menu, "Scale points up", "scale points up")
_addCommandMenuItem(menu, "Scale points down", "scale points down")
_addSlider(menu, "Transparency", "_setTransparency(%value%)", 10, 0)
_addCommandMenuItem(menu, "Point Type", "pointtype all")
_addCommandMenuItem(menu, "Next Model", "model down")
_addSlider(menu, "Animate", "_setFrameRate(%value%)", 10, 0)
#_addCommandMenuItem(menu, "Toggle Model Rotate", "")
#_setFrameRate(8)

im = loadImage("logo.jpg")
if im:
   mi = menu.addImage(im)
   ics = mi.getImage().getSize() * 0.5
   mi.getImage().setSize(ics)

setEventFunction(onEvent)
setUpdateFunction(onUpdate)

queueCommand(":freefly")

#Create the viewer
lv = _lvu = lavavu.Viewer(omegalib=True, hidden=False, quality=1, port=8080, initscript=False, usequeue=True)

#Pass our LavaVu instance to LavaVR and init
_lvr = LavaVR.initialize(_lvu.app)

#Passed working directory and script as args to run
import sys
if len(sys.argv) > 0:
    wd, fn = os.path.split(sys.argv[0])
    if len(wd):
        os.chdir(wd)
    if len(fn) == 0:
        fn = "init.py"
    if not os.path.exists(fn) or not os.path.isfile(fn):
        fn = "init.script"

    print "Running " + fn + " from " + wd
    filename, file_extension = os.path.splitext(fn)
    if file_extension == '.py':
        script = open(fn).read()
        #Hack to swap any returned viewer creation with LVR instance
        script = script.replace('lavavu.Viewer', '_lvu #lavavu.Viewer')
        exec(script, globals())
    else:
        _lvu.file(fn)


