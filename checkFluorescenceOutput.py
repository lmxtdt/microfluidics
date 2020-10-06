# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 16:21:43 2020

@author: Lia Thomson

This script is meant to adjust the ratio of oil/fluorescent liquid used to make
droplets, so that the droplets' luminescence falls within a desired range. It
checks this by taking a picture using microManager regularly.
OLD. Does not use current droplet-finding algorithm in dropletAnalysisFuncs.py
"""


#another script
import sys

sys.path.append(r"C:\Users\Nikon\Desktop\MCCDAQ\automation")
sys.path.append(r"C:\Program Files\Micro-Manager-2.0gamma")

import uManagerFuncs as ts
import AutomationChannels as ac
import numpy as np
import cv2
import matplotlib.pyplot as plt
import time as tm

def setupMicroscope():
    #set up devices, camera settings
    ts.setup()
    ts.mmc.setProperty("filter", "Label", "3-FITC") #GFP filter
    ts.mmc.setProperty("cam", "Binning", "2x2") #adjust binning

#finds median of a grayscale image, considering only values <= maxMin
def findMedian(grayImage, maxMin = 256):
    bins = np.zeros((1,256))
    for i in range(grayImage.shape[0]):
        for j in range(grayImage.shape[1]):
            value = grayImage[i, j]
            bins[0,value] += 1
            
    maxVal = -1
    maxIndex = -1
    for i in range(maxMin):
        if bins[0, i] > maxVal:
            maxIndex = i
            maxVal = bins[0, i]
    return (maxIndex)

def show(img):
    plt.imshow(img, cmap = "gray")
    plt.show()
#looks for droplets and returns mean value of them if they're found, -1 if not
#based on detection of circles and comparing median background value to
#mean circle value.
def checkFluorescence(img):
    
    #convert image (16-bit) to 8-bit, for HoughCircles function
    normalized = np.zeros(img.shape, dtype = "uint8")
    cv2.normalize(img, normalized, 0, 255, cv2.NORM_MINMAX, dtype = 8)
    bimg = cv2.medianBlur(normalized, 5) #blur 8 bit
    blur16 = cv2.medianBlur(img, 5) #blur 16 bit

    #detect droplets    
                                #param1: sensitivity; param2: related to circumference
    droplets = cv2.HoughCircles(bimg, cv2.HOUGH_GRADIENT,dp = 1, minDist = 20, param1 = 20, param2=20, minRadius=10, maxRadius=40)
    if droplets is not None:
        droplets = np.round(droplets[0,:]).astype("int")
                 
        #overall average and other stuff
        overallMean = [0,0] #numerator, denominator
        mean16 = [0, 0]
        dropletMins = []

        for (x,y,r) in droplets:
            #calculate average luminosity
            #mask image to analyze single droplet data
            temp_img = np.zeros(bimg.shape, np.uint8)
            temp16 = np.zeros(blur16.shape, np.uint8)
            cv2.circle(temp_img , (x,y), r, (255,255,255), -1)
            cv2.circle(temp16 , (x,y), r, (255,255,255), -1)
            
            #get & adjust means
            meanValue = cv2.mean(bimg, mask = temp_img)
            meanValue16 = cv2.mean(blur16, mask = temp16)
            
            minValue, maxValue, minLoc, maxLoc = cv2.minMaxLoc(bimg, mask = temp_img)
            overallMean[0] += meanValue[0]
            overallMean[1] += 1
            
            mean16[0] += meanValue16[0]
            mean16[1] += 1
            
            dropletMins.append(minValue)
    else:
        return -1


    #background median & droplet mean
    maxMin = int(max(dropletMins))
    backgroundMedian = findMedian(bimg, maxMin)
    dropletMean = overallMean[0] / overallMean[1]
    dropletMean16 = mean16[0] / mean16[1]
    
    return(dropletMean, dropletMean16)
    
    return (dropletMean - backgroundMedian, dropletMean16 - backgroundMedian)

def theThing():
    #desired luminescence range [min, max]
    desired = [100, 150]
    
    #channels
    water = 0
    fluor = 1
    oil = 2
    channels = [water, fluor, oil]

    #starting voltages
    voltWater = 1.5
    voltFluor = 1
    voltOil = 2
    voltage = [voltWater, voltFluor, voltOil]
    
    #other starting values
    tooWeak = True
    increment = 0.2
    boundsVoltage = [0.5, 2.5]
    secsToWait = 30
    
    while(True):
        img = ts.pic() #take picture
        tup = checkFluorescence(img) #get mean luminescence
        fluorescence = tup[0] #mean 8 bit (0-255)
        fl16 = tup[1] #mean 16 bit (0-65,535)
        
        #display info. from image
        show(img)
        print(tm.ctime(tm.time()))
        print("Mean (8-bit): " + str(fluorescence))
        print("Mean (16-bit): " + str(fl16))
        print("tooWeak " + str(tooWeak))
        print("increment " + str(increment))
        print(voltage)
        
        #if in range
        if(desired[0] <= fluorescence and desired[1] >= fluorescence):
            print("In range")
            return True #exit function
        #else if too weak
        elif(fluorescence < desired[0]):
            if(not tooWeak): #i.e. it overcorrected
                increment = increment / 2
            
            #if there's already a lot of fluorescein, decrease water
            if((voltWater * 2) <= voltage[fluor]):
                voltage[water] -= increment
            #otherwise, increase fluorescein
            else:
                voltage[fluor] += increment
                
            tooWeak = True
        #if too strong
        else:
            if(tooWeak): #i.e. it overcorrected
                increment = increment / 2

            #if there's already a lot of water, decrease fluorescein
            if((voltFluor * 2) <= voltage[water]):
                voltage[fluor] -= increment
            else:
            #otherwise, increase water
                voltage[water] = voltage[water] + increment
            
            tooWeak = False
        
        #check voltage values; if beyond bounds, break loop
        if(voltage[water] < boundsVoltage[0] or voltage[fluor] < boundsVoltage[0]):
            print("Voltages to output too low")
            print(voltage)
            return False
        if(voltage[water] > boundsVoltage[1] or voltage[fluor] > boundsVoltage[1]):
            print("Voltages to output too high")
            print(voltage)
            return False
        
        #output voltage
        ac.outputVoltage(channels, voltage)
        
        #wait for effect
        tm.sleep(secsToWait)
    #end of while loop

if __name__ == "__main__":
    setupMicroscope()
    
    #successful = theThing()