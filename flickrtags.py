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

    # get some photos for testing
    per_page = '10' # max=500 for production use later
    endpoint = 'https://api.flickr.com/services/rest/' + \
        '?method=flickr.people.getPhotos' + \
        '&api_key=cbfb84b23a5a7af2a0bf27cc8a87d85b&user_id=' + user_id + \
        '&per_page=' + per_page + '&format=json&nojsoncallback=1'
    response = requests.get(endpoint)
    resp = json.loads(response.text)

    # iterate through the photos and display keywords/timestamp for each
    for photo in resp['photos']['photo']:
        keywords = set() # set of unique keywords
        title = photo['title']
        user_id = photo['owner']
        photo_id = photo['id']
        secret = photo['secret']
        photo_url = 'http://flickr.com/photos/' + user_id + '/' + photo_id
        keywords.add(title.strip().lower())

        # get info for this single photo
        endpoint = 'https://api.flickr.com/services/rest/' + \
            '?method=flickr.photos.getInfo' + \
            '&api_key=cbfb84b23a5a7af2a0bf27cc8a87d85b&photo_id=' + photo_id + \
            '&secret=' + secret + '&format=json&nojsoncallback=1'
        response = requests.get(endpoint)
        photo_info = json.loads(response.text)
        taken = photo_info['photo']['dates']['taken']
        for tag in photo_info['photo']['tags']['tag']:
            tagname = tag['raw']
            keywords.add(tagname.strip().lower())

        print(photo_url + ' - ' + taken + ' - ' + str(keywords))

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    get_tags_example('dogerino')
