#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 14:47:33 2020

@author: Lia Thomson

An attempt at temperature PID. Needs further testing and modification.

Reads temperature through one MCCDAQ channel, and adjusts an output voltage
accordingly. The input temperature is meant to monitor a liquid, while the 
output voltage is meant to push cold water around the liquid, to cool it.

Last updated: Sep. 25, 2020
"""

from __future__ import absolute_import, division, print_function

from mcculw import ul

import time
import sys
import tkinter as tk
import pandas as pd
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

sys.path.append(r"C:\Users\Nikon\Desktop\MCCDAQ")

from mccdaqFuncs import outputOneChannel, outputMultipleChannels, readTempChannel, readMultipleTemps
from mccdaqFuncs import initializeInputBoard, initializeOutputBoard, saveCSV

use_device_detection = True

################################### SETTINGS ##################################

BOARD_NUM_INPUT = 0
BOARD_NUM_OUTPUT = 3

INITIAL_TIME_PERIOD = 90 #changed from 60
TIME_PERIOD = 30
SAMPLE_TIME = 15

FLIP_MODIFIER= 1.25 #changed from 1.5
DESCENDING_MODIFIER = 1.5 #changed from 1.5

TOLERANCE = 0.5 #degree
MAX_VOLTAGE = 0.6
STARTING_VOLTAGE = 0.3

CHANNELS = []
cIn = 0 #input channel (read temp.)
cOut = 0 #output channel (pressure)
idealValue = 10


############################### END OF SETTINGS ###############################

increments = [0.01, 0.02, 0.05, 0.1]
upperLimits = [0, 5, 10, 15, 100]
timePeriods = [120, 60, 40, 20]
timeLimits = [0, 2, 5, 10, 100]
currVoltage = STARTING_VOLTAGE

header = ["Time"]
headerChannels = ["Channel {}".format(c) for c in CHANNELS]
header.extend(headerChannels)
header.append("Voltage")

data = []

lastDifference = 0
lastValue = idealValue

################################# BOARD INPUT #################################

def finish():
    outputOneChannel(cOut, BOARD_NUM_OUTPUT, 0)
    
    if use_device_detection:
        ul.release_daq_device(BOARD_NUM_INPUT)
        ul.release_daq_device(BOARD_NUM_OUTPUT)
    
    saveCSV("temperatureData")

def increasePressure(channel, modifier):
    global currVoltage
    
    if(currVoltage == MAX_VOLTAGE):
        print("Can't increase pressure more")
    else:
        if((currVoltage + modifier) > MAX_VOLTAGE):
            currVoltage = MAX_VOLTAGE
        else:
            currVoltage += modifier
            
        currVoltage = round(currVoltage, 2)
        
        outputOneChannel(channel, BOARD_NUM_OUTPUT, currVoltage)
        
        print("increased voltage to {} to channel {}".format(currVoltage, channel))


def decreasePressure(channel, modifier):
    global currVoltage
    
    if(currVoltage == 0):
        print("Can't decrease pressure more")
    else:
        if((currVoltage - modifier) < 0):
            currVoltage = 0
        else:
            currVoltage -= modifier
            
        currVoltage = round(currVoltage, 2)
        
        outputOneChannel(channel, BOARD_NUM_OUTPUT, currVoltage)
        
        print("decreased voltage to {} to channel {}".format(currVoltage, channel))

def calculateTimeModifier(difference):
    multiplier = 1
    if(difference * lastDifference < 0):
        #if the sign of the differences flipped, so it was increasing and now decreasing or vice versa
        #wait a longer period of time
        multiplier *= FLIP_MODIFIER
    
    if(difference > 0 and lastDifference > difference):
        #wait longer if the temperature is above the ideal, but decreasing
        multiplier *= DESCENDING_MODIFIER

    modifier = 0
    for i in range(1, len(upperLimits)):
        lower = upperLimits[i - 1]
        upper = upperLimits[i]
        if(abs(difference) > lower and abs(difference) <= upper):
            modifier = increments[i - 1]
            break

    timeWait = 60
    for i in range(1, len(timeLimits)):
        lower = timeLimits[i - 1]
        upper = timeLimits[i]
        if(abs(difference) > lower and abs(difference) <= upper):
            timeWait = timePeriods[i - 1] * multiplier
            break

    print("{}, {}\t".format(timeWait, modifier), end = "")

    return timeWait, modifier

def readTemps():
    values = []
    for i in range(len(CHANNELS)):
        c = CHANNELS[i]
        temp = readTempChannel(c, BOARD_NUM_INPUT)
        if(c == cIn):
            currValue = temp
        
        values.append(temp)
    return values, currValue

def tempPID(cIn, cOut, idealValue):
    global lastDifference
    global lastValue

    values, currValue = readTemps()

    print(time.strftime("%m-%d-%y %H:%M:%S\t", time.localtime()) +
                        "\t".join(["{}: {}".format(
                                                    i,
                                                    round(values[i], 4))
                                    for i in range(len(CHANNELS))]) + 
                        "\t",
            end = "")
    
    currDifference = currValue - idealValue
    retValue, modifier = calculateTimeModifier(currDifference)
    lastDifference = currDifference
    difference = abs(currDifference)
    
    if(difference < TOLERANCE):
        if(abs(currValue - lastValue) > 1):
            #large change since last adjustment
            if(currValue < lastValue):
                #temp. has been decreasing rapidly
                decreasePressure(cOut, 0.01)
            else:
                #temp. has been increasing rapidly
                increasePressure(cOut, 0.01)
            
            retValue *= 0.5
        print("No change")
        #in ideal range
    else:
            
        if(currValue < idealValue):
            #too cold
            decreasePressure(cOut, modifier)
        else:
            #too warm
            increasePressure(cOut, modifier)
    
    lastValue = currValue
    
    return retValue, values
      
def update():
    #start with the time
    newRow = [time.strftime("%H:%M:%S", time.localtime())]
    
    #readTemps
    timeWait, values = tempPID(cIn, cOut, idealValue)
    newRow.extend(values)
    
    #add the voltage
    newRow.append(currVoltage)
    
    data.append(newRow)
    return timeWait, values


class UpdatingFigure:
    """Object that creates and runs the updating figure. It periodically calls upon the
    update function and sample function."""
    def __init__(self):
        root = tk.Tk()
        self.root = root
        
        #make df, which will store all the data points to be used in the figure
        self.df = pd.DataFrame(np.zeros((50, len(CHANNELS))), columns = headerChannels)
        #make times, which will store all the times each sample was taken
        self.times = pd.DataFrame([i for i in range(-50, 0)])
        
        #make the figure
        figure = plt.Figure()
        ax = figure.add_subplot()
        canvas = FigureCanvasTkAgg(figure, root)
        canvas.get_tk_widget().pack()

        #make lines in the figure, one for each column in df, and plot them
        lines = []
        for column in self.df:
            lines.append(self.df[column].plot(kind = "line", ax = ax))

        #the end button
        button = tk.Button(root, text = "End", command = self.end)
        button.pack()

        #misc.
        self.canvas = canvas
        self.ax = ax
        self.lines = lines
        self.figure = figure
        
        self.cont = True
        self.jobAdjust = None
        self.jobSample = None
        
        self.startTime = time.time()

    def end(self):
        """Finish the data collection."""
        self.root.after_cancel(self.jobAdjust)
        self.root.after_cancel(self.jobSample)
        self.jobAdjust = None
        self.jobSample = None
        self.root.quit()

    def run(self):
        """Run. This is called only once."""
        #schedule sampling and adjusting
        self.jobAdjust = self.root.after(500, self.adjustVoltage)
        self.jobSample = self.root.after(2000, self.sample)

        self.root.mainloop()
    
    def adjustVoltage(self):
        """Adjust the voltage output by calling update(), update the plot, and schedule
        this function to run again."""
        
        timeWait, values = update()
        
        self.updatePlot(values)
        
        self.jobAdjust = self.root.after(int(timeWait * 1000), self.adjustVoltage)
    
    def updatePlot(self, values):
        """Update the plot."""
        
        #shift data back one
        for i in range(1, self.df.shape[0]):
            self.df.iloc[i - 1] = self.df.iloc[i]
            self.times.iloc[i - 1] = self.times.iloc[i]
            
        #add new values
        self.df.iloc[-1] = values
        self.times.iloc[-1] = time.time() - self.startTime
        
        #update the index, which will be used as the x position for each point
        self.df.index = self.times[0]

        self.ax.clear()         # clear axes from previous plotß

        #plot lines again
        for column in self.df:
            self.df[column].plot(kind = "line", ax = self.ax)

        self.canvas.draw()
    
    def sample(self):
        """Samples temperatures and adds them to data, but does not adjust voltage."""
        newRow = [time.strftime("%H:%M:%S", time.localtime())]
    
        #readTemps
        values, currValue = readTemps()
        
        newRow.extend(values)
        
        #add the voltage
        newRow.append(currVoltage)
        
        data.append(newRow)

        print(time.strftime("%m-%d-%y %H:%M:%S\t", time.localtime()) +
                    "\t".join(["{}: {}".format(
                                                i,
                                                round(values[i], 4))
                                for i in range(len(CHANNELS))]))

        #update plot
        self.updatePlot(values)
        
        self.jobSample = self.root.after(int(SAMPLE_TIME * 1000), self.sample)

def runTempPID():
    #first run the initial voltage
    update()
    time.sleep(INITIAL_TIME_PERIOD)
    u = UpdatingFigure()
    u.run()

if __name__ == '__main__':
    initializeInputBoard(BOARD_NUM_INPUT)
    initializeOutputBoard(BOARD_NUM_OUTPUT)
    runTempPID()
    finish()
        
