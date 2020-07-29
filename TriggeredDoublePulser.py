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
import AWG as awg
import digitizer
import hvi
import time

import pulses

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
awg.trigger()

awg.close()
