""" flickrtags.py
harvest Flickr tags and write to *-keyword.txt files

Flickr API documentation: https://www.flickr.com/services/api/
"""
import json
import requests

#-------------------------------------------------------------------------------
def get_tags_example(user_id):
    """Example of how to retrieve tags for photos on Flickr.

    user_id = user ID; will print tags for first 20 photos in this photostream
    """

    # try without authentication, then read this carefully:
    # https://www.flickr.com/services/api/auth.oauth.html

    # get some photos for testing
    per_page = '20' # max=500 for production use later
    endpoint = 'https://api.flickr.com/services/rest/' + \
        '?method=flickr.people.getPhotos' + \
        '&api_key=cbfb84b23a5a7af2a0bf27cc8a87d85b&user_id=' + user_id + \
        '&per_page=' + per_page + '&format=json&nojsoncallback=1' + \
        '&api_sig=66f149b05c6db3e129a84ac0ea93001d'
    response = requests.get(endpoint)
    resp = json.loads(response.text)

    # iterate through the photos and display title and tags
    for photo in resp['photos']['photo']:
        title = photo['title']
        user_id = photo['owner']
        photo_id = photo['id']
        secret = photo['secret']
        photo_url = 'http://flickr.com/photos/' + user_id + '/' + photo_id
        print(title + ' ' + photo_url)
        # now get info for this single photo
        endpoint = 'https://api.flickr.com/services/rest/' + \
            '?method=flickr.photos.getInfo' + \
            '&api_key=cbfb84b23a5a7af2a0bf27cc8a87d85b&photo_id=' + photo_id + \
            '&secret=' + secret + '&format=json&nojsoncallback=1' + \
            '&api_sig=630073f2a1c6ac5e08457143ebc979ac'
        response = requests.get(endpoint)
        photo_info = json.loads(response.text)
        print('-'*80)
        print(str(photo_info))
        print('-'*80)
        for tag in photo_info['photo']['tags']['tag']:
            tagname = tag['raw']
            print('  >> Tag: ' + tagname)

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    get_tags_example('dogerino')
