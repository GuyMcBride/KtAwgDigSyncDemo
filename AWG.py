# -*- coding: utf-8 -*-
"""
Created on Sat Jul 27 12:32:15 2019

@author: Administrator
"""

import sys
import time
import random
import numpy as np
import logging
import os
#import matplotlib.pyplot as plt

sys.path.append(r'C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
import keysightSD1 as key

log = logging.getLogger(__name__)


class AwgError(Exception):
    """Basic exception for errors raised by AWG"""
    _error = None
    _message = None
    def __init__(self, error, msg=None):
        if msg is None:
            msg = "An error occured with Awg: {}".format(key.SD_Error.getErrorMessage(error))
        super(AwgError, self).__init__(msg)
        self._error = error
    @property
    def error_message(self):
        return key.SD_Error.getErrorMessage(self._error)


class AWG:
    """Represents a PXIe M320xA type Arbitrary Waveform Generator"""

    # Queue constants
    SINGLE_CYCLE = 1
    INFINITE_CYCLES = 0
    WAVE_PRESCALER = 0


    def __init__(self, slot):
        self.handle = key.SD_AOU()
        self.sampleRate = 1E+06
        self.slot = slot
        
        # Discover the chassis number
        chassis = key.SD_Module.getChassisByIndex(1)
        if chassis < 0:
            raise AwgError(chassis)
        log.info("Configuring AWG in slot {}...".format(slot))
        error =self.handle.openWithSlotCompatibility('', chassis, slot, key.SD_Compatibility.KEYSIGHT)
        if error < 0:
            log.info("Error Opening - {}".format(error))
        self.handle.waveformFlush()
        if error < 0:
            log.info("Error Flushing waveforms - {}".format(error))
        self.channels = 0
        for channel in range(1, 5):
            error =self.handle.AWGflush(channel)
            if error < 0:
                log.info("Error Flushing AWG - {}".format(error))
            else:
                self.channels = self.channels + 1
        log.info("Finished setting up AWG in slot {}...".format(slot))
            
    
    def configure(self, experiment, refChannel = 0):
        if "Main" in experiment:
            error =self.handle.channelWaveShape(_channel, key.SD_Waveshapes.AOU_AWG)
            if error < 0:
                log.warn("Error Setting Waveshape - {}".format(error))
            log.info("Setting front panel trigger to Output...")
            error =self.handle.triggerIOconfig(key.SD_TriggerDirections.AOU_TRG_OUT)
            if error < 0:
                log.info("Error Setting Trigger to output - {}".format(error))
            error =self.handle.channelAmplitude(_channel, 1.0)
            if error < 0:
                log.warn("Error Setting Amplitude - {}".format(error))
        elif ("TriggeredDoublePulser" in experiment):
            log.info("Setting front panel trigger to Input...")
            error =self.handle.triggerIOconfig(key.SD_TriggerDirections.AOU_TRG_IN)
            if error < 0:
                log.warn("Error Setting Trigger to input - {}".format(error))
            error =self.handle.channelWaveShape(_channel, key.SD_Waveshapes.AOU_SINUSOIDAL)
            if error < 0:
                log.warn("Error Setting Waveshape - {}".format(error))
            error =self.handle.modulationAmplitudeConfig(_channel, key.SD_ModulationTypes.AOU_MOD_AM , 1.0)
            if error < 0:
                log.warn("Error  setting Amplitude Modulation - {}".format(error))
            error =self.handle.channelFrequency(_channel, 10.0E+06)
            if error < 0:
                log.warn("Error Setting default Frequency - {}".format(error))
            error =self.handle.channelAmplitude(_channel, 0.1)
            if error < 0:
                log.warn("Error Setting Amplitude - {}".format(error))
        elif ("MultiLo" in experiment):
            log.info("Setting front panel trigger to Input...")
            error =self.handle.triggerIOconfig(key.SD_TriggerDirections.AOU_TRG_IN)
            if error < 0:
                log.warn("Error Setting Trigger to input - {}".format(error))
            error =self.handle.channelWaveShape(_channel, key.SD_Waveshapes.AOU_TRIANGULAR)
            if error < 0:
                log.warn("Error Setting Waveshape - {}".format(error))
            error =self.handle.modulationAmplitudeConfig(_channel, key.SD_ModulationTypes.AOU_MOD_AM , 1.0)
            if error < 0:
                log.warn("Error  setting Amplitude Modulation - {}".format(error))
            error =self.handle.channelAmplitude(_channel, 0.0)
            if error < 0:
                log.warn("Error Setting Amplitude - {}".format(error))
            error =self.handle.channelWaveShape(refChannel, key.SD_Waveshapes.AOU_TRIANGULAR)
            if error < 0:
                log.warn("Error Setting Ref Channel Waveshape - {}".format(error))
            error =self.handle.channelAmplitude(refChannel, 1.0)
            if error < 0:
                log.warn("Error Setting Reference Channel Amplitude - {}".format(error))
           
        
    def loadWaveform(self, channels, waveform, start_delay, waveId = 1):
        """Loads a waveform and enqueues it for all the channels
        

        Parameters
        ----------
        channels : [int]
            A list of channel numbers in the range 1:4.
        waveform : [float]
            A list of waveform points, in range of -1.0 to +1.0).
        start_delay : float
            The delay from trigger to the waveform being played, in seconds.
        waveId : int, optional
            Each waveform is identified with a unique number. The default is 1.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        log.info("Loading waveform...")
        if len(waveform) == 0:
            log.info("Waveform is empty")
            return -1
    #    plt.plot(waveform)
        wave = key.SD_Wave()
        error = wave.newFromArrayDouble(key.SD_WaveformTypes.WAVE_ANALOG, 
                                        waveform)
        if error < 0:
            log.info("Error Creating Wave - {}".format(error))
        error =self.handle.waveformLoad(wave, waveId)
        if error < 0:
            log.info("Error Loading Wave - {}".format(error))
        start_delay = start_delay / 10E-09 # expressed in 10ns
        start_delay = int(np.round(start_delay))
        log.info("Enqueueing waveform {}, StartDelay = {}".format(waveId, 
                                                                  start_delay))
        for channel in channels:
            error =self.handle.AWGqueueWaveform(channel, 
                                                waveId, 
                                                key.SD_TriggerModes.SWHVITRIG, 
                                                start_delay, 
                                                1, 
                                                self.WAVE_PRESCALER)
            if error < 0:
                log.info("Queueing waveform failed! - {}".format(error))
            error =self.handle.AWGqueueConfig(channel, 
                                              key.SD_QueueMode.CYCLIC)
            if error < 0:
                log.info("Configure cyclic mode failed! - {}".format(error))
            error =self.handle.AWGstart(channel)
            if error < 0:
                log.info("Starting AWG failed! - {}".format(error))
        log.info("Finished Loading waveform")
        return 1
    
    def loadWaveforms(self, channels, waveforms, start_delays=[]):
        log.info("Loading waveforms...")
        if len(start_delays) > 0 & (len(waveforms) != len(start_delays)):
            log.error("There must be the same number of waveforms and start_delays")
        for ii in range(len(waveforms)):
            if len(start_delays) > 0:
                self.loadWaveform(channels,
                             waveforms[ii], 
                             start_delays[ii],
                             ii + 1)
            else:
                self.loadWaveform(channels,
                             waveforms[ii], 
                             0, 
                             ii + 1)
        return 1
    

    def readRegister(self, n):
        retVal =self.handle.readRegisterByNumber(n)
        return(retVal[1])
    

    def writeRegister(self, reg, setting, unit=''):
        if unit == '':
           self.handle.writeRegisterByNumber(reg, setting)
        else:
           self.handle.writeDoubleRegisterByNumber(reg, setting, unit)
    
    
    def trigger(self, channels):
        triggerMask = 0
        for channel in channels:
            triggerMask = triggerMask | channel
        self.handle.AWGtrigger(triggerMask)
        

    def stop(self, channels, turnOff=True):
        log.info("Stopping AWG...")
        triggerMask = 0
        for channel in channels:
            triggerMask = triggerMask | channel
        error = self.handle.AWGstopMultiple(triggerMask)
        if error < 0:
            log.info("Stopping AWG failed! - {}".format(error))
        if turnOff:
            for channel in channels:
                error = self.handle.channelWaveShape(channel, key.SD_Waveshapes.AOU_HIZ)
                if error < 0:
                    log.info("Putting AWG into HiZ failed! - {}".format(error))
        self.handle.close()

    def __del__(self):
        self.stop([1, 2, 3, 4])

        
    def loadFpgaImage(self, filename):
        error = self.handle.FPGAload(os.getcwd() + '\\' + filename)
        if error < 0:
           log.error('Loading FPGA bitfile: {} {}'.format(error, key.SD_Error.getErrorMessage(error)))
    

    def writeFpgaRegister(self, port, address, value):
        buf = []
        buf.append(value)
        error = self.handle.FPGAwritePCport(port, buf, address, key.SD_AddressingMode.FIXED, key.SD_AccessMode.NONDMA)
        if error < 0:
            log.error('WriteRegister: {} {}'.format(error, key.SD_Error.getErrorMessage(error)))
            log.error('Address: {}'.format(address))
            log.error('Buffer [{}]'.format(buf))
    

    def readFpgaRegister(self, port, address):
        error = self.handle.FPGAreadPCport(port, 1, address, key.SD_AddressingMode.FIXED, key.SD_AccessMode.NONDMA)
        if error < 0:
            log.error('WriteRegister: {} {}'.format(error, key.SD_Error.getErrorMessage(error)))
            log.error('Address: {}'.format(address))
        return error


if (__name__ == '__main__'):

    print("WARNING - YOU ARE RUNNING TEST CODE")
    
    from pulses import timebase
    
    t = timebase(0, 100e-6, 1e9)
    wave = np.sin(20E+06 *2 * np.pi * t)
    
    awg = AWG(2)
    print("Number of AWG channels found in slot {}: {}".format(awg.slot, awg.channels))
    awg.loadWaveform([1], wave, 0)
    awg.handle.AWGtrigger(1)

    time.sleep(10)
  
    