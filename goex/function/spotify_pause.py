import pyautogui
import os
import pickle
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

def spotify_pause():
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
    # Check to see if a song is currently playing
    if sp.currently_playing:
        pyautogui.press('stop')
    else:
        print("No song currently playing")