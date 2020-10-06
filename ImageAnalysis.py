# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 17:38:30 2020

@author: Lia Thomson.

Contains a few functions for the image analysis of droplets.
OLD. PLEASE INSTEAD USE dropletAnalysisFuncs.py

"""
import cv2
import numpy as np

from PIL import ImageEnhance, Image

def increaseContrast(img, factor = 1.5):
    """Increase the contrast of an image and return the modified image."""
    if(img.dtype != "uint8"):
        raise TypeError("img is not of type uint8.")
        
    #please run on a blurred image or blur it afterwards
    pilImg = Image.fromarray(img)
    enhanced = ImageEnhance.Contrast(pilImg)
    pilFinal = enhanced.enhance(factor)
    arrayFinal = np.array(pilFinal)
    return arrayFinal

def normalize16(image):
    """Convert a 16-bit image into an 8-bit image."""
    if(image.dtype != "uint16"):
        raise TypeError("Image is not a 16-bit image.")
        
    normalized = np.zeros(image.shape, dtype = "uint8")
    cv2.normalize(image, normalized, 0, 255, cv2.NORM_MINMAX, dtype = 8)
    return normalized

def findDroplets(img, dp, p1, p2, minR, maxR):
    """Find droplets using openCV's HoughCircles, return an array of droplets.
    
    Arguments
    ---------
    img: image to analyze; 8-bit or 16-bit
    dp: parameter for HoughCircles (suggestion: 1)
    p1: param1 for HoughCircles; low is less sensitive, high is more strict (suggestion: 20)
    p2: param2 for HoughCircles; like param1
    minR: minimum radius of any droplet in pixels
    maxR: maximum radius of any droplet in pixels
    
    Other
    -----
    HoughCircles also has a minDist parameter: the minimum distance between the centers of two circles.
    This is set to 2x the minimum radius here.
    """
    if(len(img.shape) == 3):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  
    #turn 16-bit image into 8-bit image, increase contrast
    if(img.dtype == "uint16"):
        normalized = normalize16(img)
        contrastImg = increaseContrast(normalized)
    else:
        contrastImg = increaseContrast(img)
        
    #blur
    blurred = cv2.medianBlur(contrastImg, 5)
    
    minR = int(minR)
    maxR = int(maxR)
    minDist = minR * 2
    
    #detect droplets    
                                #param1 and param2: sensitivity
    droplets = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp = dp, minDist = minDist, param1=p1,
                                param2=p2, minRadius=minR, maxRadius = maxR)
    
    if(droplets is not None and len(droplets.shape) == 3): #why isn't this consistent?
        droplets = droplets[0]
    
    return droplets

def backgroundMedian(mask, image8, image16 = None):
    """Return median(s) of image(s) using mask.
    
    Arguments
    ---------
    mask: mask, where white is background to be examined
    image8: 8-bit image
    image16: 16-bit image, optional"""
    #check image types
    if(image8.dtype != "uint8"):
        raise TypeError("First image is not of type uint8.")
    elif(image16 is not None and image16.dtype != "uint16"):
        raise TypeError("Second image is not of type uint16.")
        
    #determine if want a 16-bit median
    if(image16 is None):
        bit16 = False
    else:
        bit16 = True
    
    median8, median16 = -1, -1
    
    #8-bit median
    bins8 = [0 for x in range(256)]
    
    for i in range(image8.shape[1]):
        for j in range(image8.shape[0]):
            if(mask[i,j]):
                bins8[image8[i, j]] += 1
    
    #find median
    maxIndex8 = 0
    for i in range(len(bins8)):
        if(bins8[i] > bins8[maxIndex8]):
            maxIndex8 = i
    median8 = maxIndex8
        
    if(bit16):
        #16-bit median
        bins16 = [0 for x in range(2**16)]
        
        for i in range(image16.shape[1]):
            for j in range(image16.shape[0]):
                if(mask[i,j]):
                    bins16[image16[i, j]] += 1
        
        maxIndex16 = 0
        for i in range(len(bins16)):
            if(bins16[i] > bins16[maxIndex16]):
                maxIndex16 = i
        median16 = maxIndex16
    
    return (median8, median16)

def dropletMean(img, droplets, show = True, write = False):
    """Find the mean value of each droplet, and return the means in an array.
    
    Arguments
    ---------
    img: image to analyze
    droplets: array of droplets from findDroplets()
    show: boolean to display droplets in a new window.
    """
    if droplets is None:
        return None
    
    #make it grayscale if it isn't already
    if(len(img.shape) == 3):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  
    
    #image mask
    bgmask = np.ones(img.shape, dtype = "uint8")
    
    if(img.dtype == "uint16"):
        bit8img = normalize16(img)
    else:
        bit8img = img

    #output image
    outputImg = None
    if(show or write):
        if(img.dtype == "uint16"):
            outputImg = bit8img.copy()
        else:
            outputImg = img.copy()
    
    #blur image
    bimg = cv2.medianBlur(img, 5)
    
    droplets = np.round(droplets).astype("int")
    #print(droplets.shape)
    #print(type(droplets))
          
    means = []
    
    #show droplets in output image; find the mean luminescence
    for (x,y,r) in droplets:
        #mask for droplet
        mask = np.zeros(img.shape, dtype = "uint8")
        cv2.circle(mask, (x, y), r, 255)
        
        #mask for image
        cv2.circle(bgmask, (x, y), r, 0)
        
        #draw circle & center on output image
        if(show or write):
            cv2.circle(outputImg,(x,y),r, 255 ,2)
            cv2.rectangle(outputImg, (x-2,y-2), (x+2,y+2), 255, -1)

        #get mean for image       
        mean = cv2.mean(bimg, mask = mask)
        mean = mean[0] #because it's grayscale
        means.append(mean)

    #get background median
    if(img.dtype == "uint16"):
        medians = backgroundMedian(bgmask, bit8img, img)
    else:
        medians = backgroundMedian(bgmask, bit8img)

    #show droplets
    if(show or write):
        for i in range(len(droplets)):
            centerX = droplets[i][0]
            centerY = droplets[i][1]
            radius = droplets[i][2]
            
            if(img.dtype == "uint8"):
                mean = round(means[i] - medians[0])
            else:
                mean = round(means[i] - medians[1])
                
            cv2.putText(outputImg, str(radius), (centerX-10, centerY-10), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,255,255))
            cv2.putText(outputImg, str(mean), (centerX-10, centerY+10), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,255,255))
            
    #add text to output image
    if(show or write):
        dropletNum = "Droplets: " + str(len(droplets))
       
        cv2.putText(outputImg, dropletNum, (5, 20), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255)) 
    
    if(show):
        cv2.imshow('max-output', outputImg)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    return (means, medians, outputImg) #fix this mess later
