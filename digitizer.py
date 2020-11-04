# -*- coding: utf-8 -*-
"""
Created on Tue May 14 10:32:05 2019

@author: Administrator
"""

import sys
import numpy as np
import logging
from pulses import timebase

log = logging.getLogger(__name__)

sys.path.append(r'C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
import keysightSD1 as key


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


class Digitizer:
    """Represents a PXIe M310xA type Digitizer"""

    @property
    def handle(self):
        return self._handle

    @property
    def slot(self):
        return self._slot

    def __init__(self, slot, channels, captureTime):
        log.info("Configuring Digitizer...")
        self._handle = key.SD_AIN()
        self.sampleRate = 500E+06
        self.channels = channels
        self._slot = slot
        self.timeStamps = timebase(0, captureTime, self.sampleRate)
        self.pointsPerCycle = len(self.timeStamps)

        # Discover the chassis number
        chassis = key.SD_Module.getChassisByIndex(1)
        if chassis < 0:
            raise DigitizerError(chassis)
        error = self._handle.openWithSlotCompatibility(
            '', chassis, slot, key.SD_Compatibility.KEYSIGHT)
        if error < 0:
            log.info("Error Opening digitizer in slot #{}".format(slot))
        for channel in self.channels:
            error = self._handle.DAQflush(channel)
            if error < 0:
                log.info("Error Flushing")
            error = self._handle.channelInputConfig(
                channel, 2.0,
                key.AIN_Impedance.AIN_IMPEDANCE_50,
                key.AIN_Coupling.AIN_COUPLING_DC)
            if error < 0:
                log.info("Error Configuring channel")

    def digitize(self, trigger_delay, number_of_pulses=1):
        log.info("Starting Digitizer: Slot-{}...".format(self._slot))
        trigger_delay = trigger_delay * self.sampleRate  # expressed in samples
        trigger_delay = int(np.round(trigger_delay))
        for channel in self.channels:
            error = self._handle.DAQconfig(
                channel,
                self.pointsPerCycle,
                number_of_pulses,
                trigger_delay,
                key.SD_TriggerModes.SWHVITRIG)
#                key.SD_TriggerModes.AUTOTRIG)
            if error < 0:
                log.info("Error Configuring Acquisition")
            error = self._handle.DAQstart(channel)
            if error < 0:
                log.info("Error Starting Digitizer")

    def get_data_raw(self):
        TIMEOUT = 10000
        channelData = []
        for channel in self.channels:
            dataRead = self._handle.DAQread(
                channel,
                self.pointsPerCycle,
                TIMEOUT)
            if len(dataRead) != self.pointsPerCycle:
                log.warning(
                    "Slot:{} Attempted to Read {} samples, actually read {} samples".format(self._slot, self.pointsPerCycle, len(dataRead)))
            channelData.append(dataRead)
        return(channelData)

    def get_data(self):
        LSB = 1 / 2**14
        samples = self.get_data_raw()
        for channelData in range(len(samples)):
            samples[channelData] = samples[channelData] * LSB
        return(samples)

    def readRegister(self, regNumber):
        retVal = self._handle.readRegisterByNumber(regNumber)
        return(retVal[1])

    def __del__(self):
        self._handle.close()

######################################################
# MAIN!!!!!
######################################################


if (__name__ == '__main__'):
    print("WARNING - YOU ARE RUNNING TEST CODE")
    dig = Digitizer(7, [1], 100e-6)
    print(dig.digitize(0))
    data = dig.get_data_raw()
