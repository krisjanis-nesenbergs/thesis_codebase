import logging   # Import logging/print functionality
from .generator_constants import GeneratorConstants
import random
from shapely.geometry import Point, Polygon, LineString


class AdjustedClothingItem(object): #One clothing item, adjusted by sex and size, can contain sink and seed points

    # Seeds = list of {"x":x, "y":y, "angle":angle} for each part
    def __init__(self, clothing_id, clothing_item, sex=None, size="L", sink=None, seeds=None, precision_decimals = 6):
        self.clothing_id = clothing_id
        self.clothing_item = clothing_item
        self.size = size
        self.sex = sex
        self._precision_constant = 1*10**(-precision_decimals)

        self._part_area = None

        if self.sex is None:
            self._update_sex_from_name()

        self._adjusted_bounds = None

        self.ratio = self._get_clothe_size_ratio()

        self.sink = sink
        if self.sink is None:
            self._generate_sink_location()
        
        self.seeds = seeds
        if self.seeds is None:
            self._generate_seeds()

        self._segment_points = None

    def _generate_sink_location(self):
        random_part, random_point = self.get_random_point()
        self.sink = {"part_id":random_part, "x":random_point.x, "y":random_point.y}

    def get_random_point(self):
        random_part = self._proportional_random_part()
        random_point = self._random_point_in_shell(self.get_adjusted_part_bounds(random_part))
        return random_part, random_point

    def _proportional_random_part(self):
        part_count = self.get_part_count()

        if self._part_area == None:
            self._part_area = []
            for part_index in range(part_count):
                bounds = self.get_adjusted_part_bounds(part_index)
                interior = Polygon(bounds)
                self._part_area.append(interior.area)
        
        return random.choices(range(part_count), weights=self._part_area, k=1)[0]

    def _generate_seeds(self):
        self.seeds = []
        for pid in range(self.get_part_count()):
            pt = self._random_point_in_shell(self.get_adjusted_part_bounds(pid))
            self.seeds.append({"x":pt.x, "y":pt.y, "angle":random.randrange(0,360)})

    def _get_clothe_size_ratio(self):
        return GeneratorConstants.SIZES[self.size][self.sex]*GeneratorConstants.MM_PER_UNIT

    def _update_sex_from_name(self):
        self.sex = self.clothing_item.Name[2]
        if self.sex not in ["M","F"]:
            logging.error("Could not determine clothing item sex from its name! Defaulting to Male...")
            self.sex = "M"

    def regenerate_sink_and_seeds(self):
        self._generate_sink_location()
        self._generate_seeds()

    def regenerate_sink(self):
        self._generate_sink_location()

    def get_part_count(self):
        return len(self.clothing_item.getPartList())

    def _generate_segment_points(self):
        self._segment_points = []
        for pid, part in enumerate(self.clothing_item.getPartList()):
            part_segments = []
            for segment in part.getSegmentList():
                segment_point_list = []
                if segment[0] > segment[1]:
                    segment_point_list = self.get_adjusted_part_bounds(pid)[segment[0]:]
                    #+1 is for also selecting the last point, not last-1
                    segment_point_list.extend(self.get_adjusted_part_bounds(pid)[:segment[1]+1])   
                else:
                    #+1 is for also selecting the last point, not last-1
                    segment_point_list = self.get_adjusted_part_bounds(pid)[segment[0]:segment[1]+1]
                part_segments.append(LineString(segment_point_list))
            self._segment_points.append(part_segments)

    def _get_local_segment(self, part_id, point):
        ## find the segent ID for the current adjusted part (getSegmentList()), that is the closest to the point (min distance)
        ## return the part_id, segment_id and relative point coordinates to the segment[0] point

        if(self._segment_points is None):
            self._generate_segment_points()
        min_dist = float("inf")
        min_index = None
        for index, segment in enumerate(self._segment_points[part_id]):
            tmp_dist = segment.distance(point)
            if tmp_dist<min_dist:
                min_dist = tmp_dist
                min_index = index
        if min_dist > self._precision_constant:
            logging.error("No segment found matching the point")
            return None

        relative_point = self._segment_points[part_id][min_index].project(point, True)
        return [part_id, min_index, relative_point] # [Part_ID, segment_id, relative_point (% of the length of segment)]


    def _get_opposing_segment(self, part_id,local_segment_id):
        ## Find the other segment, that matches this one
        ## Error if more than one matching segment exists!!!
        opposing_segment = None # [Part_ID, segment_id, isinverted]
        for joint in self.clothing_item.getJointList():
            pids = joint.getParts()
            segs = joint.getSegments()
            if(pids[0]==part_id and segs[0]==local_segment_id):
                if(opposing_segment is not None):
                    logging.error("More than one Opposing segment found!")
                opposing_segment = [pids[1], segs[1], joint.isInverted()]
            if(pids[1]==part_id and segs[1]==local_segment_id):
                if(opposing_segment is not None):
                    logging.error("More than one Opposing segment found!")
                opposing_segment = [pids[0], segs[0], joint.isInverted()]
        return opposing_segment # [Part_ID, segment_id, isinverted]

    def get_opposing_point_coordinates(self, part_id, point):
        ## return local segment point in the coordinates of the opposing segment, as well as segment pointlist to check for closest
        ## points only on segment!!!
        ls = self._get_local_segment(part_id, point)
        os = self._get_opposing_segment(part_id, ls[1])
        if os is None:
            return None
        os_pointlist = self._segment_points[os[0]][os[1]]
        if os[2] is True:
            return [os[0], os_pointlist.interpolate(1-ls[2], True), os_pointlist]
        else:
            return [os[0], os_pointlist.interpolate(ls[2], True), os_pointlist]

    def get_adjusted_part_bounds(self, part_id):
        # Fill adjusted point lists for each part if not set
        if self._adjusted_bounds is None:
            self._adjusted_bounds = []
            for pid in range(self.get_part_count()):
                adjusted_point_list = self.clothing_item.getPartList()[pid].PointList
                adjusted_point_list = list(map(lambda x: [x[0]*self.ratio,x[1]*self.ratio], adjusted_point_list))
                self._adjusted_bounds.append(adjusted_point_list)
        return self._adjusted_bounds[part_id]

    @staticmethod
    def _random_point_in_shell(shell):
        interior = Polygon(shell)
        max_x = max(x for x, y in shell)
        max_y = max(y for x, y in shell)
        
        while True:
            x = round(random.uniform(0, max_x),3)
            y = round(random.uniform(0, max_y),3)
            p = Point(x,y)
            if interior.contains(p):
                return p