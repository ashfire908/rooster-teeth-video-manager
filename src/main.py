#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Rooster Teeth Video Manager
# Main program

# Import modules
import sys
import os
import datetime
import urllib2
import ConfigParser
import types
import json
from optparse import OptionParser

# Prefer cPickle/cStringIO to pickle/StringIO
try:
    from cPickle import Unpickler
except ImportError:
    from pickle import Unpickler
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# Define static variables
default_root = "~/.rtvm"

# Import the other parts of the program
#from shared import

# Define Classes and Functions
class DataManager():
    def __init__(self, filename=None):
        self.configfile = None
        self._initconfigparser()
        if filename != None:
            self.loadconfig(filename)
        self.episodedata = {}
    def _openconfig(self, filename=None, reopen=False, readfile=True):
        if reopen and filename == None and isinstance(self.configfile, types.FileType) and self.configfile.closed:
            # Reopen enabled, no filename given, self.configfile is a file, and it is closed.
            # Set the filename to the previous filename.
            filename = self.configfile.name
        if filename != None:
            # Filename given.
            # NOTE: Do we want to do something special if the file is being reopened?
            if os.path.isfile(filename) and readfile:
                # File exists or was just open.
                self.configfile = open(filename, "r")
            else:
                self.configfile = open(filename, "w")
        else:
            # Can't open file, either: reopen disabled, or file was not previously opened.
            raise
    def _getconfigdefault(self):
        # TODO: Generate default config here
        # NOTE: Actually, merge into _initconfigparser()
        pass
    def _initconfigparser(self):
        self.config = ConfigParser.SafeConfigParser(self._getconfigdefault())
    def loadconfig(self, filename=None, reopen=False, resetconfig=False):
        self._openconfig(filename, reopen)
        if resetconfig:
            self._initconfigparser()
        self.config.readfp(self.configfile)
        # Shut the file when we are done.
        self.configfile.close()
    def saveconfig(self, filename=None, reopen=True):
        self._openconfig(filename, reopen, False)
        self.config.write(self.configfile)
        self.configfile.close()
    def listsections(self):
        return self.config.sections()
    def listsettings(self, section):
        return self.config.items(section)
    def getsettings(self, request):
        settings = {}
        for subrequest in request:
            if len(subrequest) == 2 and self.config.has_section(subrequest[0]):
                returnkey = "%s:%s" % (subrequest[0], subrequest[1])
                if self.config.has_option(subrequest[0], subrequest[1]):
                    settings[returnkey] = json.loads(self.config.get(subrequest[0], subrequest[1]))
                else:
                    settings[returnkey] = None
            else:
                ErrorHandler().ignored_configget(req=subrequest)
        return settings
    def setsettings(self, request):
        for subrequest in request:
            if len(subrequest) == 3 and self.config.has_section(subrequest[0]):
                self.config.set(subrequest[0], subrequest[1], json.dumps(subrequest[2]))
            else:
                ErrorHandler().ignored_configset(req=subrequest)
    def loadepisodedata(self, filename):
        datafile = open(filename, "rb")
        unpickler = Unpickler(datafile)
        data = unpickler.load()
        newdata = self.episodedata
        if isinstance(data, types.DictionaryType):
            newdata.update(data)
        elif isinstance(data, (types.ListType, types.TupleType)):
            for epidata in data:
                if isinstance(epidata, types.DictionaryType):
                    newdata = epidata.update(newdata)
        else:
            raise RuntimeError
        self.episodedata = newdata

class VideoManager:
    def __init__(self):
        self.search_fields = ["episode_num", "episode_name", "title", "description", "mimetype", "rtid", "season", "series"]
    def search_videos(self, data, **parameters):
        results = {}
        search = {}
        # Get the search criteria
        for field, value in parameters.iteritems():
            if field in self.search_fields:
                search[field] = value
                results[field] = []
                print "Search Field %s, looking for %s." % (field, value)
        for epi_id, epi_data in data.iteritems():
            # One of the episodes in data
            # Scan the episode for the search criteria
            for field, value in search.iteritems():
                # Does the episode metadata have the requested field, and does the field's value either
                # contain the search criteria value in a list or equal search criteria value?
                if field in epi_data and (value in epi_data[field] or epi_data[field] == value):
                    results[field].append(epi_id)
        return results
    def id_data(self, ids, data):
        return_data = {}
        for vid in ids:
            if vid in data.keys():
                return_data[vid] = data[vid]
            else:
                print "ID %i not found in given episode data." % vid
        return return_data

class DownloadManager():
    def __init__(self):
        pass
    def download_file(self, url, dest, callback=None):
        # Load these from config?
        bufsize = 1024
        continue_download = True
        if callback == None:
            usecallback = False
        else:
            usecallback = True
        while os.path.isfile(dest) and usecallback:
            # Ask if file should be overwritten
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
            block = download.read(bufsize)
            if block != '':
                output_file.write(block)
                if usecallback:
                    callback.download_progress(length, download.fp.tell())
            else:
                download_done = True
        if usecallback:
            callback.download_done()
        download.close()
        output_file.close()
    def download_videos(self, data, fsroot, video_folder, mimetypes, callback=None):
        for video in data.itervalues():
            if not "files" in video.keys():
                # No files to download, skip video
                ErrorHandler().warn_msg("No video files listed for video %s" % video)
                continue
            # Get mimetypes
            avail_mimetypes = []
            for vidfile in video["files"]:
                avail_mimetypes.append(vidfile["mimetype"])
            # Select default mimetype
            selected_mimetype = avail_mimetypes[0]
            if isinstance(mimetypes, (types.ListType, types.TupleType)) and len(mimetypes) > 0:
                # Search for prefered mimetype
                for mimetype in mimetypes:
                    if mimetype in avail_mimetypes:
                        # Prefered Mimetype found
                        selected_mimetype = mimetype
                        break
            # Find url for requested mimetype
            for vidfile in video["files"]:
                if vidfile["mimetype"] == selected_mimetype:
                    url = vidfile["url"]
                    break
            download_path = os.path.join(fsroot, video_folder, video["series"], video["season"], "%s.%s" % (video["episode_name"], url.split(".").pop()))
            if not os.path.isdir(os.path.dirname(download_path)):
                ErrorHandler().info_msg("'%s' does not exist, creating." % os.path.dirname(download_path))
                os.makedirs(os.path.dirname(download_path))
            if callback != None:
                callback.download_episode(video)
            self.download_file(url, download_path, callback)

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
    # Not finished, just fragments
    # End of argument processing
    # Do path stuff?
    if not os.path.isdir(fileroot):
        # Make the fileroot folder
        os.mkdir(fileroot)
    config_filename = os.path.join(fileroot, "config")
    # Create instances of VideoManager, DataManager, and Download Manager
    videomanager = VideoManager()
    datamanager = DataManager(filename=config_filename)
    downloadmanager = DownloadManager()    
    # Load the episode data
    for datafilename in datamanager.getsettings([("Data", "episodefiles")])["Data:episodefiles"]:
        datamanager.loadepisodedata(datafilename)

# Setup to pre-start state

# Check if we are being executed
if __name__ == "__main__":
    # Prep to run
    arguments = sys.argv[1:]
    argparser = setup_optparser()
    opt = argparser.parse_args(arguments)
    # Run RTVM
    main(opt)
    sys.exit(0)
