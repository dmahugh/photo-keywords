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

    # get the first 10 photos
    per_page = '10' # max=500 for production use later
    endpoint = 'https://api.flickr.com/services/rest/' + \
        '?method=flickr.people.getPhotos' + \
        '&api_key=cbfb84b23a5a7af2a0bf27cc8a87d85b&user_id=' + user_id + \
        '&per_page=' + per_page + '&format=json&nojsoncallback=1'
    response = requests.get(endpoint)
    photolist = json.loads(response.text)

    # iterate through the photos and display keywords/timestamp for each
    for photo in photolist['photos']['photo']:
        photo_info = photo_detail(photo) # photos.getInfo API call

        # create list of keywords (including the title)
        keywords = {tag['raw'].strip().lower() for tag in photo_info['photo']['tags']['tag']}
        keywords.add(photo['title'].strip().lower())

        # display a summary of this image
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
    user_id = photo['owner']
    photo_id = photo['id']
    secret = photo['secret']

    endpoint = 'https://api.flickr.com/services/rest/' + \
        '?method=flickr.photos.getInfo' + \
        '&api_key=cbfb84b23a5a7af2a0bf27cc8a87d85b&photo_id=' + photo_id + \
        '&secret=' + secret + '&format=json&nojsoncallback=1'
    response = requests.get(endpoint)
    return json.loads(response.text)

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    get_tags_example('dogerino')
