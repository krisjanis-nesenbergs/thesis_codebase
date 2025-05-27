import logging   # Import logging/print functionality

from .clothing_part import ClothingPart

import copy


class ClothingItem(object):
    def __init__(self,name=""):
        self.Name = name #Name of the clothing item
        self._partList = [] #List of parts in this one clothing item
        self._jointList = [] #List of joints in this clothing item

    # Functon to add a part from DXF file to the PartList in this ClothingItem - including setting the provided human readable label and normalizing points in the part
    def addDXFpart(self, label, dxf_points):
        new_part = ClothingPart(label)
        logging.debug("DXF Entity: %s\n" % dxf_points)
        for point in dxf_points:
            new_part.addPoint(point[0],point[1])
        new_part.normalize()
        self._partList.append(new_part)    

    def partExists(self,part_id):
        if part_id is None:
            return False
        if len(self._partList)>part_id and part_id>=0:
            return True
        return False

    def getPartList(self):
        return self._partList

    def duplicatePart(self, part_id):
        if self.partExists(part_id):
            part = copy.deepcopy(self._partList[part_id])
            self._partList.append(part)
            return self._partList.index(part) 
        else:
            logging.error("Tried duplicating non-existant part")
            return None

    def invertPart(self, part_id):
        if self.partExists(part_id):
            self._partList[part_id].invertPart()
        else:
            logging.error("Tried to invert non-existant part")

    def renamePart(self, part_id, name):
        if self.partExists(part_id):
            self._partList[part_id].Name = name
        else:
            logging.error("Tried renaming non-existant part")

    def deletePart(self, part_id):
        if self.partExists(part_id):    
            self.removeJointPart(part_id)    
            del self._partList[part_id]     
            return part_id-1
        else:
            logging.error("Tried to delete nonexisting part!")
            return None  

    def swapPart(self, part_id, swap_steps):
        if self.partExists(part_id):
            new_part_id = part_id + swap_steps
            if new_part_id >=0 and new_part_id < len(self._partList):
                self.swapJointParts(part_id,new_part_id)
                self._partList[part_id], self._partList[new_part_id] = self._partList[new_part_id], self._partList[part_id] 
                #TODO: swap joint values of swapped parts......
                return new_part_id
            else:
                logging.warning("Could not shift part to new row.")
                return part_id      
        else:
            logging.error("Tried swapping nonexistant part")
            return None

    def appendPart(self, part):
        self._partList.append(part)  

    def addSegment(self, part_id, segment):
        if self.partExists(part_id):
            return self._partList[part_id].addSegment(segment)
        else:
            logging.error("No part exists to add segment for...")
            return None

    def changeSegmentEndpoint(self, part_id, segment_id, point_id, segment_endpoint):
        if self.partExists(part_id):
            self._partList[part_id].changeSegmentEndpoint(segment_id, point_id, segment_endpoint)
        else:
            logging.error("No part exists to change segment endpoint for...")
            return None

    def removeSegment(self, part_id, segment_id):
        if self.partExists(part_id):
            self.removeJointSegment(part_id, segment_id)
            return self._partList[part_id].removeSegment(segment_id)
        else:
            logging.error("No part exists to remove segment for...")
            return None


    def getJointList(self):
        return self._jointList

    def addJoint(self, joint):
        self._jointList.append(joint)
        return len(self._jointList) - 1

    def changeJointComposition(self, joint_id, parts, segments):
        joint_list_length = len(self._jointList)
        if joint_id is None or joint_list_length <= joint_id:
            logging.error("Tried to change unknown joint composition")
            return
        self._jointList[joint_id].changeJointComposition(parts, segments)

    def removeJoint(self, joint_id):
        if joint_id is None or joint_id >= len(self._jointList):
            return None
        del self._jointList[joint_id]
        if joint_id > 0:
            return joint_id - 1
        else:
            return None

    def invertJoint(self, joint_id):
        if joint_id is None or joint_id >= len(self._jointList):
            return None
        self._jointList[joint_id].invertState()
        return None

    def removeJointSegment(self, part_id, segment_id):
        for joint in self._jointList:
            joint.removeSegment(part_id, segment_id)

    def removeJointPart(self, part_id):
        for joint in self._jointList:
            joint.removePart(part_id)

    def swapJointParts(self, part_id, new_part_id):
        for joint in self._jointList:
            joint.swapParts(part_id, new_part_id)