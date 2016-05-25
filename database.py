# Filename:     database.py
# Author:       Adrian Padin
# Start Date:   5/25/2016

import mysql.connector
import datetime as dt

class Database:

    # Constructor
    # Reads config file and connects to database
    def __init__(self):
        
        with open('config.txt') as file:
            for line in file:
                if line.startswith('HOST'):
                    loc = line.find('=')
                    hst = line[loc+1:].rstrip()
                elif line.startswith('DATABASE'):
                    loc = line.find('=')
                    db = line[loc+1:].rstrip()
                elif line.startswith('USER'):
                    loc = line.find('=')
                    usr = line[loc+1:].rstrip()
                elif line.startswith('PASSWORD'):
                    loc = line.find('=')
                    pswd = line[loc+1:].rstrip()
                    
        config = {
            'user': usr,
            'password': pswd,
            'host': hst,
            'database': db,
            'raise_on_warnings': True
        }

        print "Connecting to database..."        
        self.cnx = mysql.connector.connect(**config)
        self.cursor = self.cnx.cursor()

    # Execute an arbitrary SQL command
    def execute(self, command):
        self.cursor.execute(command)

        # "line" contains the list of data
        for line in self.cursor:
            return line         
        

    # Return a list of the data averaged over the specified period
    # features is the list of features to query for
    # start_time and end_time must be datetime objects of the same type
    def get_avg_data(self, start_time, end_time, feature_list):
        
        if (start_time > end_time):
            raise ValueError("end_time must come after start_time")

        #Build the query:
        isFirst = True
        qry = "SELECT "
        for feature in feature_list:
            if not isFirst:
                qry += ", "
            else:
                isFirst = False

            if "motion" in feature:
                qry = qry + "SUM(" + feature + ")"
            else:
                qry = qry + "AVG(" + feature + ")"

        qry = qry + " FROM SMART WHERE dataTime BETWEEN %s AND %s"

        #Execute the query:
        self.cursor.execute(qry , (start_time, end_time))

        # "line" contains the list of data
        for line in self.cursor:
            return line
        
        
    # Destructor
    # Close the connection when the Database goes out of scope
    def __del__(self):
        self.cursor.close()
        self.cnx.close()
