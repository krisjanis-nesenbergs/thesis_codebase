import logging


class GeneratorConstants(object):

    # Defines ratios of how different sizes differ from "L" size. These ratios are different for Males and Females, so both ratios are given for each size
    SIZES = {
        "XXS": {"M": 0.70, "F": 0.68},
        "XS":  {"M": 0.77, "F": 0.76},
        "S":   {"M": 0.85, "F": 0.84},
        "M":   {"M": 0.92, "F": 0.92},
        "L":   {"M": 1.00, "F": 1.00},
        "XL":  {"M": 1.08, "F": 1.10},
        "XXL": {"M": 1.17, "F": 1.22},
        "3XL": {"M": 1.27, "F": 1.34},
        "4XL": {"M": 1.39, "F": 1.45},
        "5XL": {"M": 1.51, "F": 1.57}
    }

    #Clothing item coordinates are given in units - this constant describes, how many real life mm are in each of these units
    MM_PER_UNIT = 16.259

    NODE_DISTANCES = [ 20.0, 40.0, 80.0, 160.0]

    JOINT_RADIUSES = [ 10.0, 20.0, 40.0, 80.0, 160.0]

    SOURCE_POINTS = 100

    DESTINATION_POINTS = 1000
