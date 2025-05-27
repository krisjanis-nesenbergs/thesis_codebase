import logging   # Import logging/print functionality


class Joint(object): #A joint between two Parts
    def __init__ (self):
        self._parts = [0,0]
        self._segments = [0,0]
        self._inverted = False

    def getName(self):
        # Prefix the joint with +/- (+=normal order, -=inverted order)
        # In case segment points are [a1..aN] and [b1..bN], normal order
        # means a1 matches b1 and aN matches bN. In inverted order a1 
        # matches bN and aN matches b1
        inv_state = "+"
        if self._inverted:
            inv_state = "-"
        return inv_state + str(self._parts[0]) + "_" + str(self._segments[0])+", "+str(self._parts[1]) + "_" + str(self._segments[1])

    def getParts(self):
        return self._parts

    def getSegments(self):
        return self._segments

    def isInverted(self):
        return self._inverted

    def changeJointComposition(self, parts, segments):
        if len(parts) == 2 and len(segments) == 2:
            for i in range(2):
                if parts[i] is not None:
                    self._parts[i] = parts[i]
                else:
                    logging.error("Tried to set joint part to None!")
                    self._parts[i] = 0
                if segments[i] is not None:
                    self._segments[i] = segments[i]
                else:
                    logging.error("Tried to set joint segment to None!")
                    self._segments[i] = 0
        else:
            logging.error("Wrong joint composition vector lengths")

    def removeSegment(self, part_id, segment_id):
        if part_id is None or segment_id is None:
            logging.warning("Tried removing nonexistent segment/joint combo from Joint!")
            return
        for i in range(2):
            if self._parts[i] == part_id:
                if segment_id < self._segments[i]:
                    self._segments[i] = self._segments[i]-1
                else:
                    if segment_id == self._segments[i]:
                        self._segments[i] = 0

    def removePart(self, part_id):
        if part_id is None:
            logging.warning("Tried removing nonexistant part from Joint!")
            return
        for i in range(2):
            if part_id < self._parts[i]:
                self._parts[i] = self._parts[i]-1
            else:
                if part_id == self._parts[i]:
                    self._parts[i] = 0
                    self._segments[i] = 0

    def swapParts(self, part_id, new_part_id):
        for i in range(2):
            if part_id == self._parts[i]:
                self._parts[i] = new_part_id
            elif new_part_id == self._parts[i]:
                self._parts[i] = part_id

    def invertState(self):
        self._inverted = not self._inverted
