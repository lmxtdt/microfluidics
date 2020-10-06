# -*- coding: utf-8 -*-
"""
@author: Lia Thomson

Several MCCDAQ/MCCULW related functions for convenient use.
First, boards must be initialized using initializeInputBoard() or 
initializeOutputBoard(). Save the index returned by these functions.
The index must be passed into every other function except saveCSV().
All functions have docstrings
"""
import sys
sys.path.append(r"C:\Users\Nikon\Desktop\MCCDAQ")

from mcculw import ul
from mcculw.enums import InterfaceType, TempScale, InfoType, BoardInfo, TcType
from mcculw.ul import ULError

from examples.console import util
from examples.props.ai import AnalogInputProps
from examples.props.ao import AnalogOutputProps

import csv

######################## BOARD INTIALIZATION & RELEASE ########################
def initializeInputBoard(board):
    """Initializes a board for input.
    
    PARAMETERS
    board: either an integer index or a string name of the board to initialize
    
    RETURNS the index of the board
    """
    usingStr = False
    index = -1
    if(type(board) == int):
        index = board
    elif(type(board) == str):
        usingStr = True
    else:
        raise TypeError("Invalid Board")
        
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    # Check if any devices were found
    device = None
    try:
        for i in range(len(devices)):
            dev = devices[i]
            
            if(usingStr):
                if(str(dev) == board):
                    device = dev
                    index = i
                    break
            else:
                if(i == board):
                    device = dev
                    break
    
        if(device is not None):
            ul.create_daq_device(index, device)
            
            print("Remember to call releaseBoard({}) when finished with this board.".format(index))
        else:
            raise Exception
    except Exception:
        print("Device {} not found.".format(board))
        
    return index


def initializeOutputBoard(board):
    """Initialize a board for output.
    
    PARAMETER
    board: either an integer index or a string name of the board to initialize
    
    RETURNS the index of the board.
    """
    usingStr = False
    index = -1
    if(type(board) == int):
        index = board
    elif(type(board) == str):
        usingStr = True
    else:
        raise TypeError("Invalid Board")
        
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    # Check if any devices were found
    device = None
    try:
        for i in range(len(devices)):
            dev = devices[i]
            
            if(usingStr):
                if(str(dev) == board):
                    device = dev
                    index = i
                    break
            else:
                if(i == board):
                    device = dev
                    break
    
        if(device is not None):
            ul.create_daq_device(index, device)
            
            print("Remember to call releaseBoard({}) when finished with this baord.".format(index))
            
        else:
            raise Exception
    except Exception:
        print("Device {} not found.".format(board))
        
    return index

def releaseBoard(board):
    """Release a board once its done being used.
    
    PARAMETER
    board: integer index for the board to release
    """
    ul.release_daq_device(board)

########################### CHANNEL INPUT AND OUTPUT ##########################

def readTempChannel(channel, board):
    """Read one channel to get a temperature in celsius.
    
    PARAMETERS
    channel: an integer index for the channel to read
    board: an integer index for the board being used
    
    RETURNS value, a float of the temperature read in celsius
    """
    try:
        value = ul.t_in(board, channel, TempScale.CELSIUS)

        return value
    except ULError as e:
        util.print_ul_error(e)

def readMutipleTemps(channels, board):
    """Read multiple channels on one board to get multiple temperatures in celsius.
    
    PARAMETERS
    channels: an array of integer indexes for the channels to read
    board: an integer index for the board being used
    
    RETURNS values, a list of floats of the temperatures read in celsius
    """
    values = []
    for c in channels:
        values.append(readTempChannel(c, board))
        
    return values

def outputOneChannel(channel, board, voltage):
    """Outputs a voltage to a channel.
    
    PARAMETERS
    channel: an integer index for the channel to output to
    board: an integer index for the board being used
    voltage: an integer or float that will be output
    """
    try:
        ao_props = AnalogOutputProps(board)
        ao_range = ao_props.available_ranges[0]
        ul.v_out(board, channel, ao_range, voltage)
    except Exception as e:
        print(e)
        
def outputMultipleChannels(channels, board, volts):
    """Outputs different voltages to multiple channel.
    
    PARAMETERS
    channels: a list of integer indices to output to
    board: an integer index for the board being used
    volts: a list of integers or floats that will be output
    """
    if(len(channels) != len(volts)):
        raise Exception("Channels and voltage are different lengths.")
    
    for i in range(len(channels)):
        outputOneChannel(channels[i], board, volts[i])

################################ MISCELLANEOUS ################################
def setThermocouple(board, channel, newValue):
    """Configure the thermocouple type of a channel.
    
    PARAMETERS
    board: an integer index for the board
    channel: an integer index for the channel
    newValue: a TcType or string indicating the new value to set it to. The valid types are:
        T, J, K, T, E, R, S
    """
    if(type(board) != int):
        raise TypeError("board not an integer")
    val = None
    try:
        if(type(newValue) == str):
            strToType = {"J": TcType.J, "K": TcType.K, "T": TcType.T, "E": TcType.E,
                         "R": TcType.R, "S": TcType.S, "B": TcType.B, "N": TcType.N}
            val = strToType(newValue)
        elif(type(newValue) == TcType):
            val = TcType
        else:
            raise Exception
    except Exception:
        raise TypeError("Invalid newValue.")
    
    ul.set_config(InfoType.BOARDINFO, board, channel, BoardInfo.CHANTCTYPE, val)
        
def saveCSV(path, rows):
    """Writes a csv file.
    
    PARAMETERS
    path: the path, including the file name, but without ".csv" to write the file to
    rows: a list of rows to write. Each row itself should be a list.
    """
    fileName = "{}.csv".format(path)

    #FORMAT: droplet ID, r, mean adjusted, img name, img ID, x, y, mean unadjusted
    with open(fileName, mode = "w", newline = "") as csvFile:
        writer = csv.writer((csvFile), dialect = "excel")

        for row in rows:
            writer.writerow(row)
