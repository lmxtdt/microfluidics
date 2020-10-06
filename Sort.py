# -*- coding: utf-8 -*-
"""
@author: Lia Thomson

Draft of a script that would sort droplets based on luminescence. Incomplete.

Last updated: Sep. 25, 2020
"""

import sys
sys.path.append(r"C:\Program Files\Micro-Manager-2.0gamma")
sys.path.append(r"C:\Users\Nikon\Desktop\MCCDAQ\automation")

import uManagerFuns as umf
import AutomationChannels as ac
import ImageAnalysis as ia

m = umf.setup()

channels = [0, 1]
voltages = "x"

###

#output voltage

#stop
ac.outputVoltage(channels, [0,0]) #or such
img = umf.pic(m)
droplets = ia.findDroplets(img, 1, 20, 20, 20, 100) #parameters: how to fix

#take picture
#analyze
#average radius of droplets
#a couple more pictures probably
#change voltage
#repeat

#change direction when no droplets?