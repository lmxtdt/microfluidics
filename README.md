A collection of microfluidics-related scripts. All have dosctrings explaining what they do and whether they should still be used. Old scripts that should no longer be used are included in this repository for completeness. (And to know not to use them when coming across them in the microscope room computer.)

The files are listed below.

#Current Scripts
Usable as-is.

* arduinoGUI.py: A basic GUI to interface with an Arduino UNO
* dropletAnalysisFuncs.py: Functions and classes used to identify droplets from a grayscale picture of fluorescent droplets.
* dropletAnalysisGUI.py: A script that, when run, gives a GUI to analyze a folder of droplets, and put its output (images showing identified droplets and a summary .csv file) in another folder.
* mccdaqFuncs.py: Functions for interfacing with the MCCDAQ boards
* *Note to self: add the micromanager script if possible*

#Imperfect Scripts
Have some salvageable parts, but are not usable as-is.

* Temperature.py: A script that attempts to perform temperature PID. The right settings haven't been found and tested to ensure good performance.
* DropletWashThrough.py: Script that washes droplets through a channel, takes pictures of them, and analyzes them.
* DropletWashThrough2.py: Script that washes droplets through a channel, but does not take pictures of them. Based off DropletWashThrough.py
* AutomationChannels.py: Script that outputs varying pressure to create different types of droplets. I believe previous tests of the script worked, but I am not sure there were no issues.
* checkFluorescenceOutput.py: Script that adjusts pressure ratios when creating droplets to create droplets with a certain luminescence. The droplet identification algorithm is not as good as the one in dropletAnalysisFuncs.py

#Unusable Scripts
Outdated or incomplete scripts

* ImageAnalysis.py: Functions that attempt to identify and analyze fluorescent droplets. Does not work as well as dropletAnalysisFuncs.py
* Sort.py: Draft of a script that would sort droplets in a device based on their luminescence.
* untitled3.py: A script that analyzes all the images in a folder for droplets. Does not work as well as dropletAnalysisGUI.py
* FindParameters.py: An attempt at supervised learning to find the proper parameters to pass to HoughCircles when identifying droplets. Unnecessary when using dropletAnalysisFuncs.py