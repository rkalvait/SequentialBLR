#!/usr/bin/python
# Date: 2016-04-28
# Author: Maxwell Morgan <mjmor@umich.edu>

"""This module allows for clients to interact with the zwave
server and retrieve device data more readily than currently
available
"""

#third party imports
import socket
import urllib2
from urllib import urlopen as openurl

class ZWave(object):
    """Class designed to store and retrieve information
    pertinent to contacting Zwave devices and the Zway server
    """
    # class variable shared by all instances
    # 1.Some sort of Representation of the JSON file
    # 2.List of all devices
    # 3.Keep track of all the types
    def __init__(self, server_ip, server_port,
                 device_settings_dict):
        #class variable unquie to each instance
        self._server_ip = server_ip
        self._server_port = server_port
        self._devices = {}
        self.devices = device_settings_dict
        #Add a connection status during intiatation

    @property
    def devices(self):
        """a property to return the devices to the user if
        ZWave.devices is referenced and validate their
        dictionary they use during init
        """
        return self._devices

    @devices.setter
    def devices(self, device_settings_dict):
        if len(device_settings_dict) == 0:
            self._devices = {}
        for key in device_settings_dict:
            assert len(device_settings_dict[key]) == 2, \
                    "Device %r is not properly formatted" % key
        # Could add more ERROR CHECKING regarding input dict in this
        # function
        self._devices = device_settings_dict

    def get_data_keys(self):
        """Returns a list of english names of the data points
        available to the user corresponding to the names given
        via the initializer dictionary (i.e Fibaro Lum,
        DoorWindow open_close, etc.)
        """
        keys_list = []
        for device_id, info in self._devices.iteritems():
            key_base = info["name"]
            for data_name in info["data"]:
                key = key_base + data_name
                keys_list.append(key)
        return sorted(keys_list)

    def _check_connection(self):
        try:
            server_url = ("http://"
                          + self._server_ip + ":"
                          + self._server_port + "/")
            response = urllib2.urlopen(server_url, timeout=5)
            response.close()
        except urllib2.URLError:
            raise urllib2.URLError("The url %s could not be reached"
                                   % server_url)
        except socket.timeout:
            raise socket.timeout("Connection to the server timed out")

    def _get_data_urls(self, device_id):
        #print "_get_data_urls device_id:", device_id
        urlbase = ("http://"
                   + self._server_ip + ":"
                   + self._server_port
                   + "/ZWaveAPI/Run/devices["
                   + str(int(float(device_id))) + "].instances[")

        # dictionary storing data point descriptor as key and
        # data point url
        url_dict = {}
        data_dicts = self._devices[str(device_id)]["data"]
        device_name = self._devices[str(device_id)]["name"]
        for data_key, data_dict in data_dicts.iteritems():
            full_url = (urlbase
                        + data_dict["instance_num"]
                        + "].commandClasses["
                        + data_dict["command_class"]
                        + "].data["
                        + data_dict["data_num"]
                        + "]"
                        + data_dict["url_suffix"])
            data_type = data_dict["type"]
            url_dict[device_name + data_key] = [full_url, data_type]
        return url_dict

    def _update_device(self, device_id):
        urlbase = ("http://"
                   + self._server_ip + ":"
                   + self._server_port
                   + "/ZWaveAPI/Run/devices["
                   + str(int(float(device_id))) + "].instances[")

        data_dicts = self._devices[str(device_id)]["data"]
        for data_key, data_dict in data_dicts.iteritems():
            full_url = (urlbase
                        + data_dict["instance_num"]
                        + "].commandClasses["
                        + data_dict["command_class"]
                        + "].Get(sensorType = -1)")
            openurl(full_url)

    def get_data(self, device_id):
        """Returns a dictionary with key representing description
        of data point and values being the data
        """
        data_url_dict = self._get_data_urls(device_id)
        self._check_connection()
        device_name = self._devices[str(device_id)]["name"]
        data_dict = {}
        # make update sensor function here
        for unique_sensor, info_list in data_url_dict.iteritems():
            url_data = (urllib2.urlopen(info_list[0])).read()
            url_data = url_data.strip()
            if info_list[1] == "bool":
                # see if its a number that needs to be converted to bool
                try:
                    val = int(bool(int(url_data)))
                except ValueError:
                    # must be a string then
                    url_data = url_data.lower()
                    if "true" in url_data:
                        val = 1
                    else:
                        val = 0
            elif info_list[1] == "double":
                val = float(url_data)
            data_dict[unique_sensor] = val
        return data_dict

    def list_devices(self):
        """Returns a list of the device names"""
        device_list = []
        for devive_num, entry in self._devices.iteritems():
            device_list.append(entry["name"])
        return device_list

    def list_device_ids(self):
        """Returns list of the device ids currently
        stored in the object
        """
        device_ids = []
        for device_num, key in self._devices.iteritems():
            device_ids.append(device_num)
        return device_ids
