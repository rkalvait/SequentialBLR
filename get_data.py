#!/usr/bin/python
#
# Author: Maxwell Morgan, 2016-04-11
#

import sys
import time
import pymssql

def get_data(z_server):
    """returns a list of data from the devices present
    in z_server, not in any particular order
    """
    data_list = []
    data_list.append(int(time.time()))
    ## get data from sensors ##
    for (device_id, key) in z_server.list_device_ids():

        # If the server does not respond after ten attempts respond, exit
        for x in xrange(10):
            try:
                data_dict = z_server.get_data(device_id)
                x = 10
            except Exception:
                if x == 10:
                    print "Server connection lost. Closing down."
                    sys.exit(1)
                else:
                    print "Server connection timed out. Attempting to reconnect"
                    sleep(1)
    
        for unique_id, data_value in data_dict.iteritems():
            data_list.append(data_value)
    #print "Data_List: ", data_list
    return data_list

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
    try:
        cnx = pymssql.connect(server=host,
                              user=user,
                              password=password,
                              database=database)
    except Exception:
        print "Could not connect to power database."
        raise Exception

    cursor = cnx.cursor()

    # Query the database
    qry_base = "SELECT TOP 1 "

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
       do_stuff = row[0]
       final_power = row[0]

    cnx.close()
    return final_power
