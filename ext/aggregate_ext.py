""" Aggregation of the extended simulation run results into a single csv (2026)

Walks the extended run result trees and writes results_ext/integrated_results_ext.csv using the
same column schema as notebooks/aggregate.ipynb produced for results/integrated_results.csv, so
the two tables can be concatenated directly. Three provenance columns are appended.

The original table is neither modified nor duplicated. To analyse both runs together:

    a = pd.read_csv("results/integrated_results.csv")
    b = pd.read_csv("results_ext/integrated_results_ext.csv")
    a["CFG_run"], a["CFG_tag"], a["CFG_mc"] = "initial_2023", "", 100000
    df = pd.concat([a, b], ignore_index=True)
"""

__author__ = "Krisjanis Nesenbergs"
__version__ = "1.0"
__contact__ = 'krisjanis.nesenbergs@edi.lv'
__copyright__ = "Copyright 2026, Krisjanis Nesenbergs"
__license__ = "GPL"
__status__ = "Production"

import logging
logger = logging.getLogger()
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("=[%(levelname)s @ %(filename)s (L=%(lineno)s) F=%(funcName)s() ]= %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

import glob
import json
import os

import pandas as pd

TIERS = ["tier1", "tier2", "tier3", "tier4", "tier5", "tier5b"]

# Column name and the expression producing it, taken from notebooks/aggregate.ipynb so that the
# extended table matches the original one column for column.
COLUMNS = [
    ("CFG_ID", 'cfg["ID"]'),
    ("CFG_clothe_ID", 'cfg["clothing_id"]'),
    ("CFG_sex", 'cfg["sex"]'),
    ("CFG_size", 'cfg["size"]'),
    ("CFG_algorythm", 'cfg["algorythm"]'),
    ("CFG_node_distance", 'cfg["node_distance"]'),
    ("CFG_joint_radius", 'cfg["joint_radius"]'),
    ("T_wire_L", 'res["total_wire_length"]'),
    ("T_jumper_L", 'res["total_jumper_length"]'),
    ("T_jumper_C", 'res["total_jumper_count"]'),
    ("center_node_C", 'res["center_node_count"]'),
    ("edge_node_C", 'res["edge_node_count"]'),
    ("T_node_C", 'res["total_node_count"]'),
    ("reachable_node_C__Median", 'res["reachable_node_count"][0]'),
    ("reachable_node_C__lci", 'res["reachable_node_count"][1]'),
    ("reachable_node_C__hci", 'res["reachable_node_count"][2]'),
    ("reachable_node_C__Mean", 'res["reachable_node_count"][4]'),
    ("reachable_node_C__p05", 'res["reachable_node_count"][3][0]'),
    ("reachable_node_C__p10", 'res["reachable_node_count"][3][1]'),
    ("reachable_node_C__p25", 'res["reachable_node_count"][3][2]'),
    ("reachable_node_C__p75", 'res["reachable_node_count"][3][3]'),
    ("reachable_node_C__p90", 'res["reachable_node_count"][3][4]'),
    ("reachable_node_C__p95", 'res["reachable_node_count"][3][5]'),
    ("unreachable_node_C__Median", 'res["unreachable_node_count"][0]'),
    ("unreachable_node_C__lci", 'res["unreachable_node_count"][1]'),
    ("unreachable_node_C__hci", 'res["unreachable_node_count"][2]'),
    ("unreachable_node_C__Mean", 'res["unreachable_node_count"][4]'),
    ("unreachable_node_C__p05", 'res["unreachable_node_count"][3][0]'),
    ("unreachable_node_C__p10", 'res["unreachable_node_count"][3][1]'),
    ("unreachable_node_C__p25", 'res["unreachable_node_count"][3][2]'),
    ("unreachable_node_C__p75", 'res["unreachable_node_count"][3][3]'),
    ("unreachable_node_C__p90", 'res["unreachable_node_count"][3][4]'),
    ("unreachable_node_C__p95", 'res["unreachable_node_count"][3][5]'),
    ("reachable_wire_L__Median", 'res["reachable_wire_length"][0]'),
    ("reachable_wire_L__lci", 'res["reachable_wire_length"][1]'),
    ("reachable_wire_L__hci", 'res["reachable_wire_length"][2]'),
    ("reachable_wire_L__Mean", 'res["reachable_wire_length"][4]'),
    ("reachable_wire_L__p05", 'res["reachable_wire_length"][3][0]'),
    ("reachable_wire_L__p10", 'res["reachable_wire_length"][3][1]'),
    ("reachable_wire_L__p25", 'res["reachable_wire_length"][3][2]'),
    ("reachable_wire_L__p75", 'res["reachable_wire_length"][3][3]'),
    ("reachable_wire_L__p90", 'res["reachable_wire_length"][3][4]'),
    ("reachable_wire_L__p95", 'res["reachable_wire_length"][3][5]'),
    ("unreachable_wire_L__Median", 'res["unreachable_wire_length"][0]'),
    ("unreachable_wire_L__lci", 'res["unreachable_wire_length"][1]'),
    ("unreachable_wire_L__hci", 'res["unreachable_wire_length"][2]'),
    ("unreachable_wire_L__Mean", 'res["unreachable_wire_length"][4]'),
    ("unreachable_wire_L__p05", 'res["unreachable_wire_length"][3][0]'),
    ("unreachable_wire_L__p10", 'res["unreachable_wire_length"][3][1]'),
    ("unreachable_wire_L__p25", 'res["unreachable_wire_length"][3][2]'),
    ("unreachable_wire_L__p75", 'res["unreachable_wire_length"][3][3]'),
    ("unreachable_wire_L__p90", 'res["unreachable_wire_length"][3][4]'),
    ("unreachable_wire_L__p95", 'res["unreachable_wire_length"][3][5]'),
    ("reachable_jumper_L__Median", 'res["reachable_jumper_length"][0]'),
    ("reachable_jumper_L__lci", 'res["reachable_jumper_length"][1]'),
    ("reachable_jumper_L__hci", 'res["reachable_jumper_length"][2]'),
    ("reachable_jumper_L__Mean", 'res["reachable_jumper_length"][4]'),
    ("reachable_jumper_L__p05", 'res["reachable_jumper_length"][3][0]'),
    ("reachable_jumper_L__p10", 'res["reachable_jumper_length"][3][1]'),
    ("reachable_jumper_L__p25", 'res["reachable_jumper_length"][3][2]'),
    ("reachable_jumper_L__p75", 'res["reachable_jumper_length"][3][3]'),
    ("reachable_jumper_L__p90", 'res["reachable_jumper_length"][3][4]'),
    ("reachable_jumper_L__p95", 'res["reachable_jumper_length"][3][5]'),
    ("unreachable_jumper_L__Median", 'res["unreachable_jumper_length"][0]'),
    ("unreachable_jumper_L__lci", 'res["unreachable_jumper_length"][1]'),
    ("unreachable_jumper_L__hci", 'res["unreachable_jumper_length"][2]'),
    ("unreachable_jumper_L__Mean", 'res["unreachable_jumper_length"][4]'),
    ("unreachable_jumper_L__p05", 'res["unreachable_jumper_length"][3][0]'),
    ("unreachable_jumper_L__p10", 'res["unreachable_jumper_length"][3][1]'),
    ("unreachable_jumper_L__p25", 'res["unreachable_jumper_length"][3][2]'),
    ("unreachable_jumper_L__p75", 'res["unreachable_jumper_length"][3][3]'),
    ("unreachable_jumper_L__p90", 'res["unreachable_jumper_length"][3][4]'),
    ("unreachable_jumper_L__p95", 'res["unreachable_jumper_length"][3][5]'),
    ("reachable_jumper_C__Median", 'res["reachable_jumper_count"][0]'),
    ("reachable_jumper_C__lci", 'res["reachable_jumper_count"][1]'),
    ("reachable_jumper_C__hci", 'res["reachable_jumper_count"][2]'),
    ("reachable_jumper_C__Mean", 'res["reachable_jumper_count"][4]'),
    ("reachable_jumper_C__p05", 'res["reachable_jumper_count"][3][0]'),
    ("reachable_jumper_C__p10", 'res["reachable_jumper_count"][3][1]'),
    ("reachable_jumper_C__p25", 'res["reachable_jumper_count"][3][2]'),
    ("reachable_jumper_C__p75", 'res["reachable_jumper_count"][3][3]'),
    ("reachable_jumper_C__p90", 'res["reachable_jumper_count"][3][4]'),
    ("reachable_jumper_C__p95", 'res["reachable_jumper_count"][3][5]'),
    ("unreachable_jumper_C__Median", 'res["unreachable_jumper_count"][0]'),
    ("unreachable_jumper_C__lci", 'res["unreachable_jumper_count"][1]'),
    ("unreachable_jumper_C__hci", 'res["unreachable_jumper_count"][2]'),
    ("unreachable_jumper_C__Mean", 'res["unreachable_jumper_count"][4]'),
    ("unreachable_jumper_C__p05", 'res["unreachable_jumper_count"][3][0]'),
    ("unreachable_jumper_C__p10", 'res["unreachable_jumper_count"][3][1]'),
    ("unreachable_jumper_C__p25", 'res["unreachable_jumper_count"][3][2]'),
    ("unreachable_jumper_C__p75", 'res["unreachable_jumper_count"][3][3]'),
    ("unreachable_jumper_C__p90", 'res["unreachable_jumper_count"][3][4]'),
    ("unreachable_jumper_C__p95", 'res["unreachable_jumper_count"][3][5]'),
    ("SP_P_useful_node_C__Median", 'res["shortest_path"]["percent_useful_node_count"][0]'),
    ("SP_P_useful_node_C__lci", 'res["shortest_path"]["percent_useful_node_count"][1]'),
    ("SP_P_useful_node_C__hci", 'res["shortest_path"]["percent_useful_node_count"][2]'),
    ("SP_P_useful_node_C__Mean", 'res["shortest_path"]["percent_useful_node_count"][4]'),
    ("SP_P_useful_node_C__p05", 'res["shortest_path"]["percent_useful_node_count"][3][0]'),
    ("SP_P_useful_node_C__p10", 'res["shortest_path"]["percent_useful_node_count"][3][1]'),
    ("SP_P_useful_node_C__p25", 'res["shortest_path"]["percent_useful_node_count"][3][2]'),
    ("SP_P_useful_node_C__p75", 'res["shortest_path"]["percent_useful_node_count"][3][3]'),
    ("SP_P_useful_node_C__p90", 'res["shortest_path"]["percent_useful_node_count"][3][4]'),
    ("SP_P_useful_node_C__p95", 'res["shortest_path"]["percent_useful_node_count"][3][5]'),
    ("SP_P_useful_wire_L", 'res["shortest_path"]["percent_useful_wire_length"]'),
    ("SP_P_reachable_sensors", 'res["shortest_path"]["percent_reachable_sensors"]'),
    ("SP_P_useful_jumper_C__Median", 'res["shortest_path"]["percent_useful_jumper_count"][0]'),
    ("SP_P_useful_jumper_C__lci", 'res["shortest_path"]["percent_useful_jumper_count"][1]'),
    ("SP_P_useful_jumper_C__hci", 'res["shortest_path"]["percent_useful_jumper_count"][2]'),
    ("SP_P_useful_jumper_C__Mean", 'res["shortest_path"]["percent_useful_jumper_count"][4]'),
    ("SP_P_useful_jumper_C__p05", 'res["shortest_path"]["percent_useful_jumper_count"][3][0]'),
    ("SP_P_useful_jumper_C__p10", 'res["shortest_path"]["percent_useful_jumper_count"][3][1]'),
    ("SP_P_useful_jumper_C__p25", 'res["shortest_path"]["percent_useful_jumper_count"][3][2]'),
    ("SP_P_useful_jumper_C__p75", 'res["shortest_path"]["percent_useful_jumper_count"][3][3]'),
    ("SP_P_useful_jumper_C__p90", 'res["shortest_path"]["percent_useful_jumper_count"][3][4]'),
    ("SP_P_useful_jumper_C__p95", 'res["shortest_path"]["percent_useful_jumper_count"][3][5]'),
    ("SP_P_useful_jumper_L__Median", 'res["shortest_path"]["percent_useful_jumper_length"][0]'),
    ("SP_P_useful_jumper_L__lci", 'res["shortest_path"]["percent_useful_jumper_length"][1]'),
    ("SP_P_useful_jumper_L__hci", 'res["shortest_path"]["percent_useful_jumper_length"][2]'),
    ("SP_P_useful_jumper_L__Mean", 'res["shortest_path"]["percent_useful_jumper_length"][4]'),
    ("SP_P_useful_jumper_L__p05", 'res["shortest_path"]["percent_useful_jumper_length"][3][0]'),
    ("SP_P_useful_jumper_L__p10", 'res["shortest_path"]["percent_useful_jumper_length"][3][1]'),
    ("SP_P_useful_jumper_L__p25", 'res["shortest_path"]["percent_useful_jumper_length"][3][2]'),
    ("SP_P_useful_jumper_L__p75", 'res["shortest_path"]["percent_useful_jumper_length"][3][3]'),
    ("SP_P_useful_jumper_L__p90", 'res["shortest_path"]["percent_useful_jumper_length"][3][4]'),
    ("SP_P_useful_jumper_L__p95", 'res["shortest_path"]["percent_useful_jumper_length"][3][5]'),
    ("SP_P_unreachable_bc_short_jumper", 'res["shortest_path"]["percent_unreachable_bc_short_jumper"]'),
    ("SP_P_multiroute_reached_nodes__Median", 'res["shortest_path"]["percent_multiroute_reached_nodes"][0]'),
    ("SP_P_multiroute_reached_nodes__lci", 'res["shortest_path"]["percent_multiroute_reached_nodes"][1]'),
    ("SP_P_multiroute_reached_nodes__hci", 'res["shortest_path"]["percent_multiroute_reached_nodes"][2]'),
    ("SP_P_multiroute_reached_nodes__Mean", 'res["shortest_path"]["percent_multiroute_reached_nodes"][4]'),
    ("SP_P_multiroute_reached_nodes__p05", 'res["shortest_path"]["percent_multiroute_reached_nodes"][3][0]'),
    ("SP_P_multiroute_reached_nodes__p10", 'res["shortest_path"]["percent_multiroute_reached_nodes"][3][1]'),
    ("SP_P_multiroute_reached_nodes__p25", 'res["shortest_path"]["percent_multiroute_reached_nodes"][3][2]'),
    ("SP_P_multiroute_reached_nodes__p75", 'res["shortest_path"]["percent_multiroute_reached_nodes"][3][3]'),
    ("SP_P_multiroute_reached_nodes__p90", 'res["shortest_path"]["percent_multiroute_reached_nodes"][3][4]'),
    ("SP_P_multiroute_reached_nodes__p95", 'res["shortest_path"]["percent_multiroute_reached_nodes"][3][5]'),
    ("SP_path_L__Max", 'res["shortest_path"]["path_length_max"][0]'),
    ("SP_path_L__Max_lci", 'res["shortest_path"]["path_length_max"][1]'),
    ("SP_path_L__Max_hci", 'res["shortest_path"]["path_length_max"][2]'),
    ("SP_path_L__Median", 'res["shortest_path"]["path_length_avg"][0]'),
    ("SP_path_L__lci", 'res["shortest_path"]["path_length_avg"][1]'),
    ("SP_path_L__hci", 'res["shortest_path"]["path_length_avg"][2]'),
    ("SP_path_L__Mean", 'res["shortest_path"]["path_length_avg"][4]'),
    ("SP_path_L__p05", 'res["shortest_path"]["path_length_avg"][3][0]'),
    ("SP_path_L__p10", 'res["shortest_path"]["path_length_avg"][3][1]'),
    ("SP_path_L__p25", 'res["shortest_path"]["path_length_avg"][3][2]'),
    ("SP_path_L__p75", 'res["shortest_path"]["path_length_avg"][3][3]'),
    ("SP_path_L__p90", 'res["shortest_path"]["path_length_avg"][3][4]'),
    ("SP_path_L__p95", 'res["shortest_path"]["path_length_avg"][3][5]'),
    ("SP_path_node_C__Max", 'res["shortest_path"]["path_node_count_max"][0]'),
    ("SP_path_node_C__Max_lci", 'res["shortest_path"]["path_node_count_max"][1]'),
    ("SP_path_node_C__Max_hci", 'res["shortest_path"]["path_node_count_max"][2]'),
    ("SP_path_node_C__Median", 'res["shortest_path"]["path_node_count_avg"][0]'),
    ("SP_path_node_C__lci", 'res["shortest_path"]["path_node_count_avg"][1]'),
    ("SP_path_node_C__hci", 'res["shortest_path"]["path_node_count_avg"][2]'),
    ("SP_path_node_C__Mean", 'res["shortest_path"]["path_node_count_avg"][4]'),
    ("SP_path_node_C__p05", 'res["shortest_path"]["path_node_count_avg"][3][0]'),
    ("SP_path_node_C__p10", 'res["shortest_path"]["path_node_count_avg"][3][1]'),
    ("SP_path_node_C__p25", 'res["shortest_path"]["path_node_count_avg"][3][2]'),
    ("SP_path_node_C__p75", 'res["shortest_path"]["path_node_count_avg"][3][3]'),
    ("SP_path_node_C__p90", 'res["shortest_path"]["path_node_count_avg"][3][4]'),
    ("SP_path_node_C__p95", 'res["shortest_path"]["path_node_count_avg"][3][5]'),
    ("SP_path_jumper_C__Max", 'res["shortest_path"]["path_jumper_count_max"][0]'),
    ("SP_path_jumper_C__Max_lci", 'res["shortest_path"]["path_jumper_count_max"][1]'),
    ("SP_path_jumper_C__Max_hci", 'res["shortest_path"]["path_jumper_count_max"][2]'),
    ("SP_path_jumper_C__Median", 'res["shortest_path"]["path_jumper_count_avg"][0]'),
    ("SP_path_jumper_C__lci", 'res["shortest_path"]["path_jumper_count_avg"][1]'),
    ("SP_path_jumper_C__hci", 'res["shortest_path"]["path_jumper_count_avg"][2]'),
    ("SP_path_jumper_C__Mean", 'res["shortest_path"]["path_jumper_count_avg"][4]'),
    ("SP_path_jumper_C__p05", 'res["shortest_path"]["path_jumper_count_avg"][3][0]'),
    ("SP_path_jumper_C__p10", 'res["shortest_path"]["path_jumper_count_avg"][3][1]'),
    ("SP_path_jumper_C__p25", 'res["shortest_path"]["path_jumper_count_avg"][3][2]'),
    ("SP_path_jumper_C__p75", 'res["shortest_path"]["path_jumper_count_avg"][3][3]'),
    ("SP_path_jumper_C__p90", 'res["shortest_path"]["path_jumper_count_avg"][3][4]'),
    ("SP_path_jumper_C__p95", 'res["shortest_path"]["path_jumper_count_avg"][3][5]'),
    ("SP_path_sensor_jumper_L__Max", 'res["shortest_path"]["path_sensor_jumper_length_max"][0]'),
    ("SP_path_sensor_jumper_L__Max_lci", 'res["shortest_path"]["path_sensor_jumper_length_max"][1]'),
    ("SP_path_sensor_jumper_L__Max_hci", 'res["shortest_path"]["path_sensor_jumper_length_max"][2]'),
    ("SP_path_sensor_jumper_L__Median", 'res["shortest_path"]["path_sensor_jumper_length_avg"][0]'),
    ("SP_path_sensor_jumper_L__lci", 'res["shortest_path"]["path_sensor_jumper_length_avg"][1]'),
    ("SP_path_sensor_jumper_L__hci", 'res["shortest_path"]["path_sensor_jumper_length_avg"][2]'),
    ("SP_path_sensor_jumper_L__Mean", 'res["shortest_path"]["path_sensor_jumper_length_avg"][4]'),
    ("SP_path_sensor_jumper_L__p05", 'res["shortest_path"]["path_sensor_jumper_length_avg"][3][0]'),
    ("SP_path_sensor_jumper_L__p10", 'res["shortest_path"]["path_sensor_jumper_length_avg"][3][1]'),
    ("SP_path_sensor_jumper_L__p25", 'res["shortest_path"]["path_sensor_jumper_length_avg"][3][2]'),
    ("SP_path_sensor_jumper_L__p75", 'res["shortest_path"]["path_sensor_jumper_length_avg"][3][3]'),
    ("SP_path_sensor_jumper_L__p90", 'res["shortest_path"]["path_sensor_jumper_length_avg"][3][4]'),
    ("SP_path_sensor_jumper_L__p95", 'res["shortest_path"]["path_sensor_jumper_length_avg"][3][5]'),
    ("SP_path_router_node_branches__Max", 'res["shortest_path"]["path_router_node_branches_max"][0]'),
    ("SP_path_router_node_branches__Max_lci", 'res["shortest_path"]["path_router_node_branches_max"][1]'),
    ("SP_path_router_node_branches__Max_hci", 'res["shortest_path"]["path_router_node_branches_max"][2]'),
    ("SP_path_router_node_branches__Median", 'res["shortest_path"]["path_router_node_branches_avg"][0]'),
    ("SP_path_router_node_branches__lci", 'res["shortest_path"]["path_router_node_branches_avg"][1]'),
    ("SP_path_router_node_branches__hci", 'res["shortest_path"]["path_router_node_branches_avg"][2]'),
    ("SP_path_router_node_branches__Mean", 'res["shortest_path"]["path_router_node_branches_avg"][4]'),
    ("SP_path_router_node_branches__p05", 'res["shortest_path"]["path_router_node_branches_avg"][3][0]'),
    ("SP_path_router_node_branches__p10", 'res["shortest_path"]["path_router_node_branches_avg"][3][1]'),
    ("SP_path_router_node_branches__p25", 'res["shortest_path"]["path_router_node_branches_avg"][3][2]'),
    ("SP_path_router_node_branches__p75", 'res["shortest_path"]["path_router_node_branches_avg"][3][3]'),
    ("SP_path_router_node_branches__p90", 'res["shortest_path"]["path_router_node_branches_avg"][3][4]'),
    ("SP_path_router_node_branches__p95", 'res["shortest_path"]["path_router_node_branches_avg"][3][5]'),
    ("SP_graph_wire_L__Max", 'res["shortest_path"]["graph_max_wire_length"][0]'),
    ("SP_graph_wire_L__Max_lci", 'res["shortest_path"]["graph_max_wire_length"][1]'),
    ("SP_graph_wire_L__Max_hci", 'res["shortest_path"]["graph_max_wire_length"][2]'),
    ("SP_graph_wire_L__Median", 'res["shortest_path"]["graph_avg_wire_length"][0]'),
    ("SP_graph_wire_L__lci", 'res["shortest_path"]["graph_avg_wire_length"][1]'),
    ("SP_graph_wire_L__hci", 'res["shortest_path"]["graph_avg_wire_length"][2]'),
    ("SP_graph_wire_L__Mean", 'res["shortest_path"]["graph_avg_wire_length"][4]'),
    ("SP_graph_wire_L__p05", 'res["shortest_path"]["graph_avg_wire_length"][3][0]'),
    ("SP_graph_wire_L__p10", 'res["shortest_path"]["graph_avg_wire_length"][3][1]'),
    ("SP_graph_wire_L__p25", 'res["shortest_path"]["graph_avg_wire_length"][3][2]'),
    ("SP_graph_wire_L__p75", 'res["shortest_path"]["graph_avg_wire_length"][3][3]'),
    ("SP_graph_wire_L__p90", 'res["shortest_path"]["graph_avg_wire_length"][3][4]'),
    ("SP_graph_wire_L__p95", 'res["shortest_path"]["graph_avg_wire_length"][3][5]'),
    ("SP_graph_node_C__Max", 'res["shortest_path"]["graph_max_node_count"][0]'),
    ("SP_graph_node_C__Max_lci", 'res["shortest_path"]["graph_max_node_count"][1]'),
    ("SP_graph_node_C__Max_hci", 'res["shortest_path"]["graph_max_node_count"][2]'),
    ("SP_graph_node_C__Median", 'res["shortest_path"]["graph_avg_node_count"][0]'),
    ("SP_graph_node_C__lci", 'res["shortest_path"]["graph_avg_node_count"][1]'),
    ("SP_graph_node_C__hci", 'res["shortest_path"]["graph_avg_node_count"][2]'),
    ("SP_graph_node_C__Mean", 'res["shortest_path"]["graph_avg_node_count"][4]'),
    ("SP_graph_node_C__p05", 'res["shortest_path"]["graph_avg_node_count"][3][0]'),
    ("SP_graph_node_C__p10", 'res["shortest_path"]["graph_avg_node_count"][3][1]'),
    ("SP_graph_node_C__p25", 'res["shortest_path"]["graph_avg_node_count"][3][2]'),
    ("SP_graph_node_C__p75", 'res["shortest_path"]["graph_avg_node_count"][3][3]'),
    ("SP_graph_node_C__p90", 'res["shortest_path"]["graph_avg_node_count"][3][4]'),
    ("SP_graph_node_C__p95", 'res["shortest_path"]["graph_avg_node_count"][3][5]'),
    ("SP_graph_jumper_C__Max", 'res["shortest_path"]["graph_max_jumper_count"][0]'),
    ("SP_graph_jumper_C__Max_lci", 'res["shortest_path"]["graph_max_jumper_count"][1]'),
    ("SP_graph_jumper_C__Max_hci", 'res["shortest_path"]["graph_max_jumper_count"][2]'),
    ("SP_graph_jumper_C__Median", 'res["shortest_path"]["graph_avg_jumper_count"][0]'),
    ("SP_graph_jumper_C__lci", 'res["shortest_path"]["graph_avg_jumper_count"][1]'),
    ("SP_graph_jumper_C__hci", 'res["shortest_path"]["graph_avg_jumper_count"][2]'),
    ("SP_graph_jumper_C__Mean", 'res["shortest_path"]["graph_avg_jumper_count"][4]'),
    ("SP_graph_jumper_C__p05", 'res["shortest_path"]["graph_avg_jumper_count"][3][0]'),
    ("SP_graph_jumper_C__p10", 'res["shortest_path"]["graph_avg_jumper_count"][3][1]'),
    ("SP_graph_jumper_C__p25", 'res["shortest_path"]["graph_avg_jumper_count"][3][2]'),
    ("SP_graph_jumper_C__p75", 'res["shortest_path"]["graph_avg_jumper_count"][3][3]'),
    ("SP_graph_jumper_C__p90", 'res["shortest_path"]["graph_avg_jumper_count"][3][4]'),
    ("SP_graph_jumper_C__p95", 'res["shortest_path"]["graph_avg_jumper_count"][3][5]'),
    ("LJP_P_useful_node_C__Median", 'res["least_jumper_path"]["percent_useful_node_count"][0]'),
    ("LJP_P_useful_node_C__lci", 'res["least_jumper_path"]["percent_useful_node_count"][1]'),
    ("LJP_P_useful_node_C__hci", 'res["least_jumper_path"]["percent_useful_node_count"][2]'),
    ("LJP_P_useful_node_C__Mean", 'res["least_jumper_path"]["percent_useful_node_count"][4]'),
    ("LJP_P_useful_node_C__p05", 'res["least_jumper_path"]["percent_useful_node_count"][3][0]'),
    ("LJP_P_useful_node_C__p10", 'res["least_jumper_path"]["percent_useful_node_count"][3][1]'),
    ("LJP_P_useful_node_C__p25", 'res["least_jumper_path"]["percent_useful_node_count"][3][2]'),
    ("LJP_P_useful_node_C__p75", 'res["least_jumper_path"]["percent_useful_node_count"][3][3]'),
    ("LJP_P_useful_node_C__p90", 'res["least_jumper_path"]["percent_useful_node_count"][3][4]'),
    ("LJP_P_useful_node_C__p95", 'res["least_jumper_path"]["percent_useful_node_count"][3][5]'),
    ("LJP_P_useful_wire_L", 'res["least_jumper_path"]["percent_useful_wire_length"]'),
    ("LJP_P_reachable_sensors", 'res["least_jumper_path"]["percent_reachable_sensors"]'),
    ("LJP_P_useful_jumper_C__Median", 'res["least_jumper_path"]["percent_useful_jumper_count"][0]'),
    ("LJP_P_useful_jumper_C__lci", 'res["least_jumper_path"]["percent_useful_jumper_count"][1]'),
    ("LJP_P_useful_jumper_C__hci", 'res["least_jumper_path"]["percent_useful_jumper_count"][2]'),
    ("LJP_P_useful_jumper_C__Mean", 'res["least_jumper_path"]["percent_useful_jumper_count"][4]'),
    ("LJP_P_useful_jumper_C__p05", 'res["least_jumper_path"]["percent_useful_jumper_count"][3][0]'),
    ("LJP_P_useful_jumper_C__p10", 'res["least_jumper_path"]["percent_useful_jumper_count"][3][1]'),
    ("LJP_P_useful_jumper_C__p25", 'res["least_jumper_path"]["percent_useful_jumper_count"][3][2]'),
    ("LJP_P_useful_jumper_C__p75", 'res["least_jumper_path"]["percent_useful_jumper_count"][3][3]'),
    ("LJP_P_useful_jumper_C__p90", 'res["least_jumper_path"]["percent_useful_jumper_count"][3][4]'),
    ("LJP_P_useful_jumper_C__p95", 'res["least_jumper_path"]["percent_useful_jumper_count"][3][5]'),
    ("LJP_P_useful_jumper_L__Median", 'res["least_jumper_path"]["percent_useful_jumper_length"][0]'),
    ("LJP_P_useful_jumper_L__lci", 'res["least_jumper_path"]["percent_useful_jumper_length"][1]'),
    ("LJP_P_useful_jumper_L__hci", 'res["least_jumper_path"]["percent_useful_jumper_length"][2]'),
    ("LJP_P_useful_jumper_L__Mean", 'res["least_jumper_path"]["percent_useful_jumper_length"][4]'),
    ("LJP_P_useful_jumper_L__p05", 'res["least_jumper_path"]["percent_useful_jumper_length"][3][0]'),
    ("LJP_P_useful_jumper_L__p10", 'res["least_jumper_path"]["percent_useful_jumper_length"][3][1]'),
    ("LJP_P_useful_jumper_L__p25", 'res["least_jumper_path"]["percent_useful_jumper_length"][3][2]'),
    ("LJP_P_useful_jumper_L__p75", 'res["least_jumper_path"]["percent_useful_jumper_length"][3][3]'),
    ("LJP_P_useful_jumper_L__p90", 'res["least_jumper_path"]["percent_useful_jumper_length"][3][4]'),
    ("LJP_P_useful_jumper_L__p95", 'res["least_jumper_path"]["percent_useful_jumper_length"][3][5]'),
    ("LJP_P_unreachable_bc_short_jumper", 'res["least_jumper_path"]["percent_unreachable_bc_short_jumper"]'),
    ("LJP_P_multiroute_reached_nodes__Median", 'res["least_jumper_path"]["percent_multiroute_reached_nodes"][0]'),
    ("LJP_P_multiroute_reached_nodes__lci", 'res["least_jumper_path"]["percent_multiroute_reached_nodes"][1]'),
    ("LJP_P_multiroute_reached_nodes__hci", 'res["least_jumper_path"]["percent_multiroute_reached_nodes"][2]'),
    ("LJP_P_multiroute_reached_nodes__Mean", 'res["least_jumper_path"]["percent_multiroute_reached_nodes"][4]'),
    ("LJP_P_multiroute_reached_nodes__p05", 'res["least_jumper_path"]["percent_multiroute_reached_nodes"][3][0]'),
    ("LJP_P_multiroute_reached_nodes__p10", 'res["least_jumper_path"]["percent_multiroute_reached_nodes"][3][1]'),
    ("LJP_P_multiroute_reached_nodes__p25", 'res["least_jumper_path"]["percent_multiroute_reached_nodes"][3][2]'),
    ("LJP_P_multiroute_reached_nodes__p75", 'res["least_jumper_path"]["percent_multiroute_reached_nodes"][3][3]'),
    ("LJP_P_multiroute_reached_nodes__p90", 'res["least_jumper_path"]["percent_multiroute_reached_nodes"][3][4]'),
    ("LJP_P_multiroute_reached_nodes__p95", 'res["least_jumper_path"]["percent_multiroute_reached_nodes"][3][5]'),
    ("LJP_path_L__Max", 'res["least_jumper_path"]["path_length_max"][0]'),
    ("LJP_path_L__Max_lci", 'res["least_jumper_path"]["path_length_max"][1]'),
    ("LJP_path_L__Max_hci", 'res["least_jumper_path"]["path_length_max"][2]'),
    ("LJP_path_L__Median", 'res["least_jumper_path"]["path_length_avg"][0]'),
    ("LJP_path_L__lci", 'res["least_jumper_path"]["path_length_avg"][1]'),
    ("LJP_path_L__hci", 'res["least_jumper_path"]["path_length_avg"][2]'),
    ("LJP_path_L__Mean", 'res["least_jumper_path"]["path_length_avg"][4]'),
    ("LJP_path_L__p05", 'res["least_jumper_path"]["path_length_avg"][3][0]'),
    ("LJP_path_L__p10", 'res["least_jumper_path"]["path_length_avg"][3][1]'),
    ("LJP_path_L__p25", 'res["least_jumper_path"]["path_length_avg"][3][2]'),
    ("LJP_path_L__p75", 'res["least_jumper_path"]["path_length_avg"][3][3]'),
    ("LJP_path_L__p90", 'res["least_jumper_path"]["path_length_avg"][3][4]'),
    ("LJP_path_L__p95", 'res["least_jumper_path"]["path_length_avg"][3][5]'),
    ("LJP_path_node_C__Max", 'res["least_jumper_path"]["path_node_count_max"][0]'),
    ("LJP_path_node_C__Max_lci", 'res["least_jumper_path"]["path_node_count_max"][1]'),
    ("LJP_path_node_C__Max_hci", 'res["least_jumper_path"]["path_node_count_max"][2]'),
    ("LJP_path_node_C__Median", 'res["least_jumper_path"]["path_node_count_avg"][0]'),
    ("LJP_path_node_C__lci", 'res["least_jumper_path"]["path_node_count_avg"][1]'),
    ("LJP_path_node_C__hci", 'res["least_jumper_path"]["path_node_count_avg"][2]'),
    ("LJP_path_node_C__Mean", 'res["least_jumper_path"]["path_node_count_avg"][4]'),
    ("LJP_path_node_C__p05", 'res["least_jumper_path"]["path_node_count_avg"][3][0]'),
    ("LJP_path_node_C__p10", 'res["least_jumper_path"]["path_node_count_avg"][3][1]'),
    ("LJP_path_node_C__p25", 'res["least_jumper_path"]["path_node_count_avg"][3][2]'),
    ("LJP_path_node_C__p75", 'res["least_jumper_path"]["path_node_count_avg"][3][3]'),
    ("LJP_path_node_C__p90", 'res["least_jumper_path"]["path_node_count_avg"][3][4]'),
    ("LJP_path_node_C__p95", 'res["least_jumper_path"]["path_node_count_avg"][3][5]'),
    ("LJP_path_jumper_C__Max", 'res["least_jumper_path"]["path_jumper_count_max"][0]'),
    ("LJP_path_jumper_C__Max_lci", 'res["least_jumper_path"]["path_jumper_count_max"][1]'),
    ("LJP_path_jumper_C__Max_hci", 'res["least_jumper_path"]["path_jumper_count_max"][2]'),
    ("LJP_path_jumper_C__Median", 'res["least_jumper_path"]["path_jumper_count_avg"][0]'),
    ("LJP_path_jumper_C__lci", 'res["least_jumper_path"]["path_jumper_count_avg"][1]'),
    ("LJP_path_jumper_C__hci", 'res["least_jumper_path"]["path_jumper_count_avg"][2]'),
    ("LJP_path_jumper_C__Mean", 'res["least_jumper_path"]["path_jumper_count_avg"][4]'),
    ("LJP_path_jumper_C__p05", 'res["least_jumper_path"]["path_jumper_count_avg"][3][0]'),
    ("LJP_path_jumper_C__p10", 'res["least_jumper_path"]["path_jumper_count_avg"][3][1]'),
    ("LJP_path_jumper_C__p25", 'res["least_jumper_path"]["path_jumper_count_avg"][3][2]'),
    ("LJP_path_jumper_C__p75", 'res["least_jumper_path"]["path_jumper_count_avg"][3][3]'),
    ("LJP_path_jumper_C__p90", 'res["least_jumper_path"]["path_jumper_count_avg"][3][4]'),
    ("LJP_path_jumper_C__p95", 'res["least_jumper_path"]["path_jumper_count_avg"][3][5]'),
    ("LJP_path_sensor_jumper_L__Max", 'res["least_jumper_path"]["path_sensor_jumper_length_max"][0]'),
    ("LJP_path_sensor_jumper_L__Max_lci", 'res["least_jumper_path"]["path_sensor_jumper_length_max"][1]'),
    ("LJP_path_sensor_jumper_L__Max_hci", 'res["least_jumper_path"]["path_sensor_jumper_length_max"][2]'),
    ("LJP_path_sensor_jumper_L__Median", 'res["least_jumper_path"]["path_sensor_jumper_length_avg"][0]'),
    ("LJP_path_sensor_jumper_L__lci", 'res["least_jumper_path"]["path_sensor_jumper_length_avg"][1]'),
    ("LJP_path_sensor_jumper_L__hci", 'res["least_jumper_path"]["path_sensor_jumper_length_avg"][2]'),
    ("LJP_path_sensor_jumper_L__Mean", 'res["least_jumper_path"]["path_sensor_jumper_length_avg"][4]'),
    ("LJP_path_sensor_jumper_L__p05", 'res["least_jumper_path"]["path_sensor_jumper_length_avg"][3][0]'),
    ("LJP_path_sensor_jumper_L__p10", 'res["least_jumper_path"]["path_sensor_jumper_length_avg"][3][1]'),
    ("LJP_path_sensor_jumper_L__p25", 'res["least_jumper_path"]["path_sensor_jumper_length_avg"][3][2]'),
    ("LJP_path_sensor_jumper_L__p75", 'res["least_jumper_path"]["path_sensor_jumper_length_avg"][3][3]'),
    ("LJP_path_sensor_jumper_L__p90", 'res["least_jumper_path"]["path_sensor_jumper_length_avg"][3][4]'),
    ("LJP_path_sensor_jumper_L__p95", 'res["least_jumper_path"]["path_sensor_jumper_length_avg"][3][5]'),
    ("LJP_path_router_node_branches__Max", 'res["least_jumper_path"]["path_router_node_branches_max"][0]'),
    ("LJP_path_router_node_branches__Max_lci", 'res["least_jumper_path"]["path_router_node_branches_max"][1]'),
    ("LJP_path_router_node_branches__Max_hci", 'res["least_jumper_path"]["path_router_node_branches_max"][2]'),
    ("LJP_path_router_node_branches__Median", 'res["least_jumper_path"]["path_router_node_branches_avg"][0]'),
    ("LJP_path_router_node_branches__lci", 'res["least_jumper_path"]["path_router_node_branches_avg"][1]'),
    ("LJP_path_router_node_branches__hci", 'res["least_jumper_path"]["path_router_node_branches_avg"][2]'),
    ("LJP_path_router_node_branches__Mean", 'res["least_jumper_path"]["path_router_node_branches_avg"][4]'),
    ("LJP_path_router_node_branches__p05", 'res["least_jumper_path"]["path_router_node_branches_avg"][3][0]'),
    ("LJP_path_router_node_branches__p10", 'res["least_jumper_path"]["path_router_node_branches_avg"][3][1]'),
    ("LJP_path_router_node_branches__p25", 'res["least_jumper_path"]["path_router_node_branches_avg"][3][2]'),
    ("LJP_path_router_node_branches__p75", 'res["least_jumper_path"]["path_router_node_branches_avg"][3][3]'),
    ("LJP_path_router_node_branches__p90", 'res["least_jumper_path"]["path_router_node_branches_avg"][3][4]'),
    ("LJP_path_router_node_branches__p95", 'res["least_jumper_path"]["path_router_node_branches_avg"][3][5]'),
    ("LJP_graph_wire_L__Max", 'res["least_jumper_path"]["graph_max_wire_length"][0]'),
    ("LJP_graph_wire_L__Max_lci", 'res["least_jumper_path"]["graph_max_wire_length"][1]'),
    ("LJP_graph_wire_L__Max_hci", 'res["least_jumper_path"]["graph_max_wire_length"][2]'),
    ("LJP_graph_wire_L__Median", 'res["least_jumper_path"]["graph_avg_wire_length"][0]'),
    ("LJP_graph_wire_L__lci", 'res["least_jumper_path"]["graph_avg_wire_length"][1]'),
    ("LJP_graph_wire_L__hci", 'res["least_jumper_path"]["graph_avg_wire_length"][2]'),
    ("LJP_graph_wire_L__Mean", 'res["least_jumper_path"]["graph_avg_wire_length"][4]'),
    ("LJP_graph_wire_L__p05", 'res["least_jumper_path"]["graph_avg_wire_length"][3][0]'),
    ("LJP_graph_wire_L__p10", 'res["least_jumper_path"]["graph_avg_wire_length"][3][1]'),
    ("LJP_graph_wire_L__p25", 'res["least_jumper_path"]["graph_avg_wire_length"][3][2]'),
    ("LJP_graph_wire_L__p75", 'res["least_jumper_path"]["graph_avg_wire_length"][3][3]'),
    ("LJP_graph_wire_L__p90", 'res["least_jumper_path"]["graph_avg_wire_length"][3][4]'),
    ("LJP_graph_wire_L__p95", 'res["least_jumper_path"]["graph_avg_wire_length"][3][5]'),
    ("LJP_graph_node_C__Max", 'res["least_jumper_path"]["graph_max_node_count"][0]'),
    ("LJP_graph_node_C__Max_lci", 'res["least_jumper_path"]["graph_max_node_count"][1]'),
    ("LJP_graph_node_C__Max_hci", 'res["least_jumper_path"]["graph_max_node_count"][2]'),
    ("LJP_graph_node_C__Median", 'res["least_jumper_path"]["graph_avg_node_count"][0]'),
    ("LJP_graph_node_C__lci", 'res["least_jumper_path"]["graph_avg_node_count"][1]'),
    ("LJP_graph_node_C__hci", 'res["least_jumper_path"]["graph_avg_node_count"][2]'),
    ("LJP_graph_node_C__Mean", 'res["least_jumper_path"]["graph_avg_node_count"][4]'),
    ("LJP_graph_node_C__p05", 'res["least_jumper_path"]["graph_avg_node_count"][3][0]'),
    ("LJP_graph_node_C__p10", 'res["least_jumper_path"]["graph_avg_node_count"][3][1]'),
    ("LJP_graph_node_C__p25", 'res["least_jumper_path"]["graph_avg_node_count"][3][2]'),
    ("LJP_graph_node_C__p75", 'res["least_jumper_path"]["graph_avg_node_count"][3][3]'),
    ("LJP_graph_node_C__p90", 'res["least_jumper_path"]["graph_avg_node_count"][3][4]'),
    ("LJP_graph_node_C__p95", 'res["least_jumper_path"]["graph_avg_node_count"][3][5]'),
    ("LJP_graph_jumper_C__Max", 'res["least_jumper_path"]["graph_max_jumper_count"][0]'),
    ("LJP_graph_jumper_C__Max_lci", 'res["least_jumper_path"]["graph_max_jumper_count"][1]'),
    ("LJP_graph_jumper_C__Max_hci", 'res["least_jumper_path"]["graph_max_jumper_count"][2]'),
    ("LJP_graph_jumper_C__Median", 'res["least_jumper_path"]["graph_avg_jumper_count"][0]'),
    ("LJP_graph_jumper_C__lci", 'res["least_jumper_path"]["graph_avg_jumper_count"][1]'),
    ("LJP_graph_jumper_C__hci", 'res["least_jumper_path"]["graph_avg_jumper_count"][2]'),
    ("LJP_graph_jumper_C__Mean", 'res["least_jumper_path"]["graph_avg_jumper_count"][4]'),
    ("LJP_graph_jumper_C__p05", 'res["least_jumper_path"]["graph_avg_jumper_count"][3][0]'),
    ("LJP_graph_jumper_C__p10", 'res["least_jumper_path"]["graph_avg_jumper_count"][3][1]'),
    ("LJP_graph_jumper_C__p25", 'res["least_jumper_path"]["graph_avg_jumper_count"][3][2]'),
    ("LJP_graph_jumper_C__p75", 'res["least_jumper_path"]["graph_avg_jumper_count"][3][3]'),
    ("LJP_graph_jumper_C__p90", 'res["least_jumper_path"]["graph_avg_jumper_count"][3][4]'),
    ("LJP_graph_jumper_C__p95", 'res["least_jumper_path"]["graph_avg_jumper_count"][3][5]'),
]

_COMPILED = [(name, compile(expression, "<columns>", "eval")) for name, expression in COLUMNS]


def extract_config(json_string):
    tmp_obj = json.loads(json_string)
    return {"ID": tmp_obj["experiment_id"], "clothing_id": tmp_obj["clothing_id"],
            "size": tmp_obj["size"], "sex": tmp_obj["sex"],
            "algorythm": tmp_obj["tesselation_algorithm"],
            "node_distance": tmp_obj["node_distance"], "joint_radius": tmp_obj["joint_radius"]}


def get_result(result_folder, algorythm, ex_id, cfg, tier):
    try:
        with open(result_folder + algorythm + "/" + str(ex_id).zfill(7) + ".json", 'r') as ex_file:
            res = json.load(ex_file)
    except FileNotFoundError:
        return None

    fres = {}
    for name, expression in _COMPILED:
        try:
            fres[name] = eval(expression, {}, {"cfg": cfg, "res": res})
        except (KeyError, IndexError, TypeError):
            fres[name] = None

    meta = res.get("_run_meta", {})
    fres["CFG_run"] = meta.get("run", "extended_2026")
    fres["CFG_tag"] = tier
    fres["CFG_mc"] = meta.get("monte_carlo_iterations", 100000)
    return fres


def main():
    logger.critical("Aggregating extended run results")
    console_handler.setLevel(logging.INFO)

    EXPERIMENT_DIR = "./simulation_ext/"
    RESULT_FOLDER = "./results_ext/"
    OUTPUT_FILE = "./results_ext/integrated_results_ext.csv"

    data = []
    for tier in TIERS:
        for cfgfilename in sorted(glob.glob(EXPERIMENT_DIR + "*_" + tier + "_config.json")):
            config = os.path.basename(cfgfilename)[:-len("_" + tier + "_config.json")]
            found = 0
            with open(cfgfilename) as infile:
                for line in infile:
                    if not line.strip():
                        continue
                    cfg = extract_config(line)
                    res = get_result(RESULT_FOLDER + tier + "/", config, cfg["ID"], cfg, tier)
                    if res:
                        data.append(res)
                        found = found + 1
            if found:
                print("Completed loading " + tier + " / " + config + ": " + str(found) + " results")

    if not data:
        logging.error("No results found - run this from the repository root")
        return

    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_FILE, sep=',', encoding='utf-8')
    print("END: " + str(len(df)) + " rows written to " + OUTPUT_FILE)
    print(df.groupby(["CFG_run", "CFG_tag"]).size().to_string())


if __name__ == '__main__':
    main()
