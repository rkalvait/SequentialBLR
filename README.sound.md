Notes and Setup of Audio Sensor for Raspberry Pi
==============

The following microphone, purchased from Amazon, was used: [Super Mini USB 2.0 Microphone](https://goo.gl/6KRlix). We used this [blog post from Simply Me](https://goo.gl/dOVq84) as a starting point for writing our python code. The blog uses Ruby but we used its functionality to write our python version below:

    import subprocess
    sample_time = 1

    while True:

        command = "/usr/bin/arecord -D plughw:1,0 -d " + str(sample_time) + " -f S16_LE | /usr/bin/sox -t .wav - -n stat"

        p = subprocess.Popen(command, bufsize=1, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        for line in p.stdout:
            if "Maximum amplitude" in line:
                print "Max:", line.split()[-1]

The functionality of this is two-fold all of which are outlined in the command variable above. The *arecord* program runs first which records a sound bite for the length in second specified by the sample_time. The second part is the [SoX analyzer](http://sox.sourceforge.net/), which needs to be installed prior to use (using “sudo apt-get install sox” on Linux). The SoX analyzer prints out data points from the recorded sample such as mean amplitude, max amplitude, length in seconds and more. 

The data point we care most about is the Maximum amplitude during the recording. The sample_time dictates how long your program halts and records using arecord. We recommend using a short sample time because it will stall your program by the sample_time. In addition, keep in mind sample_time must be an integer, hence the smallest value that sample_time can be is 1 second. 
