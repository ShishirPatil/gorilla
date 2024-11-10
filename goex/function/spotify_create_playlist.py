import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

def spotify_create_playlist(name,user):
    # Define required scopes for playback
    scope = "playlist-modify-public,playlist-modify-private"

    # Initialization
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id='0322795be61e4903af31ff1c14248eb0',
        client_secret='493439dbbf2143acb9ce28ad6dd62634',
        redirect_uri='http://localhost:8888/callback',  #Change ID, Secret, and redirct uri to match the correct ones
        scope=scope
    ))

    # create playlist with inputted name and user ID
    try:
        playlist = sp.user_playlist_create(user=user, name=name, public=True, collaborative=False, description='')
        print(f"Playlist '{name}' created")
        return playlist
    except spotipy.SpotifyException as e:
        print("Error", e)