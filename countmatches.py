"""countmatches.py

Count number of exact timestamp matches between Flickr metadata and backups.
"""
from collections import Counter
import configparser
import datetime
import glob
import json
import os
import sys
import time

import requests

#-------------------------------------------------------------------------------
class _settings:
    processed = 0
    exactmatch = 0

#-------------------------------------------------------------------------------
def cache_filename(*, user_id, pageno, datatype):
    """Get filename for local cached page of Flickr data.

    user_id = Flickr user ID
    pageno = page #
    datatype = 'tags' or 'photostream'

    Returns the filename to be used for reading/writing this cached data.
    """
    filename = user_id + '-' + datatype + '-page' + str(pageno).zfill(3) + '.json'
    source_folder = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(source_folder, 'cache/' + filename)

#-------------------------------------------------------------------------------
def filename_ts(filename=None):
    """Return timestamp as a string.

    filename = optional file, if passed then timestamp is returned for the file

    Otherwise, returns current timestamp.
    <internal>
    """
    if filename:
        unixtime = os.path.getmtime(filename)
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(unixtime))
    else:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

#-------------------------------------------------------------------------------
def generate_stats():
    """Generate statistics from cached Flickr tag data.
    """
    #/// create a CSV showing # photos and tags per photo, summarized by month since August 2008

    users = ['dogerino', 'dougerino'] # list of user IDs whose data is cached
    keywords = [] # master list of tags

    # Generate year/month totals for photos uploaded to dogerino and dougerino, so
    # that we can do a stacked bar chart showing the migration from 100% dougerino to
    # mostly dogerino we're interested in Oct 2004 through August 2016 ...
    ymtotals = dict()
    for year in range(2004, 2017):
        for month in range(1, 13):
            if (year == 2004 and month < 10) or (year == 2016 and month > 8):
                continue
            yearmonth = str(year) + '-' + str(month).zfill(2)
            for user_id in users:
                ymtotals[yearmonth + '-' + user_id + '-keywords'] = 0
                ymtotals[yearmonth + '-' + user_id + '-photos'] = 0

    for user_id in users:
        tot_photos = 0
        tot_tags = 0
        for filename in glob.glob('cache/' + user_id + '-tags-*.json'):
            with open(filename, 'r') as fhandle:
                jsondata = json.loads(fhandle.read())
                for photo in jsondata:
                    # increment totals
                    tot_photos += 1
                    ymdictkey = photo['taken'][:7] + '-' + user_id + '-photos'
                    if ymdictkey in ymtotals:
                        ymtotals[ymdictkey] += 1
                    tot_tags += len(photo['keywords']) - 1 # -1 because of 'flickr-userid' tag
                    # add keywords to master list of tags
                    ymdictkey = photo['taken'][:7] + '-' + user_id + '-keywords'
                    for keyword in photo['keywords']:
                        # don't include auto-generated tags (flickr-dogerino/flickr-dougerino)
                        if not keyword.lower().startswith('flickr-'):
                            keywords.append(keyword)
                            if ymdictkey in ymtotals:
                                ymtotals[ymdictkey] += 1

        # print photo/tag totals for this user ID
        print('{0} = {1} photos, {2} tags total'.format(user_id, tot_photos, tot_tags))

    # print most common tags
    tagtotals = Counter(keywords)
    print('Total unique tags across ' + '/'.join(users) + ': {}'.format(len(tagtotals)))
    for tag, cnt in tagtotals.most_common(20):
        print(tag, cnt)

    # print year/month totals (in CSV format)
    columns = ['yearmonth']
    for user_id in users:
        columns.append(user_id + '-photos')
        columns.append(user_id + '-keywords')
    print(','.join(columns))
    for year in range(2004, 2017):
        for month in range(1, 13):
            if (year == 2004 and month < 10) or (year == 2016 and month > 8):
                continue
            yearmonth = str(year) + '-' + str(month).zfill(2)
            values = [yearmonth]
            for user_id in users:
                values.append(str(ymtotals[yearmonth + '-' + user_id + '-photos']))
                values.append(str(ymtotals[yearmonth + '-' + user_id + '-keywords']))
            print(','.join(values))

#-------------------------------------------------------------------------------
def get_apikey(app):
    """Get Flickr API key for specified application.

    app = identifier for a section in the ../_private/flickr.ini file where
          API keys are stored

    Returns the API key. Prints an error to the console if not found.
    """
    source_folder = os.path.dirname(os.path.realpath(__file__))
    datafile = os.path.join(source_folder, '../_private/flickr.ini')

    config = configparser.ConfigParser()
    config.read(datafile)
    try:
        retval = config.get(app, 'api_key')
    except configparser.NoSectionError:
        print('ERROR: could not find api_key for ' + app + '!')
        retval = None

    return retval

#-------------------------------------------------------------------------------
def seconds_delta(timestamp1, timestamp2):
    """Calculate the number of seconds between two timestamps.

    timestamp1/timestamp2 = 'YYYY-MM-DD HH:MM:SS' strings

    Returns the number of seconds between these two date/time representations.
    """
    datetime1 = str_to_datetime(timestamp1)
    datetime2 = str_to_datetime(timestamp2)
    diff = datetime1 - datetime2 # creates a timedelta object
    return abs(diff.total_seconds())

#-------------------------------------------------------------------------------
def str_to_datetime(timestamp):
    """Convert a 'YYYY-MM-DD HH:MM:SS' string to a datetime object.
    """
    year = int(timestamp[:4])
    month = int(timestamp[5:7])
    day = int(timestamp[8:10])
    hours = int(timestamp[11:13])
    minutes = int(timestamp[14:16])
    seconds = int(timestamp[17:19])
    return datetime.datetime(year, month, day, hours, minutes, seconds)

#-------------------------------------------------------------------------------
def ts_filename(timestamp):
    """Convert a Flickr timestamp to a list of possible matching files in the
    photos folder hierarchy.

    timestamp = 'YYYY-MM-DD HH:MM:SS' format assumed (all components required)

    Returns a list of 0 or more possible matching filenames.
    """
    matches = []
    photo_home = 'd:\\doug\\photos' #/// get from phototag config settings
    month_folder = os.path.join(photo_home,
                                timestamp[:4],
                                timestamp[5:7])
    day_folder = os.path.join(month_folder, timestamp[8:10])

    matches.extend(ts_search(day_folder, timestamp))
    if not matches:
        # if no matches in day folder, try the month folder
        matches.extend(ts_search(month_folder, timestamp))

    return matches

#-------------------------------------------------------------------------------
def ts_search(folder, timestamp):
    """Search a folder for photos matching a timestamp.

    folder = folder name
    timestamp = timestamp to match, 'YYYY-MM-DD HH:MM:SS'

    Returns a list of full-path filenames that match the timestamp.
    """
    #folder = 'c:\\temp' #/// for testing
    matchlist = []

    for filename in glob.glob(os.path.join(folder, '*.*')):
        _, fext = os.path.splitext(filename)
        if fext.lower() not in ['.jpg', '.jpeg', '.nef', '.png', '.bmp', '.gif']:
            continue
        file_ts = filename_ts(filename)
        if file_ts == timestamp:
            matchlist.append(filename)

    if matchlist:
        _settings.exactmatch += 1

    return matchlist

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    for user_id in ['dogerino', 'dougerino']:
        for datasource in glob.glob('cache/' + user_id + '-tags-*.json'):
            print('SOURCE -> ' + datasource)
            with open(datasource, 'r') as fhandle:
                jsondata = json.loads(fhandle.read())
                for photo in jsondata:
                    TS = photo['taken']
                    PHOTOFILENAME = ts_filename(TS)
                    _settings.processed += 1
                    #if processed >= 50:
                    #    sys.exit()
            print('total photos processed: {0}'.format(_settings.processed))
            print('total exact matches:    {0}'.format(_settings.exactmatch))
