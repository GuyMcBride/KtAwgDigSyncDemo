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

CHASSIS = 1
DIGITIZER_SLOT = 5
DIGITIZER_CHANNEL = 1
AWG_SLOT = 2
AWG_CHANNEL = 4

AWG_DELAY = 0e-9
DIGITIZER_DELAY = 20e-9

PULSE_WIDTH = 5E-06
CAPTURE_WIDTH = 10E-06
CARRIER_FREQUENCY = 10E+06

log = logging.getLogger('Main')

def setup_logging(
    default_path='logging.json',
    default_level=logging.INFO,
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
    
    awg_h = awg.open(CHASSIS, AWG_SLOT, AWG_CHANNEL)
    dig_h = dig.open(CHASSIS, DIGITIZER_SLOT, DIGITIZER_CHANNEL, CAPTURE_WIDTH)
    
    awg.loadWaveform(wave, AWG_DELAY)
    dig.digitize(DIGITIZER_DELAY)
    
    hvi_path = os.getcwd() + '\\SyncStart.hvi'
    hvi_mapping = {'Module 1': awg_h, 'Module 0': dig_h}
    hvi.init(hvi_path, hvi_mapping)

    hvi.start()

    samples = dig.get_data()
    plt.plot(dig.timeStamps / 1e-06, samples)
    plt.xlabel("us")
    
    hvi.close()
    dig.close()
    awg.close()
    