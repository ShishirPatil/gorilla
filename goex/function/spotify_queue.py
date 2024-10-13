import os
import pickle
import spotipy
from spotipy import add_to_queue
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
def spotify_queue(song_name):
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
    # Get track uri from the song name
    # '''searches song name and finds the most popular match and then provides the URI from that'''
    results = sp.search(q=song_name, type='track', limit=1)
    tracks = results['tracks']['items']
    if tracks:
        song = tracks[0]['uri'] 
    else:
        print("No tracks found for:", song_name)
        return None
    # Uses the URI to play the song on Spotify
    add_to_queue(song, device_id=None)