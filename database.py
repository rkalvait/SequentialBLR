# Filename:     database.py
# Author:       Adrian Padin
# Start Date:   5/25/2016

import mysql.connector

class Database:

    # Constructor
    # Reads config file 
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
        self.cursor = cnx.cursor()
        
        
    def get_avg_data(self, start_time, end_time):
        
        
        
        
    def __del__(self):
        self.cursor.close()
        self.cnx.close()
