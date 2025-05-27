import math
from shapely.geometry import Point, LineString, LinearRing, Polygon

import logging

class Tessellator(object):

    # Tesselation function only accepts the 11 Archimedial / semi-regular tessellation algorithms. It can be argued, 
    # that there are 12 because "3.3.3.3.6" can be two distinct variations, but for the purposes of this it is
    # implemented as one of them.
    ALGORITHMS = [ 
        "3.3.3.3.3.3",
        "3.3.3.3.6",
        "3.3.3.4.4",
        "3.3.4.3.4",
        "3.4.6.4",
        "3.6.3.6",
        "3.12.12",
        "4.4.4.4",
        "4.6.12",
        "4.8.8",
        "6.6.6",
        "4.6.12.a",
        "4.6.12.b"
    ]
    
    # Define specific vertex configurations and transition of angles over edges for recursion (if come from angle a,
    # which angle should be first on the other end). Also "mirror" parameter determines inverse angle order for 
    # tessellations which have changes between vertexes with angles in clockwise/counter clockwise directions
    _CONFIG = {
        "3.3.3.3.3.3": { "angles": [60,60,60,60,60,60], "next_angle_index": [1,2,3,4,5,0]}, #any index order ok
        "3.3.3.3.6":   { "angles": [60,60,60,60,120],   "next_angle_index": [1,3,2,0,4]}, #mirror variant index [2,1,3,0,4]/ [1,3,2,0,4]
        "3.3.3.4.4":   { "angles": [60,60,60,90,90],    "next_angle_index": [1,2,0,4,3]},
        "3.3.4.3.4":   { "angles": [60,60,90,60,90],    "next_angle_index": [1,3,2,0,4]},
        "3.4.6.4":     { "angles": [60,90,120,90],      "next_angle_index": [0,3,2,1]},
        "3.6.3.6":     { "angles": [60,120,60,120],     "next_angle_index": [0,3,2,1]}, #also other index possibilities like [0,1,2,3]
        "3.12.12":     { "angles": [60,150,150],        "next_angle_index": [0,2,1]},
        "4.4.4.4":     { "angles": [90,90,90,90],       "next_angle_index": [1,2,3,0]}, #any index order ok
        "4.6.12":      { "angles": [90,120,150],        "next_angle_index": [0,2,1], "mirror":[90,150,120]},
        "4.8.8":       { "angles": [90,135,135],        "next_angle_index": [0,2,1]},
        "6.6.6":       { "angles": [120,120,120],       "next_angle_index": [1,2,0]}, #any index order ok
        "4.6.12.a":     { "angles": [90,120,150],        "next_angle_index": [2,1,0]}, #NonArchimedian!!!!!
        "4.6.12.b":    { "angles": [90,120,150],        "next_angle_index": [0,2,1]}  #NonArchimedian!!!!!

    }
    
    def __init__(self, algorithm = "3.3.3.3.3.3", edge_length = 1, bounds = None, maximum_iterations = None,
                 debug_recursion = False, precision_decimals = 6):
        self._bounds = None
        self._interior = None
        self._debug_recursion = debug_recursion
        self._finished = True
        self._precision = precision_decimals
        self.algorithm = algorithm
        self.edge_length = edge_length
        self.bounds = bounds
        self.maximum_iterations = maximum_iterations
        self._reset_internal_state()
    
    @property
    def bounds(self):
        """ Gets and safely sets the current bounds """
        return self._bounds

    @bounds.setter
    def bounds(self, value):
        # For more complex checking to ensure that tessellation continues after crossing multiple edges back into bounds
        # a LinearRing object is required! Also a Polygon object representing interior is required for checking if endpoint is in bounds.
        if value is None:
            self._bounds = None
            self._interior = None
            return
        else:
            if not isinstance(value, list):
                logging.error("Could not set bounds! Value must be a list of coordinates!")
                return
            if not len(value)>2:
                logging.error("Bounds must have at least 3 coordinate points!")
                return
        # TODO - some error check would be nice if bounds can actually be turned into LinearRing and Polygon
        self._bounds = LinearRing(value)
        self._interior = Polygon(value)

    def _reset_internal_state(self):
        self._tessellation = { 
            "network": {},
            "points": {},
            "edge_points": {}
        }
        self._iterations_left = self.maximum_iterations
        if self._iterations_left is not None:
            self._iterations_left += 1
        self._finished = False
        
    def clear_results(self):
        self._reset_internal_state()
        
    def generate(self, point, initial_angle = 0):
        if self.algorithm not in Tessellator.ALGORITHMS:
            logging.error("Bad parameter tessellation algorithm: Unknown configuration! ("+self.algorithm+")")
            return

        if self._bounds is None and self.maximum_iterations is None:
            logging.error("Must set either bounding coordinates or max iterations, otherwise recursion will run forever!")
            return
        
        if self._interior is not None and self._interior.area<0.0000001:
            logging.error("Bounds object must enclose an area > 0 !")
            return

        if not self._interior.contains(point):
            logging.error("Seed point must be inside bounds enclosure!")
            return

        if self._finished:
            logging.warning("Generating tessellation over an existing sample - possible data loss")
        self._reset_internal_state()
        self._tessellate(point, initial_angle)
        self._finished = True

    def _extract_list_from_hashtable(self, htable):
        lst = []
        for key in htable:
            lst.append(htable[key])
        return lst
        
    def get_generated_grid(self):
        if not self._finished:
            logging.warning("Requested generated grid, without calling generate() first!")
        return self._extract_list_from_hashtable(self._tessellation["network"])

    def get_generated_grid_length(self):
        if not self._finished:
            logging.warning("Requested generated grid, without calling generate() first!")
        grid_length = 0.0
        for edge in self._tessellation["network"]:
            grid_length = grid_length + self._tessellation["network"][edge].length
        return grid_length        
    
    def get_generated_grid_point_count(self):
        if not self._finished:
            logging.warning("Requested generated grid point count, without calling generate() first!")
        return len(self._tessellation["points"])

    def get_generated_edge_points(self):
        if not self._finished:
            logging.warning("Requested generated edge points, without calling generate() first!")
        return self._extract_list_from_hashtable(self._tessellation["edge_points"])
    
    def _get_tuple_hash(self, tuple):
        x = '{number:.{digits}f}'.format(number=tuple[0], digits=self._precision)
        y = '{number:.{digits}f}'.format(number=tuple[1], digits=self._precision)
        return x+"_"+y        

    def _get_point_hash(self, point):
        # Provides point hash of form "X.XXX_Y.YYY" based on self._precision
        return self._get_tuple_hash(point.coords[0])

    def _get_edge_hash(self, my_edge):
        # Provides edge hash of form "X.XXX_Y.YYY-x.xxx_y.yyy" based on self._precision
        points = my_edge.coords
        p1 = self._get_tuple_hash(points[0])
        p2 = self._get_tuple_hash(points[1])
        if p2<p1: #Hash two edges with swapped end points the same (order them in ascending order)
            p1, p2 = p2, p1
        return p1+"-"+p2

    def _point_is_processed(self, shapely_point):
        phash = self._get_point_hash(shapely_point)
        if phash in self._tessellation["points"]:
            return True
        return False

    def _edge_is_new(self, shapely_edge):
        # Comparison for shapely LineStrings is buggy in current version, so have to check both combinations of endpoint rough equiality
        ehash = self._get_edge_hash(shapely_edge)
        if ehash in self._tessellation["network"]:
            return False
        return True

    def _pointify_collection(self, shape_collection):
        point_list = []
        for item in shape_collection:
            if isinstance(item, Point):
                point_list.append(item)
                continue
            if isinstance(item, LineString):
                for coordpair in list(item.coords):
                    point_list.append(Point(coordpair))
        return point_list
        
    def _get_closest_point(self, point, point_list):
        mdist = math.inf
        mp = None
        for pt in point_list:
            dst = point.distance(pt)
            if dst<mdist:
                mdist = dst
                mp = pt
        return mp


    def _debug(self, message):
        if self._debug_recursion:
            print(message)
            logging.debug(message)
    
    def _tessellate(self, point, zero_angle, angle_index = 0, counter_clockwise = True, recursion_path = ""):
        # Fill recursion path for debugging
        if self._debug_recursion:
            recursion_path += str(angle_index)

        self._debug("["+recursion_path+"] Entering ...")

        # Check if this iteration does not exceed maximum_iterations
        if self.maximum_iterations is not None:
            self._iterations_left -= 1
            if self._iterations_left < 1:
                self._debug("["+recursion_path+"] Max Tessellation recursion reached - Not executing - LIMIT")
                return
            
        # Check if point still is not processed otherwise - do nothing
        if self._point_is_processed(point):
            self._debug("["+recursion_path+"] Processed point reached - Not executing - DEADEND. "+str(point.xy))
            return
        
        # Can process - add point to processed list
        self._tessellation["points"][self._get_point_hash(point)] = point
        
        # Load configuration:
        config = Tessellator._CONFIG[self.algorithm]
        angles = config["angles"]
        if(counter_clockwise and ("mirror" in config)):
            angles = config["mirror"]
        step_count = len(angles)
            
        # Start tessellation!
        current_angle = zero_angle
        for i in range(0, step_count):
            current_angle_index = (i+angle_index)%step_count
            current_angle += angles[current_angle_index]
            endx = point.x + self.edge_length * math.cos(math.radians(current_angle))
            endy = point.y + self.edge_length * math.sin(math.radians(current_angle))
            new_point = Point(endx,endy)
            new_edge = LineString([point, new_point])
            out_of_bounds = False
            if (self._edge_is_new(new_edge)):
                if self._bounds is not None:
                    #new_linestring = LineString(new_edge)
                    tmp = new_edge.intersection(self.bounds)
                    if hasattr(type(tmp), '__iter__') or tmp is None or tmp.is_empty:
                        #Zero or more than one intersection - possibly both ends in!!!
                        tlist = []
                        if not tmp.is_empty:
                            tlist = list(tmp)
                        if len(tlist)>0:
                            #multiple intersections
                            p_list = self._pointify_collection(tlist)
                            edge_point = self._get_closest_point(point, p_list)
                            new_edge = LineString([point, edge_point])
                            self._tessellation["edge_points"][self._get_point_hash(edge_point)] = edge_point
                            out_of_bounds = True
                            # Check if endpoint is in _interior. If so, add end edge as well and cancel out of bounds!
                            if(self._interior.contains(new_point)):
                                edge_point = self._get_closest_point(new_point, p_list)
                                new_edge2 = LineString([edge_point, new_point])
                                self._tessellation["edge_points"][self._get_point_hash(edge_point)] = edge_point
                                self._tessellation["network"][self._get_edge_hash(new_edge2)] = new_edge2
                                out_of_bounds = False
                    else:
                        #Exactly one intersection (could be Point or LineString)
                        if isinstance(tmp, Point):
                            new_edge = LineString([point, tmp])
                            self._tessellation["edge_points"][self._get_point_hash(tmp)] = tmp
                            out_of_bounds = True
                        if isinstance(tmp, LineString):
                            edge_point = self._get_closest_point(point, list(tmp.coords))
                            new_edge = LineString([point, edge_point])
                            self._tessellation["edge_points"][self._get_point_hash(edge_point)] = edge_point
                            out_of_bounds = True

                    # FYI - what is happening up there...:
                    # Here the new edge can overlap bounds and even cross several bounds.. if list(tmp)=[] no intersections
                    # If length(list(tmp))>1 = multiple intersections. Could substract the geometry object tmp and get multiple
                    # Resulting segments. Must check which segments are within the bounds... if crossing point, the next segment not in bounds
                    # if crossing LineSegment, then bounding state is the same.
                    # IF endpoint withing bounds, then hit_bound = False. This can lead to several small edges being appended, but
                    # tessellation continues from the endpoint only not these small endpoints
                    
                # TODO: Here is a small bug (no need to fix): if edge is cut by bound, the new shorter one is not checked with _edge_is_new, but just overwritten
                # This double assignment is just more efficient than to double check every edge for this rare condition.
                self._tessellation["network"][self._get_edge_hash(new_edge)] = new_edge
                self._debug("["+recursion_path+"]{"+str(current_angle_index)+"} LINE: ("+str(point.x)+";"+str(point.y)+")->("+str(new_point.x)+";"+str(new_point.y)+")")
            if out_of_bounds:
                continue
            # Recursively process the new_point
            new_direction = not counter_clockwise
            reversed_angle = (current_angle + 180) % 360
            next_angle_index = config["next_angle_index"][current_angle_index]
           
            self._tessellate(new_point, reversed_angle, next_angle_index, new_direction, recursion_path)