import os
import pickle
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

def spotify_play_album(album_name):
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
    # Searches the album name and finds the most popular match and then provides the URI from that
    results = sp.search(q=album_name, type='album', limit=1)
    albums = results['album']['items']
    if albums:
         album = albums[0]['uri'] 
    else:
        print("No tracks found for:", album_name)
        return None
    # Uses the URI to play the album on Spotify
    try:
        for track in album:
            sp.start_playback(uris=[track])
            print("Playing")
    except spotipy.SpotifyException as e:
        print("Error", e)
