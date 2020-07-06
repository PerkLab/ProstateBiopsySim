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

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area

    #set up slicer scene
    slicer.mrmlScene.Clear()
    scene = self.getPath("/Resources/scene.mrb")


    try:
      slicer.util.loadScene(scene)
    except RuntimeError:
      self.makeScene()


    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    ''' default code. not being used atm---------------------------------------------------------------------
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

    #
    # output volume selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Volume: ", self.outputSelector)

    #
    # threshold value
    #
    self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget.singleStep = 0.1
    self.imageThresholdSliderWidget.minimum = -100
    self.imageThresholdSliderWidget.maximum = 100
    self.imageThresholdSliderWidget.value = 0.5
    self.imageThresholdSliderWidget.setToolTip("Set threshold value for computing the output image. Voxels that have intensities lower than this value will set to zero.")
    parametersFormLayout.addRow("Image threshold", self.imageThresholdSliderWidget)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)'''

    #
    # Save button
    #
    self.saveButton = qt.QPushButton("Save Scene")
    self.saveButton.enabled = True
    parametersFormLayout.addRow(self.saveButton)

    # connections
    self.saveButton.connect('clicked(bool)', self.onApplyButton)
    #self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    #self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # function to load files from the resources folder
  def getPath(self, path):
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

    file_path = os.path.join(script_dir, path)
    return file_path

  #function to create the scene if there is no saved version
  def makeScene(self):

    US_path = self.getPath("Resources/prostate_US.nrrd")
    zone_path = self.getPath("Resources/zones.seg.nrrd")


    volumeNode = slicer.util.loadVolume(US_path)
    zoneNode = slicer.util.loadLabelVolume(zone_path)

    labelmapVolumeNode = slicer.util.getNode('zones')
    seg = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
    slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelmapVolumeNode, seg)
    seg.CreateClosedSurfaceRepresentation()
    slicer.mrmlScene.RemoveNode(labelmapVolumeNode)
    segDisplay = seg.GetDisplayNode()
    segDisplay.SetVisibility(False)

    # create and name all transforms
    ReferenceToRAS = slicer.vtkMRMLTransformNode()
    ProbeToReference = slicer.vtkMRMLTransformNode()
    ImageToProbe = slicer.vtkMRMLTransformNode()
    ProbeModelToProbe = slicer.vtkMRMLTransformNode()

    slicer.mrmlScene.AddNode(ReferenceToRAS)
    ReferenceToRAS.SetName("ReferenceToRAS")
    slicer.mrmlScene.AddNode(ProbeToReference)
    ProbeToReference.SetName("ProbeToReference")
    slicer.mrmlScene.AddNode(ImageToProbe)
    ImageToProbe.SetName("ImageToProbe")
    slicer.mrmlScene.AddNode(ProbeModelToProbe)
    ProbeModelToProbe.SetName("ProbeModelToProbe")

    # Create hierarchy
    volumeNode.SetAndObserveTransformNodeID(ImageToProbe.GetID())
    ProbeModelToProbe.SetAndObserveTransformNodeID(ProbeToReference.GetID())
    ImageToProbe.SetAndObserveTransformNodeID(ProbeToReference.GetID())
    ProbeToReference.SetAndObserveTransformNodeID(ReferenceToRAS.GetID())


  #function to load in previously saved transforms
  def loadScene(self, scenePath):
    slicer.util.loadScene(scenePath)


  #save the scene to resources to be reloaded later
  def saveScene(self):
    # Generate file name
    sceneSaveFilename = "C:/Users/cat_w/OneDrive - Queen's University/Perk Lab/USRA project 2020/ProstateBiopsySim" \
                        "/UltrasoundSimModule/Resources/saved-scene-.mrb"

    # Save scene
    if slicer.util.saveScene(sceneSaveFilename):
      logging.info("Scene saved to: {0}".format(sceneSaveFilename))
    else:
      logging.error("Scene saving failed")



  def importDicom(dicomDataDir, dicomDatabase=None, copyFiles=False):
    """ Import DICOM files from folder into Slicer database
    """
    try:
      indexer = ctk.ctkDICOMIndexer()
      assert indexer is not None
      if dicomDatabase is None:
        logging.info('Hi')
        dicomDatabase = slicer.dicomDatabase
      logging.info("hi")
      indexer.addDirectory(dicomDatabase, dicomDataDir, copyFiles)
      logging.info("hi")
      indexer.waitForImportFinished()
    except Exception as e:
      import traceback
      traceback.print_exc()
      logging.error('Failed to import DICOM folder ' + dicomDataDir)
      return False
    return True

  def onApplyButton(self):
    self.saveScene()

    '''logic = UltrasoundSimModuleLogic()
      enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
      imageThreshold = self.imageThresholdSliderWidget.value
      logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode(), imageThreshold, enableScreenshotsFlag)
  '''


  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()



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
