#import math
from shapely.geometry import Point, LineString, LinearRing, Polygon, MultiLineString
from matplotlib import pyplot
import numpy

import logging

class Visualizer(object):
    
    def __init__(self):
        self._reset_internal_state()
    

    def _reset_internal_state(self):
        self._visualizer = { 
            "fig": None,
            "count": 0,
            "x_offset": [0],
            "scale": 1.0
        }
            
    def clear_results(self):
        self._reset_internal_state()
        
    def generate(self, point, initial_angle = 0):
        # TODO some error checking
        #if self.algorithm not in Tessellator.ALGORITHMS:
        #    logging.error("Bad parameter tessellation algorithm: Unknown configuration! ("+self.alorithm+")")
        #    return

        self._reset_internal_state()
        #self._tessellate(point, initial_angle)
        #self._finished = True

    def get_coords_from_points (self, points, closed):
        x = []  #Do we need these inital coordinates? What happens when one point is given??? Auto draw points of Ring/String as well??? TODO...
        y = []
        coord_list = []
        data = None
        if isinstance(points, Point) or isinstance(points, LinearRing) or isinstance(points, LineString) or isinstance(points, MultiLineString):
            return points.xy
        if len(points)>0:
            if isinstance(points, dict):
                pts = []
                for label in points:
                    pts.append(points[label])
                points = pts
            if isinstance(points[0], list) and isinstance(points[0][0], Point):
                pts = []
                for ptl in points:
                    #print()
                    pts.append(LineString([(ptl[0].x, ptl[0].y), (ptl[1].x, ptl[1].y)]))
                points = pts
            if isinstance(points[0], Point):
                for ptl in points:
                    tx, ty = ptl.xy
                    x.append(tx[0])
                    y.append(ty[0])
                if(closed):
                    tx, ty = points[0].xy
                    x.append(tx[0])
                    y.append(ty[0])
                coord_list.append((x, y))
                return coord_list
                
                
            if isinstance(points[0], LineString):
                data = MultiLineString(points)
                for ln in data.geoms:
                    x, y = ln.xy
                    coord_list.append((x, y))
                return coord_list
        if(len(points)>1):
            if closed:
                data = LinearRing(points)
            else:
                data = LineString(points)
            return data.xy
        return (x, y)


    def plot(self, points, multicolor = True, closed=False, existing_figure = None, x_offset = 0, y_offset = 0, scale=1.0, color_value=None, markersize = 10.0):
        if(color_value is not None):
            multicolor = False
        else:
            color_value = 'black'
        fig = None
        ax = None
        x_offset = x_offset * scale
        y_offset = y_offset * scale
        if existing_figure is not None:
            fig = existing_figure
            ax = fig.get_axes()[0]
        else:
            fig = pyplot.figure(None, dpi=90)
            ax = fig.add_subplot(111)
            ax.set_aspect(1)
            ax.set_axis_off()
        res = self.get_coords_from_points(points, closed)
        if isinstance(res, list):
            for x, y in res:
                x = numpy.array(x)*scale
                y = numpy.array(y)*scale
                if multicolor:
                    ax.plot(x+x_offset, y+y_offset, marker = '.', markersize=markersize) #Ploto ar punktiņiem un krāsaini
                else:
                    ax.plot(x+x_offset, y+y_offset, marker = '', color=color_value, linewidth=0.5, markersize = markersize)   #Ploto bez punktiņiem drukai melnbalti
        else:
            x, y = res
            x = numpy.array(x)*scale
            y = numpy.array(y)*scale

            if multicolor:
                ax.plot(x+x_offset, y+y_offset, marker = '.', markersize=markersize)
            else:
                ax.plot(x+x_offset, y+y_offset, marker = '', color=color_value, linewidth=0.5, markersize = markersize)
        return fig

    ## TODO More visualization features, like jumpers and better layout?
    ## Format beautiful code

    def plot_on_prev(self, points, multicolor=True, closed=False, part_id = 0, color_value=None, markersize = 10.0):
        self._visualizer["fig"] = self.plot(points, multicolor = multicolor, closed = closed, existing_figure=self._visualizer["fig"], scale = self._visualizer["scale"], x_offset=self._visualizer["x_offset"][part_id], color_value=color_value, markersize = markersize)

    def visualize_jumper(self, jumper):
        p1 = Point(jumper[0][0].x + self._visualizer["x_offset"][jumper[0][1]], jumper[0][0].y)
        p2 = Point(jumper[1][0].x + self._visualizer["x_offset"][jumper[1][1]], jumper[1][0].y)
        self.plot_on_prev([p1, p2], color_value="red")
        return None

    def visualize_point(self, point, part):
        self.plot_on_prev(point, part_id=part, markersize=15.0)

    def visualize_a_clothe(self, a_clothe, tessellations = None, scale = 1.0):
        self.clear_results()
        part_count = a_clothe.get_part_count()
        self._visualizer["x_offset"]=[0]*part_count
        self._visualizer["scale"]=scale
        

        for part_index in range(part_count):
            self.plot_on_prev(a_clothe.get_adjusted_part_bounds(part_index), closed = True, multicolor = False, part_id=part_index)

            if tessellations is not None:
                self.plot_on_prev(tessellations[part_index], multicolor=False, part_id=part_index)
                

            if part_index == a_clothe.sink["part_id"]:
                pt = Point(a_clothe.sink["x"], a_clothe.sink["y"])
                self.plot_on_prev(pt, part_id=part_index, markersize=40.0)

            ptt = Point(a_clothe.seeds[part_index]["x"], a_clothe.seeds[part_index]["y"])
            
            self.plot_on_prev(ptt, part_id=part_index)

            if(part_index<part_count-1):
                self._visualizer["x_offset"][part_index+1] = self._visualizer["x_offset"][part_index] + max(x for x, y in a_clothe.get_adjusted_part_bounds(part_index))+10*scale

        self._visualizer["fig"].set_size_inches(self._visualizer["fig"].get_size_inches()*scale)