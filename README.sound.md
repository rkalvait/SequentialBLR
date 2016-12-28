Notes and Setup on Audio Sensor for Raspberry Pi

The following microphone, purchased from Amazon, was used: Super Mini USB 2.0 Microphone. We used this blog post from Simply Me as a starting point for writing our python code. The blog uses Ruby but we used its functionality to write our python version below:

    import subprocess
    sample_time = 1

    while True:

        command = "/usr/bin/arecord -D plughw:1,0 -d " + str(sample_time) + " -f S16_LE | /usr/bin/sox -t .wav - -n stat"

        p = subprocess.Popen(command, bufsize=1, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        for line in p.stdout:
            if "Maximum amplitude" in line:
                print "Max:", line.split()[-1]

The functionality of this is two-fold. The arecord program records a sound bit for the length of sample_time, which is in seconds. The second part is the sox analyzer, which needs to be installed prior to use (using “sudo apt-get install sox”). The sox analyzer prints out the following data points from the recorded sample:

The data point we care about is the Maximum amplitude that occurred within the given sample_time. The sample time dictates how long your program halts and records. We recommend using a short sample time because it will stall your program by the sample_time. In addition, keep in mind sample_time must be an integer, hence the smallest value that sample_time can be is 1 second. 
