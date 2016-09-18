""" flickrtags.py
harvest Flickr tags and write to *-keyword.txt files

Flickr API documentation: https://www.flickr.com/services/api/
"""
import configparser
import json
import os
import requests

#-------------------------------------------------------------------------------
def cache_photostream(user_id):
    """Retrieve a user's list of photos and save locally.

    user_id = the Flickr user whose photos will be listed

    Files are written to the cache subfolder, one per page of API results.
    """
    per_page = '500'
    api_key = get_apikey('dougerino-jamiesearcher')

    endpoint = 'https://api.flickr.com/services/rest/' + \
        '?method=flickr.people.getPhotos' + \
        '&api_key=' + api_key + \
        '&user_id=' + user_id + \
        '&per_page=' + per_page + '&format=json&nojsoncallback=1'

    response = requests.get(endpoint)
    jsondata = json.loads(response.text)
    write_photostream(user_id=user_id, pageno=1, jsondata=jsondata)

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

        write_photostream(user_id=user_id, pageno=pageno, jsondata=jsondata)
        #if pageno >= 3:
        #    break

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
def write_photostream(*, user_id, pageno, jsondata):
    """Write a page of photostream results to local cache.

    user_id = Flickr user ID
    pageno = page number of the paged results from the Flickr API
    jsondata = the JSON payload returned for this user/page

    The data is written to the cache subfolder with this naming convention:
    <user>-photostream-pageXXX.json
    """
    print('Caching photo list for {0} page # {1}'.format(user_id, pageno))

    filename = user_id + '-photostream-page' + str(pageno).zfill(3) + '.json'
    source_folder = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(source_folder, 'cache/' + filename)

    with open(filename, 'w') as fhandle:
        fhandle.write(json.dumps(jsondata, indent=4, sort_keys=True))

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    #get_tags_example('dogerino')
    cache_photostream('dougerino')
