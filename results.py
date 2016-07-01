"""CSV reading/writing helper functions

Filename:     results.py
Author(s):    apadin
Start Date:   2016-06-24

This module contains two useful helper functions:
- readResults(csvfile)
- writeResults(csvfile, results)

These functions assist in the reading and writing of 
results files in a particular format.
    
"""

import csv


def readResults(csvfile):
    """Retrieve data in file given by 'csvfile'.
    
    This function reads in the data located in 'csvfile' and return a tuple
    of lists containing the data from each column. It assumes that the data
    has a header row and skips over it.

    """
    
    with open(csvfile, 'rb') as infile:
        reader = csv.reader(infile)
        reader.next()
        return zip(*reader)


def writeResults(csvfile, results):
    """Save 'results' data in file given by 'csvfile'.
    
    This function takes the column data given in 'results' and writes it to
    the file given by 'csvfile', overwriting the old file if one exists

    """
    
    with open(csvfile, 'wb') as outfile:
        writer = csv.writer(outfile)
        row_list = zip(*results) #Get columns out of rows
        for row in row_list:
            writer.writerow(row)
            