#!/usr/bin/python
#
# Author: Maxwell Morgan, 2016-04-11
#

import sys
import time
import pymssql
import subprocess

# Get the max volume from the microphone
# sample_time is in seconds
def get_sound(sample_time=1):
    
    command = "/usr/bin/arecord -D plughw:1,0 -d " + str(sample_time) + " -f S16_LE | /usr/bin/sox -t .wav - -n stat"
    p = subprocess.Popen(command, bufsize=1, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    for line in p.stdout:
        if "Maximum amplitude" in line:
            return line.split()[-1]


# Get ZWave sensor data
def get_data(z_server):
    """returns a list of data from the devices present
    in z_server, not in any particular order
    """
    data_list = []
    data_list.append(int(time.time()))
    ## get data from sensors ##
    for (device_id) in z_server.list_device_ids():
        # If the server does not respond after ten attempts respond, exit
        for x in xrange(10):
            try:
                data_dict = z_server.get_data(device_id)
                x = 10
            except Exception:
                if x == 10:
                    print "Server connection lost. Closing down."
                    raise Exception
                else:
                    print "Server connection timed out. Attempting to reconnect"
                    time.sleep(1)
    
        for unique_id, data_value in data_dict.iteritems():
            data_list.append(data_value)
    #print "Data_List: ", data_list
    return data_list


# Get power data from power database
def get_power(config_info):
    """Connects to the MS SQL database and retrieves the value to be used as
    total power consumption for the home
    """
    user = config_info["database"]["credentials"]["username"]
    password = config_info["database"]["credentials"]["password"]
    host = config_info["database"]["credentials"]["host"]
    port = config_info["database"]["credentials"]["port"]
    database = config_info["database"]["credentials"]["database_name"]

    host = host + " " + port

    # Connect to database
    while True:
        try:
            cnx = pymssql.connect(server=host,
                                  user=user,
                                  password=password,
                                  database=database)
            break

        except Exception:
            print "Could not connect to power database."
            time.sleep(1)

    cursor = cnx.cursor()

    # Query the database
    Avg_over = 4
    qry_base = "SELECT TOP " + str(Avg_over)

    for data_column in config_info["database"]["table"]["data_columns"]:
        qry_base += "[" + data_column + "],"

    # strip off last comma
    qry_base = qry_base[:-1]

    qry = (qry_base + " FROM "
           + "[" + database + "].[dbo].["
           + config_info["database"]["table"]["name"] + "]"
           + " ORDER BY [") + (config_info["database"]["table"]["time_column"] + "] DESC")
    cursor.execute(qry)
    # Aggregate power to a single number
    # TODO, aggregate the power values in some way
    final_power = 0
    for row in cursor:
        # this is where the value are, index the row returned
        # like row[0] for first data column, row[1] for second
        # data column, etc.
       final_power = final_power + max(row[0],0) + max(row[1],0) # + 4.068189 #offset shark_1 to zero
       print "Shark_2, Shark_1, Final Power", row[0], row[1], final_power
    cnx.close()
    return final_power/Avg_over
