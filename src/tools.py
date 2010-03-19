#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Rooster Teeth Video Manager
# Developer / Maintainers tools

# Import all the stuff we need
from urllib import unquote, unquote_plus
import urllib2
import types
import re
from HTMLParser import HTMLParser
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
try:
    from cPickle import Pickler, Unpickler
except ImportError:
    from pickle import Pickler, Unpickler

# Import the other parts of the program
from shared import parse_bliptv

def waste_time(x):
    mark = 0
    while mark < x:
        mark += 1

def unquote_url(url, plus=False):
    """Removes all those nasty and annoying quotes (eg. %20).
    
    Can take a string or a list/tuple of urls.
    If plus if True, it will also fix the plus and convert them to spaces."""
    if isinstance(url, types.StringTypes):
        if plus:
            return unquote_plus(url)
        else:
            return unquote(url)
    elif isinstance(url, (types.ListType, types.TupleType)):
        urls = []
        for single_url in url:
            if plus:
                urls.append(unquote_plus(single_url))
            else:
                urls.append(unquote(single_url))
        return urls

def downloadsimple(url):
    """"Dumb" little function to download a url and return the datafile
    
    Takes a url as a string."""
    downloader = urllib2.build_opener()
    request = urllib2.Request(url)
    download = downloader.open(request)
    data = download.read()
    return data

def vidid_grabber(url):
    reg_blipid = re.compile(r"[&]?file=http://blip.tv/rss.flash/([0-9]+)[&]?", re.IGNORECASE)
    reg_vidid = re.compile(r'''src=['"]http://blip.tv/play/(.+?)['"]''', re.IGNORECASE)
    ids = []
    parser = EmbedLinkParser()
    # Can't override the Parser's __init__ so we set it here.
    parser.embedlinks = []
    url = unquote_url(url)
    page = downloadsimple(url)
    parser.feed(page)
    foundembedlinks = parser.embedlinks
    if len(foundembedlinks) == 0:
        print "No embed links found. URL: %s" % url
        return None
    for link in foundembedlinks:
        try:
            linkid = reg_vidid.search(link).groups()[0]
        except AttributeError:
            print "Link Failed match on '%s'." % link
        else:
            ids.append(unquote_url(linkid).split(".", 1)[0]) # SL
    if len(ids) == 0:
        print "No ids. URL: %s" % url
        return None
    download = urllib2.urlopen("http://blip.tv/play/%s" % ids[0])
    idurl = download.geturl()
    download.close()
    try:
        bpid = reg_blipid.search(unquote_url(idurl, True)).groups()[0]
    except AttributeError:
        print "ID Failed match on '%s'." % bpid
        return None
    else:
        return bpid

class EmbedLinkParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        dic = {}
        for k, v in attrs:
            dic[k] = v
        if tag == "input" and "id" in dic and dic["id"] == "embedCode":
            self.embedlinks.append(dic["value"])

def generate_episodedata_pickle(episodes):
    picklefile = StringIO()
    data = {}
    for ep in episodes:
        epdata = {}
        epdata.update(ep)
        blipid = vidid_grabber("http://roosterteeth.com/archive/episode.php?id=%i" % ep["rtid"])
        if blipid != None:
            epdata.update(parse_bliptv(downloadsimple("http://blip.tv/rss/flash/%s" % blipid)))
        data[ep["rtid"]] = epdata
    pickler = Pickler(picklefile, -1)
    pickler.dump(data)
    # Rewind the tape before returning it. Pun intended.
    picklefile.seek(0)
    return picklefile

def generate_episodedata_request(ids):
    genep_request = []
    print "Don't make any typos."
    for epid in ids:
        genep_id = {}
        genep_id["rtid"] = epid
        genep_id["series"] = raw_input("[ID %i] Series: " % epid)
        tmpin = input("[ID %i] Episode number (-1 if there is none): " % epid)
        if tmpin < 0:
            tmpin = None
        genep_id["episode"] = tmpin 
        genep_id["episodename"] = raw_input("[ID %i] Episode name: " % epid)
        tmpin = raw_input("[ID %i] Season (type 'None' if there is none): " % epid)
        if tmpin.lower() == "none":
            tmpin = None
        genep_id["season"] = tmpin
        genep_request.append(genep_id)
    return genep_request

def generate_episodedata_interface(ids=None):
    print "Episode data generator. Assumes everything uses the bliptv backend."
    print "Built like crap. Handle with care."
    print "Don't make any typos."
    if ids == None:
        try:
            ids = input("Ids, this is input(): ")
        except EOFError:
            print "No ids given."
            raise
    request = []
    
    for epid in ids:
        genep_id = {}
        genep_id["rtid"] = epid
        genep_id["series"] = raw_input("[ID %i] Series: " % epid)
        tmpin = input("[ID %i] Episode number (-1 if there is none): " % epid)
        if tmpin < 0:
            tmpin = None
        genep_id["episode"] = tmpin 
        genep_id["episodename"] = raw_input("[ID %i] Episode name: " % epid)
        tmpin = raw_input("[ID %i] Season (type 'None' if there is none): " % epid)
        if tmpin.lower() == "none":
            tmpin = None
        genep_id["season"] = tmpin
        request.append(genep_id)
    print "Generating data, this may take awhile..."
    # Waste time
    waste_time(5)
    data = generate_episodedata_pickle(request)
    choice = input("Return [True] or save [False]? ")
    if choice:
        return data.read()
    else:
        filename = raw_input("Filename (no error checking, write mode): ")
        datafile = open(filename, "w")
        datafile.write(data.read())
        datafile.close()
        print "Saved."

def dump_pickleddata(data, fromfile=False):
    if fromfile:
        datafile = open(data, "rb")
    else:
        datafile = StringIO()
        datafile.write(data)
        datafile.seek(0)
    unpickler = Unpickler(datafile)
    data = unpickler.load()
    datafile.close()
    return data
