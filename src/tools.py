#!/usr/bin/env python
# Rooster Teeth Video Manager
# Devloper / Maintianers tools

# Import all the stuff we need
from urllib import unquote, unquote_plus
import urllib2
import types
import re
from HTMLParser import HTMLParser
from main import VideoManager
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
try:
    from cPickle import Pickler
except ImportError:
    from Pickle import Pickler

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
    parser.embedlinks = []
    url = unquote_url(url)
    page = downloadsimple(url)
    # Next lines are a hack to fix the bad code line that causes HTTPParser to crash and burn.
    pagesplit = page.split("\n")
    pagesplit.remove('<link rel="shortcut icon" href=http://images.roosterteeth.com/assets/style/favicon.ico">')
    page = "\n".join(pagesplit)
    parser.feed(page)
    foundembedlinks = parser.embedlinks
    if len(foundembedlinks) == 0:
        print "No embed links found."
        return None
    for link in foundembedlinks:
        try:
            id = reg_vidid.search(link).groups()[0]
        except AttributeError:
            print "Link Failed match on '%s'." % link
        else:
            ids.append(unquote_url(id).split(".", 1)[0])
    if len(ids) == 0:
        print "No ids."
        return None
    download = urllib2.urlopen("http://blip.tv/play/%s" % ids[0])
    idurl = download.geturl()
    try:
        download.close()
    except:
        print "can't close download. learn to code."
    try:
        id = reg_blipid.search(unquote_url(idurl, True)).groups()[0]
    except AttributeError:
        print "ID Failed match on '%s'." % id
        return None
    else:
        return id

class EmbedLinkParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        dic = {}
        for k, v in attrs:
            dic[k] = v
        if tag == "input" and "id" in dic and dic["id"] == "embedCode":
            self.embedlinks.append(dic["value"])

def generate_data(ids):
    picklefile = StringIO()
    data = {}
    for id in ids:
        blipid = vidid_grabber("http://roosterteeth.com/archive/episode.php?id=%i" % id)
        if blipid == None:
            data[id] = None
        else:
            data[id] = VideoManager().parse_bliptv(downloadsimple("http://blip.tv/rss/flash/%s" % blipid))
    pickler = Pickler(picklefile, -1)
    pickler.dump(data)
    picklefile.seek(0)
    return picklefile