# Filename:     zway.py
# Authors:      apadin, mjmor, yabskbd, dvorva
# Start Date:   5/9/2016

"""Interface for gathering data from ZWave devices running
on a ZWay server.

This python library is effectively a wrapper for the existing
JSON library published by ZWay. It requires that the server
software is already installed and running on the host machine.

It also requires knowledge of the devices on the network. 
Hopefully this restriction will be lifted once I figure out
a way to parse this information from the devices page. 

- Adrian Padin, 1/20/2017

"""


#==================== LIBRARIES ====================#
import os
import json
import requests


#==================== CLASSES ====================#

class Server(object):

    def __init__(self, host, port, device_dict={}):
        """
        Initialize connection to the network and obtain
        a list of available devices.
        """
                
        # Check connection to the host
        self.base_url = "http://{}:{}/ZWaveAPI/".format(host, port)
        try:
            requests.post(self.base_url + "Data")
        except Exception:
            raise Exception("connection could not be established")
        
        # Obtain device dictionary
        if (device_dict == {}):
            self.update_devices()
        else:
            self.devices = device_dict

    def update_devices(self):
        """
        Fetch device information from the server and generate device dictionary.
        Used on startup, as well as when adding or removing devices.
        """
        
        self.devices = {}
        devices_page = requests.post(self.base_url + "Run/devices").json()

        for device_id_base in devices_page:
            device_count = 0
            instances = devices_page[device_id_base]['instances']
            for instance_num in instances:
                commandClasses = instances[instance_num]['commandClasses']
                for commandClass in commandClasses:
                    if (commandClass == '48' or commandClass == '49'):
                        for data_num in commandClasses[commandClass]['data']:
                            if (data_num.isdigit()):
                                data_dict = {}
                                data_dict['instance_num'] = instance_num
                                data_dict['command_class'] = commandClass
                                data_dict['data_num'] = data_num
                                if (commandClass == '48'):
                                    data_dict['url_suffix'] = 'level.value'
                                    data_dict['type'] = 'bool'
                                else: 
                                    data_dict['url_suffix'] = 'val.value'
                                    data_dict['type'] = 'double'
                                    
                                device_id = "{}.{}".format(device_id_base, device_count)
                                self.devices[device_id] = {}
                                self.devices[device_id]['data'] = data_dict
                                device_count += 1
                                
                                sensor_type = self.sensor_type(device_id)
                                sensor_type = sensor_type.replace(' ', '_')
                                name = device_id_base + '_' + sensor_type
                                self.devices[device_id]['name'] = name

        return self.devices
    
    def device_IDs(self):
        """Return a list of available device IDs"""
        return self.devices.keys()

    def software_version(self):
        """Get the version of ZWay software running on this server"""
        command = self.base_url + "Data"
        Data_dict = requests.post(self.base_url + command).json()
        return Data_dict['controller']['data']['softwareRevisionVersion']
        
    def battery_level(self, device_id):
        instance = self.devices[str(device_id)]['data']['instance_num']
        command = "Run/devices[{}].instances[0].Battery.data.last.value".format(device_id, instance)
        battery_percent = requests.post(self.base_url + command).content
        return int(battery_percent)
        
    def get_data(self, device_id):
        """Fetch the data from this sensor given device ID and device information"""
        device_id = str(device_id)
        instance_num  = self.devices[device_id]['data']['instance_num']
        command_class = self.devices[device_id]['data']['command_class']
        data_num      = self.devices[device_id]['data']['data_num']
        data_type     = self.devices[device_id]['data']['type']
        suffix        = self.devices[device_id]['data']['url_suffix']
        device        = int(float(device_id))
        
        # Update the device
        command = "Run/devices[{}].instances[{}].commandClasses[{}].Get(sensorType=-1)"
        command = command.format(device, instance_num, command_class)
        requests.post(self.base_url + command).content

        # Retrieve data
        command = "Run/devices[{}].instances[{}].commandClasses[{}].data[{}].{}"
        command = command.format(device, instance_num, command_class, data_num, suffix)
        data = requests.post(self.base_url + command).content
        
        if (data_type == 'bool'):
            data = 1 if (data == 'true') else 0
        
        return float(data)
        
    def sensor_type(self, device_id):
        """Return string representing the type of data from this device."""
        device_id = str(device_id)
        device        = int(float(device_id))
        instance_num  = self.devices[device_id]['data']['instance_num']
        command_class = self.devices[device_id]['data']['command_class']
        data_num      = self.devices[device_id]['data']['data_num']
        
        # Issue the command
        command = "Run/devices[{}].instances[{}].commandClasses[{}].data[{}].sensorTypeString.value"
        command = command.format(device, instance_num, command_class, data_num)
        return requests.post(self.base_url + command).content
        
    def sensor_name(self, device_id):
        """Return string representing the name of this device."""
        return self.devices[device_id]['name']
        
    def save_devices_to_file(self, fh):
        """Prints device dictionary to a file-like object in json format."""
        json.dump(self.devices, fh)

''' Future Updates

To get type of sensor:
    results['0']['commandClasses']['49']['data']['1']['sensorTypeString']['value']

'''
