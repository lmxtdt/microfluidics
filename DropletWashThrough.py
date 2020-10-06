# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 16:35:20 2020

@author: Lia Thomson

Washes droplets through a device in cycles, stopping to take a picture.
OLD. May use valid methods (except the analyzeDroplets function), but has not
been used or updated in months.
"""

import sys

sys.path.append(r"C:\Users\Nikon\Desktop\MCCDAQ\automation")
sys.path.append(r"C:\Program Files\Micro-Manager-2.0gamma")

import AutomationChannels as ac
import uManagerFuncs as umf
import numpy as np
import time as tm
import cv2
import csv
from glob import glob
from os import mkdir

def analyzeDroplets(img, imgNum, array):
    normalized = np.zeros(img.shape, dtype = "uint8")
    cv2.normalize(img, normalized, 0, 255, cv2.NORM_MINMAX, dtype = 8)
    bimg = cv2.medianBlur(normalized, 5) #blur 8 bit
    blur16 = cv2.medianBlur(img, 5) #blur 16 bit
    
    #detect droplets    
                                #param1: sensitivity; param2: related to circumference
    droplets = cv2.HoughCircles(bimg, cv2.HOUGH_GRADIENT,1, minDist = 40, param1=20,
                                param2=20, minRadius=20, maxRadius=70)
        
    if droplets is not None:
        droplets = np.round(droplets[0,:]).astype("int") #what does this do
        
        #show droplets in output image
        for (x,y,r) in droplets:
            #calculate average luminosity
            #mask image to analyze single droplet data
            temp_img = np.zeros(bimg.shape, np.uint8)
            cv2.circle(temp_img , (x,y), r, (255,255,255), -1)
                
            #get mean
            meanValue = cv2.mean(blur16, mask = temp_img)
            
            #add droplet data to the image array
            currentRow = [imgNum]
            currentRow.append(meanValue[0])
            currentRow.append(r)
            array.append(currentRow)

channelsOutput = [2, 3] #numbers of the channels that output voltage

numLoops = 400 #number of pictures to take
numStages = 3 #number of different voltages there will be each thing
secPerStage = [2, 5, 5] #it's an array now

#fill array voltage based on increment
voltageValues = np.zeros((numStages, len(channelsOutput)))

#manual filling in of voltageValues

voltageValues[0] = [1.2, 0.8]
voltageValues[1] = [0, 0]
voltageValues[2] = [0.8, 1.1]


###################

showEach = True

#file paths
overallPath = r"C:\Users\Nikon\Desktop\Theo\200302c-1.2-0.8"

date = tm.ctime(tm.time()).split(" ")
hour = date[4].split(":")
finalHour = hour[0] + "_" + hour[1] + "_" + hour[2]
finalDate = date[1]+ "-" + date[3] + "-" + date[5] + "-"+ finalHour
csvPath = overallPath + "\\" + finalDate + ".csv"

imagesPath = overallPath + "\\imgs\\"
if(len(glob(imagesPath)) == 0):
    mkdir(imagesPath)
    
#csv file: open, write header
csvFile = open(csvPath, mode = "a")
w = csv.writer(csvFile)
w.writerow(["number", "mean", "radius"])

m = umf.setup()

#other stuff
startTime = tm.time()
lastTime = startTime
for i in range(numLoops): #do the whole procedure numLoops times
    for j in range(numStages): #go through each stage
        ac.outputVoltage(channelsOutput, voltageValues[j])
        print(voltageValues[j])
        timeToSleep = secPerStage[j] - (tm.time() - lastTime) #adjusts for the time taken to outputVoltage and analyze images
        tm.sleep(timeToSleep)
        lastTime = tm.time()
        if(j == 1): #second stage, i.e. 0 voltage stage
            #take picture
            img = umf.pic(m)
            
            #show picture & time taken
            if(showEach):
                print(tm.ctime(lastTime))
                umf.show(img)

            #analyze droplets and write results            
            #array = []
            #analyzeDroplets(img, i, array)
            #for row in array:
            #    w.writerow(row)
            
            #save images
            imageName = imagesPath + str(i)
            umf.saveImage(img, imageName)
            
ac.outputVoltage(channelsOutput, [0,0])
csvFile.close()