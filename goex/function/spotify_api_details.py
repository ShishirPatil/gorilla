import spotipy
from spotipy.oauth2 import SpotifyOAuth

def create_spotify_api_object():
    scope = "user-library-read"

    client_id = 'd711dfc0d97440cb898b08fbdc2083c1' 
    client_secret = '1d4854768be047438a72d48a8c4622ab'
    redirect_uri = 'http://localhost:8888/callback'

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id = client_id,
                                                client_secret = client_secret,
                                                redirect_uri = redirect_uri,
                                                scope=scope))