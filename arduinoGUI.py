#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Lia Thomson

Arduino GUI: A basic GUI for manipulating an Arduino board. (Set up for an
Arduino UNO.) Easy to run. Just ensure PORT is set to the correct value.

Last updated: Sep. 25, 2020.
"""


import pyfirmata as f
import tkinter as tk

proceed = True

PORT = "COM7" #CHANGE AS APPROPRIATE

#initialize board
try:
    BOARD = f.Arduino(PORT)
except Exception:
    print("ERROR: Could not connect to Arduino at port: {}".format(PORT))
    proceed = False

####################           SETTINGS/CONSTANTS         ####################
MILLISECONDS_BETWEEN_UPDATES = 100

#PWM pin nunmbers (assuming this is an Arduino UNO)
PWM_PINS = [3,5,6,9,10,11]

#number of digital and analog pins
NUM_DIGITAL = 14
NUM_ANALOG = 6

#reference dicts for pin settings
COLORS = {"Don't use": "#999",
  "Input": "green",
  "Basic output": "blue",
  "PWM output": "purple"}

MAP = {"Don't use": False,
  "Input": "i",
  "Basic output": "o",
  "PWM output": "p"}

####################           TKINTER WINDOWS         ####################
class InitializeWindow(tk.Frame):
    #Initialization window, which gathers info. on how to intiialize the pins
    def __init__(self):
        #make the root
        root = tk.Tk()
        root.title("Set Up Arduino")

        #establish which digital ports can be used for PWM output
        digitalPWM = [False for i in range(NUM_DIGITAL)]
        for index in PWM_PINS:
            digitalPWM[index] = True
        
        #GUI header
        i = 0
        bigTitle = tk.Label(root, text = "SET UP ARDUINO", bg = "#ddd",
                            padx = 5, pady = 5,
                            font = ("Courier", 20))
        bigTitle.grid(row = i, columnspan = 3, sticky = "NEWS")
        
        i += 1
        
        #analog settings
        #analog header
        analogLabel = tk.Label(root, text = "ANALOG PINS", bg = "#ddd",
                               padx = 5, pady = 5)
        analogLabel.grid(row = i, columnspan = 3, sticky = "NEWS")
        
        i += 1
        
        analogVariables = []
        analogCanvases = []

        #create variables and display for each analog pin
        for j in range(NUM_ANALOG):
            #label of analog pin
            label = tk.Label(root, text = "Analog {}".format(j), font = "Courier")
            
            #option menu of modes for pin
            values = ["Don't use", "Input"] #analog pins only read
            useVar = tk.StringVar(root)
            useVar.set(values[0])
            analogVariables.append(useVar)
            use = tk.OptionMenu(root, useVar, *values)
            
            #canvas changes color depending on option selected
            canvas = tk.Canvas(root, width = 20, height = 10, bg = "#999")
            analogCanvases.append(canvas)
            
            #set command that is called when the variable changes
            commandRef = lambda j=j: lambda var, indx, mode: self.changeAnalog(j)
            commandRef = commandRef()
            useVar.trace_add("write", callback = commandRef)

            #grid
            label.grid(row = i, column = 0, sticky = "E")
            use.grid(row = i, column = 1, sticky = "NEWS")
            canvas.grid(row = i, column = 2, sticky = "NEWS")
            
            i += 1
        
        #digital settings
        #digital header
        digitalLabel = tk.Label(root, text = "DIGITAL PINS", bg = "#ddd",
                                padx = 5, pady = 5)
        digitalLabel.grid(row = i, columnspan = 3, sticky = "NEWS")
        
        i += 1
        
        digitalVariables = []
        digitalCanvases = []

        #create variables and display for each digital pin
        for j in range(NUM_DIGITAL):
            #determine if ~ required after pin number
            pwm = digitalPWM[j]
            pwmStr = " "
            if(pwm):
                pwmStr = "~"
        
            #label of digital pin
            label = tk.Label(root, text = "Digital {:>2}{}".format(j, pwmStr), font = "Courier")
            
            #option menu of modes for pin
            values = ["Don't use", "Input", "Basic output"]
            if(pwm):
                values.append("PWM output")
            
            useVar = tk.StringVar(root)
            useVar.set(values[0])
            digitalVariables.append(useVar)
            use = tk.OptionMenu(root, useVar, *values)
            
            #canvas changes color depending on option selected
            canvas = tk.Canvas(root, width = 20, height = 10, bg = "#999")
            digitalCanvases.append(canvas)

            #set command that is called when the variable changes
            commandRef = lambda j=j: lambda var, indx, mode: self.changeDigital(j)
            commandRef = commandRef()
            useVar.trace_add("write", callback = commandRef)
            
            #grid
            label.grid(row = i, column = 0, sticky = "E")
            use.grid(row = i, column = 1, sticky = "W")
            canvas.grid(row = i, column = 2, sticky = "NEWS")

            i += 1
            
        #submission label
        submitLabel = tk.Label(root, text = "SUBMIT", bg = "#ddd",
                               padx = 5, pady = 5)
        submitLabel.grid(row = i, columnspan = 3, sticky = "NEWS")
        
        i += 1
        
        #submit button
        submitButton = tk.Button(root, text = "Submit", command = self.submit)
        submitButton.grid(row = i, columnspan = 3, sticky = "NEWS")
                
        #assign important variables to self
        self.root = root
        self.analogVariables = analogVariables
        self.digitalVariables = digitalVariables
        self.digitalCanvases = digitalCanvases
        self.analogVariables = analogVariables
        self.analogCanvases = analogCanvases


    def changeDigital(self, i):
        """Change color of canvas for digital pins."""
        var = self.digitalVariables[i].get()
        canvas = self.digitalCanvases[i]
        
        canvas.config(bg = COLORS[var])
    
    def changeAnalog(self, i):
        """Change color of canvas for analog pins."""
        var = self.analogVariables[i].get()
        canvas = self.analogCanvases[i]
                
        canvas.config(bg = COLORS[var])
        
    def submit(self):
        """Submit the settings for initialization."""

        #gather modes of analog pins to use
        analogPins = []
        for i in range(len(self.analogVariables)):
            value = self.analogVariables[i].get()
            mapped = MAP[value]
            analogPins.append(mapped)
           
        #gather modes of digital pins to use
        digitalPins = []
        for i in range(len(self.digitalVariables)):
            value = self.digitalVariables[i].get()
            mapped = MAP[value]
            digitalPins.append(mapped)

        #destroy current window
        self.root.destroy()
        
        #create new window that is the main control GUI
        newWindow = ArduinoGUI(analogPins, digitalPins)
        newWindow.run()
                    
    def run(self):
        self.root.mainloop()

class ArduinoGUI(tk.Frame):
    #Main GUI window, controls output and reads input.

    def __init__(self, analogInfo, digitalInfo):
        print("CLOSE WINDOW TO STOP PROGRAM.")
        
        #create loading screen
        root = tk.Tk()
        root.title("Loading")

        label = tk.Label(root, text = "LOADING ARDUINO...",
                         padx = 10, pady = 10, font = ("Courier", 36))
        label.pack()
        
        #assign objects to self
        self.label = label
        self.root = root
        self.analogInfo = analogInfo
        self.digitalInfo = digitalInfo

    def run(self):
        """Run the window."""

        self.root.after(100, self.processInfo)
        self.root.mainloop()
        
    def processInfo(self):
        #loads board & pins
        
        #for convenience
        analogInfo = self.analogInfo
        digitalInfo = self.digitalInfo
        
        try:
            #arrays of analog and digital pins, with either None, or the pin object
            analog = []
            digital = []
                    
            #parse through everything and initialize
            #analog
            for j in range(len(analogInfo)):
                if analogInfo[j]:
                    analog.append(BOARD.get_pin("a:{}:{}".format(j, analogInfo[j])))
                else:
                    analog.append(None)
    
            #digital
            for j in range(len(digitalInfo)):
                if(digitalInfo[j]):
                    digital.append(BOARD.get_pin("d:{}:{}".format(j, digitalInfo[j])))
                else:
                    digital.append(None)
                    
            #destroy the "LOADING ARDUINO..." label
            self.label.destroy()
            
            #assign objects to self
            self.analog = analog
            self.digital = digital
            
            #populate window with control elements
            self.fillWindow()
            
        except Exception as e:
            print(e)
            
            #destroy the "LOADING ARDUINO..." label
            self.label.destroy()
            
            #replace label with the error message.
            self.label = tk.Label(self.root, text = "ERROR: {}".format(e),
                                  fg = "red", padx = 5, pady = 5)
            self.label.pack()
        
    def fillWindow(self):
        #fills the window with useful stuff
        root = self.root
        root.title("Arduino Control")
        
        i = 0
        
        #header
        header = tk.Label(root, text = "CONTROL PINS", font = ("COURIER", 20),
                          bg = "#999", padx = 5, pady = 5)
        header.grid(row = i, columnspan = 3, sticky = "NEWS")
        
        i += 1

        #spacer
        tk.Canvas(root, height = 10).grid(row = i, columnspan = 3, sticky = "NEWS")
        
        i += 1

        #analog pins header
        analogHeader = tk.Label(root, text = "ANALOG", bg = "#999")
        analogHeader.grid(row = i, columnspan = 3, sticky = "NEWS")
        
        i += 1

        #create, display, and store the variables for input for each pin
        analogVars = []
        self.analogVars = analogVars
        #go through the analogs
        for j in range(len(self.analogInfo)):
            if self.analogInfo[j]:
                #label
                label = tk.Label(root, text = " ANALOG {:>2}".format(j), font = "Courier")
                
                label.grid(row = i, column = 0, sticky = "NEWS")
                
                if(self.analogInfo[j] == "i"): #it wouldn't be anything else
                    #analog input
                    #variable
                    inputVar = tk.StringVar(root)
                    inputVar.set("      ")
                    analogVars.append(inputVar)

                    #display value
                    tk.Label(root, text = "Reading: ").grid(row = i, column = 1, sticky = "E")
                    display = tk.Label(root, textvariable = inputVar, font = "Courier")
                    display.grid(row = i, column = 2, sticky = "W")
                    
                    #color
                    label.config(fg = "green")
                else:
                    analogVars.append(None)
                
                i += 1
            else:
                analogVars.append(None)

        #section break
        tk.Canvas(root, height = 10).grid(row = i, columnspan = 3, sticky = "NEWS")
        
        i += 1

        #digital pins header
        digitalHeader = tk.Label(root, text = "DIGITAL", bg = "#999")
        digitalHeader.grid(row = i, columnspan = 3, sticky = "NEWS")
        
        i += 1

        #create, display, and store the variables for input or output for each pin
        digitalVars = []
        self.digitalVars = digitalVars
        #go through the digital pins
        for j in range(len(self.digitalInfo)):
            if(self.digitalInfo[j]):
                label = tk.Label(root, text = "DIGITAL {:>2}".format(j), font = "Courier")
                label.grid(row = i, column = 0, sticky = "E")
                
                #INPUT
                if(self.digitalInfo[j] == "i"):
                    #binary input
                    #variable
                    inputVar = tk.StringVar(root)
                    inputVar.set("      ")
                    digitalVars.append(inputVar)

                    #display text
                    tk.Label(root, text = "Reading: ").grid(row = i, column = 1, sticky = "E")
                    display = tk.Label(root, textvariable = inputVar, font = "Courier")
                    display.grid(row = i, column = 2, sticky = "W")
                    
                    #color
                    label.config(fg = "green")
                    
                #BASIC/BINARY OUTPUT
                elif(self.digitalInfo[j] == "o"):
                    #variable
                    outputVar = tk.IntVar(root)
                    outputVar.set(0)
                    digitalVars.append(outputVar)
                    
                    #checkbox
                    checkbox = tk.Checkbutton(root, text = "Toggle", onvalue = 1, offvalue = 0,
                                              variable = outputVar)
                    tk.Label(root, text = "Write 5V: ").grid(row = i, column = 1, sticky = "E")
                    checkbox.grid(row = i, column = 2, sticky = "W")

                    #color
                    label.config(fg = "blue")

                #PWM OUTPUT
                elif(self.digitalInfo[j] == "p"):
                    #variable
                    outputVar = tk.StringVar(root)
                    outputVar.set("0")
                    digitalVars.append(outputVar)
                    
                    #entry
                    validateVolts = root.register(self.validateVolts)
                    entry = tk.Entry(root, width = 3, validate = "key", validatecommand = (validateVolts, "%P"),
                                     textvariable = outputVar)
                    entry.grid(row = i, column = 1, sticky = "NEWS")
                    
                    #scale
                    scale = tk.Scale(root, from_ = 0, to_ = 5, resolution = 0.01, variable = outputVar,
                                     digits = 3, showvalue = False,
                                     orient = tk.HORIZONTAL, length = 200)
                    scale.grid(row = i, column = 2, sticky = "NEWS")
                    
                    #color
                    label.config(fg = "purple")
                    
                #ELSE (not possible)
                else:
                    digitalVars.append(None)
                    
                i += 1
            else:
                digitalVars.append(None)

        #section break
        tk.Canvas(root, height = 10).grid(row = i, columnspan = 3, sticky = "NEWS")
        
        i += 1

        #final information
        digitalHeader = tk.Label(root, text = "Close window to end program.", bg = "#999")
        digitalHeader.grid(row = i, columnspan = 3, sticky = "NEWS")
        
        i += 1

        #iterator for analog pins
        it = f.util.Iterator(BOARD)
        it.start()
    
        #begin updating the pins
        self.root.after(100, self.updatePins)

    def validateVolts(self, entry):
        """Check if a modification to an entry would result in a valid voltage."""

        try:
            if(float(entry) >= 0 and float(entry) <= 5):
                return True
            else:
                return False
        except ValueError:
            return False

    def updatePins(self):
        """Update pins, updates regularly (every MILLISECONDS_BETWEEN_UPDATES)"""
        
        #schedule function to run again
        self.root.after(MILLISECONDS_BETWEEN_UPDATES, self.updatePins)
        
        #go through analog pins
        for i in range(len(self.analogInfo)):
            if(self.analogInfo[i]):
                #read input
                if(self.analogInfo[i] == "i"):
                    newInput = self.analog[i].read()
                    if(newInput is not None):
                        asVolts = round(newInput * 5, 4)
                        asStr = "{:>6} V".format(asVolts)
                        self.analogVars[i].set(asStr)

        #go through digital pins
        for i in range(len(self.digitalInfo)):
            if(self.digitalInfo[i]):
                #read input
                if(self.digitalInfo[i] == "i"):
                    newInput = self.digital[i].read()
                    if(newInput is not None):
                        asVolts = round(newInput * 5, 4)
                        asStr = "{:>6} V".format(asVolts)
                        self.digitalVars[i].set(asStr)
                #binary output
                elif(self.digitalInfo[i] == "o"):
                    outValue = self.digitalVars[i].get()
                    self.digital[i].write(outValue)
                #pwm output
                elif(self.digitalInfo[i] == "p"):
                    outFive = float(self.digitalVars[i].get())
                    outValue = outFive / 5
                    self.digital[i].write(outValue)

#Run the initialization window if the board was found.
if(proceed):
    x = InitializeWindow()
    x.run()

    BOARD.exit()
