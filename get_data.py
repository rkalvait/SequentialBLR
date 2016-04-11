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

st.check_settings()
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
