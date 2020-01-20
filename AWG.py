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
#import matplotlib.pyplot as plt

sys.path.append(r'C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
import keysightSD1 as key

log = logging.getLogger(__name__)

# globals to this module (essentially this is a singleton class)
__awg = key.SD_AOU()
_channel = 1

# Queue constants
SINGLE_CYCLE = 1
INFINITE_CYCLES = 0
WAVE_PRESCALER = 0


class AwgError(Exception):
    """Basic exception for errors raised by Digitizer"""
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


def open(slot, channel):
    global _channel
        # Discover the chassis number
    chassis = key.SD_Module.getChassisByIndex(1)
    if chassis < 0:
        raise AwgError(chassis)
    log.info("Configuring AWG in slot {}...".format(slot))
    _channel = channel
    error = __awg.openWithSlotCompatibility('', chassis, slot, key.SD_Compatibility.KEYSIGHT)
    if error < 0:
        log.info("Error Opening - {}".format(error))
    __awg.waveformFlush()
    if error < 0:
        log.info("Error Flushing waveforms - {}".format(error))
    __awg.AWGflush(_channel)
    if error < 0:
        log.info("Error Flushing AWG - {}".format(error))
    error = __awg.channelWaveShape(_channel, key.SD_Waveshapes.AOU_AWG)
    if error < 0:
        log.info("Error Setting Waveshape - {}".format(error))
    error = __awg.channelAmplitude(_channel, 1.0)
    if error < 0:
        log.info("Error Setting Amplitude - {}".format(error))
    log.info("Setting front panel trigger to Output...")
    error = __awg.triggerIOconfig(key.SD_TriggerDirections.AOU_TRG_OUT)
    if error < 0:
        log.info("Error Setting Trigger to output - {}".format(error))
    log.info("Finished setting up AWG in slot {}...".format(slot))
    return __awg
    
def loadWaveform(waveform, start_delay, waveId = 1):
    log.info("Loading waveform...")
    if len(waveform) == 0:
        log.info("Waveform is empty")
        return -1
#    plt.plot(waveform)
    wave = key.SD_Wave()
    error = wave.newFromArrayDouble(key.SD_WaveformTypes.WAVE_ANALOG, waveform)
    if error < 0:
        log.info("Error Creating Wave - {}".format(error))
    error = __awg.waveformLoad(wave, waveId)
    if error < 0:
        log.info("Error Loading Wave - {}".format(error))
    start_delay = start_delay / 10E-09 # expressed in 10ns
    start_delay = int(np.round(start_delay))
    log.info("Enqueueing waveform {}, StartDelay = {}".format(waveId, start_delay))
    error = __awg.AWGqueueWaveform(_channel, waveId, key.SD_TriggerModes.SWHVITRIG, start_delay, 1, WAVE_PRESCALER)
    if error < 0:
        log.info("Queueing waveform failed! - {}".format(error))
    error = __awg.AWGqueueConfig(_channel, key.SD_QueueMode.CYCLIC)
    if error < 0:
        log.info("Configure cyclic mode failed! - {}".format(error))
    error = __awg.AWGstart(_channel)
    if error < 0:
        log.info("Starting AWG failed! - {}".format(error))
    log.info("Finished Loading waveform")
    return 1

def loadWaveforms(waveforms, start_delays):
    log.info("Loading waveforms...")
    if len(waveforms) != len(start_delays):
        log.error("There must be the same number of waveforms and start_delays")
    for ii in range(len(waveforms)):
        loadWaveform(waveforms[ii], start_delays[ii], ii + 1)
    return 1

def close():
    log.info("Stopping AWG...")
    error = __awg.AWGstop(_channel)
    if error < 0:
        log.info("Stopping AWG failed! - {}".format(error))
    error = __awg.channelWaveShape(_channel, key.SD_Waveshapes.AOU_HIZ)
    if error < 0:
        log.info("Putting AWG into HiZ failed! - {}".format(error))
    __awg.close()
    log.info("Finished stopping and closing AWG")

if (__name__ == '__main__'):

    print("WARNING - YOU ARE RUNNING TEST CODE")
    
    import simpleMain
    
    t = simpleMain.timebase(0, 100e-6, 1e9)
    wave = np.sin(simpleMain.hertz_to_rad(20E+06) * t)
    
    open(1, 2, 1)
    loadWaveform(wave, 0)
    __awg.AWGtrigger(_channel)

    time.sleep(10)
    close()
    