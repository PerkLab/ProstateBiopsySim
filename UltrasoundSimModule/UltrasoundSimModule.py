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

  IMAGE_TO_PROBE = "ImageToProbe"
  PROBE_TO_REFERENCE = "ProbeToReference"
  PROBEMODEL_TO_PROBE = 'ProbeModelToProbe'
  ROTATED_TO_PROBEMODEL = "RotatedToProbeModel"

  def init(self, parent):
    ScriptedLoadableModuleWidget.__init__(self, parent)

    #self.logic = SingleSliceSegmentationLogic()

    # Members
    self.ui = None


  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/UltrasoundSimModule.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    #to choose the input TRUS.
    #self.ui.inputTRUSSelector.setMRMLScene(slicer.mrmlScene)
    self.ui.ComboBox.currentIndexChanged.connect(self.makeScene)

    #connect buttons
    #self.ui.upButton.connect('clicked(bool)', lambda: self.onUpDownArrowButton("up"))
   # self.ui.downButton.connect('clicked(bool)', lambda: self.onUpDownArrowButton("down"))
    self.ui.rightButton.connect('clicked(bool)', lambda: self.onRightLeftArrowButton("right"))
    self.ui.leftButton.connect('clicked(bool)', lambda: self.onRightLeftArrowButton("left"))
    self.ui.saveButton.connect('clicked(bool)', self.onSaveButton)
    self.ui.Zones.connect('toggled(bool)', self.showZones)
    #self.ui.PZone.connect('clicked(bool)', self.onPZClick)
    self.ui.zoneSelect.currentIndexChanged.connect(self.identifyZone)

    self.shortcutUp = qt.QShortcut(slicer.util.mainWindow())
    self.shortcutUp.setKey(qt.QKeySequence("Up"))
    self.shortcutDown = qt.QShortcut(slicer.util.mainWindow())
    self.shortcutDown.setKey(qt.QKeySequence("Down"))
    self.shortcutRight = qt.QShortcut(slicer.util.mainWindow())
    self.shortcutRight.setKey(qt.QKeySequence("Right"))
    self.shortcutLeft = qt.QShortcut(slicer.util.mainWindow())
    self.shortcutLeft.setKey(qt.QKeySequence("Left"))
    self.connectKeyboardShortcuts()

  #custom layout to show 3D view and yellow slice
  def splitSliceViewer(self):

    customLayout = """
    <layout type="horizontal" split="true">
      <item>
       <view class="vtkMRMLViewNode" singletontag="1">
         <property name="viewlabel" action="default">1</property>
       </view>
      </item>
      <item>
       <view class="vtkMRMLSliceNode" singletontag="Yellow">
        <property name="orientation" action="default">Sagittal</property>
        <property name="viewlabel" action="default">Y</property>
        <property name="viewcolor" action="default">#EDD54C</property>
       </view>
      </item>
    </layout>
    """

    # Built-in layout IDs are all below 100, so you can choose any large random number
    # for your custom layout ID.
    customLayoutId = 501

    layoutManager = slicer.app.layoutManager()
    layoutManager.layoutLogic().GetLayoutNode().AddLayoutDescription(customLayoutId, customLayout)

    # Switch to the new custom layout
    layoutManager.setLayout(customLayoutId)

  #function to create the scene
  def makeScene(self):

    # set up slicer scene
    slicer.mrmlScene.Clear()
    patient = self.ui.ComboBox.currentIndex

    #only set up the scene if a patient is selected
    if patient != 0:
      scene = self.resourcePath('scene'+ str(patient) + '.mrb')
      slicer.util.loadScene(scene)

      TRUSVolume = slicer.mrmlScene.GetFirstNodeByName("TRUS")
      probeModel = slicer.mrmlScene.GetFirstNodeByName("probe_v01")
      zoneNode = slicer.mrmlScene.GetFirstNodeByName("Segmentation")
      self.splitSliceViewer()  # get the yellow slice

      #load TRUS and probe
      if TRUSVolume is None:
        US_path = self.resourcePath('registered_zones/Patient_' + str(patient) + '/TRUS.nrrd')
        slicer.util.loadVolume(US_path)
      if probeModel is None:
        probe_path = self.resourcePath('probe_v01.stl')
        probeModel = slicer.util.loadModel(probe_path)
      #load zone segmentation
      if zoneNode is None:
        zone_path = self.resourcePath('registered_zones/Patient_' + str(patient) + '/Zones.seg.nrrd')
        zoneNode = slicer.util.loadLabelVolume(zone_path)

        labelmapVolumeNode = zoneNode
        seg = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelmapVolumeNode, seg)
        seg.CreateClosedSurfaceRepresentation()
        slicer.mrmlScene.RemoveNode(labelmapVolumeNode)
        segDisplay = seg.GetDisplayNode()
        segDisplay.SetVisibility(False)

      # create and name all transforms
      ReferenceToRAS =  slicer.mrmlScene.GetFirstNodeByName("ReferenceToRAS")
      ProbeToReference =  slicer.mrmlScene.GetFirstNodeByName(self.PROBE_TO_REFERENCE)
      SliceToImage =  slicer.mrmlScene.GetFirstNodeByName("SliceToImage")
      ProbeModelToProbe =  slicer.mrmlScene.GetFirstNodeByName(self.PROBEMODEL_TO_PROBE)
      RotatedToProbeModel = slicer.mrmlScene.GetFirstNodeByName(self.ROTATED_TO_PROBEMODEL)
      ImageToProbe = slicer.mrmlScene.GetFirstNodeByName(self.IMAGE_TO_PROBE)

      if RotatedToProbeModel is None:
        RotatedToProbeModel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode", self.ROTATED_TO_PROBEMODEL)
      if ProbeModelToProbe is None:
        ProbeModelToProbe = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode", self.PROBEMODEL_TO_PROBE)
      if SliceToImage is None:
        SliceToImage = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode", "SliceToImage")
      if ReferenceToRAS is None:
        ReferenceToRAS = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode", "ReferenceToRAS")
      if ProbeToReference is None:
        ProbeToReference = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode", self.PROBE_TO_REFERENCE)
      if ImageToProbe is None:
        ImageToProbe = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode", self.IMAGE_TO_PROBE)

      # Create hierarchy
      probeModel.SetAndObserveTransformNodeID(RotatedToProbeModel.GetID())
      ProbeModelToProbe.SetAndObserveTransformNodeID(ProbeToReference.GetID())
      SliceToImage.SetAndObserveTransformNodeID(ImageToProbe.GetID())
      ProbeToReference.SetAndObserveTransformNodeID(ReferenceToRAS.GetID())
      RotatedToProbeModel.SetAndObserveTransformNodeID(ProbeModelToProbe.GetID())
      ImageToProbe.SetAndObserveTransformNodeID(ProbeToReference.GetID())

      # Clean up extra camera nodes
      for i in range(3):
        camera = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLCameraNode')
        slicer.mrmlScene.RemoveNode(camera)


  def enter(self):
    """Runs whenever the module is reopened"""
    logging.info('Entered module')
    self.connectKeyboardShortcuts()
    #self.ui.ComboBox.currentIndexChanged.connect(makeScene())

  #connect arrow keys to transform node. ONLY WORKS WHEN SLICER RESTARTS
  def connectKeyboardShortcuts(self):
    self.shortcutUp.connect('activated()', lambda: self.onUpDownArrowButton("up"))
    self.shortcutDown.connect('activated()', lambda : self.onUpDownArrowButton("down"))
    self.shortcutRight.connect('activated()', lambda : self.onRightLeftArrowButton("right"))
    self.shortcutLeft.connect('activated()', lambda: self.onRightLeftArrowButton("left"))
    # keyboard shortcuts for arrow keys

  #show and hide zones based on check box
  def showZones(self):
    checked = self.ui.Zones.isChecked()
    zoneNode = slicer.mrmlScene.GetFirstNodeByName("Segmentation")
    segDisplay = zoneNode.GetDisplayNode()

    if checked:
      segDisplay.SetVisibility(True)
    else:
      segDisplay.SetVisibility(False)

  #NEXT. GET FIDUCIALS WORKING
  def identifyZone(self):
    zones = ["Peripheral", "Central", "Anterior", "Transitional"]
    index = self.ui.zoneSelect.currentIndex
    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
    fiducialNode = slicer.vtkMRMLMarkupsFiducialNode()
    slicer.mrmlScene.AddNode(fiducialNode)
    fiducialNode.CreateDefaultDisplayNodes()
    fiducialNode.SetName(zones[index-1])
    selectionNode.SetActivePlaceNodeID(fiducialNode.GetID())
    interactionNode.SetCurrentInteractionMode(interactionNode.Place)

#FOR SCORING LATER. Draw ROI around each segment.
  def bindSegments(self):
    segmentationNode = slicer.mrmlScene.GetFirstNodeByName('Segmentation')

    # Compute bounding boxes
    import SegmentStatistics
    segStatLogic = SegmentStatistics.SegmentStatisticsLogic()
    segStatLogic.getParameterNode().SetParameter("Segmentation", segmentationNode.GetID())
    segStatLogic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.obb_origin_ras.enabled", str(True))
    segStatLogic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.obb_diameter_mm.enabled", str(True))
    segStatLogic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.obb_direction_ras_x.enabled",
                                                 str(True))
    segStatLogic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.obb_direction_ras_y.enabled",
                                                 str(True))
    segStatLogic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.obb_direction_ras_z.enabled",
                                                 str(True))
    segStatLogic.computeStatistics()
    stats = segStatLogic.getStatistics()

    # Draw ROI for each oriented bounding box.
    import numpy as np
    for segmentId in stats['SegmentIDs']:
      # Get bounding box
      obb_origin_ras = np.array(stats[segmentId, "LabelmapSegmentStatisticsPlugin.obb_origin_ras"])
      obb_diameter_mm = np.array(stats[segmentId, "LabelmapSegmentStatisticsPlugin.obb_diameter_mm"])
      obb_direction_ras_x = np.array(stats[segmentId, "LabelmapSegmentStatisticsPlugin.obb_direction_ras_x"])
      obb_direction_ras_y = np.array(stats[segmentId, "LabelmapSegmentStatisticsPlugin.obb_direction_ras_y"])
      obb_direction_ras_z = np.array(stats[segmentId, "LabelmapSegmentStatisticsPlugin.obb_direction_ras_z"])
      # Create ROI
      segment = segmentationNode.GetSegmentation().GetSegment(segmentId)
      roi = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLAnnotationROINode")
      roi.SetName(segment.GetName() + ' bounding box')
      roi.SetXYZ(0.0, 0.0, 0.0)
      roi.SetRadiusXYZ(*(0.5 * obb_diameter_mm))
      # Position and orient ROI using a transform
      obb_center_ras = obb_origin_ras + 0.5 * (
                obb_diameter_mm[0] * obb_direction_ras_x + obb_diameter_mm[1] * obb_direction_ras_y + obb_diameter_mm[
          2] * obb_direction_ras_z)
      boundingBoxToRasTransform = np.row_stack((np.column_stack(
        (obb_direction_ras_x, obb_direction_ras_y, obb_direction_ras_z, obb_center_ras)), (0, 0, 0, 1)))
      boundingBoxToRasTransformMatrix = slicer.util.vtkMatrixFromArray(boundingBoxToRasTransform)
      transformNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
      transformNode.SetAndObserveMatrixTransformToParent(boundingBoxToRasTransformMatrix)
      roi.SetAndObserveTransformNodeID(transformNode.GetID())
      box = roi.GetDisplayNode()
      box.SetVisibility(False)


  #arrow buttons now connected to probe model. up/down rotation.
  def onUpDownArrowButton(self, arrow):
    RotatedToProbeModel = slicer.mrmlScene.GetFirstNodeByName(self.ROTATED_TO_PROBEMODEL)
    ImageToProbe = slicer.mrmlScene.GetFirstNodeByName(self.IMAGE_TO_PROBE)

    ProbeModelToCOR = vtk.vtkTransform()
    Rotation = vtk.vtkTransform()
    CORToRotatedtModel = vtk.vtkTransform()
    RotatedToProbeModelTransform = vtk.vtkTransform()
    ImageToProbeModelTransform = vtk.vtkTransform()
    ImageToCOR = vtk.vtkTransform()
    CORToImage = vtk.vtkTransform()
    ImageRotation = vtk.vtkTransform()

    RotatedMatrix = RotatedToProbeModel.GetMatrixTransformFromParent()

    if arrow == "up":
        NumberOfRotations = RotatedMatrix.GetElement(2, 1) / 0.034
        rotationAngle = -2

    if arrow == "down":
        NumberOfRotations = (RotatedMatrix.GetElement(1, 2) / 0.034)
        rotationAngle = 2

    # Do not allow the user to move the probe more than 3 times in one direction. To be amended during scanning protocols
    if NumberOfRotations <= 1:
        # rotate probe model
        ProbeModelToCOR.Translate(8, 4, -150)
        Rotation.RotateX(rotationAngle * (NumberOfRotations + 1))
        CORToRotatedtModel.Translate(-8, -4, 150)
        RotatedToProbeModelTransform.Concatenate(CORToRotatedtModel)
        RotatedToProbeModelTransform.Concatenate(Rotation)
        RotatedToProbeModelTransform.Concatenate(ProbeModelToCOR)
        # rotate TRUS
        ImageToCOR.Translate(0, 20, 90)
        ImageRotation.RotateX(rotationAngle * (NumberOfRotations + 1))
        CORToImage.Translate(0, -20, -90)
        ImageToProbeModelTransform.Concatenate(CORToImage)
        ImageToProbeModelTransform.Concatenate(ImageRotation)
        ImageToProbeModelTransform.Concatenate(ImageToCOR)

        RotatedToProbeModel.SetMatrixTransformToParent(RotatedToProbeModelTransform.GetMatrix())
        ImageToProbe.SetMatrixTransformToParent(ImageToProbeModelTransform.GetMatrix())

  #right left rotation
  def onRightLeftArrowButton(self, arrow):
    RotatedToProbeModel = slicer.mrmlScene.GetFirstNodeByName(self.ROTATED_TO_PROBEMODEL)
    ImageToProbe = slicer.mrmlScene.GetFirstNodeByName(self.IMAGE_TO_PROBE)

    ProbeModelToCOR = vtk.vtkTransform()
    Rotation = vtk.vtkTransform()
    CORToRotatedtModel = vtk.vtkTransform()
    RotatedToProbeModelTransform = vtk.vtkTransform()
    RotatedMatrix = RotatedToProbeModel.GetMatrixTransformFromParent()
    # transforms to rotate the image
    ImageToProbeModelTransform = vtk.vtkTransform()
    ImageToCOR = vtk.vtkTransform()
    CORToImage = vtk.vtkTransform()
    ImageRotation = vtk.vtkTransform()

    # Check current rotatedtoprobe matrix against its original positioning to determine how much the user has already
    # rotated it
    if arrow == "right":
        NumberOfRotations = (RotatedMatrix.GetElement(2, 0) / 0.02)
        rotationAngle = 1
    if arrow == "left":
        NumberOfRotations = (RotatedMatrix.GetElement(0, 2) / 0.02)
        rotationAngle = -1

     # Do not allow the user to move the probe more than 3 times in one direction. To be amended during scanning protocols
    if NumberOfRotations <= 6:
      ProbeModelToCOR.Translate(8, 4, -150)
      Rotation.RotateY(rotationAngle * (NumberOfRotations + 1))
      CORToRotatedtModel.Translate(-8, -4, 150)
      RotatedToProbeModelTransform.Concatenate(CORToRotatedtModel)
      RotatedToProbeModelTransform.Concatenate(Rotation)
      RotatedToProbeModelTransform.Concatenate(ProbeModelToCOR)

      RotatedToProbeModelTransform.Update()

      # rotate TRUS
      ImageToCOR.Translate(0, 20, 90)
      ImageRotation.RotateY((rotationAngle*1.5) * (NumberOfRotations + 1))
      CORToImage.Translate(0, -20, -90)
      ImageToProbeModelTransform.Concatenate(CORToImage)
      ImageToProbeModelTransform.Concatenate(ImageRotation)
      ImageToProbeModelTransform.Concatenate(ImageToCOR)

      RotatedToProbeModel.SetMatrixTransformToParent(RotatedToProbeModelTransform.GetMatrix())
      ImageToProbe.SetMatrixTransformToParent(ImageToProbeModelTransform.GetMatrix())


#unsure about this...
  def disconnectKeyboardShortcuts(self):

    self.shortcutUp.activated.disconnect()
    logging.info(self.shortcutUp.activated)



  def exit(self):
    logging.info("exiting")
    self.disconnectKeyboardShortcuts()
    logging.info("done")

  #save the scene to resources to be reloaded later
  def onSaveButton(self):

    #clean up nodes that do not need to be saved
    delete = [slicer.mrmlScene.GetFirstNodeByName(self.PROBE_TO_REFERENCE), slicer.mrmlScene.GetFirstNodeByName(self.ROTATED_TO_PROBEMODEL),
              slicer.mrmlScene.GetFirstNodeByName(self.IMAGE_TO_PROBE),slicer.mrmlScene.GetFirstNodeByName('probe_v01'),
              slicer.mrmlScene.GetFirstNodeByName("Segmentation")]

    for i in delete:
      slicer.mrmlScene.RemoveNode(i)

    patient = self.ui.ComboBox.currentIndex
    # Generate file name
    sceneSaveFilename = "C:/Users/cat_w/OneDrive - Queen's University/Perk Lab/USRA project 2020/ProstateBiopsySim" \
                        "/UltrasoundSimModule/Resources/scene" + str(patient) + ".mrb"

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
