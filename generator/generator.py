#import math
from shapely.geometry import Point, LineString, LinearRing, Polygon, MultiLineString

from .experiment_cfg import ExperimentConfiguration
from .generator_constants import GeneratorConstants
from .adjusted_clothing_item import AdjustedClothingItem
from tessellator import Tessellator

import logging

class ClothingExperimentGenerator(object):


    
    def __init__(self, clothe_list):
        self.clothe_list = clothe_list
        
        self._reset_internal_state()
    

    def _reset_internal_state(self):
        pass
        
    def clear_results(self):
        self._reset_internal_state()
        
    def generate_configuration(self):
        if self.clothe_list is None:
            logging.error("Generator needs a valid non-empty Clothe List!")
            return

        self._reset_internal_state()
        experiment_no = 0
        for tessellation_algorithm in Tessellator.ALGORITHMS:
            for clothe_id, clothe_item in enumerate(self.clothe_list):
                for size in GeneratorConstants.SIZES:
                    adjusted_clothe = AdjustedClothingItem(clothe_id, clothe_item,size=size)
                    for node_distance in GeneratorConstants.NODE_DISTANCES:
                        for joint_radius in GeneratorConstants.JOINT_RADIUSES:
                            #for it in range(1):
                            adjusted_clothe.regenerate_sink_and_seeds()
                            experiment_no = experiment_no + 1
                            new_config = ExperimentConfiguration(experiment_no, adjusted_clothe, tessellation_algorithm, node_distance, joint_radius)

                            yield new_config


