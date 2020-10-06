#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Lia Thomson

These functions are used to analyze an image for droplets, then store data
about both the image and its droplets, which can be written as output.

Imported by dropletAnalysisGUI, but can be used independently.
"""

import cv2 as cv
from matplotlib import pyplot as plt
import numpy as np
import os
from glob import glob
import csv

#change the working directory
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#################### CLASSES ####################

class Droplet:
    #represents a single droplet, with x, y position, r radius, and a mean
    def __init__(self, x, y, r, mean = -1):
        self.x = x
        self.y = y
        self.r = r
        self.mean = mean
        
    def __repr__(self):
        return "<Droplet ({x}, {y}, {r})>".format(x = self.x, y = self.y, r = self.r)
    
    def setMean(self, newMean):
        self.mean = newMean
        
    def getXstr(self):
        return str(self.x)
    
    def getYstr(self):
        return str(self.y)
    
    def getRstr(self):
        return str(self.r)
    
    def getMean(self):
        return self.mean

class Image:
    #represents a taken image. Contains a name, median, droplets, and steps, 
    #which are images of the process
    def __init__(self, name, droplets, median, steps):
        self.name = name
        self.median = median
        self.droplets = droplets
        self.steps = steps
                
        #make sure all images are in RGB format
        for key in self.steps:
            if(len(self.steps[key].shape) == 3):
                self.steps[key] = cv.cvtColor(self.steps[key], cv.COLOR_BGR2RGB)
            else:
                self.steps[key] = cv.cvtColor(self.steps[key], cv.COLOR_GRAY2RGB)
    
    def __repr__(self):
        return "<Image {}>".format(self.name)
    
    def getName(self):
        return self.name
    
    def getMedian(self):
        return self.median
    
    def getDroplets(self):
        return self.droplets
    
    def getSteps(self):
        return self.steps
    
    def getImg(self):
        return self.steps["final"]
            
class ImageCollection:
    #represents a group of Images (usually from a folder.) Contains a list of 
    #Images and the index of the "current" image. 
    def __init__(self):
        self.allImgs = []
        self.index = 0
        
    def __repr__(self):
        return "<ImageCollection of length {}>".format(self.getLength())

    def getLength(self):
        return len(self.allImgs)
    
    def getIndex(self):
        return self.index
    
    def current(self):
        if(self.getLength() > 0):
            return self.allImgs[self.index]
        else:
            return None
    
    def next(self):
        #change current image to the next one.
        if(self.getLength() > 0):
            self.index += 1
            if(self.index > self.getLength() - 1):
                self.index = 0
                
            return self.allImgs[self.index]
        else:
            return None
        
    def previous(self):
        #change current image to the previous one.
        if(self.getLength() > 0):
            self.index -= 1
            if(0 > self.index):
                self.index = self.getLength() - 1
                
            return self.allImgs[self.index]
        else:
            return None

    def add(self, newImg):
        self.allImgs.append(newImg)

    def get(self, i):
        return self.allImgs[i]
    
    def getFinal(self, i):
        return self.allImgs[i][1].getFinal()

    def writeData(self, path):
        fileName = "{}.csv".format(path)

        #FORMAT: droplet ID, r, mean adjusted, img name, img ID, x, y, mean unadjusted
        with open(fileName, mode = "w") as csvFile:
            writer = csv.writer((csvFile), dialect = "excel")
            
            #header
            csvHead = ["Droplet ID", "Radius", "Mean (adjusted)",
                        "Image Name", "Image ID", "X pos.", "Y pos.", "Mean (unadjusted)"]
            writer.writerow(csvHead)

            #each image
            for i in range(self.getLength()):
                img = self.get(i)

                droplets = img.getDroplets()

                for j in range(len(droplets)):
                    imgName = img.getName()
                    imgID = i

                    dropID = "I{imgID}-D{dropNum}".format(imgID = imgID, dropNum = j)

                    r = droplets[j].getRstr()
                    x = droplets[j].getXstr()
                    y = droplets[j].getYstr()

                    meanU = round(droplets[j].getMean(), 2)
                    meanA = meanU - img.getMedian()

                    writer.writerow([dropID, r, meanA,
                                    imgName, imgID, x, y, meanU])

#################### HELPER FUNCTIONS ####################

def show(img):
    #for debugging
    plt.imshow(img, cmap = "gray")

def threshold(img, thresh):
    #shortcut for thresholding an image
    ret, threshed = cv.threshold(img, thresh, 255, cv.THRESH_BINARY)
    return threshed

def black(refImg):
    #shortcut for a black uint8 image
    return np.zeros(refImg.shape, dtype = "uint8")

def normalize16(image):
    """Convert a 16-bit image into an 8-bit image."""
    if(image.dtype != "uint16"):
        raise TypeError("Image is not a 16-bit image.")
        
    normalized = np.zeros(image.shape, dtype = "uint8")
    cv.normalize(image, normalized, 0, 255, cv.NORM_MINMAX, dtype = 8)
    return normalized

def medianMasked(img, mask):
    if(len(img.shape) != 2):
        raise Exception("img is not 2-dimensional")
    elif(len(mask.shape) != 2):
        raise Exception("mask is not 2-dimensional")
    
    if(img.dtype == "uint8"):
        hist = cv.calcHist([img], [0], mask, [256], (0, 256))
    elif(img.dtype == "uint16"):
        hist = cv.calcHist([img], [0], mask, [2 ** 16], (0, 2 ** 16))
    else:
        raise TypeError("img is not of type uint8 or uint16")

    median = medianHist(hist)

    return median

def medianHist(hist):
    """Returns the median index of a histogram."""
    max = hist[1][0]
    maxIndex = 1
    for i in range(1, len(hist)):
        if(hist[i][0] > max):
            max = hist[i][0]
            maxIndex = i
    
    return maxIndex

def getThresh(img, blur = True):
    """Returns the threshold value for an image.
    
    PARAMETERS:
        img: 8-bit grayscale image, as a np array
        blur: whether to blur the image before calculating the histogram
    
    RETURNS:
        The threshold value to use.
    
    METHOD:
        First, blur the image
        Second, generate a histogram from the image
        Next, travel through the histogram starting a little after the median
        Then, the function searches for when the histogram increases again
        If there is no increase, it returns the index of (median + 2)
        
        This method is based off the assumption that the histogram will have
        at least two peaks. The largest peak is of dark background pixels.
        The next peak is of the lighter droplets. The value of where the 
        second peak starts can thus be used to separate droplets from their
        background.
    """
    
    #blur
    if(blur):
        blurred = cv.GaussianBlur(img, (5, 5), 1)
    else:
        blurred = img

    #get median
    hist = cv.calcHist(images = [blurred], 
                        channels = [0], 
                        mask = None, 
                        histSize = [256], 
                        ranges = (0, 256))
    median = medianHist(hist)
    
    #initialize values to traverse through the histogram
    #starting from the median + 4

    #i: index
    i = median + 4
    #retValue: threshold value to return
    retValue = median + 4
    #oldNum: the value of the histogram at the previous index
    oldNum = hist[i][0]
    
    i += 1
    
    #go through the histogram, finding when the frequency of a value goes up, not down
    while(i < 256):
        if(hist[i][0] > oldNum):
            retValue = i - 1
            break
        else:
            oldNum = hist[i][0]
            i += 1
    
    return retValue

def tooDark(img, circle):
    """Determines if a circle in a thresholded image is over 20% black.
    This is used to determine if a droplet is a false positive.
    """
    #unpack the circle
    x, y, r = circle
    
    r = int(r)
    x = int(x)
    y = int(y)
    
    #make mask
    mask = black(img)
    mask = cv.circle(mask, (x, y), r, 1, -1)
    
    #find pixels where the droplet should be, but the img has nothing
    different = ((mask == 1) & (img == 0))

    #calculate percentage of the circle that is black    
    white = np.sum(different)
    total = np.sum(mask)
    percentage = white / total
        
    return (percentage > 0.2) #Cut-off value is 20%; 10% is too low

def findOverlapping(main, circles):
    """Returns list of circles that overlap with main."""
    ret = []

    x1, y1, r1 = main

    for circle in circles:
        #unpack
        x2, y2, r2 = circle

        #calculate a^2 + b^2
        a2b2 = abs(x1 - x2) **2 + abs(y1 - y2) **2
        #calculate c^2 (min distance for them to not overlap)
        c2 = (r1 + r2) ** 2

        #add circle if the circles overlap
        if(c2 > a2b2):
            ret.append(circle)
    
    return ret

#################### ANALYZE FUNCTIONS ####################

def analyzeImage(path, outputFolder, imgType,
                 minR = 5, maxR = 30, dp = 1, p1 = 15, p2 = 15,
                 debug = False):
    """Analyzes an image for droplets.
    
    PARAMETERS:
        path: string path of an 8-bit or 16-bit grayscale image to analyze
        outputFolder: string path of the folder to write output to
        imgType: string type of images to write
        minR: integer minimum radius of a droplet, in pixels. 
            Passed to HoughCircles
        maxR: integer maximum radius of a droplet, in pixels.
            Passed to HoughCircles
        dp: float amount to scale an image in HoughCircles
        p1: param1 for HoughCircles. Lower values are more sensitive
        p2: param2 for HoughCircles. Lower values are more sensitive.
        debug: boolean, whether to write all debugging images
    """
    gray = cv.imread(path, cv.IMREAD_ANYDEPTH)
    #grayOrig is the same as gray if the image is 8-bit
    #if it is 16-bit, grayOrig is also 16-bit, while gray will be converted
    grayOrig = np.copy(gray)
    
    #If the image is 16-bit, convert gray to 8-bit
    if(gray.dtype == "uint16"):
        gray = normalize16(gray)
        
    circled = cv.cvtColor(gray, cv.COLOR_GRAY2BGR)
    
    #image names
    imgName = os.path.split(path)[1]
    print("\t{}".format(imgName))
    #reformat imgName so there are no periods
    imgName = imgName[:-4].replace("-", "_").replace(".", "-")

    #                   THRESHOLDING
    #Thresholding is meant to separate the droplets from the background of
    #the grayscale image. The method assumes that more pixels in the image
    #are of the dark background than of the bright droplets.

    #thresh: threshold value to use
    thresh = getThresh(gray)
    #threshed: thresholded image
    threshed = threshold(gray, thresh)
    #gray image using threshed as a mask to remove the background
    masked = cv.bitwise_and(gray, threshed)
    
    #assume the mask being too white means it's too noisy
    if(np.mean(threshed) > 40): #40 is arbitrarily; can adjust later
        i = 1
        
        #re-threshold and mask the image until it is not so light
        while(np.mean(threshed) > 40):
            thresh = getThresh(masked, False)
            threshed = threshold(gray, thresh)
            masked = cv.bitwise_and(gray, threshed)
            masked = cv.medianBlur(masked, 3)
            
            i += 1
        
        #adjust the output image to state that it has been re-filtered
        circled = cv.putText(circled, "re-filtered {} time(s)".format(i), (5, 20),
                             cv.FONT_HERSHEY_PLAIN, 1, (0, 0, 255))

    #blur the masked image extensively
    #median blur helps remove stray white pixels from the background
    blurMed1 = cv.medianBlur(masked, 3)
    #gaussian blur fills in droplets and makes them smoother
    blurGaus = cv.GaussianBlur(blurMed1, (3,3), 1)
    #some extra blurring (why?)
    blurMed2 = cv.medianBlur(blurGaus, 5)
    blurred = cv.GaussianBlur(blurMed2, (3,3), 1)
    
    blurredThreshed = threshold(blurred, 0)         #for tooDark()
    
    #                   FIND DROPLETS
    #This section uses the blurred image, which should have cleanly
    #separated the droplets from the background, and attempts to identify
    #droplets (circles)

    #use the HoughCircles function to detect circles
    minDist = 2 * minR + 1
    droplets = cv.HoughCircles(blurred, cv.HOUGH_GRADIENT,
                               dp = dp, minDist = minDist,
                               param1=p1, param2=p2,
                               minRadius=minR, maxRadius = maxR)

    #adjust the droplets to be in the desired format
    if(droplets is not None and len(droplets.shape) == 3):
        droplets = droplets[0]

    if(droplets is not None):
        droplets = droplets.round(0).astype(int).tolist()

    #initialize removed, which collects droplets deemed false positives
    removed = []

    #                   OVERLAPPING DROPLETS
    #Many overlapping detected droplets in the same region are usually
    #just part of one, larger droplet that was not detected. Thus, this
    #section first determines where droplets overlap. Then, it uses this
    #information to attempt to find a single larger droplet in regions
    #of overlap.
    
    #overlapping: image. Every droplet will be drawn on it very lightly
    #so lighter parts of overlapping are where multiple droplets overlap
    overlapping = black(gray)
    overlap2 = black(gray)
    if((droplets is not None) and (np.mean(threshed) < 150)):
        #search for droplets that are too dark (i.e. probably not droplets)
        for drop in droplets:
            if tooDark(blurredThreshed, drop):
                removed.append(drop)
            
        #remove dark droplets
        for drop in removed:
            droplets.remove(drop)
        
        #mark all of the detected circles on overlapping
        for (x, y, r) in droplets:
            #draw the droplet very lightly on a black image
            circleBase = cv.circle(black(gray), (x, y), r, 1, -1)
            #add the droplet to overlapping
            overlapping = overlapping + circleBase
            
        #editOverlap is a black and white image indicating regions in
        #the miage where at least two droplets overlap
        editOverlap = threshold(overlapping, 1)
            
        for (x, y, r) in droplets:
            #draw the droplet very lightly on a black image (again)
            circleBase = cv.circle(black(gray), (x, y), r, 1, -1)

            #get the overlap between this droplet and editOverlap
            bitAnd = np.bitwise_and(circleBase, editOverlap)

            #if there at least one pixel of overlap, draw this
            #droplet onto overlap2
            if np.max(bitAnd) >= 1:
                overlap2 = overlap2 + circleBase
                
    #clean overlap2 so all values are either black and white
    #no gray
    overlap2 = threshold(overlap2, 0)        
        
    #initialize some images
    overlapResult = black(gray)
    markers = black(gray)
    
    #deal with overlapping droplets
    if(np.max(overlapping) > 1):
        #to attempt to find the complete shape, where droplets overlap
        #use connectedComponents and watershed
        retConnected, markers = cv.connectedComponents(overlap2)
        markers = markers + 1
        #unknown is region that is in the blurred image, but not overlap2
        unknown = np.bitwise_xor(overlap2, threshold(blurred, 1))
        markers[unknown == 255] = 0
        #watershed
        markers = cv.watershed(cv.cvtColor(blurred, cv.COLOR_GRAY2BGR), markers)
        #make markers usable
        markers[markers == -1] = 0
        markers = np.uint8(markers)
        markers = threshold(markers, 1)

        #find contours
        im, contours, hierarchy = cv.findContours(markers,
                                                    cv.RETR_LIST,
                                                    cv.CHAIN_APPROX_SIMPLE)
        
        #go through each contour
        for contour in contours:
            #if the area of the contour isbig enough
            if(cv.contourArea(contour) > maxR * maxR * 0.5):
                #make a bounding rectangle from the contour
                x, y, w, h = cv.boundingRect(contour)
                
                #overlapMask: mask to use when trying to re-find
                #the big droplet. It is a rectangle slightly bigger
                #than the bounding rectangle of the contour.
                overlapMask = black(gray)
                overlapMask = cv.rectangle(overlapMask,
                                           (x - int(w / 4), y - int(h / 4)),
                                           (x + int(w * 1.25), y + int(h * 1.25)),
                                           255, -1)
                #also draw the boundaries of the overlapMask
                #on overlapping (to view later for debugging etc.)
                overlapping = cv.rectangle(overlapping,
                                           (x - int(w / 4), y - int(h / 4)),
                                           (x + int(w * 1.25), y + int(h * 1.25)),
                                           100, 1)
                
                #make a blockSize for adaptiveThreshold that is odd
                blockSize = int(max(w * 1.5, h * 1.5))
                if(blockSize % 2 != 1):
                    blockSize += 1
                
                #mask the contour
                maskedContour = cv.bitwise_and(overlapMask, markers)
                #add the masked contour to overlapResult
                overlapResult = cv.bitwise_or(overlapResult, maskedContour)
                
                #try to find droplets again, but with larger parameters
                newMinDist = blockSize
                newMinR = max(int(maxR * 0.5), minR)
                newMaxR = blockSize
                newP1 = int(p1 * 0.5)
                newP2 = int(p2 * 0.5)
                                    
                newDrops = cv.HoughCircles(maskedContour, cv.HOUGH_GRADIENT,
                                           dp = dp, minDist = newMinDist,
                                           param1 = newP1, param2 = newP2,
                                           minRadius = newMinR, maxRadius = newMaxR)
                
                #re-format the newly found droplets, if necessary
                if(newDrops is not None and len(newDrops.shape) == 3):
                    newDrops = newDrops[0]

                if(newDrops is not None and len(newDrops) == 1):
                    newDrops = newDrops.round(0).astype(int).tolist()

                    #add new droplets if they are valid
                    for drop in newDrops:
                        if(not tooDark(blurredThreshed, drop)):

                            xD, yD, rD = drop

                            #remove other droplets that overlap with this new one
                            dropsToRemove = findOverlapping(drop, droplets)
                            
                            for dropRemove in dropsToRemove:
                                droplets.remove(dropRemove)
                                removed.append(dropRemove)
                            
                            #add the new one
                            droplets.append(drop)

                            overlapResult = cv.circle(overlapResult, (xD, yD), rD, 100, 1)
        
    #if droplets were found, and are valid, write them to circled
    if((droplets is not None) and (np.mean(threshed) < 150)):
        for (x, y, r) in droplets:
            circled = cv.circle(circled, (x, y), r, (255,0,0))
            circled = cv.putText(circled, str(r), (int(x - r / 2), y), cv.FONT_HERSHEY_PLAIN, 1, (255, 0, 0))
    #otherwise, write that the droplets were not found, or weren't valid
    else:
        circled = cv.putText(circled, "No droplets or image is poor quality",
                             (0, gray.shape[1]),
                             cv.FONT_HERSHEY_PLAIN, 3, (255, 0, 0))
    
    #make the final image as a copy of circled
    final = np.copy(circled)

    #write the removed droplets to circled, in red
    if((removed is not None) and np.mean(threshed) < 150):
        for (x, y, r) in removed:
            circled = cv.circle(circled, (x, y), r, (0,0,255))
            circled = cv.putText(circled, str(r), (int(x - r / 2), y), cv.FONT_HERSHEY_PLAIN, 1, (0, 0, 255))

    #make Droplets (class instances) from the valid droplets
    dropletInstances = []
    if((droplets is not None) and (np.mean(threshed) < 150)):
        for (x, y, r) in droplets:
            mask = black(gray)
            cv.circle(mask, (x, y), r, 255)
            
            mean = cv.mean(grayOrig, mask = mask)[0]
            
            newDroplet = Droplet(x, y, r, mean)
            dropletInstances.append(newDroplet)


    #                   OUTPUT
    #Create an ImageCollection and Images to summarize the output.
    #In addition, write the output images.

    #get median of the background
    inverseMask = black(gray)
    inverseMask[blurredThreshed == 0] = 255
    imgMedian = medianMasked(grayOrig, inverseMask)

    if(debug):
        #folder for the output image
        subFolder = os.path.join(outputFolder, imgName)
        try:
            os.mkdir(subFolder)
        except FileExistsError:
            pass
        
        #all of the images
        allFiles = {"original": grayOrig,
                    "mask": threshed,
                    "blurred": blurred,
                    "overlapping": overlapping,
                    "markers": markers,
                    "overlapResult": overlapResult,
                    "allDroplets": circled,
                    "final": final
                    }

        newImage = Image("{}.{}".format(imgName, imgType), dropletInstances, imgMedian, allFiles)

        i = 0

        for fileName in allFiles.keys():
            cv.imwrite(os.path.join(subFolder, "{}-{}.png".format(i, fileName)), allFiles[fileName])
            i += 1

    else:
        allFiles = {"final": final}
        newImage = Image("{}.{}".format(imgName, imgType), dropletInstances, imgMedian, allFiles)
        
        cv.imwrite(os.path.join(outputFolder,  "{}.png".format(imgName)), final)

    return newImage

def analyzeFolder(inputFolder, outputFolder, imgType,
                  minR = 5, maxR = 30, dp = 1, p1 = 15, p2 = 15,
                  debug = False):
    """Analyzes all images in the inputFolder with the imgType (e.g. png, jpg),
    and writes it to the output folder.
    Assumes the background is darker than the droplets, 
    and that the majority of the image is background."""
    #find all images
    images = glob(os.path.join(inputFolder, "*.{}".format(imgType)))

    print("Analyzing {} .{} images in: {}".format(len(images),
                                                  imgType,
                                                  inputFolder))

    #create ImageCollection
    collection = ImageCollection()

    #go through each image
    for fn in images:
        newImage = analyzeImage(fn, outputFolder, imgType,
                                minR, maxR, dp, p1, p2, debug)
        collection.add(newImage)


    return collection

