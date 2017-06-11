#
# Copyright (C) 2005 Industrial Research Limited
#
#
# Data structures for representing types of measurement
#

class MeasurementType:
    """Define identifiers for the various types of measurement we perform.
    There are only three basic types, but many variations."""
    Unknown = -1
    SinglePhase1 = 0
    SinglePhase2 = 1
    SinglePhase3 = 2
    FourWireStar = 3
    ThreeWireStar = 4
    Delta = 5
    DeltaPhase1 = 6
    DeltaPhase2 = 7
    DeltaPhase3 = 8
    DeltaPhase12 = 9
    DeltaPhase23 = 10
    DeltaPhase31 = 11
    DeltaMeasurements = (Delta, DeltaPhase1, DeltaPhase2, DeltaPhase3, DeltaPhase12, DeltaPhase23, DeltaPhase31)
    labels = ["Single Phase (1)", "Single Phase (2)", "Single Phase (3)", "Four Wire Star", "Three Wire Star", "Delta", "Delta (1)", "Delta (2)", "Delta (3)", "Delta (1-2)", "Delta (2-3)", "Delta (3-1)"]

class Measurement:
    """A description of a measurement. What is requested in a measurement.
    The actual data is in a results object."""
    def __init__ (self, n, pause, V1, V2, V3, I1, I2, I3, theta, f, rangeV, rangeI, counts, mtype):
        """Initialisation is fairly direct. In the case of a single-phase
        measurement, only the appropriate phase of V or I is used."""
        self.repetitions = n
        self.pause = pause
        # Enforce the type for single-phase measurement types.
        if mtype == MeasurementType.SinglePhase1:
            self.V = [ V1, 0.0, 0.0 ]
            self.I = [ I1, 0.0, 0.0 ]            
        elif mtype == MeasurementType.SinglePhase2:
            self.V = [ 0.0, V2, 0.0 ]
            self.I = [ 0.0, I2, 0.0 ]
        elif mtype == MeasurementType.SinglePhase3:
            self.V = [ 0.0, 0.0, V3 ]
            self.I = [ 0.0, 0.0, I3 ]
        elif mtype == MeasurementType.DeltaPhase1:
            self.V = [ V1, V2, V3 ]
            self.I = [ I1, 0.0, 0.0 ]            
        elif mtype == MeasurementType.DeltaPhase2:
            self.V = [ V1, V2, V3 ]
            self.I = [ 0.0, I2, 0.0 ]
        elif mtype == MeasurementType.DeltaPhase3:
            self.V = [ V1, V2, V3 ]
            self.I = [ 0.0, 0.0, I3 ]    
        elif mtype == MeasurementType.DeltaPhase12:
            self.V = [ V1, V2, V3 ]
            self.I = [ I1, I2, 0.0 ]
        elif mtype == MeasurementType.DeltaPhase23:
            self.V = [ V1, V2, V3 ]
            self.I = [ 0.0, I2, I3 ]
        elif mtype == MeasurementType.DeltaPhase31:
            self.V = [ V1, V2, V3 ]
            self.I = [ I1, 0.0, I3 ]
        else:
            self.V = [ V1, V2, V3 ]
            self.I = [ I1, I2, I3 ]
        self.theta = theta
        self.f = f
        self.rangeV = rangeV
        self.rangeI = rangeI
        self.mtype = mtype
        self.countsperwh = counts
    def __str__ (self):
        """This format is suitable for a CSV file."""
        return "%f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %d, %d," % tuple (self.V + self.I + [self.theta, self.f, self.rangeV, self.rangeI, self.countsperwh, self.mtype])
