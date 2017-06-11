# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 16:29:00 2013

@author: j.gawith
"""

import sourcebase

import visa2 as visa
#import gtk
from utilities import *
from measurement import *
import sys

# DC offset constants. Updated 03/10/2015. TJS.

_V6105A_23 = [-0.000887,-0.001539,-0.001082]
_V6105A_45 = [-0.001727,-0.003393,-0.002174]
_V6105A_90 = [-0.006556,-0.011145,-0.007825]
_V6105A_180 = [-0.012757,-0.020953,-0.014605]
_V6105A_360 = [-0.019983,-0.034608,-0.023033]
_V6105A_650 = [-0.024016,-0.050580,-0.032330]
_V6105A_1008 = [-0.021451,-0.058428,-0.033978]

_I6105A_025 = [0.000018,0.000020,0.000022]
_I6105A_05 = [0.000039,0.000038,0.000040]
_I6105A_1 = [0.000077,0.000068,0.000080]
_I6105A_2 = [0.000149,0.000141,0.000157]
_I6105A_5 = [0.000407,0.000366,0.000405]
_I6105A_10 = [0.000961,0.001067,0.000970]
_I6105A_21 = [0.002033,0.001931,0.002108]

_52120A_2 = [0.000065,-0.000173,-0.000300]
_52120A_20 = [0.000524,-0.001950,-0.003208]
_52120A_120 = [0.001894,0.006345,0.000750]


class FLUKE (sourcebase.SourceBase):
    def __init__ (self, address="GPIB::17"):
        rm = visa.ResourceManager()
        self.interface = rm.open_resource(address)
        #self.interface = visa.instrument (address)
        self.interface.timeout = 10
        self.mtype = MeasurementType.SinglePhase1
        self.use_52120A = [1,1,1]   #Use current amp on chanel 1,2,3? 0=NO, 1=YES
        self.high_current_setting = [0,0,0] #0=AUTO, 1=HIGH
        self.v1 = 0
        self.v2 = 0
        self.v3 = 0
        self.i1 = 0
        self.i2 = 0
        self.i3 = 0
        self.current = 0
        self.voltage_dc_offset = [0,0,0]
        self.current_dc_offset = [0,0,0]
        self.phase = 0
        self.frequency = 0

    def set_frequency (self, f):
        if f>60 or f<40:
                raise Exception("Frequency out of range")
        self.frequency = f
    def set_phase (self, phi):
        if abs(phi)>360:
            raise Exception("Phase angle out of range")
        if abs(phi)>180:
            if phi>0:
                phi = phi - 360
            else:
                phi = phi + 360
        self.phase = phi

    def set_current (self, i1, i2=None, i3=None):
        self.i1 = i1
        self.i2 = i2
        self.i3 = i3

    def set_voltage (self, v1, v2=None, v3=None):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

    def _set_high_current_range(self,currenta):
        current = float(currenta)
        if current < 0:
            raise Exception("Current must be positive")
        if current <= 1.999:
            high_current_range = 2.0
            self.current_dc_offset = _52120A_2
        elif current <= 19.99:
            high_current_range = 20.0
            self.current_dc_offset = _52120A_20
        elif current <= 119.99:
            high_current_range = 120.0
            self.current_dc_offset = _52120A_120
        else:
            raise Exception("Current above 120A")
        return high_current_range

    def _set_current_range (self, current):
        if current < 0:
            raise Exception("Current must be positive")
        if current <= 0.249:
            current_range_low = 0.05
            current_range_high = 0.25
            self.current_dc_offset = _I6105A_025
        elif current <= 0.499:
            current_range_low = 0.05
            current_range_high = 0.5
            self.current_dc_offset = _I6105A_05
        elif current <= 0.999:
            current_range_low = 0.1
            current_range_high = 1
            self.current_dc_offset = _I6105A_1
        elif current <= 1.999:
            current_range_low = 0.2
            current_range_high = 2
            self.current_dc_offset = _I6105A_2
        elif current <= 4.999:
            current_range_low = 0.5
            current_range_high = 5
            self.current_dc_offset = _I6105A_5
        elif current <= 9.99:
            current_range_low = 1
            current_range_high = 10
            self.current_dc_offset = _I6105A_10
        elif current <= 20.99:
            current_range_low = 2
            current_range_high = 21
            self.current_dc_offset = _I6105A_21
        else:
            raise Exception("Current above 21A, please use 52120A high current option")
        return current_range_high,current_range_low

    def _set_voltage_range (self, voltage):
        limit = 600
        if self.frequency*10 < limit:
            limit = self.frequency*10
        if voltage < 0:
            raise Exception("Voltage must be positive")
        if voltage <= 23.0:
            voltage_range= 23
            self.voltage_dc_offset = _V6105A_23
        elif voltage <= 45.0:
            voltage_range= 45
            self.voltage_dc_offset = _V6105A_45
        elif voltage <= 90.0:
            voltage_range= 90
            self.voltage_dc_offset = _V6105A_90
        elif voltage <= 180:
            voltage_range= 180
            self.voltage_dc_offset = _V6105A_180
        elif voltage <= 360:
            voltage_range= 360
            self.voltage_dc_offset = _V6105A_360
        elif voltage <= limit:
            voltage_range = 650
            self.voltage_dc_offset = _V6105A_650
        else:
            raise Exception("Voltage above RD31 voltage limit")
        return voltage_range

    def _setup_chanel(self, phase_num,voltage,voltage_phase,current,current_phase):
        fitted = self.interface.query ("SOUR:PHAS%i:FITT?" %phase_num)
        if fitted == "0":
            raise Exception("Phase %i not fitted" %phase_num)
        voltage_range = self._set_voltage_range(voltage)
        if self.use_52120A[phase_num - 1] == 0:
            current_range_high,current_range_low = self._set_current_range(current)
        else:
            high_current_range = self._set_high_current_range(current)
        #current_offset = self.current_dc_offset

        self.interface.write ("SOUR:PHAS%i:VOLT:RANG %f,%f" %(phase_num,0,voltage_range))
        self.interface.write ("SOUR:PHAS%i:VOLT:MHAR:HARM1 %f,%f" %(phase_num,voltage,voltage_phase))
        self.interface.write ("SOUR:PHAS%i:VOLT:MHAR:HARM0 %f,%f" %(phase_num,self.voltage_dc_offset[phase_num-1],0))
        if self.use_52120A[phase_num - 1] == 0:
            self.interface.write ("SOUR:PHAS%i:CURR:RANG %f,%f" %(phase_num,current_range_low,current_range_high))
        else:
            eamp = self.interface.query("SOUR:PHAS%i:CURR:EAMP:FITT?" %phase_num)
            if eamp == "0":
                raise Exception("52120 not fitted on phase %i" %phase_num)
            if self.high_current_setting[phase_num - 1] == 0:
                self.interface.write ("SOUR:PHAS%i:CURR:EAMP:TERM:MODE AUTO" %phase_num)
            else:
                self.interface.write ("SOUR:PHAS%i:CURR:EAMP:TERM:MODE HIGH" %phase_num)
            self.interface.write ("SOUR:PHAS%i:CURR:EAMP:RANG 0,%f" %(phase_num,high_current_range))
        self.interface.write ("SOUR:PHAS%i:CURR:MHAR:HARM1 %f,%f" %(phase_num,current,current_phase))
        self.interface.write ("SOUR:PHAS%i:CURR:MHAR:HARM0 %f,%f" %(phase_num,self.current_dc_offset[phase_num-1],0))

    def set_mode (self, mtype):
        self.mtype = mtype
        if mtype == MeasurementType.SinglePhase1:
            self._enable_chanels(1,1,0,0,0,0)
        elif mtype == MeasurementType.SinglePhase2:
            self._enable_chanels(0,0,1,1,0,0)
        elif mtype == MeasurementType.SinglePhase3:
            self._enable_chanels(0,0,0,0,1,1)
        else:
#           if  mtype == MeasurementType.Delta:        # 31/7/14 - added Delta which was previously missing.
#               self._enable_chanels(1,1,1,0,1,1)
            if  mtype == MeasurementType.DeltaPhase1:
                self._enable_chanels(1,1,1,0,1,0)
            elif mtype == MeasurementType.DeltaPhase2:
                self._enable_chanels(1,0,1,1,1,0)
            elif mtype == MeasurementType.DeltaPhase3:
                self._enable_chanels(1,0,1,0,1,1)
            elif mtype == MeasurementType.DeltaPhase12:
                self._enable_chanels(1,1,1,1,1,0)
            elif mtype == MeasurementType.DeltaPhase23:
                self._enable_chanels(1,0,1,1,1,1)
            elif mtype == MeasurementType.DeltaPhase31:
                self._enable_chanels(1,1,1,0,1,1)
            else:
                self._enable_chanels(1,1,1,1,1,1)

    def _enable_chanels(self,V1,I1,V2,I2,V3,I3):
        fitt1 = self.interface.query ("SOUR:PHAS1:FITT?")
        fitt2 = self.interface.query ("SOUR:PHAS2:FITT?")
        fitt3 = self.interface.query ("SOUR:PHAS3:FITT?")
        if  fitt1 == "1":
            self.interface.write ("SOUR:PHAS1:VOLT:MHAR:STAT %i" %V1)
            self.interface.write ("SOUR:PHAS1:CURR:MHAR:STAT %i" %I1)
            self.interface.write ("SOUR:PHAS1:VOLT:STAT %i" %V1)
            self.interface.write ("SOUR:PHAS1:CURR:STAT %i" %I1)
        if  fitt2 == "1":
            self.interface.write ("SOUR:PHAS2:VOLT:MHAR:STAT %i" %V2)
            self.interface.write ("SOUR:PHAS2:CURR:MHAR:STAT %i" %I2)
            self.interface.write ("SOUR:PHAS2:VOLT:STAT %i" %V2)
            self.interface.write ("SOUR:PHAS2:CURR:STAT %i" %I2)
        if  fitt3 == "1":
            self.interface.write ("SOUR:PHAS3:VOLT:MHAR:STAT %i" %V3)
            self.interface.write ("SOUR:PHAS3:CURR:MHAR:STAT %i" %I3)
            self.interface.write ("SOUR:PHAS3:VOLT:STAT %i" %V3)
            self.interface.write ("SOUR:PHAS3:CURR:STAT %i" %I3)

    def _error_check (self):
        error = self.interface.query ("SYST:ERR?")
        if error[0] <> "0":
            raise Exception("Fluke error", error)

    def start (self):
        if self.mtype == MeasurementType.SinglePhase1:
            self._setup_chanel(1,self.v1,0,self.i1,self.phase)
        elif self.mtype == MeasurementType.SinglePhase2:
            self._setup_chanel(2,self.v2,-120,self.i2,self.phase)
        elif self.mtype == MeasurementType.SinglePhase3:
            self._setup_chanel(3,self.v3,120,self.i3,self.phase)
        else:
            self._setup_chanel(1,self.v1,0,self.i1,self.phase)
            self._setup_chanel(2,self.v2,-120,self.i2,self.phase)
            self._setup_chanel(3,self.v3,120,self.i3,self.phase)
        self.interface.write ("SOUR:FREQ %f" %self.frequency)
        self._error_check()
        self.interface.write ("OUTP:STAT ON")
        sleep(5)
        on = self.interface.query("OUTP:STAT?")
        if on == "0":
            raise Exception("Power not on, check connections")
        sleep (30) # Neccessary settling time

    def stop (self):
        self.interface.write ("OUTP:STAT OFF")

    def initialise (self,time=5):
        self.stop ()
        self.interface.write ("*CLS")
        self.interface.write ("*RST")
        self.interface.write ("OUTP:SENS 0")
        self.interface.write ("OUTP:RAMP:TIME {}".format(time))

    def _use_52120A(self,use_52120A):
        self.use_52120A = use_52120A

    def _high_current_setting(self,high_current_setting):
        self.high_current_setting = high_current_setting

    def shutdown (self):
        self.stop ()




def test ():
    print "TEST"
    fluke = FLUKE(address='ASRL1::INSTR')
    fluke.initialise ()
    fluke.set_mode (MeasurementType.FourWireStar)
    fluke._use_52120A([1,1,1])
    fluke._high_current_setting([0,0,0])
    fluke.set_frequency (50)
    fluke.set_phase (0)
    fluke.set_voltage (63.5, 0, 0)
    fluke.set_current (5,0,0)
    fluke.start ()
    sleep (65)
    fluke.stop ()
    fluke.shutdown ()

if __name__ == "__main__":
    test ()
