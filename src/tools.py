#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Rooster Teeth Video Manager
# Developer / Maintainers tools

# Import all the stuff we need
import sys
from urllib import unquote, unquote_plus
import urllib2
import types
import re
import lxml.html
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

def get_blipid(url):
    reg_blipid = re.compile(r"[&]?file=http://blip.tv/rss.flash/([0-9]+)[&]?", re.IGNORECASE)
    vidlink = None
    # Prep the url, grab the page, and parse it.
    url = unquote_url(url)
    parser = lxml.html.parse(url)
    for element in parser.iter(tag="link"):
        if "rel" in element.attrib and element.attrib["rel"] == "video_src" and "href" in element.attrib:
            vidlink = element.attrib["href"]
    if vidlink == None:
        # No vid link found
        print "No video link found. URL: %s" % url
        return None
    download = urllib2.urlopen(vidlink)
    idurl = download.geturl()
    download.close()
    try:
        bpid = reg_blipid.search(unquote_url(idurl, True)).groups()[0]
    except AttributeError:
        print "ID Failed match on '%s'." % bpid
        return None
    else:
        return bpid

def generate_episodedata_pickle(episodes):
    data = {}
    sys.stderr.write("Processed videos: ")
    for ep in episodes:
        epdata = {}
        epdata.update(ep)
        blipid = get_blipid("http://roosterteeth.com/archive/episode.php?id=%i" % ep["rtid"])
        if blipid != None:
            page = urllib2.urlopen("http://blip.tv/rss/flash/%s" % blipid)
            epdata.update(parse_bliptv(page.read()))
            page.close()
        data[ep["rtid"]] = epdata
        sys.stderr.write("%s " % ep["rtid"])
    sys.stderr.write("\n")
    picklefile = StringIO()
    pickler = Pickler(picklefile, -1)
    pickler.dump(data)
    picklefile.seek(0)
    return picklefile

def generate_episodedata_request(ids):
    genep_request = []
    print "Don't make any typos."
    for epid in ids:
        genep_id = {}
        genep_id["rtid"] = epid
        genep_id["series"] = raw_input("[ID %i] Series: " % epid)
        genep_id["season"] = raw_input("[ID %i] Season (type 'None' if there is none): " % epid)
        if genep_id["season"].lower() == "none":
            genep_id["season"] = None
        genep_id["episode_num"] = input("[ID %i] Episode number (None if there isn't one.): " % epid)
        genep_id["episode_name"] = raw_input("[ID %i] Episode name: " % epid)
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
        genep_id["season"] = raw_input("[ID %i] Season (type 'None' if there is none): " % epid)
        if genep_id["season"].lower() == "none":
            genep_id["season"] = None
        genep_id["episode_num"] = input("[ID %i] Episode number (None if there is none): " % epid)
        genep_id["episode_name"] = raw_input("[ID %i] Episode name: " % epid)
        request.append(genep_id)
    print "Generating data, this may take awhile..."
    # Waste time
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

def print_data(data):
    for epi_id, epi_data in data.iteritems():
        print """\
Episode ID/RTID: %s/%s
 |- Series: %s
 |- Season: %s
 |- Episode Number: %s
 |- Episode Name: %s
 |- Description: "%s"
 |- Runtime: %s
 |- Timestamp: %s\
""" % (epi_id, epi_data["rtid"], epi_data["series"], epi_data["season"], epi_data["episode_num"],\
       epi_data["episode_name"], epi_data["description"], epi_data["runtime"], epi_data["timestamp"])
        bliptv_vars = [["blip_id", "BlipTV ID:"], ["blip_embed_id", "BlipTV Embed ID:"], ["blip_guid", "BlipTV GUID:"], ["blip_title", "BlipTV Title:"]]
        for blip_var in bliptv_vars:
            if blip_var[0] in epi_data.keys():
                print " |- %s %s" % (blip_var[1], epi_data[blip_var[0]])
        for file in epi_data["files"]:
            print """\
 |- File -\\
 |        |- URL: %s
 |        |- Mimetype: %s
 |        |- Role: %s
 |        |- Filesize: %s
 |        |- Height: %s
 |        |- Width: %s
 |        |- Video Codec: %s
 |        |- Audio Codec: %s
 |        \\- Default: %s\
 """ % (file["url"], file["mimetype"], file["role"], file["filesize"], file["height"],\
        file["width"], file["video_codec"], file["audio_codec"], file["default"])
        print ""