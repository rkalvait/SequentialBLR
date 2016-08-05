#SequentialBLR
##Overview
This repository hosts files for running the Sequential BLR algorithm on a Raspberry Pi. This project is known to work on the Pi 2 and Pi 3 running Raspbian Jessie.

This program is designed to work specifically with Z-wave home sensors connected to a Z-way server. The Z-wave sensors used in our implementation were:

* Fibaro Multisensor (3)
* EcoLink Door/Window Sensor
* Aeon Labs Appliance Switch

The total costs of this project were:

Raspberry Pi 3:      $35

Fibaro Sensors (3): $180

Aeon Labs Switch:    $30

Door/Window Sensor:  $30

Total Cost:         $275

##Installation, Configuration and Usage
###Installation
To get started, first download these files onto your Raspberry Pi. Make sure you have Python 2.6 or 2.7 installed.
There are a number of required packages that must be installed for proper use, including numpy, scipy, and others. 
To install these packages, simply run the following command:

`sudo make install_all`

###Configuration


#####NOTE: The power readings for our test unit came from a separate database. If you choose to gather power data in some other method, you must either put your data into a database or change how power data is gather in get_data.py

The following files must be modified with the type of sensors being used:

* `config/config.json` contains information about how to access the z-way server and power database.
* `config/sensors.json` contains information needed by the z-way server to access the z-wave sensors.

Samples of these files are provided in the config folder. They can be edited to match the desired settings. 

#####NOTE: The device\_name of each device in sensors.json must be _unique_. If you have a mulitsensor such as the Fibaro you can list each individual sensor device as 'device_number.1 or device_number.2' and so on. 

###Usage
####The Algorithm
This is a brief discussion of the algorithm that is used in the analysis, which is necessary to understanding some of the input parameters.

Periodically (for example, once every minute), the program gathers data about the house such as temperature, humidity, etc. as well as the total power used during that minute. 
After recording this data, the program then looks at the previous data it has collected and tries to predict what the next power measurement should be. 
An anomaly is detectd when the actual power usage and the predicted usage do not line up. 


####Running the Python Script
Once the configuration files have been setup, open a terminal (or SSH into the Pi), navigate to the folder that contains the scripts, and run the following command:

`python pi_seq_BLR_AVG.py [-s] <granularity> <window\_size> <forecasting\_interval>`

The arguments are as follows:
* [-s] : This is an optional flag that specifies whether you are using sound or not. There is more information on this below.
* granularity : The granularity is the time between measurements, in minutes. In other words, if the granularity is 5, data will be recorded every 5 minutes.
* window_size : The window is the amount of past data to look at when making a prediction, in hours.
* forecasting_interval : The interval is the amount of time between "training sessions"; in other words, how often the program really looks at all the past data as opposed to just making a prediction. This is measured in hours.

An example would look like this:

`python pi_seq_BLR_AVG.py 1 24 1`

After running this command, the program will immediately starting collecting and analyzing data. 
However, it requires a certain amount of data to be collected before it can start making prediction.
This means that you will not see any predictions made until after the `window size` number of hours have passed.
In the example above, this would mean predictions will start being made after 24 hours of running the script.

####Logging
The program is configured to leave behind a log of its past predictions in the following location:

`/var/log/sequential_predictions.log`

This file can be checked at any time to view any past entries since the first running of the script.
It also contains information about errors and other problems, which can be useful if the program fails unexpectedly.

##Reporting Problems or Suggesting Improvements
Please feel free to use "Issues" feature of our Github page to report issues or recommend improvements.
We are always looking to improve and we appreciate feedback of any kind.


