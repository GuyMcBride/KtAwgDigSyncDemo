# -*- coding: utf-8 -*-
"""
Created on Tue Aug 11 15:49:19 2020

@author: gumcbrid
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

LOOPS = 4

PULSE_WIDTHS = [1E-06, 2E-06]
PULSE_BANDWIDTHS = [1E+06, 10E+06]
PULSE_FREQUENCIES = [20E+6, 100E+06]
PULSE_AMPLITUDES = [1.0, 0.5]

awg_h = awg.open(AWG_SLOT, AWG_CHANNEL)

awg.loadFPGA("firmware_MultiLO_CLF_K42.sbp")
awg.writeFpgaRegister(0, 0, 209715)
awg.writeFpgaRegister(0, 0, 419430)

awg.configure("TriggeredDoublePulser")

hvi_path = os.getcwd() + '\\MultiLO_CLF.hvi'
hvi_mapping = {'AWG0': awg_h}
hvi.init(hvi_path, hvi_mapping)

pulses = []
for ii in range(len(PULSE_WIDTHS)):
    pulse = pulseLab.createPulse(SAMPLE_RATE, PULSE_WIDTHS[ii], PULSE_BANDWIDTHS[ii], 1)
    pulses.append(pulse.wave)
    plt.plot(pulse.timebase, pulse.wave)

tic = time.perf_counter()
scaledPulses = []
for ii in range(len(pulses)):
    scaledPulses.append(pulses[ii] * PULSE_AMPLITUDES[ii])
awg.loadWaveforms(scaledPulses)

toc = time.perf_counter()
log.info("Calculating and downloading waveforms took: {}ms".format((toc - tic) / 1E-03))

tic = time.perf_counter()
awg.writeRegister(0, PULSE_FREQUENCIES[0], 'Hz')
freq1 = awg.readRegister(0)
log.info("Frequency Pulse 1: {}".format(freq1))

awg.writeRegister(3, PULSE_FREQUENCIES[1], 'Hz')
freq2 = awg.readRegister(3)
log.info("Frequency Pulse 2: {}".format(freq2))

awg.writeRegister(15, LOOPS)
loops = awg.readRegister(15)
log.info("Loops Required: {}".format(loops))

toc = time.perf_counter()
log.info("Writing HVI registers took: {}ms".format((toc - tic) / 1E-03))
hvi.start()

#awg.trigger()

time.sleep(1)
loops = awg.readRegister(15)
log.info("Loop Counter: {}".format(loops))

hvi.close()
awg.close()
