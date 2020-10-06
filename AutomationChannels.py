
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 30 15:56:50 2020

@author: Lia Thomson

Creates droplets with varying voltages of the oil/water/fluorescence ratios.
Has not been updated in months, but should still work.
"""


from __future__ import absolute_import, division, print_function

import sys

sys.path.append(r"C:\Users\Nikon\Desktop\MCCDAQ")


#from builtins import *  # @UnusedWildImport
from mcculw import ul
from mcculw.ul import ULError
from mcculw.enums import InterfaceType, TempScale

from examples.console import util
from examples.props.ao import AnalogOutputProps
#import ctypes
from examples.props.ai import AnalogInputProps

import time as tm

import numpy as np
import csv
#import matplotlib.pyplot as plt

use_device_detection = True

################################### SETTINGS ##################################

channelsToRead = [] #numbers of the channels to read
channelsOut = [0, 1, 2] #numbers of the channels that output voltage

numStages = 3 #number of different voltage arrangements to do
itPerStage = 1 #number of times loop through each stage

startingVoltages = [0,0,0]
amountsToIncrease = [0,0,0]

zeroVoltageAtEnd = False #if false, voltages will stay at settings of last stage
writeToCSV = False

############################### END OF SETTINGS ###############################

def incrementVoltage(voltageArray, starting, increase):
    if(len(voltageArray[0]) != len(starting) or len(starting) != len(increase)):
        print("voltage arrays must be of same length.")
        return False #this probably does not matter
        
    #fill in starting voltages
    for i in range(len(voltageArray)):
        voltage[0,i] = startingVoltages[i]
    #increase by increment
    for j in range(numStages - 1): #go through each row
        for k in range(len(voltageArray)): #go through each column
            voltageArray[j + 1, k] = voltageArray[j, k] + increase[k]
    
    return True

#fill array voltage based on increment
voltage = np.zeros((numStages, len(channelsOut))) #array of voltages:
            #each row is one stage, each column is a channel    

incrementVoltage(voltage, startingVoltages, amountsToIncrease)

########## Fill in array "voltage" here if not using incrementVoltage #########

#function that prints out the settings & checks if they're desired
#mostly print statements
def checkSettings(read, out, stages, iterations, zero, csv, voltage):
    print("---------- Settings ----------")
    print("There are " + str(stages) + " stages, with " + str(iterations) +
          " iterations each (~" + str(iterations) + "-" +str(iterations * 3) +
          " seconds each stage).")
    if(zero):
        print("Voltages WILL be zeroed after the program runs.")
    else:
        print("Voltages will NOT be zeroes after the program runs.")
    if(csv):
        print("The results WILL be stored to a CSV file.")
    else:
        print("The results will NOT be stored to a CSV file.")
    
    print("\nWill read channels: " + str(read))
    print("Will output to channels: " + str(out))
    print("Voltages: " + str(voltage))
    
    print("Proceed? (y/n)", end = " ")
    proceed = input()
    
    if(proceed == "y" or proceed == "yes" or proceed == "Y"):
        print("Proceeding...")
        return True
    else:
        print("Edit settings and re-run.")
        return False

#input function
def readVoltage(channelNum):
    board_num = 2

    if use_device_detection:
        ul.ignore_instacal()
        if not util.config_first_detected_device(board_num):
            print("Could not find device.")
            return

    channel = channelNum

    ai_props = AnalogInputProps(board_num)
    if ai_props.num_ai_chans < 1:
        util.print_unsupported_example(board_num)
        return

    ai_range = ai_props.available_ranges[0]

    try:
        # Get a value from the device
        if ai_props.resolution <= 16:
            # Use the a_in method for devices with a resolution <= 16
            value = ul.a_in(board_num, channel, ai_range)
            # Convert the raw value to engineering units
            eng_units_value = ul.to_eng_units(board_num, ai_range, value)
        else:
            # Use the a_in_32 method for devices with a resolution > 16
            # (optional parameter omitted)
            value = ul.a_in_32(board_num, channel, ai_range)

            # Convert the raw value to engineering units
            eng_units_value = ul.to_eng_units_32(board_num, ai_range, value)

        # Display the raw value
#        print("Raw Value: " + str(value))
        # Display the engineering value
#        print("Engineering Value: " + '{:.3f}'.format(eng_units_value))
        return(eng_units_value)
    except ULError as e:
        util.print_ul_error(e)
    finally:
        if use_device_detection:
            ul.release_daq_device(board_num)

#output function
def outputVoltage(channels, volts):
    if(len(channels) != len(volts)):
        raise Exception("Channels and voltage are different lengths.")
    
    #find the board
    board_num = 0

    ul.release_daq_device(board_num)
    if use_device_detection:
        ul.ignore_instacal()
        devices = ul.get_daq_device_inventory(InterfaceType.ANY)
        # Check if any devices were found
        if len(devices) > 0:
                if(board_num==1):
                    device = devices[0]
                else:
                    device = devices[1]
                # Print a messsage describing the device found
#                print("Found device: " + device.product_name +
#                      " (" + device.unique_id + ")\n")
                # Add the device to the UL.
                ul.create_daq_device(board_num, device)
                print(True)

    ao_props = AnalogOutputProps(board_num)
    if ao_props.num_chans < 1:
        util.print_unsupported_example(board_num)
        return

    ao_range = ao_props.available_ranges[0]

    try:
        #print(
        #    "Outputting " + str(data_value) + " Volts to channel "
        #    + str(channel) + ".")
        # Send the value to the device (optional parameter omitted)
        #for loop inside the thing
        for i in range(len(channels)):
            ul.v_out(board_num, channels[i], ao_range, volts[i])
        return(volts)
    except ULError as e:
        util.print_ul_error(e)
    finally:
        if use_device_detection:
            ul.release_daq_device(board_num)
            
def getTemp():
    result = ul.t_in(2, 0, TempScale.CELSIUS)
    return result
#from mcculw import enums
    #ul.set_config(InfoType.BOARDINFO, 2, 0, BoardInfo.CHANTCTYPE, TcType.K)
    #ul.get_config(InfoType.BOARDINFO, 2, 9, BoardInfo.CHANTCTYPE)

############################ MAIN CODE (FOR LOOPS) ############################
            
def executeCode(channelsToRead, channelsOut, numStages, itPerStage, 
                zeroVoltageAtEnd, writeToCSV, voltage, returnArray = True):
#check settings before proceeding
    proceed = checkSettings(channelsToRead, channelsOut, numStages, itPerStage, 
                                zeroVoltageAtEnd, writeToCSV, voltage)
    if(proceed):
        #make the array of the input & output settings
        arrayRows = itPerStage * numStages
        arrayColumns = 2 + len(channelsOut) + len(channelsToRead)
        array = np.full((arrayRows, arrayColumns), -1) #-1 in the array signals it wasn't filled, here
        array = array.astype("float")
        currentArrayRow = 0
        
        for stage in range(numStages):
        
            #output voltage
            outV = outputVoltage(channelsOut, voltage[stage])
            
            #read data; add rows to array
            for i in range(itPerStage):
                
                #fill in the time on the array
                currentTime = tm.time()
                array[currentArrayRow, 0] = currentTime #will eventually be the date
                array[currentArrayRow, 1] = currentTime - array[0, 0] #current time - time zero
                
                for j in range(len(outV)):
                    array[currentArrayRow, 2 + j] = outV[j]
                
                #read input
                for l in range(len(channelsToRead)):
                    chNum = channelsToRead[l]
                    inV = readVoltage(chNum) #get input from channel
                    
                    array[currentArrayRow, 2 + len(channelsOut) + l] = inV
                    
                currentArrayRow += 1
                
                tm.sleep(1)
    
                #plot
                #fig, ax = plt.subplots()
        
                #ax.set(xlabel='time (s)', ylabel='voltage (mV)',
                #   title='Input')
                #ax.grid()
               
                #plt.show()
            #end of for loop & data collection
                    
            ###### stop sending signals to everything #####
            if(zeroVoltageAtEnd):
                zeroVoltage = list(np.zeros((1,len(channelsOut)))[0])
                outputVoltage(channelsOut, zeroVoltage)
        
        ############################ WRITE TO CSV #########################
        if(writeToCSV):
            #make file name based on start time
            date = tm.localtime(array[0, 0])
            fileName = str(date.tm_year)
            if date.tm_mon < 10:
                fileName = fileName + "0" + str(date.tm_mon)
            else:
                fileName = fileName + str(date.tm_mon)
                
            if date.tm_mday < 10:
                fileName = fileName + "0" + str(date.tm_mday)
            else:
                fileName = fileName + str(date.tm_mday)
            
            fileName = fileName + "_" + str(date.tm_hour) + str(date.tm_min) + ".csv"
            
            #open file & write to it
            with open(fileName, mode = "w") as csvFile:
                writer = csv.writer((csvFile), dialect = "excel")
                
                #header
                csvHead = ["Date", "Time (sec)"]
                for i in channelsOut:
                    text = "Channel " + str(i)
                    csvHead.append(text)
    
                for k in channelsToRead:
                    text = "Read " + str(k)
                    csvHead.append(text)
                
                writer.writerow(csvHead)
    
                #actual rows
                for i in range(currentArrayRow):
                    tempRow = list(array[i])
                    tempRow[0] = tm.ctime(tempRow[0])
                    writer.writerow(tempRow)
                
            csvFile.close()
        
        if(returnArray):
            return array
        return
    
#call to the function

if __name__ == "__main__":
    executeCode(channelsToRead, channelsOut, numStages, itPerStage, 
                zeroVoltageAtEnd, writeToCSV, voltage, True)