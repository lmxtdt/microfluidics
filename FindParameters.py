# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 16:28:55 2020

@author: Lia Thomson

Supervised learning to find optimal parameters for HoughCircles function.
OLD. A better droplet-recognition algorithm is in dropletAnalysisFuncs.py.
"""

import cv2
import numpy as np
import sys
sys.path.append(".")
import ImageAnalysis as ia

from glob import glob
from os import mkdir

import time as tm

sampleImages = [r"E:\Theo\200302\imgs\2-8.png", r"E:\Theo\200302b\imgs\29-8.png",
                r"E:\Theo\200302b\imgs\75-8.png", r"E:\Theo\200302b\imgs\3-8.png"]
sampleRanges = [(21,24),(8,8),(8,9),(25,27)]

saveGoodParams = []

imageList = []

for imgName in sampleImages:
    imageList.append(cv2.imread(imgName, cv2.COLOR_BGR2GRAY))

###############################################################################

def findLowestValues(table, minToReturn, index, tooLow, indices):
    """Recursive function called by mostAccurate."""
    #get the index of the minimum
    minIndex = 0
    for i in range(len(table)):
        #if the row's value is smaller than the current minIndex, but is bigger than tooLow
        if(table[minIndex][index] > table[i][index] and table[i][index] > tooLow):
            minIndex = i

    #go through and add indices for the rows where the value = min found
    for i in range(len(table)):
        if(table[minIndex][index] == table[i][index]):
            indices.append(i)

    #recurse if there aren't enough
    if(len(indices) < minToReturn):
        numLeftToGet = minToReturn - len(indices)
        currentMin = table[minIndex][index]
        return findLowestValues(table, numLeftToGet, index, currentMin, indices)
    #return
    else:
        return indices

def mostAccurate(table, minToReturn, index):
    """Examine table at a certain column and return the rows with at least the minToReturn-th smallest values.
    
    Arguments
    ---------
    table: 2-dimensional table to search
    minToReturn: integer; minimum number of rows to return; if multiple rows have the same value, return them all
    index: column index of the value to sort the rows by
    """
    indices = findLowestValues(table, minToReturn, index, -1, [])
    returnTable = []
    for i in indices:
        returnTable.append(table[i])
        
    return returnTable

def isBrighter(droplet, bgMedian, img):
    """Evaluate if the mean value of a droplet is greater than the median value of the background."""
    #find mean value of a droplet
    mask = np.zeros(img.shape, dtype = "uint8")
    cv2.circle(mask, (droplet[0], droplet[1]), droplet[2], 255)
    mean = cv2.mean(img, mask)
    
    #subtract the backgroundMedian
    difference = mean[0] - bgMedian
    
    return(difference > 5) #5 is an arbitrary value

def est2(dp, p1, p2, minR, maxR, img):
    """Identify droplets in an image; return the total number of droplets found and the number of false positives."""
    circles = ia.findDroplets(img, dp, p1, p2, minR, maxR)

    #if no droplets found
    if(circles is None):
        return (0, 0)
    
    #get mean of each droplet & median of background
    means, medians, output = ia.dropletMean(img, circles, False)
    #determine which median to use    
    if(img.dtype == "uint16"):
        med = 1
    else:
        med = 0
    
    #categorize droplets
    falsePositives = []
    correct = []
    
    for i in range(len(circles)):
        if(means[i] > medians[med]):
            correct.append(circles[i]) #technically unnecessary; maybe useful later
        else:
            falsePositives.append(circles[i])
    
    return((len(circles), len(falsePositives)))
        

def roughEstimate(images, desiredRange):
    #get a rough estimate
    #input: training images and classifications
    #output: parameters that can roughly find them
    #will likely be overly sensitive, i.e. too many false positives
    
    if(len(images) != len(desiredRange)):
        raise Exception("images and desiredRange not same length")
    
    variance = 2
    
    #starting values
    cDP = 4
    cP1 = 70
    cP2 = 70
    cMinR = 5   #manual entry for droplet size would probably be better
    cMaxR = 30  #could there be multiple sets of paramters for differently sized
    
    #amount to vary
    iDP = 1
    iP1 = 10
    iP2 = 10
    iMin = 5
    iMax = 5
    
    #absolute maximum radius allowed
    maxMaxR = 80
    
    #combine info. for all training images
    sumRanges = [0,0]

    for i in range(len(desiredRange)):
        sumRanges[0] += desiredRange[i][0]
        sumRanges[1] += desiredRange[i][1]
    
    #loop through 2x
    for i in range(2):
        #increments
        iDP = iDP / (i + 1)
        iP1 = iP1 / (i + 1)
        iP2 = iP2 / (i + 1)
        iMin = iMin / (i + 1)
        iMax = iMax / (i + 1)
                
        last = -1
        secondToLast = -1
        hadToBreak = False
        
        while(True):
            #test parameters on all images
            positiveResults = 0
            
            for j in range(len(images)):            
                results = est2(cDP, cP1, cP2, cMinR, cMaxR, images[j]) 
                positiveResults += results[0] - results[1]
        
            roughRange = (sumRanges[0]/variance, variance*sumRanges[1])
        
            print(positiveResults)
            print(roughRange)
            print((cDP, cP1, cP2, cMinR, cMaxR))

            #check if it's oscillating
            if(secondToLast == positiveResults):
                hadToBreak = True
                lastParameters = (cDP, cP1, cP2, cMinR, cMaxR)
            else:
                hadToBreak = False
                secondToLast = last
                last = positiveResults
        
            #if it's in the right range
            if(positiveResults >= roughRange[0] and positiveResults <= roughRange[1]):
                variance = variance * 0.75
                break #the while loop; proceed to more precise stuff
            elif(positiveResults < roughRange[1]):
                #decrease parameters
                if((cDP - iDP) > 1):
                    cDP -= iDP
                if(cP1 - iP1 > 1):
                    cP1 -= iP1
                if(cP2 - iP2 > 1):
                    cP2 -= iP2
                if(cMinR - iMin > 5):
                    cMinR -= iMin
                if(cMaxR - iMax > cMinR):
                    cMaxR -= iMax
            else: #increase parameters
                cDP += iDP
                cP1 += iP1
                cP2 += iP2
                if(cMaxR + iMax < maxMaxR):
                    cMaxR += iMax
                if(cMinR + iMin < cMaxR):
                    cMinR += iMin
        
            if(hadToBreak):
                currParameters = (cDP, cP1, cP2, cMinR, cMaxR)
                break

    if(hadToBreak):
        #ok
        lows = [-1, -1, -1, -1, -1]
        highs = [-1, -1, -1, -1, -1]
        for i in range(len(lastParameters)):
            lows[i] = min(lastParameters[i], currParameters[i])
            highs[i] = max(lastParameters[i], currParameters[i])

        params = (lows[0], lows[1], lows[2],
                  highs[0], highs[1], highs[2],
                  lows[3], highs[4])

    else:
        #find the lower parameters
        if((cDP - iDP) > 1):
            lowDP = cDP - iDP
        else:
            lowDP = cDP
        if(cP1 - iP1 > 1):
            lowP1 = cP1 - iP1
        else:
            lowP1 = cP1
        if(cP2 - iP2 > 1):
            lowP2 = cP2 - iP2
        else:
            lowP2 = cP2
        if(cMinR - iMin > 5):
            lowRadius = cMinR - iMin
        else:
            lowRadius = cMinR

        #find the upper parameters
        highDP = cDP + iDP
        highP1 = cP1 + iP1
        highP2 = cP2 + iP2

        if(cMaxR + iMax < maxMaxR):
            highRadius = cMaxR + iMax
        else:
            highRadius = cMaxR

        #i don't know if I like this format
        params = (lowDP, lowP1, lowP2,
                  highDP, highP1, highP2,
                  lowRadius, highRadius)
        
    return params

    #great now you have a rough estimate
    
def fineEstimate(startDP, startP1, startP2, endDP, endP1, endP2, minR, maxR, images, desiredRange):
    """Vary parameters of HoughCircles to analyze list of images, and assess accuracy. Return best parameters.
    
    Arguments
    ---------
    startDP: lowest value DP to evaluate (for HoughCircles)
    startP1: lowest value param1 to evaluate (for HoughCircles)
    startP2: lowest value param2 to evaluate (for HoughCircles)
    endDP: highest value DP to evaluate (for HoughCircles)
    endP1: highest value param1 to evaluate (for HoughCircles)
    endP2: highest value param2 to evaluate (for HoughCircles)
    minR: minimum radius (for HoughCircles)
    maxR: maximum radius (for HoughCircles)
    images: list of images
    desiredRange: list of tuples containing the range of accepted number of droplets for each image
                  e.g. [(4,4), (10,13)] indicates there are 4 droplets in image 1 and 10-13 in image 2.
    """
    numIterationsEach = 3 #except it will iterate through numIterationsEach + 1 times

    print("Note: this function takes a long time to run, since it will need to examine each image "
          + str((numIterationsEach + 1)**3) + " times." +"\nPlease be patient.")
    
    startTime = tm.time()

    #table = ["DP", "Param 1", "Param 2", "Total Circles", "False Positives"]
    table = []
    
    #values to iterate through
    dpValues = []
    p1Values = []
    p2Values = []

    dpStep = (endDP - startDP) / numIterationsEach
    for i in range(numIterationsEach):
        dpValues.append(startDP + (i * dpStep))
    dpValues.append(endDP)

    p1Step = (endP1 - startP1) / numIterationsEach
    for i in range(numIterationsEach):
        p1Values.append(startP1 + (i * p1Step))
    p1Values.append(endP1)

    p2Step = (endP2 - startP2) / numIterationsEach
    for i in range(numIterationsEach):
        p2Values.append(startP2 + (i * p2Step))
    p2Values.append(endP2)

    #go through every combination
    print("Going through all possible values:")
    for dp in dpValues:
        print(dp)
        for p1 in p1Values:
            print("\t" + str(p1))
            for p2 in p2Values:
                print("\t\t" + str(p2))
                totalFound = 0
                totalFalse = 0
                #run parameters on all sample images
                for img in images:
                    results = est2(dp, p1, p2, minR, maxR, img)
                    totalFound += results[0]
                    totalFalse += results[1]
                
                #add results to the table
                tableRow = [dp, p1, p2, minR, maxR, totalFound, totalFalse]
                table.append(tableRow)

    #get the range of desired number of droplets
    sumRange = [0, 0]
    for imgRange in desiredRange:
        sumRange[0] += imgRange[0]
        sumRange[1] += imgRange[1]

    #add the distance from the desired range to the table
    for row in table:
        detected = row[-2] - row[-1]
        if(detected >= sumRange[0] and detected <= sumRange[1]):
            distance = 0
        else:
            minusFirst = sumRange[0] - detected
            minusSecond = sumRange[1] - detected
            distance = min(minusFirst, minusSecond)
        row.append(abs(distance))
        
    #get the best sets of parameters from the table
    goodParameters = mostAccurate(table, 3, -1)

    #save params to a global variable
    global saveGoodParams
    saveGoodParams = goodParameters

    finishTime = tm.time()
    
    print("Start time: " + tm.ctime(startTime) + " Finish time: " + tm.ctime(finishTime))
    print("Total time taken: " + str(finishTime - startTime) + " seconds.")

    return goodParameters

def overallEstimate(images, desiredRange):
    """Run roughEstimate and fineEstimate together, return the set of best parameters."""
    rough = roughEstimate(images, desiredRange)
    fineSet = fineEstimate(rough[0], rough[1], rough[2], rough[3], rough[4], rough[5], rough[6], rough[7], images, desiredRange)
    return fineSet

def saveParameters(goodParameters, foldersPath, images):
    """Analyze images using given parameters and save to folder.
    
    Arguments
    ---------
    goodParameters: list of parameters to use
    foldersPath: path of folder to save everything in
    images: list of images to analyze
    """
    for i in range(len(goodParameters)):
        #make the folder
        folderName = foldersPath + "\\" + str(i)
        if(len(glob(folderName)) == 0):
            mkdir(folderName)
        
        #write the parameters to a txt file
        parametersName = folderName + "\\parameters.txt"
        f = open(parametersName, "w")
        dp = goodParameters[i][0]
        p1 = goodParameters[i][1]
        p2 = goodParameters[i][2]
        minR = int(goodParameters[i][3])
        maxR = int(goodParameters[i][4])
        f.write("DP: " + str(dp))
        f.write("\nP1: " + str(p1))
        f.write("\nP2: " + str(p2))
        f.write("\nminR: " + str(minR))
        f.write("\nmaxR: " + str(maxR))
        f.close()
        
        #write the images
        imgID = 0
        for img in images:
            drops = ia.findDroplets(img, dp, p1, p2, minR, maxR)
            
            if drops is not None:                
                means, medians, output = ia.dropletMean(img, drops, False, True)
            else:
                output = img.copy()
                
            imgName = folderName + "\\" + str(i) + "-" + str(imgID) + ".png"
            imgID += 1
            
            cv2.imwrite(imgName, output)
    
    return True