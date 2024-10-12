import os
import pickle 
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# results = sp.current_user_saved_tracks()
# for idx, item in enumerate(results['items']):
#     track = item['track']
#     print(idx, track['artists'][0]['name'], " – ", track['name'])

album = 'spotify:album:4o57W8cMFiKf2NVbGSE9jH'

results = sp.artist_albums(album, album_type='album')
albums = results['items']
while results['next']:
    results = sp.next(results)
    albums.extend(results['items'])

for album in albums:
    print(album['name'])