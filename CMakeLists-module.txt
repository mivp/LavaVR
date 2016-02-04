#request_dependency(cyclops)

# The following line makes sure the cyclops module is installed.
#if(TARGET cyclops)

# Set the module name here
SET(MODULE_NAME LavaVR)

# Set module name and source files here
add_library(${MODULE_NAME} MODULE 
        LavaVR.cpp
        LavaVu/src/LavaVu.cpp
        LavaVu/src/Server.cpp
        LavaVu/src/InteractiveViewer.cpp
        LavaVu/src/OpenGLViewer.cpp
        LavaVu/src/base64.cpp
        LavaVu/src/ColourMap.cpp
        LavaVu/src/Colours.cpp
        LavaVu/src/DrawingObject.cpp
        LavaVu/src/Extensions.cpp
        LavaVu/src/FontSans.cpp
        LavaVu/src/Geometry.cpp
        LavaVu/src/GraphicsUtil.cpp
        LavaVu/src/Util.cpp
        LavaVu/src/Lines.cpp
        LavaVu/src/Model.cpp
        LavaVu/src/Points.cpp
        LavaVu/src/QuadSurfaces.cpp
        LavaVu/src/Shaders.cpp
        LavaVu/src/Shapes.cpp
        LavaVu/src/Tracers.cpp
        LavaVu/src/TriSurfaces.cpp
        LavaVu/src/Vectors.cpp
        LavaVu/src/Volumes.cpp
        LavaVu/src/VideoEncoder.cpp
        LavaVu/src/View.cpp
        LavaVu/src/Win.cpp
        LavaVu/src/tiny_obj_loader.cc
        LavaVu/src/jpeg/jpge.cpp
        LavaVu/src/jpeg/jpgd.cpp
        LavaVu/src/json.cpp
        LavaVu/src/mongoose/mongoose.c
        LavaVu/src/sqlite3/src/sqlite3.c
        )

# Set the module library dependencies here
target_link_libraries(${MODULE_NAME}
        dl
        z
        png
        omega 
        omegaToolkit 
        )

#######################################################################################################################
# Setup compile info

add_definitions(-DUSE_OMEGALIB -DUSE_ZLIB -DHAVE_LIBPNG -DUSE_FONTS -DSHADER_PATH="LavaVu/src/shaders/")
add_definitions(-DDEBUG -g)
#add_definitions(-O3)

#------------------------------------------------------------------------------
# DO NOT MODIFY ANYTHING BELOW AFTER THIS LINE
set_target_properties(${MODULE_NAME} PROPERTIES PREFIX "")
if(WIN32)
        set_target_properties(${MODULE_NAME} PROPERTIES FOLDER modules SUFFIX ".pyd")
endif()

