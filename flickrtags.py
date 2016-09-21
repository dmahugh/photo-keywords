""" flickrtags.py
harvest Flickr tags and write to *-keyword.txt files

Flickr API documentation: https://www.flickr.com/services/api/
"""
from collections import Counter
import configparser
import glob
import json
import os
import requests

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
def cache_photostream(user_id):
    """Retrieve a user's list of photos and save locally.

    user_id = the Flickr user whose photos will be listed

    Files are written to the cache subfolder, one per page of API results.
    """
    per_page = '100'
    api_key = get_apikey('dougerino-jamiesearcher')

    endpoint = 'https://api.flickr.com/services/rest/' + \
        '?method=flickr.people.getPhotos' + \
        '&api_key=' + api_key + \
        '&user_id=' + user_id + \
        '&per_page=' + per_page + '&format=json&nojsoncallback=1'

    response = requests.get(endpoint)
    jsondata = json.loads(response.text)
    write_cache(user_id=user_id, pageno=1, datatype='photostream', jsondata=jsondata)

    tot_pages = jsondata['photos']['pages']
    for pageno in range(2, tot_pages + 1):
        endpoint = 'https://api.flickr.com/services/rest/' + \
            '?method=flickr.people.getPhotos' + \
            '&api_key=' + api_key + \
            '&user_id=' + user_id + \
            '&per_page=' + per_page + \
            '&page=' + str(pageno) + \
            '&format=json&nojsoncallback=1'

        response = requests.get(endpoint)
        jsondata = json.loads(response.text)

        write_cache(user_id=user_id, pageno=pageno, datatype='photostream', jsondata=jsondata)
        #if pageno >= 3:
        #    break

#-------------------------------------------------------------------------------
def cache_tags(*, user_id, pageno):
    """Retrieve photo tags for a page of user's photostream.

    user_id = Flickr user ID
    pageno = page # of results

    Reads the locally cached data (as saved by cache_photostream()) for the
    specified user/page, then iterates through the photos and makes an API
    call to get information about each one, then writes all of the tag data
    for the page's photos into a file in the cache folder named
    <user>-tags-pageXXX.json
    """
    filename = cache_filename(user_id=user_id, pageno=pageno, datatype='photostream')
    with open(filename, 'r') as datafile:
        photolist = json.loads(datafile.read())['photos']['photo']

    master_list = [] # list of photos (dictionaries)

    photo_limit = None # set this to a small number for quick testing of a few photos
    for photo in photolist:
        photo_info = photo_detail(photo)

        photo_url = 'http://flickr.com/photos/' + user_id + '/' + photo['id']
        taken = photo_info['photo']['dates']['taken']
        title = photo['title'].strip().lower()

        keywords = [tag['raw'].strip().lower() for tag in photo_info['photo']['tags']['tag']]
        keywords.append('flickr-' + user_id)

        taglist = ','.join(sorted(keywords))

        try:
            print(photo_url + ' - ' + taken + ' - ' + title + ' - ' + taglist)
        except UnicodeEncodeError as e:
            print('*** UnicodeEncodeError ***')

        master_list.append({'user_id': user_id,
                            'title': title,
                            'taken': taken,
                            'keywords': keywords,
                            'photo_url': photo_url})

        if photo_limit:
            photo_limit -= 1
            if photo_limit == 0:
                break

    write_cache(user_id=user_id, pageno=pageno, datatype='tags', jsondata=master_list)

#-------------------------------------------------------------------------------
def generate_stats():
    """Generate statistics from cached Flickr tag data.
    """
    #/// create a CSV showing # photos and tags per photo, summarized by month since August 2008

    users = ['dogerino', 'dougerino'] # list of user IDs whose data is cached
    keywords = [] # master list of tags

    #/// need a different approach here - generate year/month totals for photos uploaded to
    # dogerino and dougerino, so that we can do a stacked bar chart showing the migration
    # from 100% dougerino to mostly dogerino
    photosbymonth = [] # list of year/month for all photos

    for user_id in users:
        tot_photos = 0
        tot_tags = 0
        for filename in glob.glob('cache/' + user_id + '-tags-*.json'):
            with open(filename, 'r') as fhandle:
                jsondata = json.loads(fhandle.read())
                for photo in jsondata:
                    # increment totals
                    tot_photos += 1
                    tot_tags += len(photo['keywords']) - 1 # -1 because of 'flickr-userid' tag
                    # add keywords to master list of tags
                    for keyword in photo['keywords']:
                        # don't include auto-generated tags (flickr-dogerino/flickr-dougerino)
                        if not keyword.lower().startswith('flickr-'):
                            keywords.append(keyword)
                    # add to year/month totals
                    photosbymonth.append(photo['taken'][:7])

        # print photo/tag totals for this user ID
        print('{0} = {1} photos, {2} tags total'.format(user_id, tot_photos, tot_tags))

    # print most common tags
    tagtotals = Counter(keywords)
    print('Total unique tags across ' + '/'.join(users) + ': {}'.format(len(tagtotals)))
    for tag, cnt in tagtotals.most_common(20):
        print(tag, cnt)

    # print the year/month totals
    ymtotals = Counter(photosbymonth)
    for yearmonth in sorted(ymtotals):
        print(yearmonth + ',' + str(ymtotals[yearmonth]))

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
def get_tags_example(user_id):
    """Example of how to retrieve tags for photos on Flickr.

    user_id = Flickr user ID; will print tags for photos in this photostream
    """
    photolist = photostream(user_id)
    for photo in photolist['photos']['photo']:

        photo_info = photo_detail(photo)

        photo_url = 'http://flickr.com/photos/' + user_id + '/' + photo['id']
        taken = photo_info['photo']['dates']['taken']
        title = photo['title'].strip().lower()

        keywords = {tag['raw'].strip().lower() for tag in photo_info['photo']['tags']['tag']}
        keywords.add('flickr-' + user_id)

        taglist = ','.join(sorted(keywords))
        print(photo_url + ' - ' + taken + ' - ' + title + ' - ' + taglist)

#-------------------------------------------------------------------------------
def photo_detail(photo):
    """Get detailed information for a photo.

    photo = the JSON representation of a photo as returned by the
            people.getPhotos API call.

    Returns the JSON output of the photos.getInfo API call for this photo.
    """
    photo_id = photo['id']
    api_key = get_apikey('dougerino-jamiesearcher')

    endpoint = 'https://api.flickr.com/services/rest/' + \
        '?method=flickr.photos.getInfo' + \
        '&api_key=' + api_key + \
        '&photo_id=' + photo_id + \
        '&format=json&nojsoncallback=1'

    response = requests.get(endpoint)
    return json.loads(response.text)

#-------------------------------------------------------------------------------
def photostream(user_id):
    """Returns the list of photos for specified user.
    """
    per_page = '10' # max=500 for production use later; need to handle pagination
    api_key = get_apikey('dougerino-jamiesearcher')

    endpoint = 'https://api.flickr.com/services/rest/' + \
        '?method=flickr.people.getPhotos' + \
        '&api_key=' + api_key + \
        '&user_id=' + user_id + \
        '&per_page=' + per_page + '&format=json&nojsoncallback=1'

    response = requests.get(endpoint)
    return json.loads(response.text)

#-------------------------------------------------------------------------------
def write_cache(*, user_id, pageno, datatype, jsondata):
    """Write photo tag data to local cache for one page of photostream.

    user_id = Flickr user ID
    pageno = page number of the paged results from the Flickr API
    jsondata = the JSON payload - list of photos (dictionaries)

    The data is written to the cache subfolder with this naming convention:
    <user>-tags-pageXXX.json
    """
    filename = cache_filename(user_id=user_id, pageno=pageno, datatype=datatype)
    print('--> writing ' + filename)

    with open(filename, 'w') as fhandle:
        fhandle.write(json.dumps(jsondata, indent=4, sort_keys=True))

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    #get_tags_example('dogerino')
    #cache_photostream('dogerino')
    #cache_photostream('dougerino')

    # dogerino: DONE
    # dougerino: 1-90 done, to do = 91-121
    #user_id = 'dougerino'
    #start = 91
    #end = 121
    #for pageno in range(start, end + 1):
    #    cache_tags(user_id=user_id, pageno=pageno)

    generate_stats()
