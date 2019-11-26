#from __future__ import print_function
#######################################
# init.py : LavaVu OmegaLib init script
#######################################
print(" -------------------------- Loading LavaVR -------------------------- ")
import sys
sys.path.append('LavaVu')
import lavavu
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
nosort = False
saveAnimate = 7 # 10 fps
ftime = 0

#LavaVu functions
_lvu = None
lv = None
def _sendCommand(cmd):
  global lv
  #if isMaster():
  #print("Sending","_lvu.commands('" + cmd + "')")
  #queueCommand("_lvu.commands('" + cmd + "')")
  _lvu.commands(cmd)
  #_lvu.app.queueCommands(cmd)
  #if isMaster():
  #    _lvu.commands(cmd)
  #_lvu.commands(cmd)

#LavaVu menu
mm = MenuManager.createAndInitialize()
menu = mm.getMainMenu()

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

objmnu = menu.addSubMenu("Objects")
objmnu.addLabel("Toggle Objects")
filemnu = menu.addSubMenu("State/Scripts")
_addMenuItem(filemnu, "Save Default State", "_lvr.saveDefaultState()")
_addMenuItem(filemnu, "Save New State", "_lvr.saveNewState()")
_addSlider(menu, "Height Scale", "_setZScale(%value%)", 10, 1)
_addCommandMenuItem(menu, "Scale points up", "scale points up")
_addCommandMenuItem(menu, "Scale points down", "scale points down")
_addSlider(menu, "Transparency", "_setTransparency(%value%)", 10, 0)
#_addCommandMenuItem(menu, "Point Type", "pointtype all")
_addCommandMenuItem(menu, "Next Model", "model down")
_addSlider(menu, "Animate", "_setFrameRate(%value%)", 10, 0)
mi=_addMenuItem(menu,"Toggle Head Tracking", "toggleHeadTracking(getDefaultCamera())",getDefaultCamera().isTrackingEnabled())
mi=_addMenuItem(menu,"Reset Orientation", "getDefaultCamera().setOrientation(Quaternion(0.5, 0.5, 0.5, 0.5))")

objectMenu = dict()
def _toggleObject(name):
  #if not isMaster():
  #  return

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

transp = 0.0
def _setTransparency(val):
  global mnulabels, transp
  trval = (10 - val) / 10.0
  if trval <= 0.01: trval = 0.01
  trans = float("{0:.1f}".format(trval))
  if trans != transp:
    _sendCommand('alpha ' + str(trans))
    mnulabels["Transparency"].setText("Transparency: " + str(trans))
    transp = trans

def _setFrameRate(val):
  if not isMaster():
    return
  global animate, nosort
  animate = val
  #This disables sort when animating, can be much faster
  if nosort:
      if val == 0:
        _sendCommand("sort on")
      else:
        _sendCommand("sort off")

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
  #Adds menu item to load a state or script file
  global filemnu
  mitem = filemnu.addButton(filename, "_sendCommand('file "  + filename + "'); _lvr.updateState()")

def runScript(filename, *args):
    script = open(filename).read()
    #script = script.replace('import lavavu', '#import lavavu')
    #script = script.replace('lavavu.Viewer', 'VRViewer')
    script = script.replace('lavavu.Viewer', '_lvu #')
    sys.argv = args
    print(args)
    #https://stackoverflow.com/a/437857
    code = compile(script, filename, 'exec')
    exec(code, globals(), locals())
    #exec(script, globals(), locals())

def _addScriptMenuItem(filename):
  #Adds menu item to load a python script
  global filemnu
  mitem = filemnu.addButton(filename, "runScript('"  + filename + "')")


def _populateFileMenu():
  #Clear first
  global filemnu
  c = filemnu.getContainer()
  #First 2 entries fixed..
  for idx in range(2,c.getNumChildren()):
    item = c.getChildByIndex(idx)
    c.removeChild(item)

  #Skip the loading scripts
  skip = ["init.script", "init.py"]
  if hasattr(sys, 'argv') and len(sys.argv) > 0:
    skip += [sys.argv[0]]
  import os

  #Python files
  for file in sorted(glob.glob("*.py")):
      if os.path.basename(file) not in skip:
          _addScriptMenuItem(file)

  #LavaVu Script files
  for file in sorted(glob.glob("*.script")):
      if os.path.basename(file) not in skip:
          _addFileMenuItem(file)

  #LavaVu json state files
  for file in sorted(glob.glob("*.json"), reverse=True):
      _addFileMenuItem(file)


def onUpdate(frame, t, dt):
  global animate, cmds, mnulabels, ftime

  #Hacky, just do this a few frames in as does nothing if command issued on script run
  if frame == 5:
    if isMaster():
        #Initial state load, on master only
        queueCommand("_sendCommand('file state.json');")
        queueCommand("_lvr.updateState();")
    #Update menus
    queueCommand("_populateObjectMenu();")
    queueCommand("_populateFileMenu();")

  if animate > 0 and isMaster():
    elapsed = t - ftime
    fps = (10.0 - animate) * 4.0
    spf = 1.0 / fps
    #print("fps %f spf %f elapsed %f" % (fps, spf, elapsed))
    if elapsed > spf:
      _sendCommand("next")
      mnulabels["Animate"].setText("Animate: " + str(int(round(1.0 / elapsed))) + "fps")
      ftime = t

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
  #if type == ServiceType.Wand:
  #Turn animate on/off
  if (e.isButtonDown( EventFlags.ButtonUp )): # D-Pad up
      if animate:
        saveAnimate = animate
        _setFrameRate(0)
      else:
        _setFrameRate(saveAnimate)

def toggleHeadTracking(camera):
  camera.setTrackingEnabled(not camera.isTrackingEnabled())

class VRViewer(lavavu.Viewer):
    viewerlist = []

    def __init__(self, *args, **kwargs):
        global lvr, _lvr, lv
        print("CREATING NEW VR VIEWER")
        if lv:
            #Don't destroy, TODO: needs to be destroyed in render loop
            #Allow switching between all opened viewers?
            VRViewer.viewerlist.append(lv)

        #Create the viewer (disable threading by setting port=0)
        vargs = {"omegalib" : True,
                 "hidden" : False,
                 "quality" : 1,
                 "port" : 0,
                 "initscript" : False,
                 "usequeue" : True,
                 "validate" : True, #Allow custom properties
                 "border" : 0,
                 "axis" : False}
        vargs.update(kwargs) #Apply user kwargs
        print(vargs)
        super(VRViewer, self).__init__(*args, **vargs)

        lv = self

        #Start web server on master
        self["validate"] = False
        if isMaster():
            self.serve(port=9988)
            print("Web server running on:", self.server.port)

        #Pass our LavaVu instance to LavaVR and init
        print(lavavu.__file__,lavavu.__version__)
        lvr = _lvr = LavaVR.initialize(self.app)

    def __del__(self):
        print("CLOSING")
        self.app.destroy()
        print("DESTROYED")

#DEFAULT GLOBAL VIEWER
_lvu = VRViewer()

#Load a script given path
def loadScript(path="", *args):
    wd, fn = os.path.split(path)
    if len(wd):
        os.chdir(wd)
    if not os.path.exists(fn) or not os.path.isfile(fn):
        fn = "init.script"
    if not os.path.exists(fn) or not os.path.isfile(fn):
        fn = "init.py"

    print("Running " + fn + " from " + wd)
    filename, file_extension = os.path.splitext(fn)
    if file_extension == '.py':
        runScript(fn, *args)
    elif os.path.exists(fn):
        ##Create a default viewer for .script files
        #global _lvu
        #_lvu = VRViewer()
        _lvu.file(fn)

#Passed working directory and script as args to run
if hasattr(sys, 'argv') and len(sys.argv) > 0:
    loadScript(sys.argv[0])

setEventFunction(onEvent)
setUpdateFunction(onUpdate)

#_setFrameRate(8)

im = loadImage("logo.jpg")
if im:
   mi = menu.addImage(im)
   ics = mi.getImage().getSize() * 0.5
   mi.getImage().setSize(ics)

queueCommand(":freefly")

#addQuickCommand(string cmd, string call, int args, string description)
#addQuickCommand('nf', 'cam = getDefaultCamera(); near = cam.getNearZ(); far = cam.getFarZ(); cam.setNearFarZ(near, far)', 2, 'setnearfar')
