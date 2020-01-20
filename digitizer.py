# -*- coding: utf-8 -*-
"""
Created on Tue May 14 10:32:05 2019

@author: Administrator
"""

import sys
import numpy as np
import logging

log = logging.getLogger(__name__)

sys.path.append(r'C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
import keysightSD1 as key

# globals to this module (essentially this is a singleton class)
__dig = key.SD_AIN()
_channels = [1]
_pointsPerCycle = 0
timeStamps = []
_SAMPLE_RATE = 500E+06


class DigitizerError(Exception):
    """Basic exception for errors raised by Digitizer"""
    _error = None
    _message = None
    def __init__(self, error, msg=None):
        if msg is None:
            msg = "An error occured with Awg: {}".format(key.SD_Error.getErrorMessage(error))
        super(DigitizerError, self).__init__(msg)
        self._error = error
    @property
    def error_message(self):
        return key.SD_Error.getErrorMessage(self._error)


def timebase(start, stop, sample_rate):
    start_sample = int(start * sample_rate)
    stop_sample = int(stop * sample_rate)
    timebase = np.arange(start_sample, stop_sample)
    timebase = timebase / sample_rate
    return(timebase)


def open(slot, channels, captureTime):
    log.info("Configuring Digitizer...")

    global timeStamps, _pointsPerCycle, _channels
    _channels = channels
    timeStamps = timebase(0, captureTime, _SAMPLE_RATE)
    _pointsPerCycle = len(timeStamps)
    # Discover the chassis number
    chassis = key.SD_Module.getChassisByIndex(1)
    if chassis < 0:
        raise DigitizerError(chassis)

    error = __dig.openWithSlotCompatibility('', chassis, slot, key.SD_Compatibility.KEYSIGHT)
    if error < 0:
        log.info("Error Opening digitizer in slot #{}".format(slot))
    for channel in _channels:
        error = __dig.DAQflush(channel)
        if error < 0:
            log.info("Error Flushing")
        error = __dig.channelInputConfig(channel, 2.0, key.AIN_Impedance.AIN_IMPEDANCE_50, 
                                 key.AIN_Coupling.AIN_COUPLING_DC)
        if error < 0:
            log.info("Error Configuring channel")
    return (__dig)


def digitize(trigger_delay, number_of_pulses = 1):
    trigger_delay = trigger_delay * _SAMPLE_RATE # expressed in samples
    trigger_delay = int(np.round(trigger_delay))
    for channel in _channels:
        error = __dig.DAQconfig(channel, _pointsPerCycle, number_of_pulses, trigger_delay, key.SD_TriggerModes.SWHVITRIG)
        if error < 0:
            log.info("Error Configuring Acquisition")
        error = __dig.DAQstart(channel)
        if error < 0:
            log.info("Error Starting Digitizer")

def get_data_raw():
    TIMEOUT = 10000
    channelData = []
    for channel in _channels:
        dataRead = __dig.DAQread(channel, _pointsPerCycle, TIMEOUT)
        if len(dataRead) != _pointsPerCycle:
            log.warning("Attempted to Read {} samples, actually read {} samples".format(_pointsPerCycle, len(dataRead)))
        channelData.append(dataRead)
    return(channelData)
    
def get_data():
    LSB = 1/ 2**14
    samples = get_data_raw()
    for channelData in range(len(samples)):
        samples[channelData] = samples[channelData] * LSB
    return(samples)
    

def close():
    __dig.close()

######################################################
# MAIN!!!!!
################  ####################################    
if (__name__ == '__main__'):
    print("WARNING - YOU ARE RUNNING TEST CODE")
    open( 5, [1], 100e-6)
    print(digitize(0))
    data = get_data_raw()
    close()