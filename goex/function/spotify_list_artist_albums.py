import os
import pickle
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

def spotify_list_artist_albums(artist):
    # Load spotify credentials
    credentials_path = './credentials/spotify/token.pickle'
    if os.path.exists(credentials_path):
        with open(credentials_path, 'rb') as token_file:
            spotify_token = pickle.load(token_file)
    else:
        raise FileNotFoundError("Spotify token file not found.")
    token_info = SpotifyOAuth(token=spotify_token)
    # Initialization 
    if not token_info:
        print("No account found")
        return None
    else:
        sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    if sp is None:
        return None
    # Returns the most popular artist's URI with the same name 
    results = sp.search(q=artist, type='artist', limit=1)
    artista = results['artist']['items']
    if artista:
         artistaa = artista[0]['uri'] 
    else:
        print("No artist found for:", artist)
        return None
    # Uses the artist URI to search through their spotify discography and returns the names of all their albums

    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    albums_results = spotify.artist_albums(artistaa, album_type='album')
    albums = albums_results['items']
    while albums_results['next']:
        albums_results = spotify.next(albums_results)
        albums.extend(albums_results['items'])

    for album in albums:
        print(album['name'])