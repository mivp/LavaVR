/************************************* 
 * LavaVu OmegaLib Module
 *************************************/

//TODO:
//Better near clip defaults/controls

#include <omega.h>
#include <omegaGl.h>
#include <omegaToolkit.h>
#include "LavaVu/src/LavaVu.h"
#include "LavaVu/src/Server.h"
#include <dirent.h>
#include <iostream>
#include <iomanip>
#include <ctime>

using namespace omega;
using namespace omegaToolkit;
using namespace omegaToolkit::ui;

class LavaVuApplication;

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
class LavaVuRenderPass: public RenderPass
{
public:
  LavaVuRenderPass(Renderer* client, LavaVuApplication* app): RenderPass(client, "LavaVuRenderPass"), app(app) {}
  virtual void initialize();
  virtual void render(Renderer* client, const DrawContext& context);

private:
  LavaVuApplication* app;

};

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
class LavaVuApplication: public EngineModule
{
public:
  LavaVu* glapp;
  bool isMaster;

  //Copy of commands
  std::deque<std::string> commands;
  //Widgets
  Ref<Label> statusLabel;
  Ref<Label> titleLabel;

  LavaVuApplication(): EngineModule("LavaVuApplication")
  { 
    enableSharedData();
    menuOpen = false;
    glapp = NULL; 
    SystemManager* sys = SystemManager::instance();
    isMaster = sys->isMaster();
  }

  virtual void initialize()
  {
    //Create a label for text info
    DisplaySystem* ds = SystemManager::instance()->getDisplaySystem();
    // Create and initialize the UI management module.
    myUiModule = UiModule::createAndInitialize();
    myUi = myUiModule->getUi();

    int sz = 100;
    statusLabel = Label::create(myUi);
    statusLabel->setText("");
    statusLabel->setColor(Color::Gray);
    statusLabel->setFont(ostr("fonts/arial.ttf %1%", %sz));
    statusLabel->setHorizontalAlign(Label::AlignLeft);
    statusLabel->setPosition(Vector2f(100,300));

    sz = 150;
    titleLabel = Label::create(myUi);
    titleLabel->setText("");
    titleLabel->setColor(Color::Gray);
    titleLabel->setFont(ostr("fonts/arial.ttf %1%", %sz));
    titleLabel->setHorizontalAlign(Label::AlignLeft);
    titleLabel->setPosition(Vector2f(100,100));

  }

  virtual void initializeRenderer(Renderer* r) 
  { 
    //viewer = new OpenGLViewer();
    r->addRenderPass(new LavaVuRenderPass(r, this));
  }
  
  virtual void handleEvent(const Event& evt);
  virtual void updateState();
  virtual void updateMenu();
  virtual void saveState(std::string statefile="");
  virtual void saveDefaultState();
  virtual void saveNewState();
  virtual void cameraInit();
  virtual void cameraRestore();
  virtual void cameraReset();
  virtual void commitSharedData(SharedOStream& out);
  virtual void updateSharedData(SharedIStream& in);

private:
  // The ui manager
  Ref<UiModule> myUiModule;
  // The root ui container
  Ref<Container> myUi;  
  std::string labelText;
  bool menuOpen;
  std::vector<std::string> states;
};

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void LavaVuRenderPass::initialize()
{
  RenderPass::initialize();

  // Initialize the omegaToolkit python API
  omegaToolkitPythonApiInit();
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void LavaVuRenderPass::render(Renderer* client, const DrawContext& context)
{
  if (context.task == DrawContext::SceneDrawTask)
  {
    client->getRenderer()->beginDraw3D(context);

    if (!app->glapp->viewer->isopen)
    {
      //Have to manually call these as not using a window manager
      app->glapp->viewer->open(context.tile->pixelSize[0], context.tile->pixelSize[1]);
      app->glapp->viewer->init();
      app->glapp->loadModelStep(0, 0, true); //Open/load if not already
      app->glapp->resetViews(); //Forces bounding box update



      //Transfer LavaVu camera settings to Omegalib
      app->cameraInit();

      app->updateState();
      app->updateMenu();

      //Disable auto-sort
      app->glapp->drawstate.globals["sort"] = 0;

      //Default nav speed
      omega::Camera* cam = Engine::instance()->getDefaultCamera();
      float navSpeed = app->glapp->drawstate.global("navspeed");
      CameraController* cc = cam->getController();
      View* view = app->glapp->aview;
      //cc->setSpeed(view->model_size * 0.03);
      float rotate[4], translate[3], focus[3];
      view->getCamera(rotate, translate, focus);
      if (navSpeed <= 0.0) navSpeed = abs(translate[2]) * 0.05;
      cc->setSpeed(navSpeed);
    }

    //Copy commands before consumed
    static int comlen = 0;
    app->commands = app->glapp->viewer->commands;
    //Update state after commands are processed
    if (comlen > app->commands.size() && app->commands.size() == 0)
      app->updateState();
    comlen = app->commands.size();

    //Update status label
    if (app->statusLabel->getText() != app->glapp->message)
    {
       //std::cerr << statusLabel->getText() << " != " << glapp->message << std::endl;
       app->statusLabel->setAlpha(0.5);
       app->statusLabel->setText(app->glapp->message);
    }
    //Update title label
    std::string titleText = app->glapp->aview->properties["title"];
    if (titleText.length() > 0)
    {
       if (app->titleLabel->getText() != titleText)
          app->titleLabel->setText(titleText);
    }

    //Fade out status label (doesn't seem to work in cave)
    float alpha = app->statusLabel->getAlpha();
    if (alpha < 0.01)
    {
       app->statusLabel->setText("");
       app->glapp->message[0] = '\0';
    }
    else
       app->statusLabel->setAlpha(alpha * 0.95);

    //Apply the model rotation/scaling
    View* view = app->glapp->aview;   
    //view->apply(false); //Disable focal point translate
    view->apply();

    glEnable(GL_BLEND);

    //Hack to undo the Y offset
    glTranslatef(0, 2, 0);

    //Draw overlay on first screen only
    if (context.tile->isInGrid)
    {
      if (context.tile->gridX == 0 && context.tile->gridY == 0)
      {
        app->glapp->viewer->display();
        app->glapp->aview->drawOverlay(app->glapp->aview->inverse, titleText);
      }
      else
      {
        app->glapp->objectlist = false;  //Disable text output on all but first tile
        app->glapp->status = false;
        app->glapp->viewer->display();
      }
    }

    client->getRenderer()->endDraw();

    //Process timer based commands
    app->glapp->viewer->pollInput();
  }
  else if(context.task == DrawContext::OverlayDrawTask)
  {
  }
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void LavaVuApplication::updateState()
{
  //Check for global camera loaded
  if (glapp->drawstate.globals.count("camera") > 0)
  {
    json scam = glapp->drawstate.globals["camera"];
    //std::cout << " ______\n" << glapp->drawstate.globals << "\n______" << std::endl;
    json pos = scam["position"];
    json o = scam["orientation"];

    omega::Camera* cam = Engine::instance()->getDefaultCamera();
    cam->setOrientation(o[3], o[0], o[1], o[2]);
    cam->setPosition(pos[0], pos[1], pos[2]);

    PythonInterpreter* pi = SystemManager::instance()->getScriptInterpreter();
    //std::stringstream cmd;
    //cmd << "getDefaultCamera().setOrientation(Quaternion(" << o[3] << "," << o[0] << "," << o[1] << "," << o[2] << "))";
    //std::cout << "O: " << cmd.str() << std::endl;
    //pi->queueCommand(cmd.str());
    //pi->queueCommand(cmd.str());

    //glapp->drawstate.globals.erase("camera");
  }

  //Apply clip planes
  View* view = glapp->aview;   
  omega::Camera* cam = Engine::instance()->getDefaultCamera();
  float near_clip = view->properties["near"];
  float far_clip = view->properties["far"];
  cam->setNearFarZ(0.005*near_clip, far_clip); //Set clip plane closer for CAVE use
  ///Setting clip planes can kill menu! Need to check using MenuManager::getDefaultMenuDistance()
  //MenuManager* mm = MenuManager::createAndInitialize();
  //float menuDist = mm->getDefaultMenuDistance();
  //Menu* main = mm->getMainMenu(); //float menuDist = mm->getDefaultMenuDistance();

  //Set background colour
  Colour& bg = view->background;
  cam->setBackgroundColor(Color(bg.rgba[0]/255.0, bg.rgba[1]/255.0, bg.rgba[2]/255.0, 0));
}

void LavaVuApplication::updateMenu()
{
  PythonInterpreter* pi = SystemManager::instance()->getScriptInterpreter();
  //Populate file menu
  pi->queueCommand("_populateFileMenu()");
  //Populate objects menu
  pi->queueCommand("_populateObjectMenu()");
}

void LavaVuApplication::saveState(std::string statefile)
{
  //Get camera positon, orientation and LavaVu model rotation
  omega::Camera* cam = Engine::instance()->getDefaultCamera();
  View* view = glapp->aview;
  float rotate[4], translate[3], focus[3];
  Vector3f curpos = cam->getPosition();
  omega::Quaternion curo = cam->getOrientation();
  view->getCamera(rotate, translate, focus);

  //Save in LavaVu global props and export
  json scam;
  scam["position"] = {curpos[0], curpos[1], curpos[2]};
  scam["orientation"] = {curo.x(), curo.y(), curo.z(), curo.w()};
  glapp->drawstate.globals["camera"] = scam;

  //Recently saved states, can be cycled through with Y(yellow)
  std::string state = glapp->getState();
  states.push_back(state);

  if (statefile.length())
  {
    std::ofstream file(statefile);
    if (file.good())
    {
      file << state;
      updateMenu();
    }
    else
      std::cout << "Unable to write to file: " << statefile << std::endl;
  }
}

void LavaVuApplication::saveDefaultState()
{
  saveState("state.json");
}

void LavaVuApplication::saveNewState()
{
  std::stringstream ss;
  auto t = std::time(nullptr);
  auto tm = *std::localtime(&t);
  ss << std::put_time(&tm, "%d-%m-%Y-%H-%M.json");
  saveState(ss.str());
}

void LavaVuApplication::cameraInit()
{
  //Setup camera using omegalib functions
  omega::Camera* cam = Engine::instance()->getDefaultCamera();
  View* view = glapp->aview;
  float rotate[4], translate[3], focus[3];
  Vector3f curpos = cam->getPosition();
  view->getCamera(rotate, translate, focus);

  //Set position from translate
  Vector3f newpos = Vector3f(translate[0], translate[1], -translate[2]);

  cam->setPosition(newpos);
  //From viewing distance
  //cam->setPosition(Vector3f(focus[0], focus[1], (focus[2] - view->model_size)) * view->orientation);
  //At center
  //cam->setPosition(Vector3f(focus[0], focus[1], focus[2] * view->orientation));

  //Default eye separation, TODO: set this via LavaVu property controllable via init.script
  cam->setEyeSeparation(view->eye_sep_ratio);

  int coordsys = view->properties["coordsystem"];
  cam->lookAt(Vector3f(focus[0], focus[1], focus[2] * coordsys), Vector3f(0,1,0));
  cam->setPitchYawRoll(Vector3f(0, 0, 0));
}

void LavaVuApplication::cameraRestore()
{
  //Cycle through saved camera positions / states
  static int idx = 0;

  //No saved entry or at end of list, reset to default position
  if (states.size() == 0 || idx < 0)
  {
    idx = states.size()-1;
    cameraReset();
    return;
  }

  omega::Camera* cam = Engine::instance()->getDefaultCamera();
  View* view = glapp->aview;
  //Restore the state data
  glapp->setState(states[idx]);
  updateState();

  //Set next index
  idx--;
}

void LavaVuApplication::cameraReset()
{
  //Reset the view to default starting pos
  omega::Camera* cam = Engine::instance()->getDefaultCamera();
  View* view = glapp->aview;
  float rotate[4], translate[3], focus[3];

  view->reset();
  view->init(true);  //Reset camera to default view of model

  view->getCamera(rotate, translate, focus);

  cam->setOrientation(omega::Quaternion(0, 0, 0, 1));
  cam->setPosition(Vector3f(translate[0], translate[1], -translate[2]));

  int coordsys = view->properties["coordsystem"];
  cam->lookAt(Vector3f(focus[0], focus[1], focus[2] * coordsys), Vector3f(0,1,0));
  cam->setPitchYawRoll(Vector3f(0, 0, 0));
}

void LavaVuApplication::handleEvent(const Event& evt)
{
  //printf(". %d %d %d\n", evt.getType(), evt.getServiceType(), evt.getFlags());
  if(evt.getServiceType() == Service::Pointer)
  {
    int x = evt.getPosition().x();
    int y = evt.getPosition().y();
    int flags = evt.getFlags();
    MouseButton button = NoButton;
    if (flags & 1)
      button = LeftButton;
    else if (flags & 2)
      button = RightButton;
    else if (flags & 4)
      button = MiddleButton;

    switch (evt.getType())
    {
      case Event::Down:
        //printf("%d %d\n", button, flags);
        if (button <= RightButton) glapp->viewer->mouseState ^= (int)pow(2, (int)button);
        glapp->viewer->mousePress(button, true, x, y);
        break;
      case Event::Up:
        glapp->viewer->mouseState = 0;
        glapp->viewer->mousePress(button, false, x, y);
        break;
      case Event::Zoom:
        glapp->viewer->mouseScroll(evt.getExtraDataInt(0));
        break;
      case Event::Move:
        if (glapp->viewer->mouseState)
          glapp->viewer->mouseMove(x, y);
        break;
      default:
        printf("? %d\n", evt.getType());
    }
  }
  else if(evt.getServiceType() == Service::Keyboard)
  {
    int x = evt.getPosition().x();
    int y = evt.getPosition().y();
    int key = evt.getSourceId();
    if (evt.isKeyDown(key))
    {
      if (key > 255)
      {
      //printf("Key %d %d\n", key, evt.getFlags());
        if (key == 262) key = KEY_UP;
        else if (key == 264) key = KEY_DOWN;
        else if (key == 261) key = KEY_LEFT;
        else if (key == 263) key = KEY_RIGHT;
        else if (key == 265) key = KEY_PAGEUP;
        else if (key == 266) key = KEY_PAGEDOWN;
        else if (key == 260) key = KEY_HOME;
        else if (key == 267) key = KEY_END;
      }
      //glapp->viewer->keyPress(key, x, y);
    }
  }
  else if(evt.getServiceType() == Service::Wand)
  {
    std::stringstream buttons;
    if (evt.isButtonDown(Event::Button1)) //Y(yellow)
      buttons << "Button1 ";
    if (evt.isButtonDown(Event::Button2)) //Circle / B(red)
      buttons << "Button2 ";
    if (evt.isButtonDown(Event::Button3)) //Cross / A(green)
      buttons << "Button3 ";
    if (evt.isButtonDown(Event::Button4)) //X(blue)
      buttons << "Button4 ";
    if (evt.isButtonDown(Event::Button5)) //L1
      buttons << "Button5 ";
    if (evt.isButtonDown(Event::Button6)) //??
      buttons << "Button6 ";
    if (evt.isButtonDown(Event::Button7)) //L2
      buttons << "Button7 ";
    if (evt.isButtonDown(Event::Button8)) //??
      buttons << "Button8 ";
    if (evt.isButtonDown(Event::Button9)) //??
      buttons << "Button9 ";
    if (evt.isButtonDown(Event::ButtonLeft ))
      buttons << "ButtonL ";
    if (evt.isButtonDown(Event::ButtonRight ))
      buttons << "ButtonR ";
    if (evt.isButtonDown(Event::ButtonUp))
      buttons << "ButtonU ";
    if (evt.isButtonDown(Event::ButtonDown))
      buttons << "ButtonD ";
    std::string buttonstr = buttons.str();
    if (buttonstr.length() > 0)
    {
       std::cout << buttonstr << " : Analogue LR: " << evt.getAxis(0) << " UD: " << evt.getAxis(1) << std::endl;
      //Clear loaded camera data on button press
      if (glapp->drawstate.globals.count("camera") > 0)
        glapp->drawstate.globals.erase("camera");
    }

    int x = evt.getPosition().x();
    int y = evt.getPosition().y();
    int key = evt.getSourceId();

    if (evt.isButtonDown(Event::Button2)) //Circle
    {
       menuOpen = true;
       printf("Menu opened\n");
    }
    else if (evt.isButtonDown(Event::Button3)) //Cross
    {
       if (menuOpen)
       {
         menuOpen = false;
         printf("Menu closed\n");
         //Load any changes to files/objects
         updateMenu();
       }
       else
       {
         //Save state in list on menu close press without menu open
         saveState();
         //Depth sort geometry?
         //glapp->aview->sort = true;
       }
    }
    else if (evt.isButtonDown(Event::Button1)) //Y
    {
       //Cycle through saved camera positions
       cameraRestore();
    }
    else if (evt.isButtonDown(Event::Button4)) //X
    {
       //Pressing this screws up audio??
    }
    else if (evt.isButtonDown(Event::Button7))
    {
       //L2 Trigger (large)
      // std::cout << "L2 Trigger " << std::endl;
      if (evt.isButtonDown(Event::ButtonLeft ))
      {
        glapp->parseCommands("zoomclip -0.01");
        //evt.setProcessed();
      }
      else if (evt.isButtonDown(Event::ButtonRight ))
      {

        glapp->parseCommands("zoomclip 0.01");
        //evt.setProcessed();
      }
      else if (evt.isButtonDown(Event::ButtonUp))
      {
         //evt.setProcessed();
      }
      else if (evt.isButtonDown(Event::ButtonDown))
      {
         //evt.setProcessed();
      }
      if (evt.isButtonDown(Event::Button5))
      {
         //Depth sort geometry
         glapp->aview->sort = true;
      }

    }
    else if (evt.isButtonDown(Event::Button5))
    {
      //L1 Trigger (small) - Multi-press to fine tune
      if (evt.isButtonDown(Event::ButtonLeft ))
      {
         glapp->parseCommands("scale all 0.95");
         //evt.setProcessed();
      }
      else if (evt.isButtonDown(Event::ButtonRight ))
      {
         glapp->parseCommands("scale all 1.05");
         //evt.setProcessed();
      }
      else if (evt.isButtonDown(Event::ButtonUp))
      {
         //Reduce eye separation
         omega::Camera* cam = Engine::instance()->getDefaultCamera();
         cam->setEyeSeparation(cam->getEyeSeparation()-0.01);
         printf("Eye-separation set to %f\n", cam->getEyeSeparation());
         //evt.setProcessed();
      }
      else if (evt.isButtonDown(Event::ButtonDown))
      {
         //Increase eye separation
         omega::Camera* cam = Engine::instance()->getDefaultCamera();
         cam->setEyeSeparation(cam->getEyeSeparation()+0.01);
         printf("Eye-separation set to %f\n", cam->getEyeSeparation());
         //evt.setProcessed();
      }
      else
      {
         //Depth sort geometry
         //glapp->aview->sort = true;
      }
    }
    else if (evt.isButtonDown(Event::ButtonUp ))
    {
        //if (GeomData::opacity > 0.0) GeomData::opacity -= 0.05;
        //glapp->redrawViewports();
    }
    else if (evt.isButtonDown(Event::ButtonDown ))
    {
        //if (GeomData::opacity < 1.0) GeomData::opacity += 0.05;
        //glapp->redrawViewports();
        glapp->parseCommands("timestep 0");
    }
    else if (evt.isButtonDown(Event::ButtonLeft ))
    {
        glapp->parseCommands("model up");
    }
    else if (evt.isButtonDown( Event::ButtonRight ))
    {
        glapp->parseCommands("model down");
    }
    else
    {
        //Grab the analog stick horizontal axis
        float analogLR = evt.getAxis(0);
        //Grab the analog stick vertical axis
        float analogUD = evt.getAxis(1);
        if (abs(analogUD) + abs(analogLR) > 0.01)
        {
           //Default is model rotate, TODO: enable timestep sweep mode via menu option
           bool sweep = glapp->drawstate.global("sweep");
           if (!sweep)
           {
               //L2 Trigger (large)
               if (abs(analogUD) > 0.02)
               {
                  std::stringstream rcmd;
                  rcmd << "rotate x " << analogUD;
                  glapp->parseCommands(rcmd.str());
               }
               if (abs(analogLR) > 0.02)
               {
                  std::stringstream rcmd;
                  rcmd << "rotate y " << analogLR;
                  glapp->parseCommands(rcmd.str());
               }
               //evt.setProcessed();
            }
            else if (abs(analogUD) > abs(analogLR))
            {
               if (analogUD > 0.02)
                 glapp->parseCommands("timestep down");
               else if (analogUD < 0.02)
                 glapp->parseCommands("timestep up");
               //evt.setProcessed();
            }
        }
    }
  }
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void LavaVuApplication::commitSharedData(SharedOStream& out)
{
   std::stringstream oss;
   if (isMaster)
   {
     for (int i=0; i < commands.size(); i++)
       oss << commands[i] << std::endl;
   }
   out << oss.str();
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void LavaVuApplication::updateSharedData(SharedIStream& in)
{
   std::string commandstr;
   in >> commandstr;

   if (!isMaster && commandstr.length())
   {
      glapp->viewer->commands.clear();
      std::stringstream iss(commandstr);
      std::string line;
      while(std::getline(iss, line))
      {
         //glapp->viewer->commands.push_back(line);
         glapp->queueCommands(line);
      }
   }
}

///////////////////////////////////////////////////////////////////////////////

//https://wiki.python.org/moin/boost.python/HowTo#SWIG_exposed_C.2B-.2B-_object_from_Python
struct PySwigObject
{
  PyObject_HEAD
  void * ptr;
  const char * desc;
};

void* extract_swig_wrapped_pointer(PyObject* obj)
{
  char thisStr[] = "this";
  //first we need to get the this attribute from the Python Object
  if (!PyObject_HasAttrString(obj, thisStr))
    return NULL;

  PyObject* thisAttr = PyObject_GetAttrString(obj, thisStr);
  if (thisAttr == NULL)
    return NULL;

  //This Python Object is a SWIG Wrapper and contains our pointer
  void* pointer = ((PySwigObject*)thisAttr)->ptr;
  Py_DECREF(thisAttr);
  return pointer;
}

LavaVuApplication* initialize(PyObject* lvswig)
{
  LavaVuApplication* vrm = new LavaVuApplication();
  //Use existing app
  if (lvswig)
  {
    LavaVu* lvapp = (LavaVu*)extract_swig_wrapped_pointer(lvswig);
    printf("Using passed LavaVu instance, %p\n", lvapp);
    vrm->glapp = lvapp;
  }

  ModuleServices::addModule(vrm);
  vrm->doInitialize(Engine::instance());

  return vrm;
}

///////////////////////////////////////////////////////////////////////////////
// Python API
#include "omega/PythonInterpreterWrapper.h"
BOOST_PYTHON_MODULE(LavaVR)
{
  // OmegaViewer
  PYAPI_REF_BASE_CLASS(LavaVuApplication)
      PYAPI_METHOD(LavaVuApplication, saveDefaultState)
      PYAPI_METHOD(LavaVuApplication, saveNewState)
      ;

  def("initialize", initialize, PYAPI_RETURN_REF);
}

