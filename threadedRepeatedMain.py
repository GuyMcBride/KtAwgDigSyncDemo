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
import digitizer as dig
import hvi
import time

import concurrent.futures
import queue
import threading


DIGITIZER_SLOT = 6
DIGITIZER_CHANNELS = [2,3]
AWG_SLOT = 8
AWG_CHANNEL = 4

AWG_DELAYS = [0e-9, 0E-09]
DIGITIZER_DELAY = 0e-9

PULSE_WIDTH = 5E-06
CAPTURE_WIDTH = 200E-06
CARRIER_FREQUENCIES = [10E+06, 20E+6]

PRI = 500.0E-6
NUMBER_OF_PULSES = 1000

PULSES_TO_PLOT = 0

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


def getData(pipe, event, pulses):
    """Get Data from digitizer."""
    logging.info("Started getData")
    start_time = time.time()
    for pulse in range(pulses):
        samples = dig.get_data_raw()
#        logging.info("GetData retrieved: %d", len(samples))
        pipe.put(samples)
    end_time = time.time()
    elapsed = end_time - start_time
    samplesProcessed = (pulses * len(samples[0]) * len(samples))
    logging.info ("getData processed %d Msamples in %f s", samplesProcessed / 1e6, elapsed)
    logging.info("getData rate: {}Msa/s in lumps of {} samples".format(samplesProcessed / elapsed / 1e6, dig._pointsPerCycle))


def processData(pipe, event, pulses):
    """Pretend we're saving samples to the database."""
    logging.info("Started processData")
    start_time = time.time()
    for pulse in range(pulses):
        samples = pipe.get()
#        time.sleep(0.001)
    end_time = time.time()
    elapsed = end_time - start_time
    samplesProcessed = (pulses * len(samples[0]) * len(samples))
    logging.info ("processData processed %d Msamples in %f s", samplesProcessed / 1e6, elapsed)
    logging.info("processData rate: {}Msa/s in lumps of {} samples".format(samplesProcessed / elapsed / 1e6, dig._pointsPerCycle))


if (__name__ == '__main__'):
    setup_logging()

    # Create a simple pulse of carrier
    t = timebase(0, PULSE_WIDTH, 1e+09)
    waves = []
    for carrier in CARRIER_FREQUENCIES:
        wave = np.sin(hertz_to_rad(carrier) * t)
        wave = np.concatenate([wave, np.zeros(100)])
        waves.append(wave)

    awg_h = awg.open(AWG_SLOT, AWG_CHANNEL)
    dig_h = dig.open(DIGITIZER_SLOT, DIGITIZER_CHANNELS, CAPTURE_WIDTH)

#    awg.loadWaveform(waves[0], AWG_DELAYS[0])
    awg.loadWaveforms(waves, AWG_DELAYS)
    dig.digitize(DIGITIZER_DELAY, NUMBER_OF_PULSES)

    hvi_path = os.getcwd() + '\\SyncStartRepeated.hvi'
    hvi_mapping = {'AWG': awg_h, 'DIG': dig_h}
    hvi.init(hvi_path, hvi_mapping)

    hvi.start(NUMBER_OF_PULSES, PRI)

    # Allow the memory to partially fill.
    time.sleep(PRI * NUMBER_OF_PULSES / 100)
    log.info("Reading Waveforms....")

    pipeline = queue.Queue(maxsize=0)
    event = threading.Event()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(getData, pipeline, event, NUMBER_OF_PULSES)
        executor.submit(processData, pipeline, event, NUMBER_OF_PULSES)

        time.sleep(10)
        logging.info("Main: about to set event")
        event.set()
        logging.info("main thread event: {}".format(event.is_set()))
    hvi.close()
    dig.close()
    awg.close()
