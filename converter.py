import time
import datetime as dt
from grapher import CSV, DATE_FORMAT
import sys

infile = open(sys.argv[1], 'rb')
outfile = open(sys.argv[2], 'wb')

infile.next()
outfile.write("Time,Target,Prediction\n")

count = 0
for line in infile:
    line = line.rstrip()
    line = line.split(',')
    try:
        y_time = dt.datetime.strptime(line[2], '%Y-%m-%d %H:%M:%S')
    except:
        y_time = dt.datetime.fromtimestamp(float(line[2]))


    outfile.write(dt.datetime.strftime(y_time, DATE_FORMAT) + ',')
    outfile.write(line[0] + ',')
    outfile.write(line[1] + '\n')
    count += 1
    
print "Copied %d lines" % count
