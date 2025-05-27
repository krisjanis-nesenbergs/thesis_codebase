""" Clothing data management/cleanup user interface (UI)

This class uses PyQt5 to draw UI and manage user input events.
The events / visualization data interact with a backend class defined in
clothing_data_management_backend.py of the clothing library.

For visualization it uses auto-generated PyQt5 form in dxf_marking_form.py.
    This form is generated from dxf_marking_form.ui file with command:
        pyuic5 dxf_marking_form.ui -o dxf_marking_form.py
    The dxf_marking_form.ui file can be edited with free Qt Designer app.

Additionally my_utils file is imported for custom constants/helper functions.

This UI is part of Thesis project on smart clothing by Krisjanis Nesenbergs.
Further licensing information in dunder (double underscore) vars below
"""

__author__ = "Krisjanis Nesenbergs"
__version__ = "0.1"
__contact__ = 'krisjanis.nesenbergs@edi.lv'
__copyright__ = "Copyright 2017, Krisjanis Nesenbergs"
__license__ = "GPL"
__status__ = "Prototype"

import logging   # Import logging/print functionality
from .my_utils import FRAME # IntEnum for TOP/BOTTOM frame definitions

# Main data processing backend class:
from .clothing_data_management_backend import ClothingDataManagementBackend

from PyQt5 import QtWidgets # for PyQt5 Window support         
from .dxf_marking_form import Ui_MainWindow   # Import ui window definition (generated)

class CLothingDataManagementUI(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        """ Initialize the UI window and attach events to UI elements"""
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Initiate data backend for this clothing data cleanup form
        self.clothes = ClothingDataManagementBackend()

        # Set up ui item events
        self.ui.actionNew_project.triggered.connect(self.actionNewClicked)
        self.ui.actionSave_project.triggered.connect(self.actionSaveClicked)
        self.ui.actionOpen_project.triggered.connect(self.actionLoadClicked)
        self.ui.actionLoad_DXF_file.triggered.connect(
                                            self.actionLoadDXFClicked)
        self.ui.actionExit.triggered.connect(self.actionExitClicked)
        self.ui.clotheListWidget.itemSelectionChanged.connect(
                                            self.clotheListSelected)
        self.ui.partListWidget.itemSelectionChanged.connect(
                                            self.partListSelected)
        self.ui.buttonLoad1.clicked.connect(self.load1)
        self.ui.buttonLoad2.clicked.connect(self.load2)
        self.ui.actionAdd_new_file.triggered.connect(self.actionAddfileClicked)
        self.ui.actionRename_file.triggered.connect(
                                            self.actionRenamefileClicked)
        self.ui.actionDelete_file.triggered.connect(
                                            self.actionDeletefileClicked)
        self.ui.actionMove_up_file.triggered.connect(
                                            self.actionMoveUpfileClicked)
        self.ui.actionMove_down_file.triggered.connect(
                                            self.actionMoveDownfileClicked)
        self.ui.actionRename_part.triggered.connect(
                                            self.actionRenamePartClicked)
        self.ui.actionMove_part_up.triggered.connect(
                                            self.actionMoveUpPartClicked)
        self.ui.actionMove_part_down.triggered.connect(
                                            self.actionMoveDownPartClicked)
        self.ui.actionChange_parent_item.triggered.connect(
                                            self.actionChangeParentPartClicked)
        self.ui.actionDuplicate_part.triggered.connect(
                                            self.actionDuplicatePartClicked)
        self.ui.actionInverse_part.triggered.connect(
                                            self.actionInversePartClicked)
        self.ui.actionDelete_part.triggered.connect(
                                            self.actionDeletePartClicked)        
        # As segments can be drawn in both TOP and BOTTOM frames, events need
        # to be attached to both in a loop over FRAME IntEnum (TOP/BOTTOM)
        self.segmentLists = [self.ui.segmentList1, self.ui.segmentList2]
        segmentChangedEvents = [self.segmentChanged1, self.segmentChanged2]
        self.segmentAddButtons = [self.ui.addSegment1, self.ui.addSegment2]
        segmentAddEvents = [self.addSegment1, self.addSegment2]
        self.segmentRemoveButtons = [self.ui.removeSegment1, self.ui.removeSegment2]
        segmentRemoveEvents = [self.removeSegment1, self.removeSegment2]
        for segment in FRAME:
            self.segmentLists[segment].activated.connect(
                                                segmentChangedEvents[segment])
            self.segmentAddButtons[segment].clicked.connect(
                                                segmentAddEvents[segment])
            self.segmentRemoveButtons[segment].clicked.connect(
                                                segmentRemoveEvents[segment])
        self.ui.jointList.activated.connect(self.jointChanged)
        self.ui.loadJoint.clicked.connect(self.loadJoint)
        self.ui.storeJoint.clicked.connect(self.saveJoint)
        self.ui.addJoint.clicked.connect(self.addJoint)
        self.ui.removeJoint.clicked.connect(self.removeJoint)
        self.ui.invertJoint.clicked.connect(self.invertJoint)

    ########################### Helper functions ##############################

    def allowDismissCurrentProject(self):           
        """ Check if current project can be safely closed

        If project has unsaved changes, asks if closing is allowed.

        Returns:
            True: Can be closed (does not need saving)
            False: Cannot close - needs saving
        """

        if self.clothes.isSaved():                          # If is saved, everything ok - return
            return True

        msg = "Close the current project without saving?"   # Pop up question "Close without saving?" and allow dismissing if user confirms
        reply = QtWidgets.QMessageBox.question(self, 'Message', msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        return (reply == QtWidgets.QMessageBox.Yes)

    def getListWidgetSelectedRow(self, widget):
        """ Returns first selected row of list widget provided or None """
        selection = widget.selectedItems()
        selected_row_id = None
        if len(selection)>0:
            selected_row = selection[0]
            selected_row_id = widget.row(selected_row)
        return selected_row_id


    ##################### Re-drawing UI on change #############################

    def redrawClothesListForm(self):
        """ Redraws ClothesItems list and sub information

        Usually used when some information changes on whole clothing
        item level (new items, new project etc.) so no old info shown

        Clear the list form, populate with new ClothesItem names,
        If there is an active one, select it, finally refresh subparts
        """
        
        self.ui.clotheListWidget.clear()                        

        for clothes_item in self.clothes.getClothesList():      
            self.ui.clotheListWidget.addItem(clothes_item.Name)
        
        active_item = self.clothes.active_item_id
        if active_item is not None:
            self.ui.clotheListWidget.setCurrentRow(active_item)
        
        # Refresh part list of selected item, as it could have changed
        self.redrawPartListForm()
        # Refresh joint list of selected item as it could have changed
        self.redrawJointListForm()

    def redrawJointListForm(self):
        """ Redraws the joint list form when clothing item changes """
        logging.info("Redrawing joint list!!")
        self.ui.jointList.clear()
        for item in self.clothes.getJointList():
            self.ui.jointList.addItem(item.getName())

        active_joint = self.clothes.active_joint_id
        if active_joint is not None:
            self.ui.jointList.setCurrentIndex(active_joint)


    def redrawPartListForm(self):
        """ Redraws Parts list and sub information

        Usually used when some information changes on the current
        clothing item level (new/rename parts etc.) so no old info shown

        Clear the list form, populate with new Part names,
        If there is an active one, select it, finally refresh segments
        """
        
        self.ui.partListWidget.clear()

        for part_item in self.clothes.getPartList():
            self.ui.partListWidget.addItem(part_item.Name)
        
        active_part = self.clothes.active_part_id   
        if active_part is not None:
            self.ui.partListWidget.setCurrentRow(active_part)

        # Redraw form containing segment visualization and dropdowns
        self.redrawSegmentListForm()

    def redrawSegmentListForm(self):
        for frame in FRAME:
            self.segmentLists[frame].clear()
            for item in self.clothes.getSegmentList(frame):
                self.segmentLists[frame].addItem(str(item))

            active_segment = self.clothes.getActiveSegmentID(frame)
            if active_segment is not None:
                self.segmentLists[frame].setCurrentIndex(active_segment)
        self.updateDisplay()

    def updateDisplay(self):
        # this redraws the line graphics
        self.redraw()

    def redraw(self):
        """ Calls PyQt5 Window update/repaint to refresh graphics

        Results in paintEvent() event being called
        """
        self.update()

    def paintEvent(self,event):
        self.clothes.redraw(self,event)


    ###################### UI Element Events ##################################

    ## Related to ClotheItem list

    def clotheListSelected(self):
        value = self.getListWidgetSelectedRow(self.ui.clotheListWidget)
        if value is not None:
            self.clothes.active_item_id = value
        self.redrawPartListForm()
        self.redrawJointListForm()

    def actionMoveUpfileClicked(self):
        self.clothes.moveClotheItemUp()
        self.redrawClothesListForm()

    def actionMoveDownfileClicked(self):
        self.clothes.moveClotheItemDown()
        self.redrawClothesListForm()

    def actionDeletefileClicked(self):
        self.clothes.deleteClotheItem()
        self.redrawClothesListForm()        

    def actionAddfileClicked(self):
        self.clothes.addNewClotheItem("Untitled")
        self.redrawClothesListForm()

    def actionRenamefileClicked(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Rename file',
                  'Enter new name:',text=self.clothes.getSelectedClotheItemName())
        if ok:
            self.clothes.renameClotheItem(str(text))
            self.redrawClothesListForm()

    ## Related to Part list

    def partListSelected(self):
        value = self.getListWidgetSelectedRow(self.ui.partListWidget)
        if value is not None:
            self.clothes.active_part_id = value 
        self.redrawSegmentListForm()

    def actionMoveUpPartClicked(self):
        self.clothes.movePartUp()
        self.redrawPartListForm()
        self.redrawJointListForm()        

    def actionMoveDownPartClicked(self):
        self.clothes.movePartDown()
        self.redrawPartListForm()
        self.redrawJointListForm()        

    def actionDeletePartClicked(self):
        self.clothes.deletePart()
        self.redrawPartListForm()
        self.redrawJointListForm()
        self.redrawJointListForm()        

    def actionRenamePartClicked(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Rename part', 
                   'Enter new name:', text=self.clothes.getSelectedPartName())
        if ok:
            self.clothes.renamePart(str(text))
            self.redrawPartListForm()

    def actionDuplicatePartClicked(self):
        self.clothes.duplicatePart()
        self.redrawPartListForm()

    def actionInversePartClicked(self):
        self.clothes.invertPart()
        self.redrawPartListForm()

    def actionChangeParentPartClicked(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'New parent', 
            'Enter new parent row number [0-indexed]:')
        if ok:
            i = -1
            try:
                i = int(text)
            except Exception as e:
                pass
            if i>-1:
                self.clothes.changePartParent(i)
                self.redrawPartListForm()
                self.redrawJointListForm()

    def load1(self):
        self.clothes.loadActivePart(FRAME.TOP)
        self.redrawSegmentListForm()

    def load2(self):
        self.clothes.loadActivePart(FRAME.BOTTOM)
        self.redrawSegmentListForm()

    # Related to loaded parts

    def addSegment1(self):
        self.addSegment(FRAME.TOP)

    def addSegment2(self):
        self.addSegment(FRAME.BOTTOM)

    def addSegment(self, frame):
        logging.info("Adding segment!")
        self.clothes.addSegment(frame)
        self.redrawSegmentListForm()        

    def segmentChanged1(self):
        self.clothes.setActiveSegmentID(FRAME.TOP, self.ui.segmentList1.currentIndex())
        self.updateDisplay()

    def segmentChanged2(self):
        self.clothes.setActiveSegmentID(FRAME.BOTTOM, self.ui.segmentList2.currentIndex())
        self.updateDisplay()

    def removeSegment1(self):
        self.removeSegment(FRAME.TOP)

    def removeSegment2(self):
        self.removeSegment(FRAME.BOTTOM)

    def removeSegment(self, frame):
        logging.info("Removing segment!")
        self.clothes.removeSegment(frame)
        self.redrawSegmentListForm()  
        self.redrawJointListForm()   

    def addJoint(self):
        logging.info("Adding joint!")
        self.clothes.addJoint()
        self.redrawJointListForm()

    def jointChanged(self):
        self.clothes.active_joint_id = self.ui.jointList.currentIndex()
        self.redrawJointListForm()

    def removeJoint(self):
        logging.info("Removing joint!")
        self.clothes.removeJoint()
        self.redrawJointListForm()

    def loadJoint(self):
        logging.info("Loading joint!")
        self.clothes.loadJoint()
        self.redrawSegmentListForm()

    def saveJoint(self):
        logging.info("Saving joint!")
        self.clothes.saveJoint()
        self.redrawJointListForm()

    def invertJoint(self):
        logging.info("Inverting joint!")
        self.clothes.invertJoint()
        self.redrawJointListForm()



    ######################## MOUSE EVENTS #####################################


    def mousePressEvent(self, QMouseEvent):
        point = QMouseEvent.pos()
        self.clothes.MouseSelect(point.x(), point.y())

    def mouseReleaseEvent(self, QMouseEvent):
        point = QMouseEvent.pos()
        self.clothes.MouseRelease(point.x(), point.y())
        self.redrawSegmentListForm()


    ############################# SAVE / LOAD / EXIT ##########################

    # Action for menu selection Exit
    def actionExitClicked(self):
        if self.allowDismissCurrentProject():
            logging.info("Exit!")
            self.close()

    # Action for menu selection - Save project
    def actionSaveClicked(self):
        logging.info("Saving!")
        file_name = QtWidgets.QFileDialog.getSaveFileName(None, 'Save project') #Get file name where ClothesList will be stored
        self.clothes.save(file_name[0])

    # Action for menu selection - Load project
    def actionLoadClicked(self):
        if self.allowDismissCurrentProject():
            logging.info("Loading!")
            file_name = QtWidgets.QFileDialog.getOpenFileName(None, 'Load project') #Get file name where saved ClothesList is stored
            self.clothes = ClothingDataManagementBackend(file_name = file_name[0])       #Initiate new clothing data managment backend, which loads the ClothesList from specified file
            self.redrawClothesListForm()                                            #Redraw clothes list interface

    # Action for menu selection - New project
    def actionNewClicked(self):
        if self.allowDismissCurrentProject():
            logging.info("New!")
            self.clothes = ClothingDataManagementBackend()                   #Initiate new empty clothing data management backend
            self.redrawClothesListForm()                                            #Redraw clothes list interface

    # Action for menu selection - Load item from DXF file
    def actionLoadDXFClicked(self):
        logging.info("Loading DXF!")
        file_name = QtWidgets.QFileDialog.getOpenFileName(None, 'Add DXF file to project')  #Get dxf file name to open and add to project
        self.clothes.loadDXF(file_name[0])                                                  #Load ClothingItem from DXF file and add to current ClothesList 
        self.redrawClothesListForm()                                                        #Redraw clothes list interface

    # Action for event of somehow closing the program - check if saved and exit or stop exiting event if usaved and user intervention
    def closeEvent(self, event):
        if self.allowDismissCurrentProject():
            logging.info("Exiting...")
            event.accept()
        else:
            event.ignore()

















