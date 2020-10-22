# -*- coding: utf-8 -*-
"""
Created on Sat Jul 27 12:33:33 2019

@author: Administrator
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
    stop_sample = int(stop * sample_rate)
    timebase = np.arange(start_sample, stop_sample)
    timebase = timebase / sample_rate
    return(timebase)


if (__name__ == '__main__'):

    DIGITIZER_SLOT = 7
    DIGITIZER_CHANNELS = [1]
    AWG_SLOT = 2
    AWG_CHANNEL = 4
    
    AWG_DELAYS = [10e-6]
    DIGITIZER_DELAY = 00e-9
    
    PULSE_WIDTH =10E-06
    CAPTURE_WIDTH = 50E-06
    CARRIER_FREQUENCIES = [10E+06]
    CARRIER_AMPLITUDES = [1.0]
    
    PRI = 100.0E-6
    NUMBER_OF_PULSES = 10
    
    PULSES_TO_PLOT = 10

    setup_logging()

    # Create a simple pulse of carrier
    t = timebase(0, PULSE_WIDTH, 1e+09)
    waves = []
    for ii in range(len(CARRIER_FREQUENCIES)):
        wave = np.sin(hertz_to_rad(CARRIER_FREQUENCIES[ii]) * t)
        wave = wave * CARRIER_AMPLITUDES[ii]
        wave = np.concatenate([wave, np.zeros(100)])
        waves.append(wave)

    awg_h = awg.open(AWG_SLOT, AWG_CHANNEL)
    awg.configure("repeatedMain")
    dig = digitizer.Digitizer(DIGITIZER_SLOT, DIGITIZER_CHANNELS, CAPTURE_WIDTH)

#    awg.loadWaveform(waves[0], AWG_DELAYS[0])
    awg.loadWaveforms(waves, AWG_DELAYS)
    dig.digitize(DIGITIZER_DELAY, NUMBER_OF_PULSES)

    hvi_path = os.getcwd() + '\\SyncStartRepeated_A1_D1.hvi'
    hvi_mapping = {'AWG0': awg_h, 'DIG0': dig.handle}
    hvi.init(hvi_path, hvi_mapping)

    hvi.setupConstants(NUMBER_OF_PULSES, PRI)

    hvi.start()

    # Allow the memory to partially fill.
    time.sleep(PRI * NUMBER_OF_PULSES/100)
    log.info("Reading Waveforms....")

    plt.xlabel("us")
    start_time = time.time()
    for ii in range(NUMBER_OF_PULSES):
        samples = dig.get_data()
        if len(samples[0]) == 0:
            log.error("Reading appears to have timed out after {} pulses".format(ii))
            break
        if ii < PULSES_TO_PLOT:  # do not plot too many waves
            plt.plot(dig.timeStamps / 1e-06, samples[0])
    elapsed_time = time.time() - start_time
    log.info("Read {} Msamples in {}s".format((NUMBER_OF_PULSES * dig.pointsPerCycle) / 1e6, elapsed_time))
    log.info("Data rate: {}Msa/s in lumps of {} samples".format((NUMBER_OF_PULSES * dig.pointsPerCycle) / elapsed_time / 1e6, dig.pointsPerCycle))
    log.info("AWG Loop counter: {}".format(awg.readRegister(15)))
    log.info("DIG Loop counter: {}".format(dig.readRegister(15)))
    hvi.close()
    awg.close()
