



##############################  CSV FUNCTIONS  ##############################

# Read in a results file and return the three data lists
def readResults(csvfile):
    with open(csvfile, 'rb') as infile:
        reader = csv.reader(infile)
        reader.next() #Skip header row
        y_time, y_target, y_predict = [], [], []
        
        for row in reader:
            
            # Make sure none of the entries was corrupted
            #try:    y_time.append(float(row[0]))
            #except: break
            y_time.append(row[0])

            try:    y_target.append(float(row[1]))
            except: y_time.pop(); break
            
            try:    y_predict.append(float(row[2]))
            except: y_time.pop(); y_target.pop(); break

    return y_time, y_target, y_predict


# Save results to a file for later graphing
# 'csvfile' is the name of the file to be written to
# 'results' is a tuple of iterables of the same length with the data to write
def writeResults(csvfile, results):
    with open(csvfile, 'wb') as outfile:
        writer = csv.writer(outfile)
        row_list = zip(*results) #Get columns out of rows
        for row in row_list:
            writer.writerow(row)
            

##############################  CSV CLASS  ##############################
class CSV:

    # Constructor
    def __init__(self, datafile = DEFAULT_FILE):
        self.datafile = datafile


    # Reset the CSV and write the header
    # Deletes all previous data in the file
    def clear(self):
        with open(self.datafile, 'wb') as outfile:
            outfile.write('Timestamp,Target,Prediction\n') # Write the header

    # Append given data to the CSV file
    def append(self, y_time, y_target, y_predict):

        file = open(self.datafile, 'ab')

        assert(len(y_time) == len(y_target))
        assert(len(y_time) == len(y_predict))

        # y_time should be a list of UNIX timestamps
        y_time = [dt.datetime.fromtimestamp(float(t)).strftime(DATE_FORMAT) for t in y_time]
        y_target = [str(t) for t in y_target]
        y_predict = [str(t) for t in y_predict]

        for i in xrange(len(y_time)):
            file.write(y_time[i] + ',' +  y_target[i] + ',' + y_predict[i] + '\n')
        file.close()


    # Read the data in the CSV file and return results
    # Target and prediction are floats, time contains strings
    def read(self):

        file = open(self.datafile, "rb")
        file.next() # Throw out the header row

        y_time, y_target, y_predict = [], [], []

        for line in file:
            line = line.rstrip() #Remove newline
            data = line.split(',')

            # Only grow list if CSV was written properly
            if len(data) == 3:

                # Could be a timestamp or a datetime string
                try:
                    y_time.append(float(data[0]))
                except ValueError:
                    y_time.append(data[0])

                y_target.append(float(data[1]))
                y_predict.append(float(data[2]))

        file.close()
        
        

        return y_time, y_target, y_predict
