import sys                      # for printing to console
from enum import IntEnum        # for IntEnum support
from PyQt5 import QtCore        # For color constants
import math
            

class FRAME(IntEnum):
    """IntEnum for selecting TOP/BOTTOM UI visualization frame

    Used when drawing a pair of clothes, for selecting the specific
    canvas location. E.g. If canvas is vertical rectangle [0,0]-[50,100]
    TOP could be [0,0]-[50,50] and bottom [0,51]-[50,100].

    IntEnum instead of Enum used for easy calculations of coordinates
    e.g. y = y + frame_value * bottom_frame_top_coordinate
    resulting in just y if frame_value = TOP and y+bottom if BOTTOM

    Values:
        TOP: first frame (typically above)
        BOTTOM: bottom frame (typically below)
    """

    TOP = 0
    BOTTOM = 1

class CONFIG:
    """ Class for general configuration information """

    COLOR_LINE = QtCore.Qt.red
    COLOR_ACTIVE = QtCore.Qt.blue
    COLOR_LEFTHANDLE = QtCore.Qt.blue
    COLOR_RIGHTHANDLE = QtCore.Qt.red
    COLOR_LASTCLICK = QtCore.Qt.green
    HANDLE_DIAMETER = 10
    SCALE_FACTOR = 5 #3
    CANVAS_X = 500
    CANVAS_Y = 335 #215
    FRAME_HEIGHT = 345  #230

def pointDistance(p1,p2):
    """ Calculates distance between two points given """

    dx = p2[0]-p1[0]
    dy = p2[1]-p1[1]
    return math.sqrt(dx*dx+dy*dy)