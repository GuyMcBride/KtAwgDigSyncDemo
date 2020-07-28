# -*- coding: utf-8 -*-
"""
Created on Sat Feb  1 16:05:29 2020

functions that support the generation of pulsed waveforms targeted at the 
M8195A

@author: gumcbrid
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy import io as sio
from collections import namedtuple as namedtuple

Waveform = namedtuple('Waveform', 'wave, timebase')


def timebase(start, stop, sample_rate):
    start_sample = int(start * sample_rate)
    stop_sample = int(stop * sample_rate)
    timebase = np.arange(start_sample, stop_sample)
    timebase = timebase / sample_rate
    return(timebase)


def filterWave(sampleRate, bandwidth, wave):
    superRate = 10 * sampleRate
    nyquist = superRate / 2
    cutoff = bandwidth / nyquist
    b, a = signal.bessel(4, cutoff, 'low')
    filtered = signal.filtfilt(b, a, wave)
    return (filtered)


def createIdealPulseTrain(sampleRate, pulseWidth, repRate, pulseTrain):
    # Create a window of samples based on the PRI. This is a ' 10x super sampled'
    # timebase to allow more accurate edge placement. It is later downsampled
    # to the actual sample rate of the AWG
    superRate = 10 * sampleRate
    t = timebase(0, repRate * len (pulseTrain), superRate)
    wave = np.full(len(t), 0.0, dtype=float)
    for pulse in range(len(pulseTrain)):
        if pulseTrain[pulse] == 1:
            start = int(pulse * repRate * superRate)
            end = int(start + pulseWidth * superRate)
            wave[start : end] = 1.0
    return(wave)


def createPulseTrain(sampleRate, pulseWidth, repRate, pulseTrain, bandwidth):
    wave = createIdealPulseTrain(sampleRate, pulseWidth, repRate, pulseTrain)
    filteredWave = filterWave(sampleRate, bandwidth, wave)
    awgWave = signal.decimate(filteredWave, 10)
    t = timebase(0, len(awgWave) / sampleRate, sampleRate)
    return Waveform(awgWave, t)


def createPulse(sampleRate, pulseWidth, bandwidth):
    superRate = 20 * sampleRate
    # We need to create a significantly larger wave than the pulse width to
    # allow for the 'lead in' and 'lead out' of the 'shaped' waveform
    leadIn = 0.45 / bandwidth
    leadInSamples = int(leadIn * superRate)
    wave = np.concatenate([np.zeros(leadInSamples), 
                           np.ones(int(pulseWidth * superRate)), 
                           np.zeros(leadInSamples)])
    filteredWave = filterWave(sampleRate, bandwidth , wave)
    awgWave = signal.decimate(filteredWave, 10)
    t = np.arange(0, len(awgWave))
    t = t / sampleRate
    return Waveform(awgWave, t)


def createTone(sampleRate, frequency, phase, timebase):
    wave = np.sin((frequency * 2 * np.pi * timebase) + (phase * np.pi / 180))
    return wave


def createCsv(sampleRate, filename, wave):
    rpts = int(np.lcm(len(wave), 128)/len(wave))
    f = open (filename, 'w')
    f.write("SampleRate={}\n".format(int(sampleRate)))
    f.write("SetConfig=true\n")
    f.write("Y1\n")
    for sample in np.tile(wave, rpts):
        f.write("{}\n".format(sample))
    f.close()


def createMat(sampleRate, filename, wave):
    rpts = int(np.lcm(len(awgWave), 128)/len(awgWave))
    XDelta = 1 / sampleRate
    
    matparams = {'InputZoom':[[1]], 
                 'XDelta':XDelta, 
                 'XStart':[[0]], 
                 'Y': np.tile(wave, rpts)}
    sio.savemat(filename, matparams)

######################################################
# MAIN!!!!!
######################################################

if (__name__ == '__main__'):
    SAMPLE_RATE = 1e+09
    SYSTEM_BANDWIDTH = 1E+06
    
    WIDTH = 1e-6
    PRI = 100e-6
    PULSE_TRAIN = [0, 1, 1, 1, 0, 0, 1, 1, 0]   # Relative to time = 0. We need some lead-in time for the pulse shaping
    
#    waveform = createPulseTrain(SAMPLE_RATE, WIDTH, PRI, PULSE_TRAIN, SYSTEM_BANDWIDTH)
#    wave = waveform.wave
#    t = waveform.timebase
#    tone = createTone(SAMPLE_RATE, 10E6, 0, t)
#    rfWave = wave * tone
    
    pulse = createPulse(SAMPLE_RATE, WIDTH, SYSTEM_BANDWIDTH)
    
    
#    plt.plot(t, wave) 
#    plt.plot(t, rfWave)

    plt.plot(pulse.timebase, pulse.wave)