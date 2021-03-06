####################################################################################################################### 
# LavaVu module for OmegaLib
#---------------------------------------------------------------------------------------------------------------------
# Copyright 2016						Monash University
# Authors:										
#  Owen Kaluza							owen.kaluza@monash.edu
#######################################################################################################################

#request_dependency(omegalib)
cmake_minimum_required(VERSION 2.8.1) 
find_package(Omegalib)

set (CMAKE_CXX_STANDARD 11)

# Set the module name here
SET(MODULE_NAME LavaVR)

include_directories(${OMEGA_INCLUDE_DIRS})
link_directories(LavaVu/lavavu)

# Set module name and source files here
add_library(${MODULE_NAME} MODULE 
        LavaVR.cpp
        )

# Set the module library dependencies here
target_link_libraries(${MODULE_NAME}
        m
        stdc++
        dl
        z
        png
        python2.7
        ${OMEGA_LIB}
        ${OMEGA_TOOLKIT_LIB}
        LavaVu
        )

#Just use the LavaVu build in LavaVu dir as is
#Enable/disable debug build
set (DEBUG 0)
#set (DEBUG 1)
if (${DEBUG})
#  set (LVFLAGS "CONFIG=debug LIBPNG=0 TIFF=1 VIDEO=0 X11=1")
  add_definitions(-DDEBUG -g)
else()
#  set (LVFLAGS "LIBPNG=0 TIFF=1 VIDEO=0 X11=1")
  add_definitions(-DNDEBUG -O3)
endif()

#add_custom_target(
#   LavaVu
#   COMMAND $(MAKE) ${LVFLAGS} SHADER_PATH="${CMAKE_BINARY_DIR}/LavaVu/src/shaders/"
#   WORKING_DIRECTORY LavaVu
#)

#add_dependencies(LavaVR LavaVu)

#######################################################################################################################
# Setup compile info

add_definitions(-Wno-deprecated-declarations)
#add_library(common OBJECT ${srcs})

#------------------------------------------------------------------------------
# DO NOT MODIFY ANYTHING BELOW AFTER THIS LINE
set_target_properties(${MODULE_NAME} PROPERTIES PREFIX "")
if(WIN32)
        set_target_properties(${MODULE_NAME} PROPERTIES FOLDER modules SUFFIX ".pyd")
endif()

