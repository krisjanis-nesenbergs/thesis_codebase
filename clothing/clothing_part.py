from math import inf as INFINITY      # for infinity
import logging

class ClothingPart(object): #One cutout part of a clothing item
    def __init__(self, name):
        self.Name = name #Name of the part
        self.PointList = [] #list of points in the part
        self._segmentList = [] # list of defined segments

        self.base_x = INFINITY #Max number - when loading will be set to minimum point deviation from (0,0) for displaying/point normalization
        self.base_y = INFINITY
        self.normalized = False

    def addPoint(self, point_x, point_y):
        if not self.normalized:
            self.PointList.append([point_x,point_y])
            if self.base_x > point_x:
                self.base_x = point_x
            if self.base_y > point_y:
                self.base_y = point_y

    def normalize(self):
        if self.normalized:         # Only normalize if not already normalized
            return

        for i, point in enumerate(self.PointList):
            self.PointList[i][0] = point[0]-self.base_x
            self.PointList[i][1] = point[1]-self.base_y
        tmplist = []
        for i in self.PointList:
            if i not in tmplist:
                tmplist.append(i)
        self.PointList = tmplist
        self.normalized = True

    def invertPart(self):
        if not self.normalized:
            logging.warning("Part inversion requires normalized parts!")
            return False
        # Invert point order
        self.PointList.reverse()

        inversion_value = len(self.PointList) - 1
        for i, segment in enumerate(self._segmentList):
            self._segmentList[i][0], self._segmentList[i][1] = self._segmentList[i][1], self._segmentList[i][0]
            self._segmentList[i][0] = inversion_value - self._segmentList[i][0]
            self._segmentList[i][1] = inversion_value - self._segmentList[i][1]

        # TODO Segments are bad (because points are inverted....also order in pairs ir wrong... just remove???)
        # Mirror points on X axis abusing normalization
        old_base_x = self.base_x
        old_base_y = self.base_y
        self.base_y = 0
        self.base_x = 0
        for i, point in enumerate(self.PointList):
            if point[0]>self.base_x:
                self.base_x = point[0]
            self.PointList[i][0] = -point[0]
        self.base_x = -self.base_x
        self.normalized = False
        self.normalize()
        self.base_x = old_base_x
        self.base_y = old_base_y


    def getSegmentList(self):
        return self._segmentList

    def addSegment(self, segment):
        self._segmentList.append(segment)
        return len(self._segmentList) - 1

    def changeSegmentEndpoint(self, segment_id, point_id, segment_endpoint):
        segment_list_length = len(self._segmentList)
        if segment_list_length <= segment_id:
            logging.error("ERROR: Tried to change unknown segment endpoint")
            return
        self._segmentList[segment_id][segment_endpoint] = point_id

    def removeSegment(self, segment_id):
        if self.getSegment(segment_id) is None:
            return None
        del self._segmentList[segment_id]
        if segment_id > 0:
            return segment_id - 1
        else:
            return None

    def getSegment(self,segment_id):
        if segment_id is None or segment_id > len(self._segmentList):
            return None
        return self._segmentList[segment_id]

    def getSegmentPoints(self, segment_id):
        segment_point_list = []
        segment = self.getSegment(segment_id)
        if segment is None or self.PointList is None or len(self.PointList)<1:
            return segment_point_list
        if segment[0] > segment[1]:
            segment_point_list = self.PointList[segment[0]:]
            #+1 is for also selecting the last point, not last-1
            segment_point_list.extend(self.PointList[:segment[1]+1])   
        else:
            #+1 is for also selecting the last point, not last-1
            segment_point_list = self.PointList[segment[0]:segment[1]+1]
        return segment_point_list