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
AWG_REF_CHANNEL = 3

LOOPS = 4

PULSE_WIDTHS = [2E-06, 1E-06, 0.5E-06, 0.25E-06]
PULSE_BANDWIDTHS = [10E+06, 1E+06, 1E+06, 1E+06]
PULSE_FREQUENCIES = [20E+6, 50E+06, 50.5E+06, 100E+06]
PULSE_AMPLITUDES = [0.5, 0.25, 0.125, 0.125]

awg_h = awg.open(AWG_SLOT, AWG_CHANNEL)

#awg.loadFpgaImage("firmware_MultiLO_CLF_K42_triangle.sbp")
#awg.loadFpgaImage("MULTLO_CLF_K41_3_77.sbp")
awg.loadFpgaImage("test_test_partial.sbp")


def calcAandB(f, fs=1E9):
    S = 5
    T = 8
    K = (f / fs) * (S / T) * 2**25
    A = int(K)
    B = round((K-A) * 5**10) 
    return A, B

[A, B] = calcAandB(PULSE_FREQUENCIES[0])
awg.writeFpgaRegister(0, 0, A)
awg.writeFpgaRegister(0, 1, B)
[A, B] = calcAandB(PULSE_FREQUENCIES[1])
awg.writeFpgaRegister(0, 2, A)
awg.writeFpgaRegister(0, 3, B)
[A, B] = calcAandB(PULSE_FREQUENCIES[2])
awg.writeFpgaRegister(0, 4, A)
awg.writeFpgaRegister(0, 5, B)
[A, B] = calcAandB(PULSE_FREQUENCIES[3])
awg.writeFpgaRegister(0, 6, A)
awg.writeFpgaRegister(0, 7, B)

# Test register if FPGA built with PC port LO selector
awg.writeFpgaRegister(0, 8, 1)

awg.configure("MultiLo", AWG_REF_CHANNEL)

hvi_path = os.getcwd() + '\\MultiLO_CLF.hvi'
hvi_mapping = {'AWG0': awg_h}
hvi.init(hvi_path, hvi_mapping)

rawPulses = []
for ii in range(len(PULSE_WIDTHS)):
    pulse = pulseLab.createPulse(SAMPLE_RATE, PULSE_WIDTHS[ii], PULSE_BANDWIDTHS[ii], 1)
    rawPulses.append(pulse.wave)
#    plt.plot(pulse.timebase, pulse.wave)

tic = time.perf_counter()
scaledPulses = []
for ii in range(len(rawPulses)):
    scaledPulses.append(rawPulses[ii] * PULSE_AMPLITUDES[ii])
awg.loadWaveforms(scaledPulses)

toc = time.perf_counter()
log.info("Calculating and downloading waveforms took: {}ms".format((toc - tic) / 1E-03))

tic = time.perf_counter()
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
awg.close(False)
