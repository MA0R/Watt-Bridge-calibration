#
# Copyright (C) 2006 Industrial Research Limited
#

#
# Code to directly connect to the RD-31, bypassing the RRKit DLL.
#

import serial
from struct import *

from results import *
from utilities import *
from measurement import MeasurementType

import meterbase

# Metric function codes
_RAD_INST_V = 0
_RAD_INST_A = 1
_RAD_INST_W = 2
_RAD_INST_VA = 3
_RAD_INST_VAR = 4
_RAD_INST_FREQ = 5
_RAD_INST_PHASE = 6
_RAD_INST_PF = 7
_RAD_INST_ANS = 8
_RAD_INST_DPHASE = 9
_RAD_INST_V_DELTA = 10
_RAD_INST_W_DELTA = 11
_RAD_INST_VA_DELTA = 12
_RAD_INST_VAR_DELTA = 13
_RAD_INST_VAR_WYE_XCONNECTED = 14
_RAD_INST_VAR_DELTA_XCONNECTED = 15

# Note: This does not handle NaN and other edge-cases.
def TItofloat (TIfloat):
    """Convert a TI format floating point number to a native one."""
    exponent = (TIfloat >> 24) & 0xff
    if exponent == 128:
        exponent = 0
    if exponent > 128:
        exponent -= 256
    signbit = (TIfloat >> 23) & 1
    sign = 1.0 + -2.0*signbit
    mantissa_bits = TIfloat & 0x7fffff
    if mantissa_bits == 0:
        mantissa = 0.0
    else:
        if sign > 0:
            mantissa = 1.0 + mantissa_bits/(2.0**23)
        else:
            mantissa = -2 + mantissa_bits/(2.0**23)
    return mantissa*(2.0**exponent)
    

class RD31Error (Exception):
    def __init__ (self, errorcode=-1):
        self.errorcode = errorcode
    def __str__ (self):
        return "RD-31 Error: 0x%x" % self.errorcode

class RD31AutocalError (Exception):
    def __init__ (self, channel):
        self.channel = channel
    def __str__ (self):
        return "RD-31 Autocal Error on Channel %d" % self.channel

class RD31 (meterbase.MeterBase):
    
    # Initilisation and clean-up routines
    def __init__ (self, port="COM7"):
        self.port = serial.Serial (port, 57600)
        self.port.setTimeout (1)
        self.mtype = MeasurementType.FourWireStar
    def __del__ (self):
        self.port.close ()
        
    # Low-level packet formatting and I/O routines
    def _receive_packet (self):
        """Receive and extract the data from a packet from the RD-31"""
        header = self.port.read(2)
        (packet_phaseack, packet_type) = unpack (">BB", header)
        packet_ack = packet_phaseack & 0x0f
        packet_phase = packet_phaseack >> 4
        checksum = packet_type + packet_phaseack
        delay = 0
        if packet_ack == 0xc:
            payload = self.port.read (4)
            (dummy1, delay) = unpack (">HH", payload)
            checksum += sum (unpack ("B"*len(payload), payload))
            data = ""
        if packet_ack == 9:
            print "packet ack is 9, phase & type is: ", packet_phase, packet_type
            (dummy1, errorcode, dummy2) = unpack (">HHH", self.port.read (6))
            raise RD31Error, errorcode
        if packet_ack == 6:
            (length,) = unpack (">H", self.port.read (2))
            checksum += (length & 0xff) + (length >> 8)
            data = self.port.read (length)
            checksum += sum (unpack ("B"*length, data))
        if packet_ack == 3:
            data = ""
        trailer = self.port.read(2)
        (packet_checksum,) = unpack (">H", trailer)
        if checksum != packet_checksum:
            raise IOError
        sleep (delay/1000.0)
        return data
    def _send_packet (self, packet_type, phase, data = ""):
        """Construct and send a packet to the RD-31"""
        phase = phase*0xf + 0xa6
        length = len(data)
        checksum = packet_type + phase
        checksum += (length & 0xff) + (length >> 8)
        checksum += sum (unpack ("B"*length, data))
        header = pack (">BBH", phase, packet_type, length)
        trailer = pack (">H", checksum)
        output = header + data + trailer
        self.port.write (output)
    def ask (self, packet_type, phase, data=""):
        """Send a command to the RD-31 and return the response."""
        p_type = packet_type
        try:
            self._send_packet (packet_type, phase, data)
            return self._receive_packet ()
        except RD31Error, errorno:
            print str(errorno)
            if str(errorno).endswith("0x2"): # Checksum error at the far end
                print "Checksum error detected - retrying."
                print "packet type, phase and data is: ", packet_type, phase, data
                print "p_type is: ", p_type
                self.ask (p_type, phase, data) # Re-send
            else:
                raise

    # High-level routines
    def set_current_range (self, current):
        pass # We don't have user-settable current ranges.
    def set_voltage_range (self, voltage):
        pass # We don't have user-settable voltage ranges.
    def set_measurement_type (self, mtype):
        self.mtype = mtype
        
    def _get_metric (self, function):
        outdata = pack (">HH", function, 0xfffd)
        indata = self.ask (0x2E, 0, outdata)
        (dataA, dataB, dataC, dataNet, dummy) = unpack (">IIIII", indata)
        return (TItofloat (dataA), TItofloat (dataB), TItofloat (dataC), TItofloat (dataNet),)
    def _get_metric_list (self, function, phases):
        values = self._get_metric (function)
        try:
            result = [ values[x - 1] for x in phases ]
        except TypeError: # i.e. we were given a scalar for phases
            result = values[phases - 1]
        return result
    def _choose_from_type (self, a, b):
        """The choice of RD-31 function often depends on whether we are doing a delta or star
        measurement (single phase is handled elsewhere). This function is a convenience function
        to handle this common case."""
        if self.mtype in MeasurementType.DeltaMeasurements:
            return a    # Measurements Oct2012, the RD31 is connected star (2 Wattmeter mode) so return star measurement type.
        else:
            return a

    def get_voltage (self, phases = (1, 2, 3)):
        fn = self._choose_from_type (_RAD_INST_V, _RAD_INST_V_DELTA)
        return self._get_metric_list (fn, phases)
    def get_current (self, phases = (1, 2, 3)):
        return self._get_metric_list (_RAD_INST_A, phases)
    def get_phase (self, phases = (1, 2, 3)):
        fn = self._choose_from_type (_RAD_INST_PHASE, _RAD_INST_DPHASE)
        ph = self._get_metric_list (fn, phases)
        # Correct the phase convention
        try:
            return [ -x for x in ph ] 
        except TypeError:
            return -ph
    def get_active_power (self, phases = (1, 2, 3)):
        fn = self._choose_from_type (_RAD_INST_W, _RAD_INST_W_DELTA)        
        return self._get_metric_list (fn, phases)
    def get_reactive_power (self, phases = (1, 2, 3)):
        fn = self._choose_from_type (_RAD_INST_VAR, _RAD_INST_VAR_DELTA)
        return self._get_metric_list (fn, phases)
    def get_total_active_power (self):
        return sum (self.get_active_power ((1, 2, 3)))
    def get_total_reactive_power (self):
        return sum (self.get_reactive_power ((1, 2, 3)))
    def get_apparent_power (self, phases = (1, 2, 3)):
        fn = self._choose_from_type (_RAD_INST_VA, _RAD_INST_VA_DELTA)
        return self._get_metric_list (fn, phases)
    def get_frequency (self, phases = None):
        if phases == None:
            # We assume that the frequency is the same for all channels
            # and pick a representative one by default.
            phases = 1
            # Since the RD-31 measures the frequency on all phases
            # independently we have to do some fixing up if the measurement
            # is single phase.            
            if self.mtype == MeasurementType.SinglePhase2:
                phases = 2
            if self.mtype == MeasurementType.SinglePhase3:
                phases = 3
        return self._get_metric_list (_RAD_INST_FREQ, phases)
    def get_all_metric (self, phases = (1, 2, 3, 4)):
        data = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        for fn in range(16):
            data[fn] = self._get_metric_list (fn, phases)
        return data
    def autocal (self):
        self.ask (0x1b, 0, "\x00")
        self.ask (0x1b, 0, "\x01")
        self.ask (0x07, 0, "\x0c")
        sleep (3)
        # We could check for autocal errors in here, but we don't (nor
        # does the Radian software).
    def reset (self):
        """Reboot the RD-31."""
        self.ask (0x03, 0)
    def initialise (self):
        pass
    def shutdown (self):
        pass

if __name__ == "__main__":
    
    def test ():
        try:
            rd31 = RD31 ("COM7")
##        for x in range (0, 10):
##            for v in rd31.get_current ((1, 2, 3)):
##                print v,
##                print
##                sleep (1)        
##                rd31.autocal ()
##                for x in range (0, 10):
##                    for v in rd31.get_current ((1, 2, 3)):
##                        print v,
##                        print
##                        sleep (1)
        #print rd31.ask (2, 0)
#            for x in range (0, 3):
#                print rd31.get_voltage ((1, 2, 3))
#                print rd31.get_current ((1, 2, 3))
            print rd31.get_phase (3)
#               print rd31.get_phase (1)
#               print rd31.get_frequency ((1, 2, 3))
            a = rd31.get_total_active_power()
#             print rd31.get_total_reactive_power()
            sleep(9)
            b = rd31.get_total_active_power()
#             print rd31.get_total_reactive_power()
            sleep(9)
            c = rd31.get_total_active_power()
#             print rd31.get_total_reactive_power()
            print a, b, c
            #            rd31.get_all_metric()
            sleep(.5)
        except:
            rd31.port.close()
            raise
                        
    test ()
