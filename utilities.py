#!/usr/bin/env python
#
# Copyright (C) 2006 Industrial Research Limited
#
#
# Utility routines with no other obvious place (yet!).
# See individual docstrings for the details.

import os
import time
#import gobject
#import gtk

def file_in_same_place (file1, file2):
    """Return the name of file2 with file1's path. Used for
    locating files in the same path as another file."""
    directory = os.path.dirname (os.path.abspath (file1))
    name = os.path.basename (file2)
    return os.path.join (directory, name)

def sleep (t):
    """Fake the traditional sleep call, by inserting a time-out in
    the gtk event stream. From the point of view of the calling  code
    execution appears to be suspended for t seconds, but normal events
    (for windows and the like) keep being called. Nesting this call
    can produce *intersting* results, so it shouldn't be called from
    normal event handlers."""
    gobject.timeout_add (int (t*1000), gtk.main_quit)
    gtk.main ()

def timestamp ():
    """Get the current time as a string in our traditional format."""
    return time.strftime ("%d/%m/%y %H:%M:%S")

def _add_ppm (a, ppm):
    """An internal helper function - see add_ppm."""
    return a*(1.0 + ppm/1.0e6)

def add_ppm (a, ppm):
    """Return a increased by ppm parts per million. This will
    work for both scalars and lists in the obvious manner."""
    try:
        result = []
        for x, y in zip (a, ppm):
            result.append (_add_ppm (x, y))
        return result
    except:
        return _add_ppm (a, ppm)

def ppm_error (a, b):
    """Calculate pairwise differences of values from a and b in
       ppm form. Works for scalars, lists and lists of lists.
       If a > b the result is negative, i.e. it is the error
       of b with respect to a."""
    try:
        result = []
        for x, y in zip (a, b):
            result.append (ppm_error (x, y))
        return result
    except:
        try:
            return 1.0e6*(1.0 - a/b)
        except ZeroDivisionError:
            return 1e6 # Not accurate, but by that stage you don't care.

class dummy_device:
    """A generic object that we can use to get things running,
       but doesn't do any actual work. It will produce a result 
       (of NoneType) for any method call. Don't do anything that
       expects a result of a particular type - especially print."""
    log = False
    def dummy_method(self, *args):
        """The do-nothing method which we use regardless of the
        method called. Returns NoneType."""
        pass
    def __getattr__ (self, name):
        """Fake all method calls with the dummy_method."""
        if dummy_device.log:
            print "%s called." % name
        return self.dummy_method

if __name__ == '__main__':
    # Not proper tests since you have to check the results by eye, but a start.
    print add_ppm (10.0, 10.0) - 10.0
    a = [10.0, 5.0, 1.0]
    b = add_ppm (a, a)
    print a, b, ppm_error (a, b)
    print ppm_error (1.0, 1.0001)
    print timestamp ()
    sleep (10)
    print timestamp ()
    a = dummy_device ()
    a.shouldntbreak ()
