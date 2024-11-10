import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

def spotify_pause():
    # Describe Scope
    scope = "user-modify-playback-state"

    # Initialization 
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id='0322795be61e4903af31ff1c14248eb0',
        client_secret='493439dbbf2143acb9ce28ad6dd62634',
        redirect_uri='http://localhost:8888/callback',  #Change ID, Secret, and redirct uri to match the correct ones
        scope=scope
    ))

    # Get list of available devices
    devices = sp.devices()
    if not devices['devices']:
        print("No devices found")
        return None

    # Choose the first available device (or specify a preferred one)
    device_id = devices['devices'][0]['id']

    # Check to see if a song is currently playing and Pause if there is
    try: 
        if sp.currently_playing:
            sp.pause_playback()
            print('Paused')
        else:
            print("No song currently playing")
    except spotipy.SpotifyException as e:
        print('error', e)