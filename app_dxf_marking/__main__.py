""" Main entry point for Clothing Data Management UI Application

Just initializes UI from clothing_data_management_ui.py, which in turn
uses clothing_data_management_backend.py as the logic/data backend
hiding the complex logic of managing Clothing data package

The goal of this UI is to import DXF files containing parts of clothing
cleaning the data, grouping it by clothing items (e.g. shirt arm and
body parts in one Item), and defining joints between those parts
connecting specific segments of each part together resulting in 1:1
correspondance between the edges of two parts, thus allowing to
determine the potential wire routing possibilities in the simulation

Requires PyQt5 and ezdxf packages
"""

__author__ = "Krisjanis Nesenbergs"
__version__ = "1.0"
__contact__ = 'krisjanis.nesenbergs@edi.lv'
__copyright__ = "Copyright 2017, Krisjanis Nesenbergs"
__license__ = "GPL"
__status__ = "Producton" #Finished "Prototype", "Development" for this

import logging
logger = logging.getLogger()
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("=[%(levelname)s @ %(filename)s (L=%(lineno)s) F=%(funcName)s() ]= %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)    



import sys #For parameter processing

from PyQt5 import QtCore, QtWidgets # For drawing UI form
from .clothing_data_management_ui import CLothingDataManagementUI


if __name__ == '__main__':
    main()

def main():
    logger.critical("Starting full console logging (use console_handler.setLevel etc. in __main__ to change)")
    app = QtWidgets.QApplication(sys.argv)
    myapp = CLothingDataManagementUI()
    myapp.show()
    sys.exit(app.exec_())

