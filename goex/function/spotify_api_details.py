import os
import sys
import json
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def create_spotify_api_object():
    scope = "user-library-read"

    client_id = '0322795be61e4903af31ff1c14248eb0' 
    client_secret = '493439dbbf2143acb9ce28ad6dd62634'
    redirect_uri = 'http://localhost:8888/callback'

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id = client_id,
                                                client_secret = client_secret,
                                                redirect_uri = redirect_uri,
                                                scope=scope))
    return sp

sp = create_spotify_api_object()