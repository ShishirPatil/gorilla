import os
import pickle
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

def spotify_list_artist_albums(artist):
    # Initialization
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id='0322795be61e4903af31ff1c14248eb0',
        client_secret='493439dbbf2143acb9ce28ad6dd62634',
        redirect_uri='http://localhost:8888/callback', #Change ID, Secret, and redirct uri to match the correct ones
    ))

    # Returns the most popular artist's URI with the same name 
    results = sp.search(q=artist, type='artist', limit=1)
    artista = results['artists']['items']

    if artista:     
         artistaa = artista[0]['uri'] 
    else:
        print("No artist found for:", artist)
        return None

    # Uses the artist URI to search through their spotify discography and returns the names of all their albums
    albums_results = sp.artist_albums(artistaa, album_type='album')
    albums = albums_results['items']

    while albums_results['next']:
        albums_results = sp.next(albums_results)
        albums.extend(albums_results['items'])

    for album in albums:
        print(album['name'])