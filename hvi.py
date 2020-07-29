# -*- coding: utf-8 -*-
"""
Created on Thu May 23 09:46:33 2019

@author: gumcbrid
"""

import logging
import sys
import time
sys.path.append('C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
import keysightSD1 as key

__log = logging.getLogger(__name__)

__hvi = key.SD_HVI()

class HviError(Exception):
    """Basic exception for errors raised by HVI"""
    _error = None
    _message = None
    def __init__(self, error, msg=None):
        if msg is None:
            msg = "An error occured with HVI: {}".format(key.SD_Error.getErrorMessage(error))
        super(HviError, self).__init__(msg)
        self._error = error
    @property
    def error_message(self):
        return key.SD_Error.getErrorMessage(self._error)
    

def __compile_download():
    __log.info("Compiling HVI...")
    cmpID = __hvi.compile()
    if cmpID != 0:
        error = "HVI compile failed : {}".format(key.SD_Error.getErrorMessage(cmpID))
        __log.debug(error)
        raise HviError(cmpID, error)
    __log.info("Loading HVI...")
    cmpID = __hvi.load()
    if cmpID == -8038:
        __log.debug("HVI contains Demo Module. Please make sure you do an assignHW()")
    elif cmpID != 0:
        error = "HVI load failed : {}".format(key.SD_Error.getErrorMessage(cmpID))
        __log.error(error)
        raise HviError(cmpID, error)
        
def init(hviFileName, mapping):
    __log.info("Opening HVI file: {}".format(hviFileName))
    hviID = __hvi.open(hviFileName)
    if hviID ==  key.SD_Error.RESOURCE_NOT_READY: #Only for old library
        __log.debug("No Critical Error - {}: {}".format(hviID, key.SD_Error.getErrorMessage(hviID)))
        __log.debug("Using old library -> Need to compile HVI...")
    elif hviID == key.SD_Error.DEMO_MODULE: #Only for old library
        __log.debug("No Critical Error - {} {}".format(hviID, key.SD_Error.getErrorMessage(hviID)))
        __log.debug("Using old library -> need to assigning HW modules...")
    elif hviID < 0:
        __log.error("Opening HVI - {}: {}".format(hviID, key.SD_Error.getErrorMessage(hviID)))
        raise HviError(hviID, "Opening HVI - {}: {}".format(hviID, key.SD_Error.getErrorMessage(hviID)))
        
    for (module_name, module_id) in mapping.items():
        __log.info("Assigning {} to {} in slot {}".format(module_name, module_id.getProductName(), module_id.getSlot()))
        error = __hvi.assignHardwareWithUserNameAndModuleID(module_name, module_id)
        if error == -8069:
            __log.debug("Assigning HVI {}, Spurious Error- {}: {}".format(module_name, error, key.SD_Error.getErrorMessage(error)))
            __log.info("HVI HW assigned for {}, {} in slot {}".format(module_name, module_id.getProductName(), module_id.getSlot()))
        elif error < 0:
            error_msg = "HVI assign HW AOU Failed for: {}, {}: {}".format(
                    module_name, 
                    module_id,
                    key.SD_Error.getErrorMessage(error))
            __log.error(error_msg)
            raise HviError(error, error_msg)
        else:
            __log.info("HVI HW assigned for {}, {} in slot {}".format(module_name, module_id.getProductName(), module_id.getSlot()))
    # if the last module assigned has this error then it is more serious
    if error == -8069:
        __log.error("Assigning HVI - {}: {}".format(error, key.SD_Error.getErrorMessage(error)))
#        raise HviError(error)
    __compile_download()
            
def setupConstants(number_pulses = 1, pri = 0):
    # There is 280ns of intrinsic 'gap' in the HVI loop.
    gap = pri - 280e-09
    if gap < 0: gap = 0
    error = __hvi.writeDoubleConstantWithUserName('AWG0', 'GapTime', gap, 's')
    if (error < 0):
        __log.warning("Writing AWG0 GapTime - {}: {}".format(error, key.SD_Error.getErrorMessage(error)))
    error = __hvi.writeIntegerConstantWithUserName('AWG0', 'NumberOfPulses', number_pulses)
    if (error < 0):
        __log.warning("Writing AWG0 NumberOfPulses - {}: {}".format(error, key.SD_Error.getErrorMessage(error)))
    __compile_download()    # This necessary when Constants are changed

def start():
    __log.info("Starting HVI...")
    error = __hvi.start()
    if (error < 0):
        __log.error("Starting HVI- {}: {}".format(error, key.SD_Error.getErrorMessage(error)))
        
def close():
    error  = __hvi.releaseHW()
    if (error < 0):
        __log.error("Releasing HW - {}: {}".format(error, key.SD_Error.getErrorMessage(error)))
    error = __hvi.close()
    if (error < 0):
        __log.error("Closing HVI - {}: {}".format(error, key.SD_Error.getErrorMessage(error)))
