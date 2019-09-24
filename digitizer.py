# -*- coding: utf-8 -*-
"""
Created on Tue May 14 10:32:05 2019

@author: Administrator
"""

import sys
import numpy as np
import logging
import matplotlib.pyplot as plt

log = logging.getLogger(__name__)

sys.path.append(r'C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
import keysightSD1 as key

# globals to this module (essentially this is a singleton class)
__dig = key.SD_AIN()
_channel = 1
_pointsPerCycle = 0
timeStamps = []
_SAMPLE_RATE = 500E+06

def timebase(start, stop, sample_rate):
    start_sample = int(start * sample_rate)
    stop_sample = int (stop * sample_rate)
    timebase = np.arange(start_sample, stop_sample)
    timebase = timebase / sample_rate
    return(timebase)

def open(slot, channel, captureTime):
    log.info("Configuring Digitizer...")
    global timeStamps, _pointsPerCycle, _channel
    _channel = channel
    timeStamps = timebase(0, captureTime, _SAMPLE_RATE)
    _pointsPerCycle = len(timeStamps)
    error = __dig.openWithSlotCompatibility('', 1, slot, key.SD_Compatibility.KEYSIGHT)
    if error < 0:
        log.info("Error Opening digitizer in slot #{}".format(slot))
    error = __dig.DAQflush(_channel)
    if error < 0:
        log.info("Error Flushing")
    error = __dig.channelInputConfig(_channel, 2.0, key.AIN_Impedance.AIN_IMPEDANCE_50, 
                             key.AIN_Coupling.AIN_COUPLING_DC)
    if error < 0:
        log.info("Error Configuring channel")
    return (__dig)

def digitize(trigger_delay):
    trigger_delay = trigger_delay * _SAMPLE_RATE # expressed in samples
    trigger_delay = int(np.round(trigger_delay))
    error = __dig.DAQconfig(_channel, _pointsPerCycle, 1, trigger_delay, key.SD_TriggerModes.SWHVITRIG)
    if error < 0:
        log.info("Error Configuring Acquisition")
    error = __dig.DAQstart(_channel)
    if error < 0:
        log.info("Error Starting Digitizer")
    
def get_data():
    TIMEOUT = 10000
    LSB = 1/ 2**14
    dataRead = __dig.DAQread(_channel, _pointsPerCycle, TIMEOUT)
    return(dataRead * LSB)
    
def close():
    __dig.close()

######################################################
# MAIN!!!!!
################  ####################################    
if (__name__ == '__main__'):
    open(5, 1, 100e-6, 0)
    print(digitize())
    close()