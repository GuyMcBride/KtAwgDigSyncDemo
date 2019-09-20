# -*- coding: utf-8 -*-
"""
Created on Sat Jul 27 12:33:33 2019

@author: Administrator
"""

import os
import sys
import time
import json
import numpy as np
import logging.config
import matplotlib.pyplot as plt
import simpleAWG as awg
import digitizer as dig
import hvi

DIGITIZER_SLOT = 7
AWG_SLOT = 5  
PRI = 50E-06
PULSE_WIDTH = 9E-06
CAPTURE_WIDTH = 10E-06
PULSES_TO_CAPTURE = 20
CARRIER_FREQUENCY = 10E+06

log = logging.getLogger('Main')

def setup_logging(
    default_path='logging.json',
    default_level=logging.DEBUG,
    env_key='LOG_CFG'
):
    """Setup logging configuration"""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

def hertz_to_rad(hertz: float):
    return hertz * 2 * np.pi

def timebase(start, stop, sample_rate):
    start_sample = int(start * sample_rate)
    stop_sample = int (stop * sample_rate)
    timebase = np.arange(start_sample, stop_sample)
    timebase = timebase / sample_rate
    return(timebase)

if (__name__ == '__main__'):
    setup_logging()

    #Create a simple pulse of carrier
    t = timebase(0, PULSE_WIDTH, 1e+09)
    wave = np.sin(hertz_to_rad(CARRIER_FREQUENCY) * t)
    wave = np.concatenate([wave, np.zeros(100)])
    
    awg_h = awg.open(AWG_SLOT, PULSES_TO_CAPTURE, PRI)
    dig_h = dig.open(DIGITIZER_SLOT, CAPTURE_WIDTH, PULSES_TO_CAPTURE, PRI)
    
    awg.loadWaveform(wave)
    dig.digitize()
    
    hvi_path = os.getcwd() + '\\SyncStart.hvi'
    hvi_mapping = {'Module 1': awg_h, 'Module 0': dig_h}
    hvi.init(hvi_path, hvi_mapping)

    hvi.start()

    for ii in range(PULSES_TO_CAPTURE):
        samples = dig.get_data()
        plt.plot(dig.timeStamps / 1e-06, samples)
    
    hvi.close()
    dig.close()
    awg.close()
    