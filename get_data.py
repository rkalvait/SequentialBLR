#! /usr/bin/python
# vim:ts=4:sw=4:sts=4:tw=100
# -*- coding: utf-8 -*-
#
# Author: Maxwell Morgan, 2016-04-11
#

import settings as st
import time
from urllib import urlopen as openurl
import urllib2
import pymssql

#st.check_settings()
st.init()

def get_data():
	num_sensors = len(st.sensorinfo["sensors"])
	data_list = [0]*(num_sensors + 1)
    if st.sensorinfo["time"]["refreshurl"] != "null":
		data_list[0] = int(time.time())

    for i in range (0, num_sensors):
        if (st.sensorinfo["sensors"][i]["refreshurl"] != "null"):
			openurl(str(st.sensorinfo["sensors"][i]["refreshurl"]))
			urldata = (urllib2.urlopen(str(st.sensorinfo["sensors"][i]["dataurl"]))).read()
			val = urldata.strip()
			#still have to deal with string/int/etc data! cant graph string
			if "bool" in st.sensorinfo["sensors"][i]["interpret"]:
				if "true" in val: data_list[i+1] = 1
				else: data_list[i+1] = 0
			elif "double" in st.sensorinfo["sensors"][i]["interpret"]:
				rounded = '{0:.2f}'.format(float(val)) 
				data_list[i+1] = float(rounded)
			else:
				matchkey = (str(st.sensorinfo["sensors"][i]["interpret"])).strip()
				if(val == matchkey): data_list[i+1] = 1
				else: data_list[i+1] = 0

	return data_list

def get_power():
	user = json_sensor_data["database"]["credentials"]["username"],
	password = json_sensor_data["database"]["credentials"]["password"],
	host = json_sensor_data["database"]["credentials"]["host"],
	database = json_sensor_data["database"]["credentials"]["database_name"]
	cnx = pymssql.connect(server, user, password, database)

	cursor = cnx.cursor()
	qry = "SELECT TOP 1" 
		  + json_sensor_data["database"]["tables"]["data_column"] 
		  + " FROM " 
		  + json_sensor_data["database"]["tables"]["table_name"]
		  + " ORDER BY "	
		  + json_sensor_data["database"]["tables"]["time_column"] 
		  + "DESC LIMIT 1"

	cursor.execute(qry)
	cnx.commit()
	data = cursor[0][0] # cursor syntax could be wrong
	cnx.close()
	return data
