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
import pulses

log = logging.getLogger(__name__)



SAMPLE_RATE = 1E+09

PULSE_WIDTH = 1E-06
PULSE_BANDWIDTH = 1E+06

AWG_SLOT = 2
AWG_CHANNEL = 1

pulse = pulses.createPulse(SAMPLE_RATE, PULSE_WIDTH, PULSE_BANDWIDTH)
plt.plot(pulse.timebase, pulse.wave)

awg_h = awg.open(AWG_SLOT, AWG_CHANNEL)
awg.configure("TriggeredDoublePulser")

awg.loadWaveform(pulse.wave, 0)

hvi_path = os.getcwd() + '\\DoublePulse_clf.hvi'
hvi_mapping = {'AWG0': awg_h}
hvi.init(hvi_path, hvi_mapping)

awg.writeRegister(0, 20E+06, 'Hz')
freq1 = awg.readRegister(0)
log.info("Frequency Pulse 1: {}".format(freq1))

awg.writeRegister(3, 100E+06, 'Hz')
freq2 = awg.readRegister(3)
log.info("Frequency Pulse 2: {}".format(freq2))

awg.writeRegister(15, 4)
loops = awg.readRegister(15)
log.info("Loops Required: {}".format(loops))

hvi.start()

#awg.trigger()

time.sleep(1)
loops = awg.readRegister(15)
log.info("Loop Counter: {}".format(loops))

hvi.close()
awg.close()
