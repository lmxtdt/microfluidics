# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 15:19:05 2020

@author: Lia Thomson

Washes droplets through a device in cycles. Does not take pictures (unlike
DropletWashThrough.py)
"""

#washes droplets through device without taking pictures

import sys

sys.path.append(r"C:\Users\Nikon\Desktop\MCCDAQ\automation")
sys.path.append(r"C:\Program Files\Micro-Manager-2.0gamma")

import AutomationChannels as ac
import numpy as np
import time as tm

channelsOutput = [2, 3] #numbers of the channels that output voltage #3 droplets 4 oil

numLoops = 200 #number of pictures to take
numStages = 3 #number of different voltages there will be each thing
secPerStage = [3, 5, 2.5]

#fill array voltage
voltageValues = np.zeros((numStages, len(channelsOutput)))

voltageValues[0] = [1.5, 0.8]
voltageValues[1] = [0, 0]
voltageValues[2] = [0.8, 1.1]


###################

#other stuff
startTime = tm.time()
lastTime = startTime
for i in range(numLoops): #do the whole procedure numLoops times
    for j in range(numStages): #go through each stage
        ac.outputVoltage(channelsOutput, voltageValues[j])
        print(tm.ctime(tm.time()))
        print(voltageValues[j])
        timeToSleep = secPerStage[j] - (tm.time() - lastTime) #adjusts for the time taken to outputVoltage and analyze images
        tm.sleep(timeToSleep)
        lastTime = tm.time()
            
ac.outputVoltage(channelsOutput, [0,0])
print("Done.")