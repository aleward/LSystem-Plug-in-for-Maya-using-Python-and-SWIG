# randomNode.py
#   Produces random locations to be used with the Maya instancer node.

import sys
import random
import os

import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
import maya.mel as mel

# Useful functions for declaring attributes as inputs or outputs.
def MAKE_INPUT(attr):
    attr.setKeyable(True)
    attr.setStorable(True)
    attr.setReadable(True)
    attr.setWritable(True)
def MAKE_OUTPUT(attr):
    attr.setKeyable(False)
    attr.setStorable(False)
    attr.setReadable(True)
    attr.setWritable(False)

# Define the name of the node
kPluginNodeTypeName = "randomNode"

# Give the node a unique ID. Make sure this ID is different from all of your
# other nodes!
randomNodeId = OpenMaya.MTypeId(0x8704)

# Node definition
class randomNode(OpenMayaMPx.MPxNode):
    # Declare class variables:
    inNumPoints = OpenMaya.MObject()

    inMinBound = OpenMaya.MObject()
    minBX = OpenMaya.MObject()
    minBY = OpenMaya.MObject()
    minBZ = OpenMaya.MObject()

    inMaxBound = OpenMaya.MObject()
    maxBX = OpenMaya.MObject()
    maxBY = OpenMaya.MObject()
    maxBZ = OpenMaya.MObject()
    
    outPoints = OpenMaya.MObject()
    nameID = 1
    menuPath = ""
    
    # constructor
    def __init__(self):
        print("nodeInited")
        OpenMayaMPx.MPxNode.__init__(self)

    # compute
    def compute(self,plug,data):
        # This node takes in three floats for max position (X,Y,Z), three floats 
        # for min position (X,Y,Z), and the number of random points to be generated. 
        # It outputs an MFnArrayAttrsData object containing the random points. 
        if (plug == randomNode.outPoints):
            # Read the inputs
            print("Reading inputs")
            num = data.inputValue(self.inNumPoints)
            numP = num.asInt()

            minX = data.inputValue(self.minBX)
            minY = data.inputValue(self.minBY)
            minZ = data.inputValue(self.minBZ)
            
            maxX = data.inputValue(self.maxBX)
            maxY = data.inputValue(self.maxBY)
            maxZ = data.inputValue(self.maxBZ)

            # Output
            print("Setting up outputs")
            pointsHandle = data.outputValue(self.outPoints) #MFnMeshData
            pointsAAD = OpenMaya.MFnArrayAttrsData()                #MFnArrayAttrsData
            outputPointsData = pointsAAD.create()                   #MObject

            # Creating vectors for the array data
            positionArray = pointsAAD.vectorArray("position")
            idArray = pointsAAD.doubleArray("id")

            # And filling them
            for n in range(numP):
                xVal = random.uniform(minX.asFloat(), maxX.asFloat())
                yVal = random.uniform(minY.asFloat(), maxY.asFloat())
                zVal = random.uniform(minZ.asFloat(), maxZ.asFloat())

                positionArray.append(OpenMaya.MVector(xVal, yVal, zVal))
                idArray.append(n)

            pointsHandle.setMObject(outputPointsData)

        data.setClean(plug)
        print("Finished randomNode generation")
    
# initializer
def nodeInitializer():
    tAttr = OpenMaya.MFnTypedAttribute()
    nAttr = OpenMaya.MFnNumericAttribute()
    print("initializingStart")

    # initialize the input attributes
    randomNode.inNumPoints = nAttr.create("numberOfPoints", "nu", OpenMaya.MFnNumericData.kInt, 1)
    MAKE_INPUT(nAttr)
    nAttr.setMin(0)
    
    # Minimum bound
    randomNode.minBX = nAttr.create("minimumBoundX", "bx", OpenMaya.MFnNumericData.kFloat, -5.0)
    MAKE_INPUT(nAttr)

    randomNode.minBY = nAttr.create("minimumBoundY", "by", OpenMaya.MFnNumericData.kFloat, -5.0)
    MAKE_INPUT(nAttr)

    randomNode.minBZ = nAttr.create("minimumBoundZ", "bz", OpenMaya.MFnNumericData.kFloat, -5.0)
    MAKE_INPUT(nAttr)

    randomNode.inMinBound = nAttr.create("minimumBound", "b", randomNode.minBX, randomNode.minBY, randomNode.minBZ)
    MAKE_INPUT(nAttr)

    # Maximum bound
    randomNode.maxBX = nAttr.create("maximumBoundX", "xx", OpenMaya.MFnNumericData.kFloat, 5.0)
    MAKE_INPUT(nAttr)

    randomNode.maxBY = nAttr.create("maximumBoundY", "xy", OpenMaya.MFnNumericData.kFloat, 5.0)
    MAKE_INPUT(nAttr)
    
    randomNode.maxBZ = nAttr.create("maximumBoundZ", "xz", OpenMaya.MFnNumericData.kFloat, 5.0)
    MAKE_INPUT(nAttr)

    randomNode.inMaxBound = nAttr.create("maximumBound", "x", randomNode.maxBX, randomNode.maxBY, randomNode.maxBZ)
    MAKE_INPUT(nAttr)

    # initialize the output attributes
    randomNode.outPoints = tAttr.create("outPoints", "op", OpenMaya.MFnArrayAttrsData.kDynArrayAttrs)
    MAKE_OUTPUT(tAttr)
    print("initializingEnd")

    try:
        # add the attributes to the node and set up the
        randomNode.addAttribute(randomNode.inNumPoints)
        randomNode.addAttribute(randomNode.inMinBound)
        randomNode.addAttribute(randomNode.inMaxBound)
        randomNode.addAttribute(randomNode.outPoints)

        randomNode.attributeAffects(randomNode.inNumPoints, randomNode.outPoints)
        randomNode.attributeAffects(randomNode.inMinBound, randomNode.outPoints)
        randomNode.attributeAffects(randomNode.inMaxBound, randomNode.outPoints)
        print "Initialization!\n"

    except:
        sys.stderr.write( ("Failed to create attributes of %s node\n", kPluginNodeTypeName) )

# creator
def nodeCreator():
    print("creating")
    return OpenMayaMPx.asMPxPtr( randomNode() )

# initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerNode( kPluginNodeTypeName, randomNodeId, nodeCreator, nodeInitializer )
    except:
        sys.stderr.write( "Failed to register node: %s\n" % kPluginNodeTypeName )

    # Initialize MEL script
    filePath = cmds.pluginInfo('randomNode.py', query=True, path=True )
    melPath = str(os.path.dirname(filePath)) + "/RandomNodeDialog.mel"
    mel.eval("source \"" + melPath + "\";")
	
    # Allow popup to be accessed from Create menu
    mel.eval("ModCreateMenu mainCreateMenu;") # acknowledging the menu first to avoid errors
    randomNode.menuPath = cmds.menuItem(label="Open Random Node Dialog", p="mainCreateMenu", c='mel.eval(\"makeRandomNodeWindow();\")')

# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( randomNodeId )
    except:
        sys.stderr.write( "Failed to unregister node: %s\n" % kPluginNodeTypeName )

    # Remove popup from Create menu
    cmds.deleteUI(randomNode.menuPath)
