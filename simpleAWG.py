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

sys.path.append(r'C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
import keysightSD1 as key

log = logging.getLogger(__name__)

# globals to this module (essentially this is a singleton class)
__awg = key.SD_AOU()
_CHANNEL = 1

# Queue constants
SINGLE_CYCLE = 1
INFINITE_CYCLES = 0
WAVE_PRESCALER = 0
DELAY_OUT = 0

def open(slot, numberPulses, pri):
    log.info("Configuring AWG in slot {}...".format(slot))
    error = __awg.openWithSlotCompatibility('', 1, slot, key.SD_Compatibility.KEYSIGHT)
    if error < 0:
        log.info("Error Opening - {}".format(error))
    __awg.waveformFlush()
    if error < 0:
        log.info("Error Flushing waveforms - {}".format(error))
    __awg.AWGflush(_CHANNEL)
    if error < 0:
        log.info("Error Flushing AWG - {}".format(error))
    error = __awg.channelWaveShape(_CHANNEL, key.SD_Waveshapes.AOU_AWG)
    if error < 0:
        log.info("Error Setting Waveshape - {}".format(error))
    error = __awg.channelAmplitude(_CHANNEL, 1.0)
    if error < 0:
        log.info("Error Setting Amplitude - {}".format(error))
    log.info("Finished AWG in slot {}...".format(slot))
    error = __awg.writeDoubleRegisterByNumber(0, (pri - 140E-09), 's')
    if error < 0:
        log.info("Error Writing wait time")
    log.info("Register 0 = {}".format (__awg.readDoubleRegisterByNumber(0, 's')))
    error = __awg.writeRegisterByNumber(1, numberPulses)
    if error < 0:
        log.info("Error Writing number pulses")
    log.info("Register 1 = {}".format (__awg.readDoubleRegisterByNumber(1, 's')))
    return __awg
    
def loadWaveform(waveform):
    log.info("Loading waveform...")
    if len(waveform) == 0:
        log.info("Waveform is empty")
        return -1
    wave = key.SD_Wave()
    error = wave.newFromArrayDouble(key.SD_WaveformTypes.WAVE_ANALOG, waveform)
    if error < 0:
        log.info("Error Creating Wave - {}".format(error))
    error = __awg.waveformLoad(wave, 1)
    if error < 0:
        log.info("Error Loading Wave - {}".format(error))
    log.info("Enqueueing waveform #1")
    error = __awg.AWGqueueWaveform(_CHANNEL, 1, key.SD_TriggerModes.SWHVITRIG, DELAY_OUT, 1, WAVE_PRESCALER)
    if error < 0:
        log.info("Queueing waveform failed! - {}".format(error))
    error = __awg.AWGqueueConfig(_CHANNEL, key.SD_QueueMode.CYCLIC)
    if error < 0:
        log.info("Configure cyclic mode failed! - {}".format(error))
    error = __awg.AWGstart(_CHANNEL)
    if error < 0:
        log.info("Starting AWG failed! - {}".format(error))
    return 1

def close():
    log.info("Stopping AWG".format())
    error = __awg.AWGstop(_CHANNEL)
    if error < 0:
        log.info("Stopping AWG failed! - {}".format(error))
    error = __awg.channelWaveShape(_CHANNEL, key.SD_Waveshapes.AOU_HIZ)
    if error < 0:
        log.info("Putting AWG into HiZ failed! - {}".format(error))
    __awg.close()

if (__name__ == '__main__'):
    import simpleMain
    
    t = simpleMain.timebase(0, 10e-6, 1e9)
    wave = np.sin(simpleMain.hertz_to_rad(20E+06) * t)
    
    open()
    loadWaveform(wave)
#    __awg.AWGtrigger(_CHANNEL)

    time.sleep(10)    