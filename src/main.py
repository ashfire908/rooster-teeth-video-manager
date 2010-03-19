#!/usr/bin/env python
# Rooster Teeth Video Manager
# Main program

# Import modules
import sys
import os
#import types # I always end up using this for something.
import datetime
import urllib2
import ConfigParser
from optparse import OptionParser
from xml.dom import minidom
#try:
#    from cPickle import Unpickler
#except ImportError:
#    from Pickle import Unpickler

# Define static variables
default_root = "~/.rtvm"
default_configfile = "~/.rtvm/config"


# Import the other parts of the program
# No other parts to import at the moment

# Define Classes and Functions
def tobool(data):
    if data.lower() == "true":
        return True
    elif data.lower() == "false":
        return False

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
    def listsettings(self, section):
        return self.config.items(section)
    def getsettings(self, request):
        settings = []
        for subrequest in request:
            if len(subrequest) == 2 and self.config.has_section(subrequest[0]):
                if self.config.has_option(subrequest[0], subrequest[1]):
                    settings.append((subrequest[0], self.config.get(subrequest[0], subrequest[1])))
                else:
                    settings.append((subrequest[0], None))
            else:
                ErrorHandler().ignored_configget(req=subrequest)
    def setsettings(self, request):
        for subrequest in request:
            if len(subrequest) == 3 and self.config.has_section(subrequest[0]):
                self.config.set(subrequest[0], subrequest[1], subrequest[2])
            else:
                ErrorHandler().ignored_configset(req=subrequest)
    

class VideoManager:
    def __init__(self):
        pass
    def parse_bliptv(self, data):
        document = minidom.parseString(data)
        blipns = document.getElementsByTagName("rss")[0].getAttribute("xmlns:blip")
        medians = document.getElementsByTagName("rss")[0].getAttribute("xmlns:media")
        video = document.getElementsByTagName("item")[0]
        video_data = {}
        video_data["id"] = int(video.getElementsByTagNameNS(blipns, "item_id").item(0).firstChild.data)
        video_data["guid"] = video.getElementsByTagName("guid").item(0).firstChild.data
        video_data["title"] = video.getElementsByTagName("title").item(0).firstChild.data
        video_data["runtime"] = int(video.getElementsByTagNameNS(blipns, "runtime").item(0).firstChild.data)
        video_data["embed_id"] = video.getElementsByTagNameNS(blipns, "embedLookup").item(0).firstChild.data
        video_data["description"] = video.getElementsByTagNameNS(blipns, "puredescription").item(0).firstChild.data
        video_data["thumbnail"] = video.getElementsByTagNameNS(medians, "thumbnail").item(0).getAttribute("url")
        video_data["thumbnail_small"] = video.getElementsByTagNameNS(blipns, "smallThumbnail").item(0).firstChild.data
        # We use blip:datestamp rather than pubDate because pubDate is more of a
        # human readable version.
        timestamp = video.getElementsByTagNameNS(blipns, "datestamp").item(0).firstChild.data
        video_data["timestamp"] = datetime.datetime.strptime(timestamp, "%Y-%m-%jT%H:%M:%SZ")
        # Get info on media files
        mediafiles = []
        for file in video.getElementsByTagNameNS(medians, "content"):
            mediafiles.append({"url":file.getAttribute("url"),\
                               "role":file.getAttributeNS(blipns, "role"),\
                               "vcodec":file.getAttributeNS(blipns, "vcodec"),\
                               "acodec":file.getAttributeNS(blipns, "acodec"),\
                               "size":int(file.getAttribute("fileSize")),\
                               "height":int(file.getAttribute("height")),\
                               "width":int(file.getAttribute("width")),\
                               "mimetype":file.getAttribute("type"),\
                               "default":tobool(file.getAttribute("isDefault"))\
                               })
        video_data["files"] = tuple(mediafiles)
        return video_data

class DownloadManager():
    def __init__(self):
        pass
    def downloadfile(self, url, dest, callback=None):
        # Load these from config?
        bufsize = 1024
        continue_download = True
        if callback == None:
            usecallback = False
        else:
            usecallback = True
        while os.path.isfile(dest) and usecallback:
            choice = callback.ask_destoverwrite()
            if choice:
                break
            else:
                dest = callback.ask_dest()
        if not os.path.isfile(dest):
            continue_download = False
        downloader = urllib2.build_opener()
        request = urllib2.Request(url)
        if continue_download:
            output_file = open(dest, "ab")
            output_file.seek(0, 2)
            request.add_header("Range", "bytes=%i-" % os.stat(output_file).st_size)
        else:
            output_file = open(dest, "wb")
        download = downloader.open(request)
        length = download.headers.dict["content-length"]
        download_done = False
        while not download_done:
            input = download.read(bufsize)
            if input != '':
                output_file.write(input)
                if usecallback:
                    callback.download_progress(length, download.fp.tell())
            else:
                download_done = True
        if usecallback:
            callback.download_done()
        download.close()
        output_file.close()
    def downloadsimple(self, url):
        downloader = urllib2.build_opener()
        request = urllib2.Request(url)
        download = downloader.open(request)
        data = download.read()
        return data

class ErrorHandler():
    # TODO: Finish the error handler
    def __init__(self):
        pass
    def info_msg(self, msg):
        print "Info: %s" % msg
    def warn_msg(self, msg):
        print "Warning: %s" % msg
    def ignored_configset(self):
        print "BUG: ignored_configset handler is not finished."
        print "Warning: Requested configuration setting was not set."
    def ignored_configget(self):
        print "BUG: ignored_configget handler is not finished."
        print "Warning: Requested configuration setting was retrieved." 

def setup_optparser():
    """setup_optparser() -> optparse.OptionParser() instance
    
    Returns an instance of OptionParser, configured to handle parsing the
    options for RTVM"""
    optparser = OptionParser()
    # TODO: Add all the options
    optparser.add_option("-V", "--version", action="store_true", dest="version", default=False)
    return optparser

def main(optarg):
    pass

# Setup to pre-start state

# Check if we are being executed
if __name__ == "__main__":
    # Prep to run
    arguments = sys.argv[1:]
    optparser = setup_optparser()
    opt = optparser.parse_args(arguments)
    # Run RTVM
    main(opt)
    sys.exit(0)