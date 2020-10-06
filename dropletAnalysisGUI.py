#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Lia Thomson

When run, starts a tkinter window that is used to analyze a folder of images
for droplets. The output is written both as images, to visually see which
droplets were found, and as a collected .csv file that contains the data about
all of the detected droplets in all of the images.

Needs to import dropletAnalysisFuncs.py
"""

import tkinter as tk
from tkinter import filedialog
import numpy as np

from dropletAnalysisFuncs import analyzeFolder

import os

from PIL import Image, ImageTk
import cv2 as cv

def raiseWindow(window):
    window.lift()
    window.attributes('-topmost', True)
    window.after_idle(window.attributes,'-topmost',False)
    
def selectDir():
    ret = filedialog.askdirectory(mustexist = True)
    return ret

class ImageViewerGUI:
    def __init__(self, imageCollection, master):
        root = tk.Toplevel(master)
        self.root = root

        root.title("Image Viewer")

        i = 0

        #header
        self.currNameLabel = tk.Label(root, text = "IMAGE INFORMATION", bg = "#bbb")
        self.currNameLabel.grid(row = i, columnspan = 3, sticky = "NEWS")

        i += 1
        
        #image and scroll bars
        self.imgCanvas = tk.Canvas(root, width = 512, height = 512)
        
        self.scrollX = tk.Scrollbar(root, orient = "horizontal", command = self.imgCanvas.xview,
                                    bg = "green")
        self.scrollY = tk.Scrollbar(root, orient = "vertical", command = self.imgCanvas.yview,
                                    bg = "green")
        self.imgCanvas.configure(xscrollcommand = self.scrollX.set)
        self.imgCanvas.configure(yscrollcommand = self.scrollY.set)
        
        self.scrollX.grid(row = i, column = 1, sticky = "NEWS")

        i += 1

        self.scrollY.grid(row = i, column = 0, sticky = "NEWS")

        self.imgCanvas.grid(row = i, column = 1, sticky = "NEWS")

        #temporary image
        PILimg = Image.fromarray(np.zeros((512, 512), dtype = "uint8"))
        self.img = PILimg
        self.photoImage = ImageTk.PhotoImage(image = PILimg, master = self.imgCanvas)
        self.currImage = self.imgCanvas.create_image(0, 0, anchor = "nw", image = self.photoImage)
        self.imgCanvas.config(scrollregion = self.imgCanvas.bbox(tk.ALL))
        self.zoomedImg = self.img

        i += 1

        #the info screen
        self.infoCanvas = tk.Canvas(root)
        
        j = 0

        self.currName = tk.StringVar(root)
        self.currName.set("Image: -")
        self.infoLabel = tk.Label(self.infoCanvas, textvariable = self.currName)
        self.infoLabel.grid(row = j, columnspan = 2, sticky = "NEWS")
        
        j += 1
        
        self.previousButton = tk.Button(self.infoCanvas, text = "Previous image", command = self.previousImage)
        self.nextButton = tk.Button(self.infoCanvas, text = "Next image", command = self.nextImage)
        self.previousButton.grid(row = j, column = 0, sticky = "W")
        self.nextButton.grid(row = j, column = 1, sticky = "E")
        
        j += 1
        
        self.numDroplets = tk.StringVar(root)
        self.numDroplets.set("Droplets found: -")
        self.numDropletsLabel = tk.Label(self.infoCanvas, textvariable = self.numDroplets)
        self.numDropletsLabel.grid(row = j, columnspan = 2, sticky = "NEWS")
        
        j += 1
        
        self.bgMedian = tk.StringVar(root)
        self.bgMedian.set("Background median value: ")
        self.bgMedianLabel = tk.Label(self.infoCanvas, textvariable = self.bgMedian)
        self.bgMedianLabel.grid(row = j, columnspan = 2, sticky = "NEWS")
        
        j += 1
        
        self.dropletsLabel = tk.Label(self.infoCanvas, text = "Droplets", pady = 10)
        self.dropletsLabel.grid(row = j,  columnspan = 2, sticky = "NEWS")

        j += 1
        #the scrolly table
        
        self.dropletsFrame = tk.Frame(self.infoCanvas, bd = 1)#, width = 300)
        self.dropletsFrame.grid(row = j, columnspan = 2, sticky = "NEWS")
        
        self.dropletsList = tk.Listbox(self.dropletsFrame,
                                       selectmode = tk.SINGLE,
                                       width = 43,
                                       height = 20,
                                       font = ("Courier", 12, "normal"))
        self.dropletsList.insert(0, " {: ^8} | {: ^8} | {: ^8} | {: ^9}".format(
            "X pos.",
            "Y pos.",
            "Radius",
            "Mean-BG"
            ))
        self.dropletsList.insert(1, "-"*42)
        self.dropletsList.bind("<<ListboxSelect>>", self.highlightDroplet)

        self.dropletsList.grid(row = 0, column = 0, sticky = "NEWS")
        
        self.dropScroll = tk.Scrollbar(self.dropletsFrame, orient = "vertical")
        self.dropScroll.grid(row = 0, column = 1, sticky = "NEWS")
        
        self.dropletsList.config(yscrollcommand = self.dropScroll.set)
                
        j += 1

        #select the image I suppose
        self.imgNameLabel = tk.Label(self.infoCanvas, text = "Sub-Image")
        self.imgNameLabel.grid(row = j, columnspan = 2, sticky = "NEWS")
        
        j += 1
        
        self.imgNameVar = tk.StringVar(root)
        stepDict = imageCollection.current().getSteps()
        self.imgNameList = list(stepDict.keys())
        self.imgNameVar.set("final")

        self.imageDropdown = tk.OptionMenu(self.infoCanvas, self.imgNameVar, *self.imgNameList,
                                           command = self.changeImage)
        self.imageDropdown.grid(row = j, columnspan = 2, sticky = "NEWS")
        
        j += 1



        #zoom zoom
        self.zoomCanvas = tk.Canvas(self.infoCanvas)
        self.zoomCanvas.grid(row = j, columnspan = 2, sticky = "NEWS")
        
        k = 0
        self.zoomTitle = tk.Label(self.zoomCanvas, text = "Zoom Level")
        self.zoomTitle.grid(row = k, columnspan = 5, sticky = "NEWS")
        
        k += 1
        self.zoomVariable = tk.DoubleVar(self.root)
        self.zoomVariable.set(1)
        
        
        self.zoom50 = tk.Radiobutton(self.zoomCanvas, text = "50%", variable = self.zoomVariable,
                                     value = 0.5, command = self.changeZoom)
        self.zoom75 = tk.Radiobutton(self.zoomCanvas, text = "75%", variable = self.zoomVariable,
                                     value = 0.75, command = self.changeZoom)
        self.zoom100 = tk.Radiobutton(self.zoomCanvas, text = "100%", variable = self.zoomVariable,
                                      value = 1, command = self.changeZoom)
        self.zoom150 = tk.Radiobutton(self.zoomCanvas, text = "150%", variable = self.zoomVariable,
                                      value = 1.5, command = self.changeZoom)
        self.zoom200 = tk.Radiobutton(self.zoomCanvas, text = "200%", variable = self.zoomVariable,
                                      value = 2, command =  self.changeZoom)
        
        self.zoom50.grid(row = k, column = 0, sticky = "NEWS")
        self.zoom75.grid(row = k, column = 1, sticky = "NEWS")
        self.zoom100.grid(row = k, column = 2, sticky = "NEWS")
        self.zoom150.grid(row = k, column = 3, sticky = "NEWS")
        self.zoom200.grid(row = k, column = 4, sticky = "NEWS")
        
        j += 1
        
        
        self.infoCanvas.grid(row = 1, column = 2, rowspan = 2, sticky = "N")
        
        self.imageCollection = imageCollection

        self.viewImage(self.imageCollection.current())
        

    def setTitle(self, newTitle):
        self.currName.set(newTitle)

    def updateDroplets(self, droplets):
        self.dropletsList.delete(2, tk.END)
        
        i = 2
        
        #header row
        
        i += 1
        for d in droplets:
            self.dropletsList.insert(i, " {: <8} | {: <8} | {: <8} | {: <9}".format(
                d.getXstr(),
                d.getYstr(),
                d.getRstr(),
                str(round(d.getMean() - self.imageCollection.current().getMedian(), 2))
                ))

            i += 1

    def highlightDroplet(self, evt):
        indexes = self.dropletsList.curselection()
        
        #clear it first
        self.changeImage(self.imgNameVar.get())
        
        if(len(indexes) > 0):
            index = indexes[0]
        
            if(index >= 2):
                line = self.dropletsList.get(index).split("|")
                x = int(line[0].strip())
                y = int(line[1].strip())
                r = int(line[2].strip())
                
                overlayImage = np.zeros(self.imageCollection.current().getImg().shape, dtype = "uint8")
                overlayImage = cv.cvtColor(overlayImage, cv.COLOR_RGB2RGBA)
    
                overlayImage[:,:,2] = 16
                overlayImage[:,:,3] = 200
    
                overlayImage = cv.circle(overlayImage, (x, y), r, (0,0,0,0), -1)
                overlayImage = cv.circle(overlayImage, (x, y), r, (32,128,32,255), 1)
                
                self.overlayImg = Image.fromarray(overlayImage)
                self.img.paste(self.overlayImg, mask = self.overlayImg)
                    
                self.changeZoom()

    def changeImage(self, imgName):
        image = self.imageCollection.current().getSteps()[imgName]
        self.img = Image.fromarray(image)
        
        self.changeZoom()

    def changeZoom(self):
        newZoom = self.zoomVariable.get()
        
        if(newZoom == 1):
            newImg = self.img
        else:
            newImg = self.img.resize((int(self.img.width * newZoom), int(self.img.height * newZoom)))
            
        self.zoomedImg = newImg
        
        self.photoImage = ImageTk.PhotoImage(self.zoomedImg, master = self.imgCanvas)
        self.imgCanvas.itemconfig(self.currImage, image = self.photoImage)
        self.imgCanvas.config(scrollregion = self.imgCanvas.bbox(tk.ALL))
        
    def nextImage(self):
        self.viewImage(self.imageCollection.next())
    
    def previousImage(self):
        self.viewImage(self.imageCollection.previous())

    def indexOfImage(self):
        return "{} / {}".format(self.imageCollection.getIndex() + 1, self.imageCollection.getLength())

    def viewImage(self, image):
        #set the name
        self.currName.set("Image: {} ({})".format(image.getName(), self.indexOfImage()))
        self.numDroplets.set("Droplets: {}".format(len(image.getDroplets())))
    
        self.bgMedian.set("Background median: {}".format(image.getMedian()))
        
        self.img = Image.fromarray(image.getImg())
        
        self.changeImage(self.imgNameVar.get())
        
        self.updateDroplets(image.getDroplets())
        
    def run(self):
        self.root.mainloop()

class ImageAnalysisGUI:
    def __init__(self):
        root = tk.Tk()
        self.root = root
        
        root.title("Image Analysis")
        
        i = 0

        topTitle = tk.Label(root, text = "Analyze 8-bit images for droplets.", bg = "#bbb")
        topTitle.grid(row = i, columnspan = 2, sticky = "NEWS")

        i += 1

        self.buttonInput = tk.Button(root, text = "Select folder with source images", command = self.setInputFolder)
        self.buttonInput.grid(row = i, column = 0, sticky = "NEWS")
                
        i += 1

        self.inputFolderText = tk.StringVar(root)
        self.inputFolderText.set("No input folder")
        self.outputFolderText = tk.StringVar(root)
        self.outputFolderText.set("No output folder")
        
        self.inputCanvas = tk.Canvas(root)
        inputEntry = tk.Entry(self.inputCanvas, textvariable = self.inputFolderText, 
                         bg = "white", fg = "black", state = "readonly", 
                         width = 30)
        inputScroll = tk.Scrollbar(self.inputCanvas, orient = "horizontal", command = inputEntry.xview)        
        inputEntry.configure(xscrollcommand = inputScroll.set)

        inputEntry.pack(expand = 1)
        inputScroll.pack(fill = tk.X)
        self.inputCanvas.grid(row = i, column = 0, padx = 5, pady = 5)

        i += 1

        self.buttonOutput = tk.Button(root, text = "Select output folder", command = self.setOutputFolder)
        self.buttonOutput.grid(row = i, column = 0, sticky = "NEWS")

        i += 1

        self.outputCanvas = tk.Canvas(root)
        outputEntry = tk.Entry(self.outputCanvas, textvariable = self.outputFolderText, 
                         bg = "white", fg = "black", state = "readonly", 
                         width = 30)
        outputScroll = tk.Scrollbar(self.outputCanvas, orient = "horizontal", command = outputEntry.xview)        
        outputEntry.configure(xscrollcommand = outputScroll.set)

        outputEntry.pack(expand = 1)
        outputScroll.pack(fill = tk.X)
        self.outputCanvas.grid(row = i, column = 0, padx = 10, pady = 5)

        i += 1   

        #SETTINGS

        validateFloat = root.register(self.callbackFloat)
        validateInt = root.register(self.callbackInt)
        
        settingsLabel = tk.Label(root, text = "Settings", bg = "#bbb")
        settingsLabel.grid(row = i, column = 0, columnspan = 2, sticky = "NEWS")
        
        i += 1

        settingsCanvas = tk.Canvas(root)
        self.settingsCanvas = settingsCanvas
        
        self.debugVariable = tk.IntVar(root)
        self.debugVariable.set(1)
        self.debug = tk.Checkbutton(settingsCanvas, text = "Debug", variable = self.debugVariable)
        self.debug.grid(row = 0, column = 0, sticky = "W", padx = 5, pady = 5, columnspan = 2)
        
        self.imgTypeLabel = tk.Label(settingsCanvas, text = "Image type")
        self.imgTypeVar = tk.StringVar(root)
        imgTypeValues = ["png", "jpg", "jpeg", "tif"]
        self.imgTypeVar.set(imgTypeValues[0])
        self.imgType = tk.OptionMenu(settingsCanvas, self.imgTypeVar, *imgTypeValues)
        self.imgTypeLabel.grid(row = 0, column = 2, sticky = "E", padx = 5)
        self.imgType.grid(row = 0, column = 3, sticky = "W", padx = 5)

        self.dbLabel = tk.Label(settingsCanvas, text = "db (~ 1)")
        self.db = tk.Entry(settingsCanvas, width = 4, validate = "key", validatecommand = (validateFloat, "%P"))
        self.db.insert(tk.INSERT, "1")
        self.dbLabel.grid(row = 1, column = 0, sticky = "E", padx = 5)
        self.db.grid(row = 1, column = 1, sticky = "W", padx = 5)
        
        self.p1Label = tk.Label(settingsCanvas, text = "param1")
        self.p1 = tk.Entry(settingsCanvas, width = 4, validate = "key", validatecommand = (validateFloat, "%P"))
        self.p1.insert(tk.INSERT, "15")
        self.p1Label.grid(row = 2, column = 0, sticky = "E", padx = 5)
        self.p1.grid(row = 2, column = 1, sticky = "W", padx = 5)
        
        self.p2Label = tk.Label(settingsCanvas, text = "param2")
        self.p2 = tk.Entry(settingsCanvas, width = 4, validate = "key", validatecommand = (validateFloat, "%P"))
        self.p2.insert(tk.INSERT, "15")
        self.p2Label.grid(row = 3, column = 0, sticky = "E", padx = 5)
        self.p2.grid(row = 3, column = 1, sticky = "W", padx = 5)
        
        self.minRLabel = tk.Label(settingsCanvas, text = "min radius")
        self.minR = tk.Entry(settingsCanvas, width = 4, validate = "key", validatecommand = (validateInt, "%P"))
        self.minR.insert(tk.INSERT, "5")
        self.minRLabel.grid(row = 1, column = 2, sticky = "E", padx = 5)
        self.minR.grid(row = 1, column = 3, sticky = "W", padx = 5)

        self.maxRLabel = tk.Label(settingsCanvas, text = "max radius")
        self.maxR = tk.Entry(settingsCanvas, width = 4, validate = "key", validatecommand = (validateInt, "%P"))
        self.maxR.insert(tk.INSERT, "30")
        self.maxRLabel.grid(row = 2, column = 2, sticky = "E", padx = 5)
        self.maxR.grid(row = 2, column = 3, sticky = "W", padx = 5)

        self.settingsCanvas.grid(row = i, columnspan = 2, padx = 10, pady = 5, sticky = "NEWS")
        
        #submit and related text

        i += 1
        
        buttonSubmit = tk.Button(root, text = "Submit", command = self.submit)
        self.buttonSubmit = buttonSubmit
        buttonSubmit.grid(row = i)

        i += 1

        self.errorText = tk.StringVar(root)
        self.errorTextLabel = tk.Label(root, textvariable = self.errorText, fg = "red")
        self.errorTextLabel.grid(row = i)

        i += 1

        self.outputText = tk.StringVar(root)
        self.outputTextLabel = tk.Label(root, textvariable = self.outputText)
        self.outputTextLabel.grid(row = i)
        
        i += 1
        

    def setInputFolder(self):
        selected = selectDir()
        if(selected != ""):
            self.inputFolderText.set(selected)
    
    def setOutputFolder(self):
        selected = selectDir()
        if(selected != ""):
            self.outputFolderText.set(selected)

    def callbackFloat(self, entry):
        try:
            if(float(entry) > 0):
                return True
            else:
                return False
        except ValueError:
            return False

    def callbackInt(self, entry):
        try:
            asFloat = float(entry)
            if(asFloat == int(asFloat)):
                if(asFloat > 0):
                    return True

            return False
        except ValueError:
            return False
    
    def errorMsg(self, msg):
        msg = str(msg)

        self.errorText.set(msg)

    def outputMsg(self, msg):
        msg = str(msg)

        self.outputText.set(msg)

    def submit(self):
        p = {}

        canProceed = True

        #type validation & get values
        try:
            p["debug"] = bool(self.debugVariable.get())
            p["imgType"] = self.imgTypeVar.get()
            p["inputDir"] = self.inputFolderText.get()
            p["outputDir"] = self.outputFolderText.get()
            p["dp"] = float(self.db.get())
            p["p1"] = float(self.p1.get())
            p["p2"] = float(self.p2.get())
            p["minR"] = int(self.minR.get())
            p["maxR"] = int(self.maxR.get())
        except ValueError:
            canProceed = False
            self.errorMsg("ERROR: inputs are bad")

        #other validdation
        try:
            #all numbers are positive
            for key in p:
                if(type(p[key]) == float):
                    if(p[key] <= 0):
                        raise Exception("{} value must be positive.".format(key))

            #input and output directories are valid
            if(p["inputDir"] == "" or p["inputDir"] == "No input folder"):
                raise Exception("Must select an input folder.")
            else:
                if(not os.path.exists(p["inputDir"])):
                    raise Exception("Input folder does not exist.")
            if(p["outputDir"] == "" or p["outputDir"] == "No output folder"):
                raise Exception("Must select an output folder.")
            else:
                if(not os.path.exists(p["outputDir"])):
                    raise Exception("Input folder does not exist.")

            if(p["inputDir"] == p["outputDir"]):
                raise Exception("Input and output folders must be different.")
        except Exception as e:
            canProceed = False
            self.errorMsg(e)

        if(canProceed):
            #try:
            collection = analyzeFolder(p["inputDir"], p["outputDir"], p["imgType"],
                          p["minR"], p["maxR"], p["dp"],
                          p["p1"], p["p2"],
                          p["debug"])

            csvName = os.path.join(p["outputDir"], "dropletData")

            collection.writeData(csvName)

            self.outputMsg("Done.")
            
            if(collection.getLength() > 1):
                imageViewer = ImageViewerGUI(collection, self.root)
                imageViewer.run()

           # except Exception as e:
                #self.errorMsg(e)

        
    def run(self):
        raiseWindow(self.root)
        self.root.mainloop()

x = ImageAnalysisGUI()
x.run()
