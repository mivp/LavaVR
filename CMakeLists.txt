####################################################################################################################### 
# Omega Lib build for LavaVu
#---------------------------------------------------------------------------------------------------------------------
# Copyright 2013							Monash University
# Authors:										
#  Owen Kaluza							owen.kaluza@monash.edu
#######################################################################################################################
cmake_minimum_required(VERSION 2.8.1) 
project(LavaVR)

find_package(Omegalib)

# Source files
SET( srcs
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
        LavaVu/src/tiny_obj_loader.h
        LavaVu/src/jpeg/jpge.cpp
        LavaVu/src/jpeg/jpgd.cpp
        LavaVu/src/mongoose/mongoose.c
        LavaVu/src/sqlite3/sqlite3.c
   )
    
#######################################################################################################################
# Headers
SET( headers 
        LavaVu/src/ViewerApp.h
        LavaVu/src/OpenGLViewer.h
   ) 
        
#######################################################################################################################
# Setup compile info

add_definitions(-DUSE_OMEGALIB -DUSE_ZLIB -DHAVE_GLCONTEXT -DHAVE_LIBPNG -DUSE_FONTS -DSHADER_PATH="${CMAKE_BINARY_DIR}/LavaVu/src/shaders/")
#add_definitions(-DDEBUG -g)
add_definitions(-O3)
set (CMAKE_CXX_STANDARD 11)
#add_library(common OBJECT ${srcs})

include_directories(${OMEGA_INCLUDE_DIRS})

add_executable(LavaVR ${srcs} ${headers})

target_link_libraries(LavaVR m stdc++ dl z png python2.7 ${OMEGA_LIB} ${OMEGA_TOOLKIT_LIB})



