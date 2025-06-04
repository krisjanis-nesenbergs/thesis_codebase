import logging   # Import logging/print functionality
import json # For serialize/deserialize
from .generator_constants import GeneratorConstants
from .adjusted_clothing_item import AdjustedClothingItem

class ExperimentConfiguration(object): #One specific experiemtn configuratio metadata

    # Seeds = list of [x, y, angle] for each part
    def __init__(self, experiment_id=0, adjusted_clothing_item=None, tessellation_algorithm="3.3.3.3.3.3", node_distance=1, joint_radius=0.1):
        self.ID = experiment_id #identifier of the experiment
        self.adjusted_clothe = adjusted_clothing_item

        self.tessellation_algorithm = tessellation_algorithm
        self.node_distance = node_distance # tessellation scale - distance between points
        self.joint_radius = joint_radius # radius where two points on adjacent part edges can be considered joined for the purposes of traversing wires


    @staticmethod
    def _config_encode_as_dict(obj):
        return {
            "experiment_id":obj.ID,
            "clothing_id":obj.adjusted_clothe.clothing_id,
            "sex":obj.adjusted_clothe.sex,
            "size":obj.adjusted_clothe.size,
            "tesselation_algorithm":obj.tessellation_algorithm,
            "node_distance":obj.node_distance,
            "joint_radius":obj.joint_radius,
            "sink": obj.adjusted_clothe.sink,
            "seeds": obj.adjusted_clothe.seeds
        }

    def serialize(self, indent=None):
        return json.dumps(self, default=ExperimentConfiguration._config_encode_as_dict, indent=indent)

    def deserialize(self, json_string, clothe_list):
        tmp_obj = json.loads(json_string)
        self.ID = tmp_obj["experiment_id"]
        self.adjusted_clothe = AdjustedClothingItem(tmp_obj["clothing_id"], clothe_list[tmp_obj["clothing_id"]],size=tmp_obj["size"], sex=tmp_obj["sex"], sink=tmp_obj["sink"], seeds=tmp_obj["seeds"])
        self.tessellation_algorithm = tmp_obj["tesselation_algorithm"]
        self.node_distance = tmp_obj["node_distance"]
        self.joint_radius = tmp_obj["joint_radius"]


    #todo - DESERIALIZATION ALSO, then create generator loop filling configurations and printing serialization strings....
    # then save strings to file, then load strings into config objects
    # then run experiment on specific string and return results - which must be saved to file for analysis and loadable for graphing

    ### Max 200000 entries in 100MB json file...
    #TODOTODO Also need to finish AdjustedClothesItem CLASS!!!!!!!!