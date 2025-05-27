
""" Backend for visualizing and preprocessing clothing data

This class represents the logic of visualizing, selecting and editing
ClothingItem objects in ClothesList, including Part and Joint objects
"""

import logging   # Import logging/print functionality
from .my_utils import FRAME # IntEnum for TOP/BOTTOM frame definitions
from .my_utils import CONFIG    # Class containing basic configuration
from .my_utils import pointDistance # For selecting closest point to click

import ezdxf                # for DXF file processing
import ntpath               # for file name processing
from PyQt5 import QtGui     # For gui drawing
from math import inf as INFINITY    # for infinity

from clothing.clothes_list import ClothesList  #For working with list of clothes
from clothing.clothing_joint import Joint


class ClothingDataManagementBackend(object):
    """ The main backend for managing clothing data

    This class provides everything needed to edit a list of Clothing
    Items in a ClothesList object (_LoadedClothesList), including:
        * Managing the number of clothes items
        * Loading and saving changes to file
        * Editing parts in clothes items and changing their parents
        * Renaming clothes items and parts for reference
        * Defining part segments for joint seams
        * Defining joint seams between two clothing parts
        * Drawing outline and segments of parts to form canvas
        * Accepting mouse clicks for segment endpoint edits
    """

    def __init__(self, file_name = None):
        """ Initializes ClothingDataManagementBackend default values

        Initalizes default values and also loads data from file
        if file_name provided.
        """

        # Load background ClothesList object containing working set data
        self._LoadedClothesList = ClothesList(file_name)
        # Set initial values
        self._current_item_id = None
        self._current_part_id = None
        self._loaded_ids = [None, None]
        self._loaded_active_segment_ids = [None, None]
        self._last_click = None     #Stores last mouse click coordinates [x,y]
        self._current_joint_id = None

        # Stores ongoing selection [a,b], where:
        #   a = selected frame (TOP/BOTTOM)
        #   b = selected point in segment (0=left, 1=right)
        self._current_selection = None

        # Initialize properties
        self.active_item_id = None      # Reset active selection and children


    ################## Properties / Getters and Setters #######################

    @property
    def active_item_id(self):
        """ Gets and safely sets the current active clothing item """
        return self._current_item_id

    @active_item_id.setter
    def active_item_id(self, value):
        clothe_item_count = len(self.getClothesList())
        should_reset_children = False
        if value is None or clothe_item_count == 0:
            # New items are loaded or old are cleared - new state
            should_reset_children = True    
            if clothe_item_count>0:
                self._current_item_id = 0   # Set first item active
            else:
                self._current_item_id = None
        else:
            # Existing state with at least some items, but potentially
            # changed selection.
            # If no change ocurred, no need to reset everything after
            if value >= clothe_item_count or value < 0:
                value = 0      #If out of bounds select first element
            if self._current_item_id != value:
                should_reset_children = True    
                self._current_item_id = value
        if should_reset_children:
            self.active_part_id = None
            self.active_joint_id = None

    @property
    def active_part_id(self):
        """ Gets and safely sets the current active clothing part """
        return self._current_part_id

    @active_part_id.setter
    def active_part_id(self, value):
        clothe_part_count = len(self.getPartList())
        should_reset_children = False
        if value is None or clothe_part_count == 0:
            # New parts are loaded or old are cleared - new state
            should_reset_children = True    
            if clothe_part_count>0:
                self._current_part_id = 0   # Set first item active
            else:
                self._current_part_id = None
        else:
            # Existing state with at least some parts, but potentially
            # changed selection. Loaded parts are not impacted by change
            # in active part so no need to reset
            if value >= clothe_part_count or value < 0:
                value = 0      #If out of bounds select first element
            self._current_part_id = value
        if should_reset_children:
            self.setLoadedPartID(FRAME.TOP, None)
            self.setLoadedPartID(FRAME.BOTTOM, None)


    def getLoadedPartID(self,frame):
        """ Gets the current part loaded in selected frame """
        if frame not in FRAME:
            raise ValueError("ERROR: incorrect frame value for setting"
                              "loaded part ID!")
        return self._loaded_ids[frame]        

    def setLoadedPartID(self,frame,value):
        """ Safely sets loaded part in selected frame """
        if frame not in FRAME:
            raise ValueError("ERROR: incorrect frame value for setting"
                              "loaded part ID!")
        clothe_part_count = len(self.getPartList())
        should_reset_children = False
        if value is None or clothe_part_count == 0:
            should_reset_children = True
            self._loaded_ids[frame] = None
        else:
            if value >= clothe_part_count or value < 0:
                value = 0      #If out of bounds select first element
            if self._loaded_ids[frame] != value:
                should_reset_children = True    
                self._loaded_ids[frame] = value
        if should_reset_children:
            self.setActiveSegmentID(frame, None)

    def cleanLoadedPartIDs(self,value):
        """ Updates loaded part IDs, if a part is removed from list """
        for frame in FRAME:
            current_loaded_part = self.getLoadedPartID(frame)
            if current_loaded_part is not None and value < current_loaded_part:
                self.setLoadedPartID(frame, current_loaded_part - 1)
            else:
                if value == current_loaded_part:
                    self.setLoadedPartID(frame, None)

    def swapLoadedPartIDs(self, value1, value2):
        """ Updates loaded part IDs, if two parts are swapped in list """
        if(value1 != value2):
            for frame in FRAME:
                current_loaded_part = self.getLoadedPartID(frame)
                if value1 == current_loaded_part:
                    self.setLoadedPartID(frame, value2)
                elif value2 == current_loaded_part:
                    self.setLoadedPartID(frame, value1)

    @property
    def active_joint_id(self):
        """ Gets and safely sets the current active joint """
        return self._current_joint_id

    @active_joint_id.setter
    def active_joint_id(self, value):
        joint_count = len(self.getJointList())
        if value is None or joint_count == 0:
            # New items are loaded or old are cleared - new state
            if joint_count>0:
                self._current_joint_id = 0   # Set first joint active
            else:
                self._current_joint_id = None
        else:
            # Existing state with at least some items, but potentially
            # changed selection.
            if value >= joint_count or value < 0:
                value = 0      #If out of bounds select first element
            if self._current_joint_id != value:
                self._current_joint_id = value


    ####################### File Saving / Loading  ############################

    def save(self, file_name):
        """ Saves te current ClothesList to file_name file. """
        self._LoadedClothesList.save(file_name)

    def isSaved(self):
        """ Check if current ClothesList is saved in file

        Returns:
            True: if saved in file and unchanged after that
            False: if changes not saved
        """
        return self._LoadedClothesList.isSaved()

    def loadDXF(self, file_name):
        """ Load contents from DXF file as new ClothesItem in ClothesList

        file_name file is opened, data read into ClothesItem, which is 
        then added to ClothesList. Active item ID is set to loaded if
        it is the first loaded item
        """
        try:
            dwg = ezdxf.readfile(file_name)
            item_name = ntpath.basename(file_name)
            self._LoadedClothesList.addDFXitem(item_name, dwg.entities)
        except Exception as e:
            logging.error("Could not load DXF file!")
            pass
        finally:
            # If nothing selected before select loaded row (errors checked
            # in property - no need to check if actually added). If was not
            # added - the property will reset state, so this is needed!
            if self.active_item_id is None:
                self.active_item_id = 1     


    ################### Exposing ClothesList interface ########################

    def getClothesList(self):
        """ Exposes internal list of clothes """
        return self._LoadedClothesList.getClothesList()

    def moveClotheItemUp(self):
        """ Shifts ClothesItem up one space in the list """
        if self.active_item_id is not None:
            self.active_item_id = self._LoadedClothesList.swapItem(self.active_item_id, -1)

    def moveClotheItemDown(self):
        """ Shifts ClothesItem down one space in the list """
        if self.active_item_id is not None:
            self.active_item_id = self._LoadedClothesList.swapItem(self.active_item_id, 1)

    def deleteClotheItem(self):
        """ Deletes selected ClothesItem from the ClothesList """
        if self.active_item_id is not None:
            self.active_item_id = self._LoadedClothesList.deleteClotheItem(self.active_item_id)

    def renameClotheItem(self, name):
        """ Renames active ClothesItem with specified name """
        if self.active_item_id is not None:
            self._LoadedClothesList.renameClotheItem(self.active_item_id, name)

    def getSelectedClotheItemName(self):
        item = self._LoadedClothesList.getClothesItem(self.active_item_id)
        if item is not None:
            return item.Name
        logger.warning("Tried to get name of non-existant clothing item....")
        return "[not set]"

    def addNewClotheItem(self, name):
        """ Adds new ClothesItem with specified name, at end of list """
        self.active_item_id = self._LoadedClothesList.addNewClotheItem(name)


    ################### Exposing ClothingItem interface #######################

    def getPartList(self):
        """ Exposes internal list of parts, or [] if no ClothesItem loaded """
        if self.active_item_id is None:
            return []
        return self.getClothesList()[self.active_item_id].getPartList()

    def movePartUp(self):
        if self.active_item_id is not None and self.active_part_id is not None:
            old_part_id = self.active_part_id
            self.active_part_id = self._LoadedClothesList.swapPart(
                                  self.active_item_id, self.active_part_id, -1)
            self.swapLoadedPartIDs(old_part_id, self.active_part_id)

    def movePartDown(self):
        if self.active_item_id is not None and self.active_part_id is not None:
            old_part_id = self.active_part_id
            self.active_part_id = self._LoadedClothesList.swapPart(
                                  self.active_item_id, self.active_part_id, 1)
            self.swapLoadedPartIDs(old_part_id, self.active_part_id)

    def deletePart(self):
        """ Deletes selected ClothesItem from the ClothesList """
        if self.active_item_id is not None and self.active_part_id is not None:
            old_part_id = self.active_part_id
            new_part_id = self._LoadedClothesList.deletePart(
                                  self.active_item_id, self.active_part_id)
            if old_part_id != new_part_id:
                self.cleanLoadedPartIDs(old_part_id)
            self.active_part_id = new_part_id

    def renamePart(self, name):
        """ Renames active ClothesItemPart with specified name """
        if self.active_item_id is not None and self.active_part_id is not None:
            self._LoadedClothesList.renamePart(self.active_item_id,
                                               self.active_part_id, name)

    def getSelectedPartName(self):
        if self.active_item_id is not None and self.active_part_id is not None:
            partlist = self.getPartList()
        if len(partlist) > self.active_part_id:
            return partlist[self.active_part_id].Name
        logger.warning("Tried to get name of non-existant clothing part....")
        return "[not set]"

    def duplicatePart(self):
        """ Adds new ClothesItemPart with specified name, at end of list """
        if self.active_item_id is not None and self.active_part_id is not None:
            self.active_part_id = self._LoadedClothesList.duplicatePart(
                                  self.active_item_id, self.active_part_id)

    def invertPart(self):
        """ Flips part to mirror image and also renumber part points counter
        clockwise for making Left part (arm etc.) from Right part and back """
        if self.active_item_id is not None and self.active_part_id is not None:
            self._LoadedClothesList.invertPart(
                    self.active_item_id, self.active_part_id)

    def changePartParent(self, parent_id):
        """ Changed parent ClothingItem of selected Clothing Part """
        if self.active_item_id is not None and self.active_part_id is not None:
            old_part_id = self.active_part_id
            new_part_id = self._LoadedClothesList.changePartParent(
                                  self.active_item_id, parent_id,
                                  self.active_part_id)
            if old_part_id != new_part_id:
                self.cleanLoadedPartIDs(old_part_id)
                self.active_part_id = new_part_id

    def getJointList(self):
        """ Exposes internal list of parts, or [] if no ClothesItem loaded """
        if self.active_item_id is None:
            return []
        return self.getClothesList()[self.active_item_id].getJointList()

    def addJoint(self):
        self.active_joint_id = self._LoadedClothesList.addJoint(self.active_item_id, Joint())  # Select the new joint as active

    def removeJoint(self):
        self.active_joint_id = self._LoadedClothesList.removeJoint(self.active_item_id, self.active_joint_id)  # Remove joint, select previous in list as active

    def invertJoint(self):
        """ Iverts joint state between matching beginning points to beginning
            points or matching beginning points to end points (reversed)"""
        self._LoadedClothesList.invertJoint(self.active_item_id, self.active_joint_id) 


    def getActiveJoint(self):
        joint_list = self.getJointList()
        joint_list_len = len(joint_list)
        if joint_list is None or joint_list_len == 0:
            return None
        joint_id = self.active_joint_id
        if joint_id is None or joint_list_len<=joint_id:
            return None
        return joint_list[joint_id]

    def loadJoint(self):
        joint = self.getActiveJoint()
        if joint is not None:
            parts = joint.getParts()
            segments = joint.getSegments()
            for frame in FRAME:
                self.setLoadedPartID(frame, parts[frame])
                self.setActiveSegmentID(frame, segments[frame])
        else:
            logging.error("No joint to load!")

    def saveJoint(self):
        parts = []
        segments = []
        for frame in FRAME:
            parts.append(self.getLoadedPartID(frame))
            segments.append(self.getActiveSegmentID(frame))
        self._LoadedClothesList.saveJoint(self.active_item_id, self.active_joint_id, parts, segments)

    ################### Exposing ClothingPart Interface #######################

    def getSegmentList(self, frame):
        """ Exposes internal list of segments, or [] if no ClothesItem or part loaded """
        loaded_part = self.getLoadedPart(frame)
        if loaded_part is None:
            logging.debug("Cannot get segment list - loaded part is None")
            return []
        return loaded_part.getSegmentList()

    def setActiveSegmentID(self, frame, value):
        logging.debug("setting_active_segment_id "+str(value))
        if frame not in FRAME:
            raise ValueError("ERROR: incorrect frame value for setting active segment!")
        segment_count = len(self.getSegmentList(frame))
        should_reset_children = False
        if value is None or segment_count == 0:
            should_reset_children = True
            self._loaded_active_segment_ids[frame] = None
            if segment_count>0: #If exists, select first in case of None
                self._loaded_active_segment_ids[frame] = 0
        else:
            if value >= segment_count or value < 0:
                value = 0      #If out of bounds select first element
            if self._loaded_active_segment_ids[frame] != value:
                should_reset_children = True    
                self._loaded_active_segment_ids[frame] = value
        #if should_reset_children:
        #    Probably nothing to redraw when changing segent, but left here for the case it might be needed

    def getActiveSegmentID(self, frame):
        """ Gets the current segment of part loaded in selected frame """
        if frame not in FRAME:
            raise ValueError("ERROR: incorrect frame value for getting active segment!")
        return self._loaded_active_segment_ids[frame]       

    def addSegment(self, frame):
        self.setActiveSegmentID(frame, self._LoadedClothesList.addSegment(self.active_item_id, self.getLoadedPartID(frame), [0, 0]))  # Select the new segment as active

    def removeSegment(self, frame):
        self.setActiveSegmentID(frame, self._LoadedClothesList.removeSegment(self.active_item_id, self.getLoadedPartID(frame), self.getActiveSegmentID(frame)))  # Remove segment, select previous in list as active

    def getActiveSegment(self, frame):
        segment_list = self.getSegmentList(frame)
        segment_list_len = len(segment_list)
        if segment_list is None or segment_list_len == 0:
            return None
        segment_id = self.getActiveSegmentID(frame)
        if segment_id is None or segment_list_len<=segment_id:
            return None
        return segment_list[segment_id]


    def loadActivePart(self, frame):
        logging.debug("Loading active part! "+str(self.active_part_id))
        self.setLoadedPartID(frame, self.active_part_id)

    def getLoadedPart(self, frame):
        part_list = self.getPartList()
        part_list_len = len(part_list)
        if part_list is None or part_list_len == 0:
            return None
        part_id = self.getLoadedPartID(frame)
        if part_id is None or part_list_len<=part_id:
            return None
        return part_list[part_id]


##########
# Displaying stuff
##########
# Zone points...
#(433, 32) - (677, 221)
#(434, 242) - (675, 446)


    def MouseSelect(self, x, y):
        """ Describes closest segment endpoint detection on mouse down

        when mouse is pressed down, the frame in whic the click occured
        is determined and the specific endpoint closest to click found.
        This information is saved till mouse is released.
        """ 
        if self._current_selection is None:
            logging.info("Selecting segment")
            # Determine frame for which the mouse selection is relevant
            frame = FRAME.TOP
            if y>=CONFIG.FRAME_HEIGHT:
                frame = FRAME.BOTTOM

            # determine wether left or right segment endpoint is selected
            adjusted_point = self.adjustedPoint([x,y], frame)
            part = self.getLoadedPart(frame)
            segment = self.getActiveSegment(frame)

            if part is not None and segment is not None:
                distance_to_left_point = pointDistance(part.PointList[segment[0]], adjusted_point)
                distance_to_right_point = pointDistance(part.PointList[segment[1]], adjusted_point)
                segment_point_index = 0 if distance_to_left_point < distance_to_right_point else 1

                # set values for ongoing selection till mouse released
                self._current_selection = [frame,segment_point_index]

    def MouseRelease(self, x, y):
        """ Select the closest point to mouse click as new segment endpoint

        When mouse is released, the area in _current_selection is checked
        for the closest existing point to mouse click location. This
        point is now the new endpoint for the segment determined on 
        MouseSelect
        """
        logging.info("Mouse released")
        self._last_click = [x,y] #Store click value for visualization
        if self._current_selection is not None:
            frame = self._current_selection[0]
            point_list = self.getLoadedPart(frame).PointList
            adjusted_point = self.adjustedPoint([x,y], frame)
            
            # Determine the closest point to click as selected
            selected_point_id = 0
            closest_point_distance = INFINITY # the largest possible snumber

            for i, point in enumerate(point_list):
                distance = pointDistance(adjusted_point,point)
                if distance<closest_point_distance:
                    closest_point_distance = distance
                    selected_point_id = i
            self._LoadedClothesList.changeSegmentEndpoint(self.active_item_id, self.getLoadedPartID(frame), self.getActiveSegmentID(frame), selected_point_id, self._current_selection[1])
            self._current_selection = None

 
    def adjustedPoint(self, point, frame):
        """ Transform point from display form coordinates to
        internal coordinates """

        x = (point[0] - CONFIG.CANVAS_X) / CONFIG.SCALE_FACTOR
        y = (point[1] - frame*CONFIG.FRAME_HEIGHT)
        y = -(y - CONFIG.CANVAS_Y) / CONFIG.SCALE_FACTOR

        return [x,y]

    def displayTransform(self, point, frame):
        """ Transform point from internal coordinates to display
        form coordinates """

        # Scale points and move them to the drawing canvas coordinates
        x = point[0]*CONFIG.SCALE_FACTOR + CONFIG.CANVAS_X
        y = -point[1]*CONFIG.SCALE_FACTOR + CONFIG.CANVAS_Y
        # Move point to specific drawing frame (TOP/BOTTOM)
        y = y + frame*CONFIG.FRAME_HEIGHT

        return [round(x),round(y)]


    def redraw(self, form, event):
        self.drawPoints(form, event)

    def drawConnectedPoints(self, point_list, color, form, frame, closed_loop=False):
        qp = QtGui.QPainter()
        qp.begin(form)  
        qp.setPen(color)
        size = form.size()

        # Draw the provided point list as connected lines
        prev = None
        for point in point_list:
            point = self.displayTransform(point, frame)
            if prev != None:
                qp.drawLine(prev[0],prev[1],point[0],point[1])     
            prev = point
        # If at least one point in the list either close the loop or draw
        # end handles (circles)
        if prev is not None:
            first_point = self.displayTransform(point_list[0], frame)
            if closed_loop:
                # Close loop (connect last point to first)
                qp.drawLine(prev[0],prev[1],first_point[0], first_point[1])
            else:
                # Draw line end handles (circles) at the first and last point
                # Also draw location of last mouse release (full click)
                qp.setPen(CONFIG.COLOR_LEFTHANDLE)
                qp.drawEllipse(first_point[0]-round(CONFIG.HANDLE_DIAMETER/2),
                   first_point[1]-round(CONFIG.HANDLE_DIAMETER/2), 
                   CONFIG.HANDLE_DIAMETER, CONFIG.HANDLE_DIAMETER)
                qp.setPen(CONFIG.COLOR_RIGHTHANDLE)
                qp.drawEllipse(prev[0]-round(CONFIG.HANDLE_DIAMETER/2), 
                   prev[1]-round(CONFIG.HANDLE_DIAMETER/2), CONFIG.HANDLE_DIAMETER,
                   CONFIG.HANDLE_DIAMETER)
                if self._last_click is not None:
                    qp.setPen(CONFIG.COLOR_LASTCLICK)
                    qp.drawEllipse(self._last_click[0]-round(CONFIG.HANDLE_DIAMETER/2),
                       self._last_click[1]-round(CONFIG.HANDLE_DIAMETER/2),
                       CONFIG.HANDLE_DIAMETER, CONFIG.HANDLE_DIAMETER)
        qp.end()

    def drawPoints(self, form, event):
        for frame in FRAME:
            #Draw whole closed shape line
            part = self.getLoadedPart(frame)

            if part is not None:
                self.drawConnectedPoints(part.PointList, CONFIG.COLOR_LINE, form, frame, closed_loop=True)

                #Draw active selected segment line (open ends)        
                active_segment_id = self.getActiveSegmentID(frame)
                segment_point_list = part.getSegmentPoints(active_segment_id)
                self.drawConnectedPoints(segment_point_list, CONFIG.COLOR_ACTIVE, form, frame, closed_loop = False)
