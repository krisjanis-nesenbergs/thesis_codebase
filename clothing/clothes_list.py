'''
    Class representing the whole working set of ClothingItem Objects,
    together with persistence functions (Pickling to file and restoring)
    and adding new objects from DXF entities
'''

import logging   # Import logging function
import pickle  # For pickling ClothesList
from .clothing_item import ClothingItem

class ClothesList(object):
    def __init__(self, file_name = None):
        self._itemList = []         # List of ClothingItem objects
        self._saved = True          # State of the ClothesList object persistence - if False, there are unsaved changes
        if file_name is not None:
            self.load(file_name)    # Load Clothes list contents from file, if provided

    # Try loading pickled ClothesList contained _itemList from file_name file. On fail, the _itemList is set to contain no clothing items
    def load(self, file_name):
        try: 
            with open(file_name,"rb",0) as f:
                self._itemList = pickle.load(f)    #After load, Saved is still True, no change here
        except Exception as e:
            logging.error("Could not load file - either invalid file or file does not contain correct version of ClothesList") #Not really important, what error occured - could not load is the result
            self._itemList = []
            pass

    # Save (Pickle) the ClothesList contained _itemList to the file_name file
    def save(self, file_name):
        if file_name is None:           # Check if file_name is provided
            logging.warning("Could not save - no file name specified!")
            return

        try:                            # Try to load from the file and if loaded, set current list as saved.
            with open(file_name,"wb",0) as f:
                pickle.dump(self._itemList, f, 4)
            self._saved = True
        except Exception as e:
            logging.error("Could not save file!")
            pass

    # Add ClothingItem to _itemList creating it from a list of DXF file entities, set Saved to False on success
    def addDFXitem(self, item_name, dxf_entities):
        loaded_clothing_item = ClothingItem(item_name)        
        try:
            for e in dxf_entities:
                with e.points() as points:
                    loaded_clothing_item.addDXFpart("Label", points)
            self._itemList.append(loaded_clothing_item)
            self._saved = False
        except Exception as e:
            logging.error("DXF file contents corrupted or not a valid DXF file.")
            pass

    # Is the current instance saved?
    def isSaved(self):
        return self._saved

    def itemExists(self, item_id):
        if item_id is None:
            return False
        if len(self._itemList)>item_id and item_id>=0:
            return True
        return False    

    # Function for exposing the internal _itemList
    def getClothesList(self):
        return self._itemList    

    def getClothesItem(self, item_id):
        if self.itemExists(item_id):
            return self.getClothesList()[item_id]
        return None     
       
    def addNewClotheItem(self, name):
        citem = ClothingItem(name)
        self._itemList.append(citem)
        self._saved = False
        return self._itemList.index(citem) 

    def renameClotheItem(self, item_id, name):
        if self.itemExists(item_id):
            self._itemList[item_id].Name = name
            self._saved = False
        else:
            logging.error("Couldn't rename non-existent clothe item")

    def deleteClotheItem(self, item_id):
        if self.itemExists(item_id):        
            del self._itemList[item_id]
            self._saved = False
            return item_id - 1
        else:
            logging.error("Couldn't delete non-existant clothe item")
            return None

    def swapItem(self, item_id, swap_steps):
        if self.itemExists(item_id):
            self._saved = False
            new_item_id = item_id + swap_steps
            if self.itemExists(new_item_id):
                self._itemList[item_id], self._itemList[new_item_id] = self._itemList[new_item_id], self._itemList[item_id] 
                return new_item_id
            else:
                logging.warning("Could not shift item to new row.")
                return item_id     
        else:
            logging.error("Couldn't swap non-existant clothing item")
            return None

    def duplicatePart(self, item_id, part_id):
        if self.itemExists(item_id):
            self._saved = False
            return self._itemList[item_id].duplicatePart(part_id) 
        else:
            logging.error("Couldn't duplicate part of non-existant clothing item")
            return None

    def invertPart(self, item_id, part_id):
        if self.itemExists(item_id):
            self._saved = False
            self._itemList[item_id].invertPart(part_id)
        else:
            logging.error("Couldn't invert part of non-existant clothing item")

    def renamePart(self, item_id, part_id, name):
        if self.itemExists(item_id):
            self._saved = False
            self._itemList[item_id].renamePart(part_id, name)
        else:
            logging.error("Couldn't rename part of non-existant clothing item")

    def deletePart(self, item_id, part_id):        
        if self.itemExists(item_id):
            self._saved = False
            return self._itemList[item_id].deletePart(part_id)  
        else:
            logging.error("Couldn't delete part of non-existant clothing item")
            return None

    def swapPart(self, item_id, part_id, swap_steps):
        if self.itemExists(item_id):
            self._saved = False
            return self._itemList[item_id].swapPart(part_id, swap_steps)
        else:
            logging.error("Couldn't swap part of non-existant clothing item")
            return None

    def changePartParent(self, item_id, new_item_id, part_id):
        if not self.itemExists(item_id):
            logging.error("Cannot find existing parent item.")
            return None
        if not self.itemExists(new_item_id):
            logging.error("Cannot attach part to non-existent parent item")
            return part_id
        if item_id == new_item_id:
            logging.warning("Tried to change parent to the same one")
            return part_id
        self._itemList[item_id].removeJointPart(part_id)
        part_list = self._itemList[item_id].getPartList()
        part = part_list.pop(part_id)
        self._saved = False
        self._itemList[new_item_id].appendPart(part)
        return part_id - 1

 
    def addSegment(self, item_id, part_id, segment):
        if self.itemExists(item_id):
            self._saved = False
            return self._itemList[item_id].addSegment(part_id, segment)

    def changeSegmentEndpoint(self, item_id, part_id, segment_id, point_id, segement_endpoint):
        if self.itemExists(item_id):
            self._saved = False
            self._itemList[item_id].changeSegmentEndpoint(part_id, segment_id, point_id, segement_endpoint)

    def removeSegment(self, item_id, part_id, segment_id):
        if self.itemExists(item_id):
            self._saved = False
            return self._itemList[item_id].removeSegment(part_id, segment_id)


    def addJoint(self, item_id, joint):
        if self.itemExists(item_id):
            self._saved = False
            return self._itemList[item_id].addJoint(joint)

    def saveJoint(self, item_id, joint_id, parts, segments):
        if self.itemExists(item_id):
            self._saved = False
            self._itemList[item_id].changeJointComposition(joint_id, parts, segments)

    def removeJoint(self, item_id, joint_id):
        if self.itemExists(item_id):
            self._saved = False
            return self._itemList[item_id].removeJoint(joint_id)

    def invertJoint(self, item_id, joint_id):
        if self.itemExists(item_id):
            self._saved = False
            return self._itemList[item_id].invertJoint(joint_id)