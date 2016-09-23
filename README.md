# photo-keywords

Tools for managing keywords associated with photographs.

For now, only includes [flickrtags.py](https://github.com/dmahugh/photo-keywords/blob/master/flickrtags.py), a program to harvest all photo tags from my Dougerino and Dogerino accounts on Flickr.

## Flickr Tags

First step was to get all of my Flickr tags local, where I can associated them with the original images in my backup stream. This requires
two sets of calls to the Flickr API: first we get photos for each account (method=flickr.people.getPhotos), then for each photo we get
the tags and timestamp (method=flick.photos.getInfo).

Summary of data retrieved:

| Flickr account | Photos | Tags |
| --- | --- | --- |
| [Dougerino](http://flickr.com/photos/dougerino) | 12,205 | 35,742 |
| [Dogerino](http://flickr.com/photos/dogerino) | 10,713 | 27,206 |
| TOTAL | 22,918 | 62,948 |

![monthly totals](images/monthlytotals.png)

As described [here](http://mahugh.com/2013/04/02/my-backup-process/), I've been using Flickr to search my photos
for years. But now that I have all of my photo-description data local (including the Flickr tags as well as other
information from various sources), I'm going to merge it into a single consistent approach to tagging my photos.
Then I'll put together a simple search facility that I'll stand up where I can use it from any device.
