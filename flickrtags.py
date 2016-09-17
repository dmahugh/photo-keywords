""" flickrtags.py
harvest Flickr tags and write to *-keyword.txt files

Flickr API documentation: https://www.flickr.com/services/api/
"""
import configparser
import json
import os
import requests

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
        keywords = {tag['raw'].strip().lower() for tag in photo_info['photo']['tags']['tag']}
        keywords.add(photo['title'].strip().lower())
        photo_url = 'http://flickr.com/photos/' + user_id + '/' + photo['id']
        taken = photo_info['photo']['dates']['taken']
        print(photo_url + ' - ' + taken + ' - ' + str(keywords))

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
if __name__ == '__main__':
    get_tags_example('dogerino')
