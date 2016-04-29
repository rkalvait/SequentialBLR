#!/usr/bin/python
#
# Author: Maxwell Morgan, 2016-04-11
#

import time
import pymssql

def get_data(z_server):
    """returns a list of data from the devices present
    in z_server, not in any particular order
    """
    data_list = []
    data_list += int(time.time())

    ## get data from sensors ##
    for device_id in z_server.list_device_ids():
        data_dict = z_server.get_data(device_id)
        for unique_id, data_value in data_dict:
            data_list += data_value

    return data_list

def get_power(config_info):
    """Connects to the MS SQL database and retrieves the value to be used as
    total power consumption for the home
    """
    user = config_info["database"]["credentials"]["username"],
    password = config_info["database"]["credentials"]["password"],
    host = config_info["database"]["credentials"]["host"],
    port = config_info["database"]["credentials"]["port"]
    database = config_info["database"]["credentials"]["database_name"]

    # TODO, add try catch block here when connecting to the server
    cnx = pymssql.connect(server=host, user=user, password=password,
                          database=database, port=port)

    cursor = cnx.cursor()

    qry_base = "SELECT TOP 1 "

    for data_column in config_info["database"]["table"]["data_columns"]:
        qry_base += "[" + data_column + "],"

    # strip off last comma
    qry_base = qry_base[:-1]

    qry = (qry_base + " FROM "
           + "[" + config_info["database"] + ".[dbo].["
           + config_info["database"]["table"]["name"] + "]"
           + " ORDER BY ["
           + config_info["database"]["table"]["time_column"] + "] "
           + "DESC LIMIT 1")

    cursor.execute(qry)

    for row in cursor:
        # this is where the value are, index the row returned
        # like row[0] for first data column, row[1] for second
        # data column, etc.
        do_stuff = row[0]

    # TODO, aggregate the power values in some way
    final_power = 0
    cnx.close()
    return final_power
