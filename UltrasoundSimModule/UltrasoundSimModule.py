import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# UltrasoundSimModule
#

class UltrasoundSimModule(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Ultrasound Simulator" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# UltrasoundSimModuleWidget
#

class UltrasoundSimModuleWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def init(self, parent):
    ScriptedLoadableModuleWidget.__init__(self, parent)

    #self.logic = SingleSliceSegmentationLogic()

    # Members
    self.parameterSetNode = None
    self.ui = None

    # Shortcuts
    #self.shortcutDown = qt.QShortcut(slicer.util.mainWindow())
    #self.shortcutDown.setKey(qt.QKeySequence("down"))
    self.shortcutUp = qt.QShortcut(slicer.util.mainWindow())
    self.shortcutUp.setKey(qt.QKeySequence(qt.Key_Up))
    self.shortcutRight = qt.QShortcut(slicer.util.mainWindow())
    self.shortcutRight.setKey(qt.QKeySequence(qt.Key_Right))
    self.shortcutLeft = qt.QShortcut(slicer.util.mainWindow())
    self.shortcutLeft.setKey(qt.QKeySequence(qt.Key_Left))

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/UltrasoundSimModule.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    #to choose the input TRUS.
    self.ui.inputTRUSSelector.setMRMLScene(slicer.mrmlScene)

    #connect buttons
    self.ui.upButton.connect('clicked(bool)', self.onArrowButton)
    self.ui.downButton.connect('clicked(bool)', self.onArrowButton)
    self.ui.rightButton.connect('clicked(bool)', self.onArrowButton)
    self.ui.saveButton.connect('clicked(bool)', self.onSaveButton)

    #set up slicer scene
    slicer.mrmlScene.Clear()
    scene = self.resourcePath('scene.mrb')
    slicer.util.loadScene(scene)
    self.makeScene()


  #function to create the scene
  def makeScene(self):

    US_path = self.resourcePath('prostate_US.nrrd')
    zone_path = self.resourcePath('zones.seg.nrrd')
    probe_path = self.resourcePath('probe_v01.stl')

    #load US and zonal anatomy
    slicer.util.loadVolume(US_path)
    zoneNode = slicer.util.loadLabelVolume(zone_path)
    probeModel = slicer.util.loadModel(probe_path)

    labelmapVolumeNode = zoneNode
    seg = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
    slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelmapVolumeNode, seg)
    seg.CreateClosedSurfaceRepresentation()
    slicer.mrmlScene.RemoveNode(labelmapVolumeNode)
    segDisplay = seg.GetDisplayNode()
    segDisplay.SetVisibility(False)

    # create and name all transforms
    ReferenceToRAS = slicer.util.getNode("ReferenceToRAS")
    ProbeToReference = slicer.vtkMRMLTransformNode()
    ImageToProbe = slicer.util.getNode("ImageToProbe")
    ProbeModelToProbe = slicer.util.getNode("ProbeModelToProbe")

    slicer.mrmlScene.AddNode(ProbeToReference)
    ProbeToReference.SetName("ProbeToReference")

    # Create hierarchy
    probeModel.SetAndObserveTransformNodeID(ProbeModelToProbe.GetID())
    ProbeModelToProbe.SetAndObserveTransformNodeID(ProbeToReference.GetID())
    ImageToProbe.SetAndObserveTransformNodeID(ProbeToReference.GetID())
    ProbeToReference.SetAndObserveTransformNodeID(ReferenceToRAS.GetID())

    # Clean up extra camera nodes
    camera = slicer.util.getNode('Default Scene Camera')
    slicer.mrmlScene.RemoveNode(camera)


  def enter(self):
    """Runs whenever the module is reopened"""
    logging.info('Entered module widget')

    self.shortcutUp = qt.QShortcut(slicer.util.mainWindow())
    self.shortcutUp.setKey(qt.QKeySequence(qt.Key_Up))

    # Update UI
    self.connectKeyboardShortcuts()

  #connect arrow keys to transform node
  def connectKeyboardShortcuts(self):
    self.shortcutUp.connect('activated()', self.onArrowButton)
    #self.shortcutD.connect('activated()', self.onClearButton)
    #self.shortcutC.connect('activated()', self.onCaptureButton)


#TRYING TO FIGURE THIS OUT
  def onArrowButton(self):
    transform = slicer.util.getNode('ProbeToReference')
    logging.info('up pressed')

    #trying to connect buttons to ProbeToReference transform...


  #save the scene to resources to be reloaded later
  def onSaveButton(self):

    #clean up nodes that do not need to be saved
    delete = [slicer.util.getNode('prostate_US'), slicer.util.getNode('ProbeToReference'),
              slicer.util.getNode('Segmentation'),
              slicer.util.getNode('probe_v01')]

    for i in delete:
      slicer.mrmlScene.RemoveNode(i)

    # Generate file name
    sceneSaveFilename = "C:/Users/cat_w/OneDrive - Queen's University/Perk Lab/USRA project 2020/ProstateBiopsySim" \
                        "/UltrasoundSimModule/Resources/scene.mrb"

    # Save scene
    if slicer.util.saveScene(sceneSaveFilename):
      logging.info("Scene saved to: {0}".format(sceneSaveFilename))
    else:
      logging.error("Scene saving failed")



  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()


'''-----end of edited code. below is default--------------------------------------------------------------------'''
#
# UltrasoundSimModuleLogic
#

class UltrasoundSimModuleLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    # Capture screenshot
    if enableScreenshots:
      self.takeScreenshot('UltrasoundSimModuleTest-Start','MyScreenshot',-1)

    logging.info('Processing completed')

    return True


class UltrasoundSimModuleTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_UltrasoundSimModule1()

  def test_UltrasoundSimModule1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import SampleData
    SampleData.downloadFromURL(
      nodeNames='FA',
      fileNames='FA.nrrd',
      uris='http://slicer.kitware.com/midas3/download?items=5767',
      checksums='SHA256:12d17fba4f2e1f1a843f0757366f28c3f3e1a8bb38836f0de2a32bb1cd476560')
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = UltrasoundSimModuleLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
