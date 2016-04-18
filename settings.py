#!/usr/bin/python
import json
import logging
import time
import os
import sys
from urllib import urlopen as openurl
import urllib2
import binascii

'''get JSON PATH from the config file'''
JSON_PATH = ''
with open('/usr/local/sbin/SequentialBLR/config.txt') as f:
    for line in f:
        if line.startswith('JSON_PATH'):
            loc = line.find('=')
            JSON_PATH = (line[loc+1:]).rstrip()

def parse_bgcolor(bgcolor):
    if not bgcolor.startswith('#'):
        raise ValueError('A rbgcolor must start with a "#"')
    return binascii.unhexlify(bgcolor[1:])

def is_bgcolor(bgcolor):
    try:
        parse_bgcolor(bgcolor)
    except Exception as e:
        return False
    else:
        return True

def check_settings():
    generate = str(sensorinfo["generate"])
    if not(generate == "data" or generate == "graph" or generate == "both"):
        sys.exit("Error parsing JSON dictionary: 'generate' must be 'data', 'graph', or 'both'.")
    try:
        int(sensorinfo["delay"])
    except ValueError as err:
        sys.exit("Error parsing JSON dictionary: 'delay' must be an integer value.")
    data_dir_str = str(sensorinfo["datadirectory"])
    if not(data_dir_str.startswith('/') and data_dir_str.endswith('/')):
        sys.exit("Error parsing JSON dictionary: 'datadirectory' should begin and end with '/' character.")
    num_sensors = int(len(sensorinfo["sensors"]))
    if num_sensors < 1:
        sys.exit("Error parsing JSON dictionary: there must be at least one sensor configured.")
    graph_arr = []
    for i in range(num_sensors):
        if int(sensorinfo["sensors"][i]["graphnumber"]) not in graph_arr:
            graph_arr.append(int(sensorinfo["sensors"][i]["graphnumber"]))
        interpret = str(sensorinfo["sensors"][i]["interpret"])
        if not (interpret == 'bool' or interpret == 'double' or interpret == 'string' or interpret == '255'):
            sys.exit("Error parsing JSON dictionary at {}: 'interpret' must be 'double', 'bool', or 'string'." .format(str(sensorinfo["sensors"][i]["legend"])))
        try:
            openurl(str(sensorinfo["sensors"][i]["refreshurl"]))
        except Exception:
            sys.exit("Error parsing JSON dictionary at {}: the refresh URL of the {} sensor does not seem to be correct (or your Z-Way server is unreachable!!)." .format(str(sensorinfo["sensors"][i]["legend"])))
        try: 
            urllib2.urlopen(str(sensorinfo["sensors"][i]["dataurl"]), timeout = 1)
        except Exception:
            sys.exit("Error parsing JSON dictionary at {0}: the data URL of the {0} sensor does not seem to be correct (or your Z-Way server is unreachable!!)." .format(str(sensorinfo["sensors"][i]["legend"])))
        if not is_bgcolor(str(sensorinfo["sensors"][i]["linecolor"])):
            sys.exit("Error parsing JSON dictionay at {}: 'linecolor' must be a hexadecimal RGB value (i.e. #FAF0E6)" .format(str(sensorinfo["sensors"][i]["legend"])))
        
    indx = 0
    for i in sorted(graph_arr):
        if indx != i:
            sys.exit("Error parsing JSON dictionary: 'graphnumber' must be an integer between 0 and {} and must not skip any integers in that range." .format((num_sensors-1)))
        indx += 1

def init():
    global SENSOR_REF_ERR
    global SENSOR_DATA_ERR
    global LOGSERVERCONNECT
    LOGSERVERCONNECT = False
    SENSOR_REF_ERR = False
    SENSOR_DATA_ERR = False
    global sensorinfo
    global date_arr
    global open_file
    
    json_file = open(JSON_PATH)
    sensorinfo = json.load(json_file)
    if(sensorinfo["generate"] == "data" or sensorinfo["generate"] == "both"):
        logging.info("Initializing data file variables...")
        dayof_dirpath = sensorinfo["datadirectory"] + time.strftime('%Y') + time.strftime('%m') + time.strftime('%d') + '/'
        if(os.path.exists(dayof_dirpath)):
            logging.info("Changing to directory: " + dayof_dirpath)
            os.chdir(dayof_dirpath)
        else:
            logging.info(("Creating directory: " + dayof_dirpath))
            os.mkdir(dayof_dirpath)
            os.chdir(dayof_dirpath)
        logging.info("Creating: sensordata for hour: " + time.strftime("%H"))
        temp_filename = time.strftime('%Y') + time.strftime('%m') + time.strftime('%d') + '_' + time.strftime('%H') + '.txt'
        open_file = open(dayof_dirpath + temp_filename, 'w')
        hour_str = time.strftime("%H")
        day_str = time.strftime("%j")
        date_arr = [hour_str, day_str, dayof_dirpath, temp_filename]
    return
