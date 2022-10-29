#!/usr/bin/env python3

import sys
import re
import os.path
from datetime import datetime,timedelta
from collections import defaultdict
from string import Template

# config
mydebug = 1
lines=20000
formats='ts|hls|dash'
delim='?key='
timerange=1 # in minutes
# input
logfile = "/var/log/nginx/access.log"
countdir = "/www/rtmp/counts"

# run
if mydebug >= 2:
   print("DEBUG: logfile=" + logfile)

# date/time
now = datetime.now()
endtime = now
starttime = now - timedelta(minutes = timerange)
endtime_format = endtime.strftime("%d/%b/%Y:%H:%M:%S")
starttime_format = starttime.strftime("%d/%b/%Y:%H:%M:%S")
date_format_str = '%d/%b/%Y:%H:%M:%S'
if mydebug >= 2:
   print("DEBUG: starttime=", starttime)
   print("DEBUG: endtime=", endtime)
   print("DEBUG: starttime_format=", starttime_format)
   print("DEBUG: endtime_format=", endtime_format)

# define regex
lineRegex = r'^(?P<lineIPaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s(?P<lineNotSure>[A-Za-z\d-]+)\s(?P<lineUsername>[A-Za-z\d-]+)\s\[(?P<lineDateAndTime>\d{2}\/[A-Za-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2})\s(?P<lineTimezone>\+|\-\d{4})\]\s\"(?P<lineMethod>[A-Z]+)\s(?P<lineUrl>.+)\s(HTTP\/1\.1)\"\s(?P<lineStatusCode>\d{3})\s(?P<lineBytesSent>\d+)\s\"(?P<lineReferer>(\-)|(.+))\"\s\"(?P<lineUserAgent>.+)\"'
refererRegex = r'^http[s]://.*?key=(?P<streamKey>[A-Za-z0-9]+)'

## prepare variables
# dictionaries
# def def_value(): # not needed?
#   return "0"
streamKeys = defaultdict(int) # empty dictionary
streamKeysDict = defaultdict(int) # empty dictionary
totalCount = defaultdict(int) # empty dictionary

logOpen = open(logfile, 'r')
for line in logOpen.readlines():
   # empty tuple
   uniqueTuple = () # empty tuple

   if mydebug >= 2:
      print("DEBUG: line=", line)
   data = re.search(lineRegex, line)
   if data:
      datadict = data.groupdict()
      myIP = datadict["lineIPaddress"]
      myUsername = datadict["lineUsername"]
      myDateAndTime = datadict["lineDateAndTime"]
      myTimezone = datadict["lineTimezone"]
      myMethod = datadict["lineMethod"]
      myUrl = datadict["lineUrl"]
      myStatusCode = datadict["lineStatusCode"]
      myReferer = datadict["lineReferer"]
      myUserAgent = datadict["lineUserAgent"]
      if mydebug >= 2:
         print("DEBUG: data=", data)
      if mydebug >= 2:
         print("DEBUG: myIP=", myIP)
         print("DEBUG: myUsername=", myUsername)
         print("DEBUG: myDateAndTime=", myDateAndTime)
         print("DEBUG: myTimezone=", myTimezone)
         print("DEBUG: myMethod=", myMethod)
         print("DEBUG: myUrl=", myUrl)
         print("DEBUG: myStatusCode=", myStatusCode)
         print("DEBUG: myReferer=", myReferer)
         print("DEBUG: myUserAgent=", myUserAgent)
      ## commented out for testing
      if datetime.strptime(myDateAndTime,"%d/%b/%Y:%H:%M:%S") >= starttime and \
         datetime.strptime(myDateAndTime,"%d/%b/%Y:%H:%M:%S") <= endtime:
            if mydebug >= 2:
               print("DEBUG: line match=", line)
            if myStatusCode == "200" and delim in myReferer: # only bother if successful
               refererData = re.search(refererRegex, myReferer)
               if refererData:
                  refererDict = refererData.groupdict()
                  myStreamkey = refererDict["streamKey"]
                  if mydebug >= 2:
                     print("DEBUG: myStreamkey=", myStreamkey)

                  ## create dictionaries for final output
                  # array of streamKeys 
                  if not myStreamkey in streamKeys:
                     streamKeys[myStreamkey] += 1
                  if mydebug >= 2:
                     print("DEBUG: streamKeys=", streamKeys[myStreamkey])

                  # count viewers and add to dictionary
                  uniqueTuple = tuple((myStreamkey, myIP, myUsername))
                  if mydebug >= 2:
                     print("DEBUG: uniqueTuple=", uniqueTuple)
                  if uniqueTuple in streamKeysDict:
                     if mydebug >= 2:
                        print("DEBUG: Key already exists", uniqueTuple)
                  else:
                     streamKeysDict[uniqueTuple] += 1
                     totalCount[myStreamkey] += 1
                     if mydebug >= 2:
                        print("DEBUG: streamKeysDict=", streamKeysDict[uniqueTuple])
                        print("DEBUG: streamKeysDict=", totalCount[myStreamkey])

# debug
if mydebug >= 2:
   for keyCount in totalCount.keys():
      print('DEBUG: Count for {}={}'.format(keyCount, totalCount[keyCount]))

# string Template t
t = Template("""<?xml version='1.0'?>
<count name="count">
$myCount
</count>""")

for keyname in streamKeys.keys():
   if mydebug >= 2:
      print('DEBUG: keyname= {}'.format(keyname))
   # debug need only
   if mydebug >= 2:
      for key in streamKeysDict.keys():
         if keyname in key:
            print('DEBUG: Valid key= {}'.format(key))
   # update template with actual count
   xmlString = str(t.substitute({'myCount': str(totalCount[keyname])}))
   # create / update file
   filename = countdir + "/" + keyname + ".xml"
   if mydebug >= 2:
      print('DEBUG: writing count to file=', filename)
   with open(filename,'w', encoding="ascii") as f:
      if mydebug >= 2:
         print('DEBUG: writing count to count file=', xmlString)
      f.write(xmlString) # write must be str - use safe_substitute
      f.close()

logOpen.close()
exit()
