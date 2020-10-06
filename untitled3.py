# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 18:06:10 2020

@author: Lia Thomson

Analyzes all the 8-bit images in a folder and saves the results.
OLD. Uses old droplet analysis function, and is not a flexible script.
"""

import sys
sys.path.append(r"C:\Program Files\Micro-Manager-2.0gamma")
sys.path.append(r"C:\Users\Nikon\Desktop\MCCDAQ\automation")

from glob import glob
import cv2
import ImageAnalysis as ia
import csv
from uManagerFuncs import saveImage
from os import mkdir

stuff = glob(r"C:\Users\Nikon\Desktop\Theo\200302b\imgs\*-8.png")

analyzedImages = glob(r"C:\Users\Nikon\Desktop\Theo\200302b\imgs\analysis")
if(len(analyzedImages) == 0):
    mkdir(r"C:\Users\Nikon\Desktop\Theo\200302b\imgs\analysis")

f = open(r"C:\Users\Nikon\Desktop\Theo\200302b\analysis.csv", "wb")
w = csv.writer(f)

w.writerow(["x", "y", "r", "mean", "image"])

for img in stuff:
    print(img)
    image = cv2.imread(img, cv2.COLOR_BGR2GRAY)
    
    droplets = ia.findDroplets(image, 1, 19, 19, 8, 40)
    
    if droplets is not None:
        means, medians, output = ia.dropletMean(image, droplets, show = False, write = True)
        imName = r"C:\Users\Nikon\Desktop\Theo\200302b\imgs\analysis" + "\\" + img.split("\\")[-1]
        saveImage(output, imName)
        
        if (image.dtype == "uint16"):
            medToUse = 1
        else:
            medToUse = 0
        
        for i in range(len(droplets)):
            temp = droplets[0, i].tolist()
            print(image.dtype),
            print(means[i][0]),
            print(medians)
            tempMean = means[i][0] - medians[medToUse]
            temp.append(tempMean)
            imageName = img.split("\\")[-1]
            temp.append(imageName)
            w.writerow(temp)
            
f.close()