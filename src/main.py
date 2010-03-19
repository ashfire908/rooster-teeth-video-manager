#!/usr/bin/env python
# Rooster Teeth Video Manager
# Main program

# Import modules
import sys
import os
import types
import ConfigParser
from optparse import OptionParser

# Define static variables
default_root = (os.getcwd())


# Import the other parts of the program
# none so far

# Define Classes and Functions
class DataManager():
    def __init__(self, filename=None):
        if filename != None:
            self.loadconfig(filename)
    def _openconfig(self, filename=None, reopen=True):
        try:
            if self.configfile.closed:
                if filename != None:
                    if os.path.isfile(filename):
                        self.configfile = open(filename, "a")
                    elif os.path.isdir(os.path.dirname(filename)):
                        ErrorHandler().info_msg("Opening new config file at %s" % filename) 
                        self.configfile = open(filename, "w")
                elif reopen:
                    self.configfile = open(self.configfile.name, "a")
        except AttributeError:
            if filename != None:
                    if os.path.isfile(filename):
                        self.configfile = open(filename, "a")
                    elif os.path.isdir(os.path.dirname(filename)):
                        ErrorHandler().info_msg("Creating new config file at %s" % filename) 
                        self.configfile = open(filename, "w")
    def loadconfig(self, filename=None, setdefault=True, reopen=True):
        self._openconfig(filename, reopen)
        self.config = ConfigParser.SafeConfigParser(self._getconfigdefaults())
        self.configfile.seek(-1)
        if setdefault and self.configfile.tell() == 0:
            ErrorHandler().warn_msg("Writing config with just the default values at '%s'." % self.configfile.name)
            self.saveconfig()
        else:
            self.config.readfp(self.configfile)
    def saveconfig(self, filename=None, reopen=True):
        self._openconfig(filename, reopen)
        self.configfile.seek(0)
        self.config.write(self.configfile)
    def listsections(self):
        return self.config.sections()
    def setsettings(self, request):
        for subrequest in request:
            if len(subrequest) == 4 and self.config.has_section(subrequest[1]):
                self.config.set(subrequest[1], subrequest[2], subrequest[3])
            else:
                if len(subrequest) == 0:
                    ErrorHandler().ignored_configset(reqid=-1)
                elif len(subrequest) == 1:
                    ErrorHandler().ignored_configset(reqid=subrequest[0])
                else:
                    ErrorHandler().ignored_configset(reqid=subrequest[0], req=subrequest[1:])

# TODO: Finish the error handler
class ErrorHandler():
    def __init__(self):
        pass
    def info_msg(self, msg):
        print "Info: %s" % msg
    def warn_msg(self, msg):
        print "Warning: %s" % msg
    def ignored_configset(self):
        print "BUG: ignored_configset handler is not finished."
        print "Warning: Requested configuration setting was not set." 

def setup_optparser():
    """setup_optparser() -> optparse.OptionParser() instance
    
    Returns an instance of OptionParser, configured to handle parsing the
    options for RTVM"""
    optparser = OptionParser()
    # TODO: Setup the parser
    return optparser

def main():
    pass

# Setup everything

# Check if we are being executed
if __name__ == "__main__":
    # Prep to run
    arguments = sys.argv[1:]
    optparser = setup_optparser()
    opt = optparser.parse_args(arguments)
    # Run RTVM
    main()
    sys.exit(0)
