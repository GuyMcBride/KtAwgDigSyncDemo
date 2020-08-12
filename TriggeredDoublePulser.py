# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 18:22:10 2020

@author: Guy McBride, Keysight Technologies (UK) Ltd.
"""
import os
import json
import numpy as np
import logging.config
import matplotlib.pyplot as plt
import time
import AWG as awg
import hvi
import pulses as pulseLab

log = logging.getLogger(__name__)

SAMPLE_RATE = 1E+09

AWG_SLOT = 2
AWG_CHANNEL = 1

LOOPS = 8

PULSE_WIDTHS = [1E-06, 2E-06]
PULSE_BANDWIDTHS = [1E+06, 10E+06]
PULSE_FREQUENCIES = [100E+6, 20E+06]
PULSE_AMPLITUDES = [1.0, 1.0]

awg_h = awg.open(AWG_SLOT, AWG_CHANNEL)
awg.configure("TriggeredDoublePulser")

hvi_path = os.getcwd() + '\\DoublePulse_clf.hvi'
hvi_mapping = {'AWG0': awg_h}
hvi.init(hvi_path, hvi_mapping)

tic = time.perf_counter()
pulses = []
for ii in range(len(PULSE_WIDTHS)):
    pulse = pulseLab.createPulse(SAMPLE_RATE, PULSE_WIDTHS[ii], PULSE_BANDWIDTHS[ii], 1)
    pulses.append(pulse.wave)
    plt.plot(pulse.timebase, pulse.wave)
awg.loadWaveforms(pulses)
toc = time.perf_counter()
log.info("Calculating and downloading waveforms took: {}ms".format((toc - tic) / 1E-03))

tic = time.perf_counter()
#awg.writeRegister(0, PULSE_FREQUENCIES[0], 'Hz')
#freq1 = awg.readRegister(0)
#log.info("Frequency Pulse 1: {}".format(freq1))

#awg.writeRegister(3, PULSE_FREQUENCIES[1], 'Hz')
#freq2 = awg.readRegister(3)
#log.info("Frequency Pulse 2: {}".format(freq2))

#awg.writeRegister(15, LOOPS)
#loops = awg.readRegister(15)
#log.info("Loops Required: {}".format(loops))
constants = []
constants.append(hvi.constant('AWG0', 'NumLoops', LOOPS, ''))
constants.append(hvi.constant('AWG0', 'Amplitude1', PULSE_AMPLITUDES[0], 'V'))
constants.append(hvi.constant('AWG0', 'Amplitude2', PULSE_AMPLITUDES[1], 'V'))
constants.append(hvi.constant('AWG0', 'Frequency1', PULSE_FREQUENCIES[0], 'Hz'))
constants.append(hvi.constant('AWG0', 'Frequency2', PULSE_FREQUENCIES[1], 'Hz'))
hvi.setConstants(constants)

toc = time.perf_counter()
log.info("Writing HVI registers took: {}ms".format((toc - tic) / 1E-03))
hvi.start()

#awg.trigger()

time.sleep(1)
loops = awg.readRegister(15)
log.info("Loop Counter: {}".format(loops))

hvi.close()
awg.close()
