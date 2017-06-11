#
# Copyright (C) 2006 Industrial Research Limited
#

#
# An abstract base class for a source. This is just a way of defining
# the interface.
#

from measurement import *

class SourceBase:
    """A basic source of voltage and current."""
    def set_frequency (self, f):
        """Sets the frequency of all outputs."""
        raise NotImplemented
    def set_phase (self, phi):
        """Sets the phase relationship between voltage and current outputs."""
        raise NotImplemented
    def set_voltage (self, v1, v2=None, v3=None):
        """Sets the voltage outputs. If possible this should avoid
        actually applying the potentials"""
        raise NotImplemented
    def set_current (self, i1, i2=None, i3=None):
        """Sets the current outputs. If possible this should avoid
        actually applying the currents."""        
        raise NotImplemented
    def set_mode (self, mtype):
        """Sets the measurement mode."""
        raise NotImplemented
    def start (self):
        """Apply the pre-set voltages and currents at the outputs."""
        raise NotImplemented
    def stop (self):
        """Stop applying the pre-set voltages and currents. This
        should place the device into a safe state."""
        raise NotImplemented
    def initialise (self):
        """Perform set-up work. The outputs should not be live."""
        raise NotImplemented
    def shutdown (self):
        """The complement of initialise. As with stop it should place
        the device into a safe state."""
        raise NotImplemented
    def set (self, measurement):
        """Take a measurement and set the device up ready to perform it."""
        self.set_mode (measurement.mtype)
        self.set_frequency (measurement.f)
        self.set_phase (measurement.theta)
        self.set_voltage (*measurement.V)
        self.set_current (*measurement.I)

