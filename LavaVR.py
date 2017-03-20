#######################################
# init.py : LavaVu OmegaLib init script
#######################################
print " -------------------------- Loading LavaVR -------------------------- "
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
def _sendCommand(cmd):
  global _lvu
  if isMaster():
      _lvu.commands(cmd)

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

def _setZScale(level):
  global mnulabels
  if level < 1: level = 1
  _sendCommand('scale z ' + str(level))
  mnulabels["Height Scale"].setText("Height Scale: " + str(level))


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
    _sendCommand('alpha ' + str(trans))
    #_addCommand('alpha ' + str(trans))
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

def _addObjectMenuItem(name, state=True):
  global objectMenu, objmnu
  #Adds a toggle menu item to hide/show object
  mitem = objmnu.addButton(name, "_toggleObject('"  + name + "')")
  mitem.getButton().setCheckable(True)
  mitem.getButton().setChecked(state)
  objectMenu[name] = mitem

def _populateObjectMenu():
  #Clear first
  global objectMenu, objmnu
  c = objmnu.getContainer()
  for name in objectMenu:
      c.removeChild(objectMenu[name].getWidget())
  #Get list sorted by id
  objlist = sorted(_lvu.objects.values(), key=operator.attrgetter('id'))
  for obj in objlist:
      _addObjectMenuItem(str(obj["name"]), obj["visible"])

def _addFileMenuItem(filename):
  #Adds menu item to run a script
  global filemnu
  mitem = filemnu.addButton(filename, "_sendCommand('file "  + filename + "')")

def _populateFileMenu():
  #Clear first
  global filemnu
  c = filemnu.getContainer()
  #First 2 entries fixed..
  for idx in range(2,c.getNumChildren()):
    item = c.getChildByIndex(idx)
    c.removeChild(item)
  #Populate the files menu with any json files (TODO: *.py, *.script?)
  for file in sorted(glob.glob("*.json"), reverse=True):
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

def toggleHeadTracking(camera):
  camera.setTrackingEnabled(not camera.isTrackingEnabled())

#LavaVu menu
mm = MenuManager.createAndInitialize()
menu = mm.getMainMenu()

objmnu = menu.addSubMenu("Objects")
objmnu.addLabel("Toggle Objects")
filemnu = menu.addSubMenu("State")
_addMenuItem(filemnu, "Save Default State", "_lvr.saveDefaultState()")
_addMenuItem(filemnu, "Save New State", "_lvr.saveNewState()")
_addSlider(menu, "Height Scale", "_setZScale(%value%)", 10, 1)
_addSlider(menu, "Point Size", "_setPointSize(%value%)", 20, 1)
#_addCommandMenuItem(menu, "Scale points up", "scale points up")
#_addCommandMenuItem(menu, "Scale points down", "scale points down")
_addSlider(menu, "Transparency", "_setTransparency(%value%)", 10, 0)
#_addCommandMenuItem(menu, "Point Type", "pointtype all")
_addCommandMenuItem(menu, "Next Model", "model down")
_addSlider(menu, "Animate", "_setFrameRate(%value%)", 10, 0)
mi=_addMenuItem(menu,"Toggle Head Tracking", "toggleHeadTracking(getDefaultCamera())",getDefaultCamera().isTrackingEnabled())
mi=_addMenuItem(menu,"Reset Orientation", "getDefaultCamera().setOrientation(Quaternion(0.5, 0.5, 0.5, 0.5))")

#_setFrameRate(8)

im = loadImage("logo.jpg")
if im:
   mi = menu.addImage(im)
   ics = mi.getImage().getSize() * 0.5
   mi.getImage().setSize(ics)

setEventFunction(onEvent)
setUpdateFunction(onUpdate)


#Create the viewer
lv = _lvu = lavavu.Viewer(omegalib=True, hidden=False, quality=1, port=8080, initscript=False, usequeue=True)

#Pass our LavaVu instance to LavaVR and init
lvr = _lvr = LavaVR.initialize(_lvu.app)

#Load a script given path
def loadScript(path="init.py"):
    wd, fn = os.path.split(path)
    if len(wd):
        os.chdir(wd)
    if not os.path.exists(fn) or not os.path.isfile(fn):
        fn = "init.script"

    print "Running " + fn + " from " + wd
    filename, file_extension = os.path.splitext(fn)
    if file_extension == '.py':
        script = open(fn).read()
        #Hack the script to use existing lavavu module and instance
        script = script.replace('import lavavu', '#import lavavu')
        script = script.replace('lavavu.Viewer', '_lvu #lavavu.Viewer')
        exec(script, globals())
    elif os.path.exists(fn):
        _lvu.file(fn)

#Passed working directory and script as args to run
import sys
if hasattr(sys, 'argv') and len(sys.argv) > 0:
    loadScript(sys.argv[0])

#Load initial state
queueCommand("lv.file('state.json')")

queueCommand(":freefly")

