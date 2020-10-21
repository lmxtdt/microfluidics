# -*- coding: utf-8 -*-
"""
@author: Lia Thomson

Contains multiple functions useful for using the Nikon Eclipse microscope.
Must be run in Python 2.7
"""

#import MMCore package
import sys
import os
os.chdir(r"C:\Program Files\Micro-Manager-2.0gamma")
sys.path.append(r"C:\Program Files\Micro-Manager-2.0gamma")
sys.path.append(r"C:\Users\Nikon\Desktop\MCCDAQ\automation")

import MMCorePy
import numpy as np
import matplotlib.pyplot as plt
import png #why not use cv2?
import cv2
from cv2 import normalize, NORM_MINMAX

import time as tm

def setup():
    """Create micromanager core, load devices 
    (SOLA, DIA, Zyla 4.2, Nikon TI Microscope, filters), return the core."""
    print("Creating core...")
    mmc = MMCorePy.CMMCore()
    print("Loading"),
    #load and initialize everything
    
    #shutter: SOLA
    print("SOLA,"),
    mmc.loadDevice("sola", "LumencorSpectra", "Spectra")
    mmc.loadDevice("COM6", "SerialManager", "COM6")
    mmc.setProperty("sola", "Port", "COM6")
    mmc.initializeDevice("COM6")
    mmc.initializeDevice("sola")
    mmc.waitForDevice("COM6")
    mmc.waitForDevice("sola")
    
    #shutter: DIA
    print("DIA,"),
    mmc.loadDevice("dia", "NI100X", "AnalogIO")
    mmc.setProperty("dia", "IOChannel", "Dev1/ao0")
    mmc.initializeDevice("dia")
    mmc.waitForDevice("dia")
    
    #camera
    print("camera,"),
    mmc.loadDevice("cam", "AndorSDK3", "Andor sCMOS Camera")
    mmc.initializeDevice("cam")
    mmc.setCameraDevice("cam")
    mmc.setProperty("cam", "Binning", "2x2") #binning
    mmc.waitForDevice("cam")
    
    #TI Microscope
    print("microscope,"),
    mmc.loadDevice("Nikon", "NikonTI", "TIScope")
    mmc.initializeDevice("Nikon")
    mmc.waitForDevice("Nikon")
    
    #TI Nosepiece
    print("lenses,"),
    mmc.loadDevice("lenses", "NikonTI", "TINosePiece")
    mmc.initializeDevice("lenses")
    mmc.waitForDevice("lenses")
    
    #Filter
    print("filters..."),
    mmc.loadDevice("filter", "NikonTI", "TIFilterBlock1")
    mmc.initializeDevice("filter")
    mmc.setProperty("filter", "Label", "3-FITC")
    mmc.waitForDevice("filter")
    
    #z
    print("z drive..."),
    mmc.loadDevice("z", "NikonTI", "TIZDrive")
    mmc.initializeDevice("z")
    mmc.waitForDevice("z")
    
    #xy
    print("stage..."),
    mmc.loadDevice("xy", "Prior", "XYStage")
    mmc.loadDevice("COM4", "SerialManager", "COM4")
    mmc.setProperty("xy", "Port", "COM4")
    mmc.initializeDevice("COM4")
    mmc.initializeDevice("xy")
    mmc.waitForDevice("COM4")
    mmc.waitForDevice("xy")
    mmc.setXYStageDevice("xy")

    mmc.setAutoShutter(False)
    
    print("Done.")
    return mmc

def pic(mmc, filterToUse = "3-FITC"):
    """Take a fluorescent picture using SOLA, return the image.
    
    Arguments
    ---------
    mmc: micromanager core
    filterToUse: filter (default: 3-FITC)
    """
    #check if current filter block is correct; change if not
    if(mmc.getProperty("filter", "Label") != filterToUse):
        mmc.setProperty("filter", "Label", filterToUse)
        mmc.waitForDevice("filter")

    #turn SOLA on
    mmc.setProperty("sola","State","1")
    mmc.setProperty("sola", "White_Enable", "1")
    mmc.waitForDevice("sola")

    mmc.snapImage()

    #turn SOLA off
    mmc.setProperty("sola","State","0")
    mmc.setProperty("sola", "White_Enable", "0")
    mmc.waitForDevice("sola")
    
    return(mmc.getImage())

def picDia(mmc):
    """Take a brightfield picture using DIA, return the image.
    
    Arguments
    ---------
    mmc: micromanager core
    """
    #check if current filter block is correct; change if not
    if(mmc.getProperty("filter", "Label") != "1------"):
        mmc.setProperty("filter", "Label", "1------")
        mmc.waitForDevice("filter")
    
    #take picture using DIA
    mmc.setProperty("dia", "Volts", "5")
    mmc.waitForDevice("dia")
    
    mmc.snapImage()
    
    mmc.setProperty("dia", "Volts", 0)
    mmc.waitForDevice("dia")
    
    return(mmc.getImage())

def show(img):
    """Show grayscale image as a plot."""
    plt.imshow(img, cmap = "gray")
    plt.show()

def live(m, mode):
    """Open live window, which can be closed by any key press."""
    if(mode not in m.getAllowedPropertyValues("filter", "Label") and mode != "dia"):
        validModes = "dia"
        for valid in m.getAllowedPropertyValues("filter", "Label"):
            validModes += ", " + valid
        raise Exception("mode is not valid. Valid modes are: " + validModes)
        
    cv2.namedWindow("Live")
    while(True):
        #get image
        if(mode == "dia"):
            img = picDia(m)
        else:
            img = pic(m, mode)
            
        #flip image
        img = np.flip(img)
        
        #show image
        cv2.imshow("Live", img)
        
        #wait for input
        if(cv2.waitKey(20) >= 0):
            break
        
    cv2.destroyAllWindows()

def saveImage(img, path, bit8 = True, bit16 = True):
    """Save image as 8-bit and 16-bit PNGs. Return True upon successful save, False otherwise.
    
    Arguments
    ---------
    img: the image to save
    path: path to save the images, including the name (e.g. r"C:\Users\Nikon\Desktop\imageName")
    bit8: boolean, indicates if it should save img as an 8-bit PNG (default: True)
    bit16: boolean, indicates if it should save img as an 16-bit PNG (default: True)
    """
    #check image type
    if(img.dtype == "uint8" and bit16):
        bit16 = False
        print("Image is 8-bit image, can't save as 16-bit.")
    elif(img.dtype != "uint16"):
        print("Image is not 8-bit image or 16-bit image, did not save.")
        return False
    
    #save 8-bit PNG
    if(bit8):
        name8 = path + "-8.png"
        
        if(img.dtype == "uint8"):
            with open(name8, "wb") as f:
                writer = png.Writer(width = img.shape[1],
                                    height = img.shape[0],
                                    greyscale = True,
                                    bitdepth = 8)
                writer.write(f, np.reshape(img, (-1, img.shape[1])))
        else:
            with open(name8, "wb") as f:
                normImg = np.zeros(img.shape, dtype = "uint8")
                normalize(img, normImg, 0, 255, NORM_MINMAX, dtype = 8)
                writer = png.Writer(width = normImg.shape[1],
                                    height = normImg.shape[0],
                                    greyscale = True,
                                    bitdepth = 8)
                writer.write(f, np.reshape(normImg, (-1, normImg.shape[1])))

    #save 16-bit PNG
    if(bit16):
        name16 = path + "-16.png"
        with open(name16, "wb") as f:
            writer = png.Writer(width = img.shape[1],
                                height = img.shape[0],
                                greyscale = True,
                                bitdepth = 16)
            writer.write(f, np.reshape(img, (-1, img.shape[1])))

    return True

def printProperties(mmc, device):
    """Print all of the properties of the device."""
    properties = mmc.getDevicePropertyNames(device)
    for prop in properties:
        print(prop + ": " + str(mmc.getProperty(device, prop)))
    return

def pixelSize(m):
    """Return the width of a pixel in micrometers."""
    #pixel size = camera pixel size (6.5 um) * binnning
    #           / magnification A * magnification B * C mount
    pixelCamera = 6.5 #micrometers
    
    lensMag = {"0" : 4, "1" : 10, "2" : 20, "3" : 40, "4" : 60, "5" : 100}
    magnification = lensMag[m.getProperty("lenses", "State")]
    binning = int(m.getProperty("cam", "Binning")[0])
    
    size = pixelCamera * binning / magnification
    
    return size

def saveConfig(m, path):
    """Save configuration of all devices onto a file specified by path."""    
    #get all devices loaded
    allDevices = m.getLoadedDevices()
    
    #open file
    fileName = path + ".txt"
    f = open(fileName, "w")
    
    f.write("Microscope configuration saved " + tm.ctime(tm.time()) + "\n\n")
    
    #add each line for each device
    for device in allDevices:
        #device name
        f.write(device + "\n")
        f.write("----------" + "\n")
        
        #device properties
        allProps = m.getDevicePropertyNames(device)
        for prop in allProps:
            f.write(prop + ": " + str(m.getProperty(device, prop)) + "\n")
        
        f.write("\n\n")
        
    #write pixel size
    pixSize = pixelSize(m)
    f.write("Pixel size: " + str(pixSize) + " micrometers per pixel" + "\n")
    
    #close file
    f.close()

    return

def close(mmc):
    """Unload devices from the core."""
    print("Unloading devices..."),
    mmc.unloadAllDevices()
    print("Done.")
    return

###############################################################################

"""
m.getXYPosition() returns x & y coord.s of the stage
m.setXYPosition(x pos., y pos.)
m.setRelativeXYPosition(+ x pos., + y pos.)
"""

#misc. info. on the devices & their properties; for reference
"""
Devices:
    DIA
        AnalogIO/NI 100X
    TIScope
        TISCope/NikonTI
    TINosePiece
        TINosePiece/NikonTI
    TILightPath
        TILightPath/NikonTI
    TIZDrive
        TIZDrive/NikonTI
    TIPFSOffset
        TIPFSOffset/NikonTI
    TIPFSStatus
        TIPFSStatus/NikonTI
    TIFilterBlock1
        Adapter/Module: TIFilterBlock1/NikonTI
    Zyla
        Adapter/Module: AndorsCMOS Camera/AndorSDK3
    Spectra
        Adapter/Module: Spectra/LumencorSpectra
    XYStage
        Adapter/Module: XYStage/Prior

Properties:
TIFilterBlock1
    Label:
        "1------"
        "2-DAPI" (something else)
        "3-FITC" (GFP)
        etc.

Spectra
    White_Enable:
        0 (off)
        1 (on)
    White_Level:
        0-100
    Name:
        Spectra
    State:
        0 (off)
        1 (on)
"""

#getAllowedPropertyValues