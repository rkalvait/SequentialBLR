#SequentialBLR

This repository hosts files for running the sequential BLR algorithm on 
the raspberry pi. 

###Configuration 
In order to run succesfully, the following files must
be configured properly:

* config/config.json
* config/sensors.json

Samples and examples of these configuration files can be found in the 
config directory.

###Execution
Once the configuration files have been setup, the program can be run 
with verbosity using the following commands:

`python pi_seq_BLR.py`

or 

by editing the shebang command on line 1 of the pi\_seq\_BLR.py file
and changing `#!/usr/bin/python -O` to `#!/usr/bin/python`

_note the -O here means NO DEBUG_

The program can be run in silent mode (only logging) using the following
command:

`python -O pi_seq_BLR.py` 

or 

`./pi_seq_BLR.py`


###TODO
Things that still need to be done in this repository:

- [ ] add try, catch error handling when getting data from ZServer or 
        MS SQL database and logging those errors appropriately

- [ ] devise and implement an aggregation method for all the different
        power readings available from the MS SQL database

