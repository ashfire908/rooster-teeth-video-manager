#!/usr/bin/env python
# Rooster Teeth Video Manager
# Main program

# Import modules
import sys
import os
import datetime
import urllib2
import ConfigParser
import types
from optparse import OptionParser
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
        if filename != None:
            self.loadconfig(filename)
            self.configfile = StringIO()
            self.configfile.name = None
            self.configfile.close()
        self.episodedata = {}
        self.config = None
    def _openconfig(self, filename=None, reopen=True):
        if self.configfile.closed:
            if reopen and self.configfile.name != None:
                self.configfile = open(self.configfile.name, "a")
            elif filename != None:
                if os.path.isfile(filename):
                    self.configfile = open(filename, "a")
                elif os.path.isdir(os.path.dirname(filename)):
                    ErrorHandler().info_msg("Opening new config file at %s" % filename) 
                    self.configfile = open(filename, "w")
        if filename != None:
            if os.path.isfile(filename):
                self.configfile = open(filename, "a")
            elif os.path.isdir(os.path.dirname(filename)):
                ErrorHandler().info_msg("Creating new config file at %s" % filename) 
                self.configfile = open(filename, "w")
    def _getconfigdefault(self):
        # TODO: Generate default config here
        pass
    def loadconfig(self, filename=None, setdefault=True, reopen=True):
        self._openconfig(filename, reopen)
        self.config = ConfigParser.SafeConfigParser(self._getconfigdefault())
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
                    print "Debug error code 1"
        else:
            raise RuntimeError
        self.episodedata = newdata

class VideoManager:
    def __init__(self):
        self.search_fields = ["episode", "episodename", "title", "description", "mimetype", "rtid", "season", "series"]
    def search_videos(self, data, **parameters):
        results = {}
        search = {}
        # Get the list of valid search
        for field, value in parameters.iteritems():
            if field in self.search_fields:
                search[field] = value
        for epi_id, epi_data in data.iteritems():
            for field, value in search.iteritems():
                if field in epi_data and (value in epi_data[field] or epi_data[field] == value):
                    if not field in results:
                        results[field] = []
                    results[field].append(epi_id)
                elif "files:" in field and "files" in epi_data:
                    for videofile in epi_data["files"]:
                        if videofile[field.split("files:", 1)[0]] == value:
                            if not field in results:
                                results[field] = []
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
                print "Bad data."
                break
            # Get mimetypes
            avail_mimetypes = []
            for vidfile in video["files"]:
                avail_mimetypes.append(vidfile["mimetype"])
            # Select mimetype
            selected_mimetype = None
            for mimetype in mimetypes:
                if mimetype in avail_mimetypes:
                    selected_mimetype = mimetype
            if selected_mimetype == None:
                print "Couldn't find a prefered mimetype. Picking first one I see. (%s)" % avail_mimetypes[0]
                selected_mimetype = avail_mimetypes[0]
            for vidfile in video["files"]:
                if vidfile["mimetype"] == selected_mimetype:
                    url = vidfile["url"]
            download_path = os.path.join(fsroot, video_folder, video["series"], video["season"], "%s.%s" % (video["episodename"], url.split(".").pop()))
            if not os.path.isdir(os.path.dirname(download_path)):
                print "'%s' does not exist, creating." % os.path.dirname(download_path)
                os.makedirs(os.path.dirname(download_path))
            if callback != None:
                callback.download_episode(video)
            print "Downloading ID: %i"
            self.download_file(url, download_path)

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

def main(fileroot, optarg):
    # Not finished, just fragments
    
    # End of argument processing
    if not os.path.isdir(fileroot):
        # Make the fileroot folder
        os.mkdir(fileroot)
    config_filename = os.path.join(fileroot, "config")
    # Create instances of VideoManager and DataManager
    videomanager = VideoManager()
    datamanager = DataManager(filename=config_filename)
    downloadmanager = DownloadManager()    
    # Load the episode data
    for datafilename in datamanager.getsettings((("Data", "episodefiles"), )):
        datamanager.loadepisodedata(datafilename)
    # Launch interface
    

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