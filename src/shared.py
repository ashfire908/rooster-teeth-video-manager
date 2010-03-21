#!/usr/bin/env python
# Rooster Teeth Video Manager
# Misc shared code

# Import Modules
import types
import datetime
from xml.dom import minidom

def tobool(data):
    if data.lower() == "true":
        return True
    elif data.lower() == "false":
        return False

def compare_lists(orglist, mode, *lists):
    if mode == "subtract":
        for cmplist in lists:
            if isinstance(cmplist, types.DictionaryType):
                for diclist in cmplist:
                    for item in orglist:
                        if not item in diclist.values:
                            orglist.remove(item)
            elif isinstance(cmplist, (types.ListType, types.TupleType)):
                for item in orglist:
                    if not item in cmplist:
                        orglist.remove(item)
        return orglist

def parse_bliptv(data):
    document = minidom.parseString(data)
    blipns = document.getElementsByTagName("rss")[0].getAttribute("xmlns:blip")
    medians = document.getElementsByTagName("rss")[0].getAttribute("xmlns:media")
    video = document.getElementsByTagName("item")[0]
    video_data = {}
    video_data["blip_id"] = int(video.getElementsByTagNameNS(blipns, "item_id").item(0).firstChild.data)
    video_data["blip_guid"] = video.getElementsByTagName("guid").item(0).firstChild.data
    video_data["blip_title"] = video.getElementsByTagName("title").item(0).firstChild.data
    video_data["runtime"] = int(video.getElementsByTagNameNS(blipns, "runtime").item(0).firstChild.data)
    video_data["blip_embed_id"] = video.getElementsByTagNameNS(blipns, "embedLookup").item(0).firstChild.data
    # Description is optional, make sure it exists.
    if video.getElementsByTagNameNS(blipns, "puredescription").item(0).firstChild != None:
        video_data["description"] = video.getElementsByTagNameNS(blipns, "puredescription").item(0).firstChild.data
    else:
        video_data["description"] = None
    # Thumbnail is optional, make sure it exists.
    if video.getElementsByTagNameNS(medians, "thumbnail").item(0) != None:
        video_data["thumbnail"] = video.getElementsByTagNameNS(medians, "thumbnail").item(0).getAttribute("url")
    else:
        video_data["thumbnail"] = None
    # Small thumbnail is optional, make sure it exists.
    if video.getElementsByTagNameNS(blipns, "smallThumbnail").item(0) != None:
        video_data["thumbnail_small"] = video.getElementsByTagNameNS(blipns, "smallThumbnail").item(0).firstChild.data
    else:
        video_data["thumbnail_small"] = None
    # We use blip:datestamp rather than pubDate because pubDate is more of a
    # human readable version.
    timestamp = video.getElementsByTagNameNS(blipns, "datestamp").item(0).firstChild.data
    video_data["timestamp"] = datetime.datetime.strptime(timestamp, "%Y-%m-%jT%H:%M:%SZ")
    # Get info on media files
    mediafiles = []
    for mfile in video.getElementsByTagNameNS(medians, "content"):
        height = None
        width = None
        # Height and width are (apparently) optional. Check for this.
        if mfile.getAttribute("height") != "":
            height = int(mfile.getAttribute("height"))
        if mfile.getAttribute("width") != "":
            width = int(mfile.getAttribute("width"))
        mediafiles.append({"url":mfile.getAttribute("url"),\
                           "role":mfile.getAttributeNS(blipns, "role"),\
                           "video_codec":mfile.getAttributeNS(blipns, "vcodec"),\
                           "audio_codec":mfile.getAttributeNS(blipns, "acodec"),\
                           "filesize":int(mfile.getAttribute("fileSize")),\
                           "height":height,\
                           "width":width,\
                           "mimetype":mfile.getAttribute("type"),\
                           "default":tobool(mfile.getAttribute("isDefault"))\
                           })
    video_data["files"] = tuple(mediafiles)
    return video_data