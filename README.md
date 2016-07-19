#SequentialBLR
##Overview
This repository hosts files for running the sequential BLR algorithm on the raspberry pi. 

##Installation, Configuration and Usage
###Installation
There are a number of required packages that must be installed for proper use, including numpy, scipy, and others. To install these packages, simply run the following command:
`make install_all`

###Configuration 
The following files must be modified with the type of sensors being used:

* config/config.json
* config/sensors.json

These files contain information on the location of the z-way server and power database on the network. Samples are provided in the config folder. 

#####IMPORTANT: The device\_name of each device in sensors.json must be _unique_. If you have a mulitsensor such as the Fibaro you can list each individual sensor device as 'device_number.1 or device_number.2' and so on. 

###Usage
Once the configuration files have been setup, the program can be run with verbosity using the following commands:

`python pi_seq_BLR_AVG.py`

or 

`./pi_seq_BLR_AVG.py`

by editing the shebang command on line 1 of the pi\_seq\_BLR.py file
and changing `#!/usr/bin/python -O` to `#!/usr/bin/python`

_note that -O here indicates NO DEBUG_

The program can be run in silent mode (only logging) using the following command:

`python -O pi_seq_BLR_AVG.py` 

or 

`./pi_seq_BLR_AVG.py`


###TODO
Things that still need to be done in this repository:

- [ ] add try, catch error handling when getting data from ZServer or 
        MS SQL database and logging those errors appropriately

- [ ] devise and implement an aggregation method for all the different
        power readings available from the MS SQL database

