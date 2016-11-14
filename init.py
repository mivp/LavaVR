#######################################
# init.py : LavaVu OmegaLib init script
#######################################
import LavaVu.lavavu as lavavu
import LavaVR
from omega import *
from euclid import *
import urllib2
import os

cmds = []
labels = dict()
objmnu = None
filemnu = None
animate = 0
saveAnimate = 7 # 10 fps
time = 0

# add the current path to the data search paths.
addDataPath(os.getcwd())

#LavaVu functions
lvr = None
lv = None
def _sendCommand(cmd):
  if not isMaster():
    return
  #lvr.runCommand(cmd)
  lv.commands(cmd)
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
  global labels
  _sendCommand('scale points ' + str(sizeLevel))
  labels["Point Size"].setText("Point Size: " + str(sizeLevel))

transp = 0.0
def _setTransparency(val):
  global labels, transp
  trval = (10 - val) / 10.0
  if trval <= 0.01: trval = 0.01
  trans = float("{0:.1f}".format(trval))
  if trans != transp:
    #_sendCommand('alpha ' + str(trans))
    _addCommand('alpha ' + str(trans))
    labels["Transparency"].setText("Transparency: " + str(trans))
    transp = trans

def _setFrameRate(val):
  global animate
  animate = val

def _getPosition():
  #TEST: TODO: allow saving/restoring positions
  print getDefaultCamera().getPosition()

def _setPosition():
  #TEST: TODO: allow saving/restoring positions
  getDefaultCamera().setPosition(Vector3(389.07, -5763.38, 725.44))

def _addMenuItem(menu, label, call, checked=None):
  #Adds menu item, checkable optional
  mi = menu.addButton(label, call)
  if not checked == None:
    mi.getButton().setCheckable(True)
    mi.getButton().setChecked(checked)
  return mi

def _addSlider(menu, label, call, ticks, value):
  global labels
  l = menu.addLabel(label)
  labels[label] = l
  ss = menu.addSlider(ticks, call)
  ss.getSlider().setValue(value)
  ss.getWidget().setWidth(200)

def _addCommandMenuItem(menu, label, command):
  #Adds a menu item to issue a command to the control server
  return _addMenuItem(menu, label, "_sendCommand('"  + command + "')")

def _addObjectMenuItem(name, state):
  #Adds a toggle menu item to hide/show object
  global objectMenu, objmnu
  mitem = objmnu.addButton(name, "_toggleObject('"  + name + "')")
  mitem.getButton().setCheckable(True)
  mitem.getButton().setChecked(state)
  objectMenu[name] = mitem

def _addFileMenuItem(filename):
  #Adds menu item to run a script
  global filemnu
  mitem = filemnu.addButton(filename, "_sendCommand('file "  + filename + "')")

def onUpdate(frame, t, dt):
  global animate, cmds, labels, time
  #print getDefaultCamera().getPosition()
  if animate > 0:
    elapsed = t - time
    fps = (10.0 - animate) * 4.0
    spf = 1.0 / fps
    #print "fps %f spf %f elapsed %f" % (fps, spf, elapsed)
    if elapsed > spf:
      _sendCommand("next")
      labels["Animate"].setText("Animate: " + str(int(round(1.0 / elapsed))) + "fps")
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

objmnu = menu.addSubMenu("Objects")
objmnu.addLabel("Toggle Objects")
filemnu = menu.addSubMenu("Files")
filemnu.addLabel("Load files")
_addSlider(menu, "Point Size", "_setPointSize(%value%)", 50, 1)
_addCommandMenuItem(menu, "Scale points up", "scale points up")
_addCommandMenuItem(menu, "Scale points down", "scale points down")
_addSlider(menu, "Transparency", "_setTransparency(%value%)", 10, 0)
_addCommandMenuItem(menu, "Point Type", "pointtype all")
_addCommandMenuItem(menu, "Next Model", "model down")
_addSlider(menu, "Animate", "_setFrameRate(%value%)", 10, 0)
#_addCommandMenuItem(menu, "Toggle Model Rotate", "")
#_setFrameRate(8)
#_addMenuItem(menu, "Save Position", "_getPosition()")
#_addMenuItem(menu, "Restore Position", "_setPosition()")

im = loadImage("logo.jpg")
if im:
   mi = menu.addImage(im)
   ics = mi.getImage().getSize() * 0.5
   mi.getImage().setSize(ics)

setEventFunction(onEvent)
setUpdateFunction(onUpdate)

queueCommand(":freefly")

#Create the viewer
print lavavu.__file__
lv = lavavu.Viewer(hidden=False, quality=1, port=8080, initscript=False)
#lv = lavavu.Viewer(verbose=True, quality=1, port=8080, initscript=False)

lvr = LavaVR.initialize(lv.app)

