# LSystemInstanceNode.py
#   Produces random locations to be used with the Maya instancer node.

import sys
import random
import os

import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
import maya.mel as mel

import LSystem


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

def changeAttrCallback(msg, plug, otherPlug, clientData):
    print("TEST")
    if (not(msg & OpenMaya.MNodeMessage.kAttributeSet) and
		not(msg & OpenMaya.MNodeMessage.kIncomingDirection)):
		return

    if (plug == clientData.inIsFromFile):
        ifF = plug.asBool()
        clientData.setFileBool(ifF)
        print("file")

    if (plug == clientData.inGrammar):
        g = plug.asString()
        clientData.setGrammar(str(g))
        print("gram")


# Define the name of the node
kPluginNodeTypeName = "LSystemInstanceNode"

# Give the node a unique ID. Make sure this ID is different from all of your
# other nodes!
LSystemInstanceNodeId = OpenMaya.MTypeId(0x8705)

# Node definition
class LSystemInstanceNode(OpenMayaMPx.MPxNode):
    # Declare class variables:
    inIterations = OpenMaya.MObject()
    inAngle = OpenMaya.MObject()
    inStep = OpenMaya.MObject()
    
    inGrammar = OpenMaya.MObject()
    inIsFromFile = OpenMaya.MObject()
    
    outBranches = OpenMaya.MObject()
    outFlowers = OpenMaya.MObject()

    nameID = 1
    menuPath = ""
    dirPath = ""
    
    # constructor
    def __init__(self):
        print("nodeInited")
        OpenMayaMPx.MPxNode.__init__(self)

    def postConstructor(self):
        thisNode = self.thisMObject();
        OpenMaya.MNodeMessage.addAttributeChangedCallback(thisNode, changeAttrCallback, self)
        print("TESTING")

    # compute
    def compute(self,plug,data):
        # This node takes in three floats for max position (X,Y,Z), three floats 
        # for min position (X,Y,Z), and the number of random points to be generated. 
        # It outputs an MFnArrayAttrsData object containing the random points. 
        if (plug == LSystemInstanceNode.outBranches or plug == LSystemInstanceNode.outFlowers):
            # Read the inputs
            print("Reading inputs")
            itersO = data.inputValue(self.inIterations)
            iters = itersO.asInt()

            anlgeO = data.inputValue(self.inAngle)
            angle = anlgeO.asFloat()
            self.lsystem.setDefaultAngle(angle)

            stepO = data.inputValue(self.inStep)
            step = stepO.asFloat()
            self.lsystem.setDefaultStep(step)
            
            # Grammar is handled in a callback

            # TODO swig call branches and flowers vectors
            branches = LSystem.VectorPyBranch()
            flowers = LSystem.VectorPyBranch()
            self.lsystem.processPy(iters, branches, flowers)

            # Branch Output
            print("Setting up outputs")
            branchPointsHandle = data.outputValue(self.outBranches) #MFnMeshData
            branchPointsAAD = OpenMaya.MFnArrayAttrsData()          #MFnArrayAttrsData
            branchOutputPointsData = branchPointsAAD.create()       #MObject

            # Creating vectors for the array data
            branchIdArray = branchPointsAAD.doubleArray("id")
            branchPositionArray = branchPointsAAD.vectorArray("position")
            branchScaleArray = branchPointsAAD.vectorArray("scale")
            branchDirectionArray = branchPointsAAD.vectorArray("aimDirection")

            # And filling them
            for n in range(branches.size() / 2): # TODO array length
                branchIdArray.append(n)

                start = branches[2 * n]
                end = branches[2 * n + 1]
                
                xPos = (start[0] + end[0]) / 2.0
                zPos = (start[1] + end[1]) / 2.0
                yPos = (start[2] + end[2]) / 2.0

                xDir = end[0] - start[0]
                zDir = end[1] - start[1] # swapped
                yDir = end[2] - start[2]

                direction = OpenMaya.MVector(xDir, yDir, zDir)
                length = direction.length()
                direction.normalize()

                branchPositionArray.append(OpenMaya.MVector(xPos, yPos, zPos))
                branchScaleArray.append(OpenMaya.MVector(length, 0.25, 0.25))
                branchDirectionArray.append(direction)

            branchPointsHandle.setMObject(branchOutputPointsData)

            # Flower Output
            print("Setting up outputs")
            flowerPointsHandle = data.outputValue(self.outFlowers) #MFnMeshData
            flowerPointsAAD = OpenMaya.MFnArrayAttrsData()         #MFnArrayAttrsData
            flowerOutputPointsData = flowerPointsAAD.create()      #MObject

            # Creating vectors for the array data
            flowerIdArray = flowerPointsAAD.doubleArray("id")
            flowerPositionArray = flowerPointsAAD.vectorArray("position")
            flowerScaleArray = flowerPointsAAD.vectorArray("scale")
            flowerDirectionArray = flowerPointsAAD.vectorArray("aimDirection")

            # And filling them
            for n in range(flowers.size()): # TODO array length
                flowerIdArray.append(n)

                p = flowers[n]
                
                flowerPositionArray.append(OpenMaya.MVector(p[0], p[2], p[1]))
                flowerScaleArray.append(OpenMaya.MVector(0.25, 0.25, 0.25))
                flowerDirectionArray.append(OpenMaya.MVector(0.0, 0.0, 1.0))

            flowerPointsHandle.setMObject(flowerOutputPointsData)

        data.setClean(plug)
        print("Finished LSystemInstanceNode generation")

    def initLSystem(self):
        self.lsystem = LSystem.LSystem()

    def setFileBool(self, b):
        self.fromFile = b

    def setGrammar(self, grammarProgram):
        if self.fromFile == True:
            self.lsystem.loadProgram(str(LSystemInstanceNode.dirPath + grammarProgram));
        else:
        	self.lsystem.loadProgramFromString(grammarProgram);

    
# initializer
def nodeInitializer():
    tAttr = OpenMaya.MFnTypedAttribute()
    nAttr = OpenMaya.MFnNumericAttribute()
    print("initializingStart")

    # initialize the input attributes
    LSystemInstanceNode.inIterations = nAttr.create("iterations", "it", OpenMaya.MFnNumericData.kInt, 1)
    MAKE_INPUT(nAttr)
    nAttr.setMin(1)
    
    LSystemInstanceNode.inStep = nAttr.create("step", "st", OpenMaya.MFnNumericData.kFloat, 1.0)
    MAKE_INPUT(nAttr)
    nAttr.setMin(0.0)
    
    LSystemInstanceNode.inAngle = nAttr.create("angle", "an", OpenMaya.MFnNumericData.kFloat, 22.5)
    MAKE_INPUT(nAttr)
    nAttr.setMin(0.0)
    nAttr.setMax(360.0)

    LSystemInstanceNode.inGrammar = tAttr.create("grammar", "gr", OpenMaya.MFnData.kString)
    MAKE_INPUT(tAttr)

    LSystemInstanceNode.inIsFromFile = nAttr.create("fromFile", "fi", OpenMaya.MFnNumericData.kBoolean, 0)
    MAKE_INPUT(nAttr)

    # initialize the output attributes
    LSystemInstanceNode.outBranches = tAttr.create("outBranches", "ob", OpenMaya.MFnArrayAttrsData.kDynArrayAttrs)
    MAKE_OUTPUT(tAttr)
    
    LSystemInstanceNode.outFlowers = tAttr.create("outFlowers", "of", OpenMaya.MFnArrayAttrsData.kDynArrayAttrs)
    MAKE_OUTPUT(tAttr)
    print("initializingEnd")

    try:
        # add the attributes to the node and set up the
        LSystemInstanceNode.addAttribute(LSystemInstanceNode.inIterations)
        LSystemInstanceNode.addAttribute(LSystemInstanceNode.inStep)
        LSystemInstanceNode.addAttribute(LSystemInstanceNode.inAngle)

        LSystemInstanceNode.addAttribute(LSystemInstanceNode.inGrammar)
        LSystemInstanceNode.addAttribute(LSystemInstanceNode.inIsFromFile)

        LSystemInstanceNode.addAttribute(LSystemInstanceNode.outBranches)
        LSystemInstanceNode.addAttribute(LSystemInstanceNode.outFlowers)

        # Affects for branches
        LSystemInstanceNode.attributeAffects(LSystemInstanceNode.inIterations, LSystemInstanceNode.outBranches)
        LSystemInstanceNode.attributeAffects(LSystemInstanceNode.inStep,  LSystemInstanceNode.outBranches)
        LSystemInstanceNode.attributeAffects(LSystemInstanceNode.inAngle,  LSystemInstanceNode.outBranches)
        LSystemInstanceNode.attributeAffects(LSystemInstanceNode.inGrammar,  LSystemInstanceNode.outBranches)

        # Affects for flowers
        LSystemInstanceNode.attributeAffects(LSystemInstanceNode.inIterations, LSystemInstanceNode.outFlowers)
        LSystemInstanceNode.attributeAffects(LSystemInstanceNode.inStep,  LSystemInstanceNode.outFlowers)
        LSystemInstanceNode.attributeAffects(LSystemInstanceNode.inAngle,  LSystemInstanceNode.outFlowers)
        LSystemInstanceNode.attributeAffects(LSystemInstanceNode.inGrammar,  LSystemInstanceNode.outFlowers)
        print "Initialization!\n"

    except:
        sys.stderr.write( ("Failed to create attributes of %s node\n", kPluginNodeTypeName) )

# creator
def nodeCreator():
    print("creating")
    lSys = LSystemInstanceNode()
    lSys.initLSystem()
    lSys.setFileBool(False)
    return OpenMayaMPx.asMPxPtr( lSys )

# initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerNode( kPluginNodeTypeName, LSystemInstanceNodeId, nodeCreator, nodeInitializer )
    except:
        sys.stderr.write( "Failed to register node: %s\n" % kPluginNodeTypeName )

    # Initialize MEL script
    filePath = cmds.pluginInfo('LSystemInstanceNode.py', query=True, path=True )
    dirP = str(os.path.dirname(filePath))
    melPath = dirP + "/LSystemInstanceNodeDialog.mel"
    mel.eval("source \"" + melPath + "\";")

    # Setting up plants directory for filereading
    LSystemInstanceNode.dirPath = dirP + "/plants/"
    print(LSystemInstanceNode.dirPath)
	
    # Allow popup to be accessed from Create menu
    mel.eval("ModCreateMenu mainCreateMenu;") # acknowledging the menu first to avoid errors
    LSystemInstanceNode.menuPath = cmds.menuItem(label="Open LSystemInstance Dialog", p="mainCreateMenu", c='mel.eval(\"makeLSystemInstanceNodeWindow();\")')

# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( LSystemInstanceNodeId )
    except:
        sys.stderr.write( "Failed to unregister node: %s\n" % kPluginNodeTypeName )

    # Remove popup from Create menu
    cmds.deleteUI(LSystemInstanceNode.menuPath)
