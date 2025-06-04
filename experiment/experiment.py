import logging   # Import logging/print functionality
#import json # For serialize/deserialize
from tessellator import Tessellator
from shapely.geometry import Point
from generator import GeneratorConstants
from generator import adjusted_clothing_item
from collections import deque
import numpy
import matplotlib.pyplot as plt
from datetime import datetime
import sys



class Experiment(object): #One specific experiment run tooling

    def prepare_experiment(self, ex_config, precision_decimals = 6):
        # From experiment config generate tessellations of all clothe parts and return everything for experiment
        maximum_tessellation_iterations = 10000
        self._precision = precision_decimals
        self._precision_constant = 1*10**(-precision_decimals)
        self.experiment_data = {
            "tessellations": [],
            "edge_points" : [],
            "config": ex_config,
            "clothe": ex_config.adjusted_clothe,
            "grid_length": 0.0, #in mm, GeneratorConstants.MM_PER_UNIT
            "node_count": 0,
            "edge_hash": {},
            "vertex_hash": {},
            "reachable_nodes":{"shortest":set(), "least_jumpers":set()},
            "jumpers": {}
        }

        ex_tess = Tessellator(algorithm = ex_config.tessellation_algorithm, edge_length = ex_config.node_distance, maximum_iterations = maximum_tessellation_iterations)

        a_clothe = self.experiment_data["clothe"]
        part_count = a_clothe.get_part_count()

        for part_index in range(part_count):
            ex_tess.bounds = a_clothe.get_adjusted_part_bounds(part_index) #in mm
            ex_tess.clear_results()
            ex_tess.generate(Point(a_clothe.seeds[part_index]["x"],a_clothe.seeds[part_index]["y"]),a_clothe.seeds[part_index]["angle"])
            self.experiment_data["tessellations"].append(ex_tess.get_generated_grid())
            self.experiment_data["edge_points"].append(ex_tess.get_generated_edge_points())
            self.experiment_data["grid_length"] += ex_tess.get_generated_grid_length() #Don't accidentally multiply by mm units, already in mm
            self.experiment_data["node_count"] += ex_tess.get_generated_grid_point_count()
            #print(ex_tess.get_generated_grid_length(), "part grid length in mm!")
            

    def _get_tuple_hash(self, tuple, clothe_id):
        x = '{number:.{digits}f}'.format(number=tuple[0], digits=self._precision)
        y = '{number:.{digits}f}'.format(number=tuple[1], digits=self._precision)
        return str(clothe_id)+"_"+x+"_"+y        

    def _get_point_hash(self,point, clothe_id):
        # Provides point hash of form "CID_X.XXX_Y.YYY" based on self._precision
        return self._get_tuple_hash(point.coords[0], clothe_id)

    def _add_unique_hash_point(self,key1, key2, linestring, length):
        # If Linestring == None, this is a jumper!
        if key1 not in self.experiment_data["edge_hash"]:
            self.experiment_data["edge_hash"][key1] = {}
        if key2 not in self.experiment_data["edge_hash"][key1]:
            self.experiment_data["edge_hash"][key1][key2]={"linestring":linestring, "length":length}
        else:
            logging.error("Duplicate edge - IGNORED!")
    
    def _add_new_edge_to_hash(self, linestring, clothe_id):
        key1, key2, p1, p2 = self._linestring_to_keys(linestring, clothe_id)
        length = linestring.length
        #Add first endpoint
        self._add_unique_hash_point(key1, key2, linestring, length)
        #Add second endpoint
        self._add_unique_hash_point(key2, key1, linestring, length)
        
        if key1 not in self.experiment_data["vertex_hash"]:
            self.experiment_data["vertex_hash"][key1] = {"point": Point(p1), "part": clothe_id, "route_shortest":None, "route_least_jumpers": None}
        if key2 not in self.experiment_data["vertex_hash"]:
            self.experiment_data["vertex_hash"][key2] = {"point": Point(p2), "part": clothe_id, "route_shortest":None, "route_least_jumpers": None}

    def _reset_shortest_routes(self):
        for key in self.experiment_data["vertex_hash"]:
            self.experiment_data["vertex_hash"][key]["route_shortest"] = None
            self.experiment_data["vertex_hash"][key]["route_least_jumpers"] = None

    def _linestring_to_keys(self, linestring, clothe_id):
        points = linestring.coords
        key1 = self._get_tuple_hash(points[0], clothe_id)
        key2 = self._get_tuple_hash(points[1], clothe_id)
        return key1, key2, points[0], points[1]
        
    def _add_new_jumper_to_hash(self, p1, p2, clothe_id1, clothe_id2, length):
        key1 = self._get_tuple_hash(p1.coords[0], clothe_id1)
        key2 = self._get_tuple_hash(p2.coords[0], clothe_id2)
        temp_key = self._unique_line_hash(key1, key2)
        if temp_key not in self.experiment_data["jumpers"]:
            self.experiment_data["jumpers"][temp_key] = [[p1,clothe_id1],[p2,clothe_id2], length] #For jumper visualization if needed, also added to edge hash list with Linestring=None
            #Add first endpoint
            self._add_unique_hash_point(key1, key2, None, length)
            #Add second endpoint
            self._add_unique_hash_point(key2, key1, None, length)
            return temp_key
        return None
    
    def _unique_line_hash(self, key1, key2):
        if key2<key1: #Hash two edges with swapped end points the same (order them in ascending order)
            key1, key2 = key2, key1
        return key1+"_"+key2
        
        

    def prepare_geometry_hashtable(self):
        self.experiment_data["vertex_hash"]={}
        self.experiment_data["edge_hash"]={}
        for clothe_id, tess in enumerate(self.experiment_data["tessellations"]):
            for edge in tess:
                self._add_new_edge_to_hash(edge, clothe_id)
        
        # For faster experiments the data is enriched with hashtables for searching linestrings by rounded endpoint coordinates
        # as well as precalculated edge lengths
        ## Place both endpoints in hasthable "vertex_hash"
        ## part_x_y: {
        ##     {route_shortest, route_least_jumpers}
        ## }
        ## where route contains - {[jumper count, distance in units, distance in node count, list of blocked jumper targets}
        ## List of blocked jumper targets is either None, if we want to find shortest route whatever the jumper count is or
        ##    a list of parts, jumps to which are prohibited, used to not jump back to parts already visited in this route
        ##    thus leading to minimum amount of jumpers in the shortest paths
        ## Also place edges in hashtable "edge_hash" (both ways for easy access)
        ## part_x_y: {
        ##        other_end_hash: {linestring, length},
        ##            ...,
        ##            ...,
        ##        other_end_hash: {linestring, length}}
        ##           }

        return None
    
    def get_close_points(self, point, point_list, distance):
        results = []
        for candidate_point in point_list:
            if point.distance(candidate_point)<=distance:
                results.append(candidate_point)
        return results
    
    def _jumper_cleanup(self):
        for vert in self.experiment_data["vertex_hash"]:
            self.experiment_data["vertex_hash"][vert]["route_shortest"] = None
            self.experiment_data["vertex_hash"][vert]["route_least_jumpers"] = None

        for k1 in self.experiment_data["edge_hash"]:
            for k2 in list(self.experiment_data["edge_hash"][k1].keys()):
                if self.experiment_data["edge_hash"][k1][k2]["linestring"] is None:
                    ##This is a jumper, remove it (TODO NOTE: This will leave some edge_hash entries with key1 and no sub items of key two... not sure if bad..)
                    del self.experiment_data["edge_hash"][k1][k2]
        pass

    def regenerate_jumpers(self, distance):
        ##for each edge point find all other edge points and add to vertex_hash
        
        ## create Jumper list for all clothing items (ordered by lowest ID clothing item, so no double jumpers in each direction)
        ## Jumpers start on clothing part edge points and find all other edge points in joints on the other side linking them
        ##(if joint radiuss is not exceeded)regenerate_jumpers
        ## for each part and its edge point _get_local_segment > _get_opposing_segment > get opposing point coordinates >
        ## calculate distance from opposing point to all edge points of the opposing segment part > 
        ## if distance less than joint radiuss add to jumper set
        
        a_clothe = self.experiment_data["clothe"]
                
        if self.experiment_data["jumpers"] is not None and len(self.experiment_data["jumpers"])>0:
            ##jumpers were generated before - clean up!
            self._jumper_cleanup()

        self.experiment_data["jumpers"] = {}
        total_jumper_length = 0.0
        total_jumper_count = 0
        for item_id, item_edge_points in enumerate(self.experiment_data["edge_points"]):
            for edge_point in item_edge_points:
                op_point = a_clothe.get_opposing_point_coordinates(item_id, edge_point)
                if op_point is not None:
                    close_points = self.get_close_points(op_point[1],self.experiment_data["edge_points"][op_point[0]], distance)
                    #Add all close points to jumpers   
                    for close_p in close_points:
                        ## Some close edge points are from different segment, so we check if the found point in on real segment where op_point is!
                        if op_point[2].distance(close_p)<self._precision_constant:
                            j_len = close_p.distance(op_point[1])
                            tmp = self._add_new_jumper_to_hash(edge_point, close_p, item_id, op_point[0], j_len)
                            if tmp is not None:
                                total_jumper_length += j_len
                                total_jumper_count += 1

        return total_jumper_length, total_jumper_count

    def _get_closest_edge_on_part(self, point, part):
        min_dist = 9999999.0
        min_line = None
        for line in self.experiment_data["tessellations"][part]:
            dist = point.distance(line)
            if dist<min_dist:
                min_dist = dist
                min_line = line
        return min_dist, min_line
    
    def _get_center_and_CI95(self, nparr, mode = 0, percentiles = False, iterations = 1000):
        #Bootstrap variability of center tendency.
        # Modes: (0) Only for median, (1) Only for max, (2) only for median
        size = nparr.size
        
        if size == 0:
            if percentiles is True:
                return [-1.0,-1.0,-1.0, [-1.0,-1.0,-1.0,-1.0,-1.0,-1.0], -1.0]
            return [-1.0, -1.0, -1.0]


        center = 0.0
        centers = numpy.zeros(iterations)
        lci = 0.0
        hci = 0.0

        #percentiles 5th, 10th, 25th, 50th, 75th, 90th, 95th
        perc = []

        if percentiles is True:
            perc = [
                numpy.percentile(nparr, 5.0),
                numpy.percentile(nparr, 10.0),
                numpy.percentile(nparr, 25.0),
                #numpy.percentile(nparr, 50.0),  # not used = matches median
                numpy.percentile(nparr, 75.0),
                numpy.percentile(nparr, 90.0),
                numpy.percentile(nparr, 95.0)
                        ]

        #mean = 0.0
        median = 0.0
        max = 0.0

        #mean_lci = 0.0
        #mean_hci = 0.0
        median_lci = 0.0
        median_hci = 0.0
        max_lci = 0.0
        max_hci = 0.0

        
        if mode==0:
            center = numpy.median(nparr)
        if mode==1:
            center = numpy.max(nparr)
        if mode==2:
            center = numpy.mean(nparr)

        

        for i in range(iterations):
            resample = numpy.random.choice(nparr, size, replace = True)
            if mode==0:
                centers[i] = numpy.median(resample)
            if mode==1:
                centers[i] = numpy.max(resample)
            if mode==2:
                centers[i] = numpy.mean(resample)

        lci = numpy.percentile(centers, 2.5) #95% ci = 2.5-97.5, bet 99% ci - 0.5 - 99.5
        hci = numpy.percentile(centers, 97.5)

        if percentiles is True:
            mean = numpy.mean(nparr) # also calculate mean, just in case (normally using median)
            return [center, lci, hci, perc, mean]
        return [center, lci, hci]

    def get_statistics(self, nparr, plot = False, percentiles=False, mode = 0):
        # get numpy array and gather descriptive statistics as well as warn if non-normal distribution
        #print("STATS_ANALYSIS")
        if plot:
            #plt.hist(nparr, bins = 100)
            plt.hist(nparr)
            plt.title("Autohistogram with bins")
            plt.show()


        #### MODE = useless because data continuous, most values only once, Mean not good because distributions skewed/non-normal, using median mostly
        # mean = numpy.mean(nparr) - not appropriate for skewed/non-normal distributions
        
        center = self._get_center_and_CI95(nparr, mode = mode, percentiles = percentiles)

        #print(f"Median with 95% Confidence Interval: ({median[0]:.2f} ({median[1]:.2f} - {median[2]:.2f}) ++ {(median[2]-median[0]):.2f} /-- {(median[0]-median[1]):.2f}")

        return center
    
    
    def recursively_determine_distances(self):
        #Set up a queue of points to process
        ## queue contains a list of points. Two entries per point - one for each algorythm. EntrieS are lists with these items:
        ## 1) Unique ID of the point
        ## 2) Shortest distance to that point (in specific algorythm)]
        ## 3) Jumper count to point
        ## 4) Node count to point
        ## 5) None for shortest path, or list of blocked jumping parts for min jumper algorythm 
        processing_queue = deque()
        self.experiment_data["reachable_nodes"] = {"shortest":set(), "least_jumpers":set()}
        self._reset_shortest_routes()
        #find closest line sinknode, add both endpoints with distance (to projection + distance to line) to queue
        sink_point_data = self.experiment_data["clothe"].sink
        sink_point = Point(sink_point_data["x"], sink_point_data["y"])
        part_id = sink_point_data["part_id"]
        dist, closest_edge = self._get_closest_edge_on_part(sink_point, part_id)
        projected_point = closest_edge.interpolate(closest_edge.project(sink_point))

        closest_edge_end_points = closest_edge.coords
        for pt in closest_edge_end_points:
            p_key = self._get_tuple_hash(pt, part_id)
            p = Point(pt)
            d = p.distance(projected_point) + dist
            processing_queue.append([p_key, d, 0, 1, None]) #without jump block for real shortes path
            processing_queue.append([p_key, d, 0, 1, [part_id]]) #With jump block list containing this part for minimized jumpers
            self.experiment_data["vertex_hash"][p_key]["route_shortest"] = [0, d, 1, None, None, False, 0]
            self.experiment_data["vertex_hash"][p_key]["route_least_jumpers"] = [0, d, 1, None, None, False, 0]
            
        #print("Processing network...")
            
        #iterate over queue, for all points reached with lower distance/jump&distance combo, add them to queue
        # VERTEX_HASH =  structue WHERE KEYS ARE POINT ids and values={point, part, route_shortest, route_least_jumpers}
        #route contains - [jumper count, distance in units, distance in node count, list of blocked jumper targets, previous node, is furthest?, outgoing paths to route to]
        #EDGE_HASH = structure where points are keys and values={structures where keys = reachable point id and values = {linestring, length}}
        cnt_a = 1
        cnt_b = 1

        while processing_queue:
            queue_item = processing_queue.popleft()
            current_point_id = queue_item[0]
            
            if queue_item[4] == None:
                self.experiment_data["reachable_nodes"]["shortest"].add(current_point_id)
            else:
                self.experiment_data["reachable_nodes"]["least_jumpers"].add(current_point_id)

            exit_point = self.experiment_data["vertex_hash"][current_point_id] 
            #print("EH",self.experiment_data["edge_hash"])
            #print("VH",self.experiment_data["vertex_hash"])
            #exit

            #For each other point connected to  this current point that we are processing, get 
            a_spawn = 0
            b_spawn = 0

            for point_id in self.experiment_data["edge_hash"][current_point_id]:  ## TODO - PROB NOTHING - can this be not defined in some edge cases, like when cleaning jumpers out? if so check if exists first....
                entry_point = self.experiment_data["vertex_hash"][point_id]
                di = self.experiment_data["edge_hash"][current_point_id][point_id]["length"]
                if queue_item[4] == None:
                    # Processing normal distance usecase
                    new_distance = di + exit_point["route_shortest"][1]

                    if entry_point["route_shortest"] == None or new_distance < entry_point["route_shortest"][1]:
                        new_jumper_count = exit_point["route_shortest"][0]
                        if self.experiment_data["edge_hash"][current_point_id][point_id]["linestring"] == None:  #Jumper
                            new_jumper_count += 1
                        new_node_count = exit_point["route_shortest"][2] + 1
                        self.experiment_data["vertex_hash"][point_id]["route_shortest"] = [new_jumper_count,new_distance,new_node_count, None, current_point_id, False,0]

                        processing_queue.append([point_id, new_distance, new_jumper_count, new_node_count, None])
                        self.experiment_data["vertex_hash"][current_point_id]["route_shortest"][6] = self.experiment_data["vertex_hash"][current_point_id]["route_shortest"][6] + 1
                        a_spawn = 1
                        cnt_a = cnt_a + 1
                else:
                    # Processing minimum jump distance usecase
                    if self.experiment_data["edge_hash"][current_point_id][point_id]["linestring"] == None and entry_point["part"] in queue_item[4]:
                        #This is a jumper that cannot be used due to jumper_block_list (min jumper path)
                        continue #Do not jump back!!! 
                    new_distance = di + exit_point["route_least_jumpers"][1]
                    if entry_point["route_least_jumpers"] == None or new_distance < entry_point["route_least_jumpers"][1]:
                        new_jumper_count = exit_point["route_least_jumpers"][0]
                        new_jumper_exclusion = queue_item[4]
                        if self.experiment_data["edge_hash"][current_point_id][point_id]["linestring"] == None:  #Jumper
                            new_jumper_count += 1
                            new_jumper_exclusion.append(entry_point["part"])
                        new_node_count = exit_point["route_least_jumpers"][2] + 1
                        self.experiment_data["vertex_hash"][point_id]["route_least_jumpers"] = [new_jumper_count,new_distance,new_node_count, new_jumper_exclusion, current_point_id, False, 0]

                        processing_queue.append([point_id, new_distance, new_jumper_count, new_node_count, new_jumper_exclusion])
                        self.experiment_data["vertex_hash"][current_point_id]["route_least_jumpers"][6] = self.experiment_data["vertex_hash"][current_point_id]["route_least_jumpers"][6] + 1
                        b_spawn = 1
                        cnt_b = cnt_b + 1
            if a_spawn == 0:
                self.experiment_data["vertex_hash"][current_point_id]["route_shortest"][5] = True
            if b_spawn == 0:
                if self.experiment_data["vertex_hash"][current_point_id]["route_least_jumpers"] is not None: # on first run this does not exist!
                    self.experiment_data["vertex_hash"][current_point_id]["route_least_jumpers"][5] = True
   
        return cnt_a, cnt_b

    def _get_useful_grid_statistics(self, res, row):
        ## Edge hash has all unique points, while vertex_hash only reachable points
        all_nodes = self.experiment_data["edge_hash"].keys()

        #Get unreachable and reachable node counts
        reachable_count = len(self.experiment_data["reachable_nodes"]["shortest"])
        if reachable_count != len(self.experiment_data["reachable_nodes"]["least_jumpers"]):
            logging.error("Unreachable nodes for shortest path algorythm and shortes least jumper path algorythm does not match! SHOULD NEVER HAPPEN!")
        unreachable_nodes = all_nodes-self.experiment_data["reachable_nodes"]["shortest"]
        
        # Get unreachable and reachable wire lengths (potentially costs a lot of resources...)
        counted =set()
        total_unreachable_wire_length = 0.0
        total_reachable_wire_length = 0.0
        total_unreachable_jumper_length = 0.0
        total_reachable_jumper_length = 0.0
        total_unreachable_jumper_count = 0.0
        total_reachable_jumper_count = 0.0


        for point_id in self.experiment_data["edge_hash"]:
            counted.add(point_id)
            total_len = 0.0
            total_jumper_len = 0.0
            jump_count = 0.0
            for ppp in self.experiment_data["edge_hash"][point_id]:
                if ppp not in counted:
                    if self.experiment_data["edge_hash"][point_id][ppp]["linestring"] is None:
                        total_jumper_len += self.experiment_data["edge_hash"][point_id][ppp]["length"]
                        jump_count += 1
                    else:
                        total_len += self.experiment_data["edge_hash"][point_id][ppp]["length"]
            if point_id in unreachable_nodes:
                total_unreachable_wire_length += total_len
                total_unreachable_jumper_length += total_jumper_len
                total_unreachable_jumper_count +=jump_count
            else:
                total_reachable_wire_length += total_len
                total_reachable_jumper_length += total_jumper_len
                total_reachable_jumper_count +=jump_count

        # TODO - get reachable graph max and average length in path length, node count and jumper count
        max_length_sh = 0.0
        avg_length_sh = 0.0
        max_length_lj = 0.0
        avg_length_lj = 0.0
        max_size_sh = 0.0
        avg_size_sh = 0.0
        max_size_lj = 0.0
        avg_size_lj = 0.0
        max_jumpers_sh = 0.0
        avg_jumpers_sh = 0.0
        max_jumpers_lj = 0.0
        avg_jumpers_lj = 0.0
        cnt_sh = 0
        cnt_lj = 0
        
        for vertex in self.experiment_data["vertex_hash"]:
            if self.experiment_data["vertex_hash"][vertex]["route_shortest"] is not None and self.experiment_data["vertex_hash"][vertex]["route_shortest"][5] == True:
                #furthest point in shortest graph
                tmp_r = self.experiment_data["vertex_hash"][vertex]["route_shortest"]
                if max_length_sh < tmp_r[1]:
                    max_length_sh = tmp_r[1]
                if max_size_sh < tmp_r[2]:
                    max_size_sh = tmp_r[2]
                if max_jumpers_sh < tmp_r[0]:
                    max_jumpers_sh = tmp_r[0]
                avg_length_sh += tmp_r[1]
                avg_size_sh += tmp_r[2]
                avg_jumpers_sh += tmp_r[0]
                cnt_sh += 1

            if self.experiment_data["vertex_hash"][vertex]["route_least_jumpers"] is not None and self.experiment_data["vertex_hash"][vertex]["route_least_jumpers"][5] == True:
                #furthest point in shortest graph
                tmp_r = self.experiment_data["vertex_hash"][vertex]["route_least_jumpers"]
                if max_length_lj < tmp_r[1]:
                    max_length_lj = tmp_r[1]
                if max_size_lj < tmp_r[2]:
                    max_size_lj = tmp_r[2]
                if max_jumpers_lj < tmp_r[0]:
                    max_jumpers_lj = tmp_r[0]
                avg_length_lj += tmp_r[1]
                avg_size_lj += tmp_r[2]
                avg_jumpers_lj += tmp_r[0]
                cnt_lj += 1

        res[row] = [
            row, #source npk
            reachable_count,
            len(unreachable_nodes),
            total_reachable_wire_length,
            total_unreachable_wire_length,
            total_reachable_jumper_length,
            total_unreachable_jumper_length,
            total_reachable_jumper_count,
            total_unreachable_jumper_count,
            # here starts shortest path graph depth info
            max_length_sh,
            (avg_length_sh/cnt_sh),
            max_size_sh,
            (avg_size_sh/cnt_sh),
            max_jumpers_sh,
            (avg_jumpers_sh/cnt_sh),
            # here starts least jumper path graph depth info
            max_length_lj,
            (avg_length_lj/cnt_lj),
            max_size_lj,
            (avg_size_lj/cnt_lj),
            max_jumpers_lj,
            (avg_jumpers_lj/cnt_lj),
            #These will be added later
            0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
        ]

        return
#        res = {
#            "reachable_node_count": reachable_count,
#            "unreachable_node_count": len(unreachable_nodes),
#            "reachable_wire_length": total_reachable_wire_length,
#            "unreachable_wire_length": total_unreachable_wire_length,
#            "reachable_jumper_length": total_reachable_jumper_length,
#            "unreachable_jumper_length": total_unreachable_jumper_length,
#            "reachable_jumper_count": total_reachable_jumper_count,
#            "unreachable_jumper_count": total_unreachable_jumper_count,
#            "graph_depth": {
#                "shortest_path": {
#                    "max_wire_length": max_length_sh,
#                    "avg_wire_length": (avg_length_sh/cnt_sh),
#                    "max_node_count": max_size_sh,
#                    "avg_node_count": (avg_size_sh/cnt_sh),
#                    "max_jumper_count": max_jumpers_sh,
#                    "avg_jumper_count": (avg_jumpers_sh/cnt_sh)
#                },
#                "least_jumper_path": {
#                    "max_wire_length": max_length_lj,
#                    "avg_wire_length": (avg_length_lj/cnt_lj),
#                    "max_node_count": max_size_lj,
#                    "avg_node_count": (avg_size_lj/cnt_lj),
#                    "max_jumper_count": max_jumpers_lj,
#                    "avg_jumper_count": (avg_jumpers_lj/cnt_lj)
#                }
#            }
#        }
        
 
    def _path_unvisited_length(self, visited, visited_j, start_point, route):
        res_len = 0
        prev_point = None
        if start_point not in visited:
            res_len = self.experiment_data["vertex_hash"][start_point][route][1]
            visited.add(start_point)
            prev_point = start_point
            start_point = self.experiment_data["vertex_hash"][start_point][route][4]
            if prev_point is not None and start_point is not None and self.experiment_data["edge_hash"][prev_point][start_point]["linestring"] == None: # jumper
                jumper_key = self._unique_line_hash(prev_point, start_point)
                visited_j.add(jumper_key)
            while start_point is not None:
                if start_point in visited:
                    res_len -= self.experiment_data["vertex_hash"][start_point][route][1]
                    break
                else:
                    visited.add(start_point)
                prev_point = start_point
                start_point = self.experiment_data["vertex_hash"][start_point][route][4]
                if prev_point is not None and start_point is not None and self.experiment_data["edge_hash"][prev_point][start_point]["linestring"] == None: # jumper
                    jumper_key = self._unique_line_hash(prev_point, start_point)
                    visited_j.add(jumper_key)
        return res_len




    def execute_experiment(self, ex_config, getTesselation = False, pretxt = ""):
        max_radius = ex_config.joint_radius

        print( pretxt+" Executing... @ "+datetime.now().strftime("%d-%m-%Y, %H:%M:%S"), flush=True)
        while True: #on rare starting conditions tesselation fails - if so - reseed and start again
            self.prepare_experiment(ex_config)  #does tesselation
            self.prepare_geometry_hashtable()  #fills hashtables 
            jumper_length, jumper_count = self.regenerate_jumpers(ex_config.joint_radius) #regenerates jumpers (first removes old ones, clears old jumpers and distances if set so new experiment can be run)
            #a_clothe = self.experiment_data["clothe"]

            edge_node_count = 0
            for item in self.experiment_data["edge_points"]:
                edge_node_count += len(item)

            results = {
                "total_wire_length": self.experiment_data["grid_length"],
                "total_jumper_length": jumper_length,
                "total_jumper_count": jumper_count,
                "center_node_count": self.experiment_data["node_count"],  ## NOTE: this is count of actual generated nodes not including edge nodes (where they are cut off on edge intersections)
                "edge_node_count": edge_node_count,
                "total_node_count": (self.experiment_data["node_count"]+edge_node_count)
            }

            #Sanity check (Disable later to improve speed TODO)
            if results["total_node_count"] != len(self.experiment_data["edge_hash"].keys()):
                logging.error(pretxt+"ERROR - node counts don't match correctly from two calculations! SHOULD ALLWAYS MATCH... RETRYING!")
                #sys.exit(pretxt+"Catastrophic fail with tesselation! Ending...")
                self.experiment_data["clothe"].regenerate_sink_and_seeds()
                continue
            break



        ##### NUMPY ARRAY no_tres columns ##### (for each iteration of source)
        # [0] = source_id
        # [1]-[20] - see _get_useful_grid_statistics()
        # [21]-... visited stats

        ##### NUMPY ARRAY no_res columns ##### (for each iteration of source/destination)
        # [0] = source_id, [1] = target_id
        # Two columns - even = shortest route, odd = least_jumpers algorithm
        # [2]/[3] reachable (0=no/1=yes)
        # [4]/[5] unreachable due to Max node radius/epselon being exceeded (0=no/1=yes)
        # Following only for reachable end points
        # [6]/[7] distance_used
        # [8]/[9] sensor_jumper_length (The distance from sensor point to closest wire, no more than max_radius/Epsilon)
        # [10]/[11] jumper_count_used
        # [12]/[13] node_count_used
        # [14]/[15] unvisited_distance_used (gathering how much distance used in this iteration that was not used in previous iterations [Per source node])
        # [4]/[5] 
        # [4]/[5] 
        # [4]/[5] 
        # [4]/[5] 
        # [4]/[5] 
        # [4]/[5] 
        # [4]/[5] 


        experiment_total_iterations = GeneratorConstants.SOURCE_POINTS*GeneratorConstants.DESTINATION_POINTS

        np_res = numpy.zeros(shape = (experiment_total_iterations, 16))
        np_tres = numpy.zeros(shape = (GeneratorConstants.SOURCE_POINTS, 29))                            


        # For each sink location do this
        q0 = 0
        q1 = 0
        q2 = 0
        q3 = 0
        q9 = 0

        if GeneratorConstants.SOURCE_POINTS >1:
            q2 = GeneratorConstants.SOURCE_POINTS /2
        if GeneratorConstants.SOURCE_POINTS >3:
            q1 = GeneratorConstants.SOURCE_POINTS /4
            q3 = q1*3
        if GeneratorConstants.SOURCE_POINTS >9:
            q0= GeneratorConstants.SOURCE_POINTS / 10
            q9=q0*9

        for count in range(GeneratorConstants.SOURCE_POINTS):
            visited_sh = set()
            visited_lj = set()
            visited_j_sh = set()
            visited_j_lj = set()            
            if q0!=0 and count>=q0:
                q0=0
                print(pretxt+"[10 %]..", flush=True)
            if q1!=0 and count>=q1:
                q1=0
                print(pretxt+"[25 %]..", flush=True)
            if q2!=0 and count>=q2:
                q2=0
                print(pretxt+"[50 %]..", flush=True)
            if q3!=0 and count>=q3:
                q3=0
                print(pretxt+"[75 %]..", flush=True)
            if q9!=0 and count>=q9:
                q9=0
                print(pretxt+"[90 %]..", flush=True)


            self.experiment_data["clothe"].regenerate_sink()

            #TOFDO TESTING FORCE SINK LOCATION
            #self.experiment_data["clothe"].sink = {"part_id":0, "x":336.552, "y":125.698}

            tmp_a, tmp_b = self.recursively_determine_distances()
            #print("calculated distances X times (shortes_route, least_jumper_route)", tmp_a, tmp_b )

            self._get_useful_grid_statistics(np_tres,count) 
            
            #sanity check (disable later to improve speed TODO)
            if abs(results["total_wire_length"]-np_tres[count][3]-np_tres[count][4])>self._precision_constant:
                logging.error("ERROR - total wire length does not match sum of reachable and unreachable wire lengths! SHOULD ALLWAYS MATCH")
            if abs(results["total_jumper_length"]-np_tres[count][5]-np_tres[count][6])>self._precision_constant:
                logging.error("ERROR - total Jumper length does not match sum of reachable and unreachable Jumper lengths! SHOULD ALLWAYS MATCH")                


            # Get reachability statistic with montecarlo for random sensor locations
            # Generate result arrays for all random destination points, calculate results, add to specific iteration or all iteration results...
 
            for index in range(GeneratorConstants.DESTINATION_POINTS):
                part,point = self.experiment_data["clothe"].get_random_point()
                np_row = count*GeneratorConstants.DESTINATION_POINTS+index
                np_res[np_row][0]=count
                np_res[np_row][1]=index

                # Only look for lines closer to sensor than max_radius (EPSILON, same as joint radius)
                # Store a result of actual node_radius needed for the run.
                dist, closest_edge = self._get_closest_edge_on_part(point, part)
                projected_point = closest_edge.interpolate(closest_edge.project(point))
                closest_edge_end_points = closest_edge.coords
                chosen_point_s = None
                chosen_distance_s = float('inf')
                chosen_point_lj = None
                chosen_distance_lj = float('inf')
                mr = 0
                if dist>max_radius:
                    mr = 1
                else:
                    for pt in closest_edge_end_points:
                        p_key = self._get_tuple_hash(pt, part)
                        p = Point(pt)
                        d = p.distance(projected_point) + dist
                        
                        if self.experiment_data["vertex_hash"][p_key]["route_shortest"] is not None and (chosen_point_s is None or (d+self.experiment_data["vertex_hash"][p_key]["route_shortest"][1])<chosen_distance_s):
                            chosen_point_s = p_key
                            chosen_distance_s = d+self.experiment_data["vertex_hash"][p_key]["route_shortest"][1]
                        if self.experiment_data["vertex_hash"][p_key]["route_least_jumpers"] is not None and (chosen_point_lj is None or (d+self.experiment_data["vertex_hash"][p_key]["route_least_jumpers"][1])<chosen_distance_lj):
                            chosen_point_lj = p_key
                            chosen_distance_lj = d+self.experiment_data["vertex_hash"][p_key]["route_least_jumpers"][1]
                if chosen_point_s is None:
                    np_res[np_row][2] = 0
                    if mr>0:
                        np_res[np_row][4] = 1
                else:
                    np_res[np_row][2] = 1
                    np_res[np_row][6] = chosen_distance_s
                    np_res[np_row][8] = dist
                    np_res[np_row][10] = self.experiment_data["vertex_hash"][chosen_point_s]["route_shortest"][0]
                    np_res[np_row][12] = self.experiment_data["vertex_hash"][chosen_point_s]["route_shortest"][2]
                    np_res[np_row][14] = self._path_unvisited_length(visited_sh, visited_j_sh, chosen_point_s, "route_shortest")
                
                if chosen_point_lj is None:
                    np_res[np_row][3] = 0
                    if mr>0:
                        np_res[np_row][5] = 1

                else:
                    np_res[np_row][3] = 1
                    np_res[np_row][7] = chosen_distance_lj
                    np_res[np_row][9] = dist
                    np_res[np_row][11] = self.experiment_data["vertex_hash"][chosen_point_lj]["route_least_jumpers"][0]
                    np_res[np_row][13] = self.experiment_data["vertex_hash"][chosen_point_lj]["route_least_jumpers"][2]
                    np_res[np_row][15] = self._path_unvisited_length(visited_lj, visited_j_lj, chosen_point_lj, "route_least_jumpers")

            #TODO gather visited info per Source not all, then calculate in np_tres
            #counting lengths of visited jumpers
            np_tres[count][21] = len(visited_sh)/results["total_node_count"]
            np_tres[count][22] = len(visited_lj)/results["total_node_count"]

            j_len_sh = 0.0
            j_len_lj = 0.0
            for tmp in visited_j_sh:
                j_len_sh += self.experiment_data["jumpers"][tmp][2]
            for tmp in visited_j_lj:
                j_len_lj += self.experiment_data["jumpers"][tmp][2]
            
            #np_tres[count][2x] = j_len_sh
            #np_tres[count][2x] = j_len_lj        

            #counting visited nodes with at least 2 useful routing paths
            
            d_node_count_sh = numpy.zeros(shape = (len(visited_sh)))
            d_node_count_lj = numpy.zeros(shape = (len(visited_lj)))
            ii = 0
            for tmp in visited_sh:
                #if self.experiment_data["vertex_hash"][tmp]["route_shortest"] is None:
                #    print(pretxt+ "=============== Err =================== Shortest route not set from "+str(self.experiment_data["clothe"].sink)+" to point:"+tmp+" Skipping - check later!")
                #    continue
                d_node_count_sh[ii] = self.experiment_data["vertex_hash"][tmp]["route_shortest"][6]
                ii=ii+1
            ii = 0
            for tmp in visited_lj:
                #if self.experiment_data["vertex_hash"][tmp]["route_least_jumpers"] is None:
                #    print(pretxt+ "=============== Err =================== Least JUMPER route not set from "+str(self.experiment_data["clothe"].sink)+" to point:"+tmp+" Skipping - check later!")
                #    continue
                d_node_count_lj[ii] = self.experiment_data["vertex_hash"][tmp]["route_least_jumpers"][6]
                ii=ii+1

            mask_router_sh = (d_node_count_sh[:] > 1)
            mask_router_lj = (d_node_count_lj[:] > 1)
            
            np_tres[count][23] = -1.0
            np_tres[count][24] = -1.0
            if len(visited_sh) > 0:
                np_tres[count][23] = numpy.shape(d_node_count_sh[mask_router_sh])[0]/len(visited_sh)
            if len(visited_lj) > 0:
                np_tres[count][24] = numpy.shape(d_node_count_lj[mask_router_lj])[0]/len(visited_lj)

            np_tres[count][25] = -1
            np_tres[count][27] = -1.0
            if results["total_jumper_count"] != 0:
                np_tres[count][25] = len(visited_j_sh)/results["total_jumper_count"]
            if results["total_jumper_length"] != 0:
                np_tres[count][27] = j_len_sh/results["total_jumper_length"]

            np_tres[count][26] = -1
            np_tres[count][28] = -1.0
            if results["total_jumper_count"] != 0:
                np_tres[count][26] = len(visited_j_lj)/results["total_jumper_count"]
            if results["total_jumper_length"] != 0:
                np_tres[count][28] = j_len_lj/results["total_jumper_length"]


   

        print(pretxt+" Analyzing.. @ "+datetime.now().strftime("%d-%m-%Y, %H:%M:%S"), flush=True)

        mask_reachable_sp = (np_res[:,2] == 1.)
        mask_reachable_lj = (np_res[:,3] == 1.)
        reachable_sp = numpy.count_nonzero(mask_reachable_sp) # how many of monte carlo points were reachable
        reachable_lj = numpy.count_nonzero(mask_reachable_lj)




            

        # np_tres satur statistiku kas ir tikai pa source punktiem (viens skaitlis visiem destination), savukārt np_res uz katru destination punktu ir ieraksts
        results["reachable_node_count"] = self.get_statistics(np_tres[:,1], percentiles = True)
        results["unreachable_node_count"] = self.get_statistics(np_tres[:,2], percentiles = True)
        results["reachable_wire_length"] = self.get_statistics(np_tres[:,3], percentiles = True)
        results["unreachable_wire_length"] = self.get_statistics(np_tres[:,4], percentiles = True)
        results["reachable_jumper_length"] = self.get_statistics(np_tres[:,5], percentiles = True)
        results["unreachable_jumper_length"] = self.get_statistics(np_tres[:,6], percentiles = True)
        results["reachable_jumper_count"] = self.get_statistics(np_tres[:,7], percentiles = True)
        results["unreachable_jumper_count"] = self.get_statistics(np_tres[:,8], percentiles = True)
        
        mask_rout_sp = (np_tres[:,23] >=0.)
        mask_rout_lj = (np_tres[:,24] >=0.)
            
        results["shortest_path"] = {
            "percent_useful_node_count": (self.get_statistics(np_tres[:,21], percentiles = True)),
            #"useful_node_count": len(visited_sh),
            "percent_useful_wire_length": (numpy.sum(np_res[mask_reachable_sp, 14])/results["total_wire_length"]),
            #"useful_wire_length": numpy.sum(np_res[mask_reachable_sp, 14]),
            "percent_reachable_sensors": reachable_sp/experiment_total_iterations, #iterations mean how many total sensors were tested in montecarlo across all experiments
            #"reachable_sensor_count": reachable_sp, # (For calculating error/sd with all reachable sensors)
            "percent_useful_jumper_count": self.get_statistics(np_tres[:,25], percentiles = True),
            "percent_useful_jumper_length": self.get_statistics(np_tres[:,26], percentiles = True),
            "percent_unreachable_bc_short_jumper": (numpy.sum(np_res[:, 4])/experiment_total_iterations),
            "percent_multiroute_reached_nodes": (self.get_statistics(np_tres[mask_rout_sp,23], percentiles = True)),

            "path_length_max": self.get_statistics(np_res[mask_reachable_sp,6], mode=1),
            "path_length_avg": self.get_statistics(np_res[mask_reachable_sp,6], percentiles = True),

            "path_node_count_max": self.get_statistics(np_res[mask_reachable_sp,12], mode=1),
            "path_node_count_avg": self.get_statistics(np_res[mask_reachable_sp,12], percentiles = True),

            "path_jumper_count_max": self.get_statistics(np_res[mask_reachable_sp,10], mode=1),
            "path_jumper_count_avg": self.get_statistics(np_res[mask_reachable_sp,10], percentiles = True),

            "path_sensor_jumper_length_max": self.get_statistics(np_res[mask_reachable_sp,8], mode=1),
            "path_sensor_jumper_length_avg": self.get_statistics(np_res[mask_reachable_sp,8], percentiles = True),

            "path_router_node_branches_max": self.get_statistics(d_node_count_sh[mask_router_sh], mode=1),
            "path_router_node_branches_avg": self.get_statistics(d_node_count_sh[mask_router_sh], percentiles = True),  

            #probably can get more useful info from the rest of data
            #"increment_wire_length_per_sensor": self.get_statistics(np_res[mask_reachable_sp,14], percentiles = True),        # Normal distributio so can use mean, also many zeroes so cannot use mean as it is allways zero  

            "graph_max_wire_length": self.get_statistics(np_tres[:,9], percentiles = True),
            "graph_avg_wire_length": self.get_statistics(np_tres[:,10], percentiles = True),
            "graph_max_node_count": self.get_statistics(np_tres[:,11], percentiles = True),
            "graph_avg_node_count": self.get_statistics(np_tres[:,12], percentiles = True),
            "graph_max_jumper_count": self.get_statistics(np_tres[:,13], percentiles = True),
            "graph_avg_jumper_count": self.get_statistics(np_tres[:,14], percentiles = True)
        }



        results["least_jumper_path"] = {
            "percent_useful_node_count": (self.get_statistics(np_tres[:,22], percentiles = True)),
            #"useful_node_count": len(visited_lj),
            "percent_useful_wire_length": (numpy.sum(np_res[mask_reachable_lj, 15])/results["total_wire_length"]),
            #"useful_wire_length": numpy.sum(np_res[mask_reachable_sp, 15]),
            "percent_reachable_sensors": reachable_lj/experiment_total_iterations,
            #"reachable_sensor_count": reachable_lj,
            "percent_useful_jumper_count": self.get_statistics(np_tres[:,27], percentiles = True),
            "percent_useful_jumper_length": self.get_statistics(np_tres[:,28], percentiles = True),
            "percent_unreachable_bc_short_jumper": (numpy.sum(np_res[:, 5])/experiment_total_iterations),
            "percent_multiroute_reached_nodes": (self.get_statistics(np_tres[mask_rout_lj,24], percentiles = True)),

            "path_length_max": self.get_statistics(np_res[mask_reachable_lj,7], mode=1),
            "path_length_avg": self.get_statistics(np_res[mask_reachable_lj,7], percentiles = True),

            "path_node_count_max": self.get_statistics(np_res[mask_reachable_lj,13], mode=1),
            "path_node_count_avg": self.get_statistics(np_res[mask_reachable_lj,13], percentiles = True),

            "path_jumper_count_max": self.get_statistics(np_res[mask_reachable_lj,11], mode=1),
            "path_jumper_count_avg": self.get_statistics(np_res[mask_reachable_lj,11], percentiles = True),

            "path_sensor_jumper_length_max": self.get_statistics(np_res[mask_reachable_lj,9], mode=1),
            "path_sensor_jumper_length_avg": self.get_statistics(np_res[mask_reachable_lj,9], percentiles = True),

            "path_router_node_branches_max": self.get_statistics(d_node_count_lj[mask_router_lj], mode=1),
            "path_router_node_branches_avg": self.get_statistics(d_node_count_lj[mask_router_lj], percentiles = True),

            #"increment_wire_length_per_sensor": self.get_statistics(np_res[mask_reachable_lj,15], percentiles = True),   

            "graph_max_wire_length": self.get_statistics(np_tres[:,15], percentiles = True),
            "graph_avg_wire_length": self.get_statistics(np_tres[:,16], percentiles = True),
            "graph_max_node_count": self.get_statistics(np_tres[:,17], percentiles = True),
            "graph_avg_node_count": self.get_statistics(np_tres[:,18], percentiles = True),
            "graph_max_jumper_count": self.get_statistics(np_tres[:,19], percentiles = True),
            "graph_avg_jumper_count": self.get_statistics(np_tres[:,20], percentiles = True)
        }


        #self.get_statistics(np_res[mask_reachable_sp,6], True) #See the length distribution as graph and get median/CI95%

        #USELESS STATS PROBABLY, but left calculation just in case - these cvan be calculated:
        #results["shortest_path"]["useless_node_count"] = results["total_node_count"]-results["shortest_path"]["useful_node_count"]
        #results["least_jumper_path"]["useless_node_count"] = results["total_node_count"]-results["least_jumper_path"]["useful_node_count"]
        #results["shortest_path"]["useless_wire_length"] = results["total_wire_length"]-results["shortest_path"]["useful_wire_length"]
        #results["least_jumper_path"]["useless_wire_length"] = results["total_wire_length"]-results["least_jumper_path"]["useful_wire_length"]

        print(pretxt+" DONE @ "+datetime.now().strftime("%d-%m-%Y, %H:%M:%S"), flush=True)

        if getTesselation is True:
            return (self.experiment_data["tessellations"], results)
        return results
        

## 1) Generate overall tessellations
## 2) Generate hashtables
## 3) For each jumper distance (not IMPLEMENTED OPTIMIZATION - distances hardcoded in config)
##    * Generate jumpers (add them to hashtable, but keep list, so can remove them for next iteration)
## 4) For each sink 
##    * For each point reach distance (again Not implemented optimization - now just one from config)
##      - Generate network/fill in hashtable with routes - use two algorithms in two passes: Min Distance, Min Jumpers (Jumper block algorithm)
##      - Get whole grid statistics (Whole graph VS the reachable [by depth, by jumps]); 
##      - For N random points get results:
##          - is Reachable? How far (distance mm, nodes, jumpers)?
##               Might include getting sample graphs: cik punktu katrā no attālumiem (bar chart), cik jumperu nepieciešams katra punkta apmeklēšanai (bar chart), statistika
