import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

def spotify_play_album(album_name):
     # Define scopes
    scope = "user-modify-playback-state,user-read-playback-state,user-read-currently-playing"

    # Initialization
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id='0322795be61e4903af31ff1c14248eb0',
        client_secret='493439dbbf2143acb9ce28ad6dd62634',
        redirect_uri='http://localhost:8888/callback',  #Change ID, Secret, and redirct uri to match the correct ones
        scope=scope
    ))

    # Searches the album name and finds the most popular match and then provides the URI from that
    results = sp.search(q=album_name, type='album', limit=1)
    albums = results['albums']['items']
    if albums:
         album = albums[0]['uri'] 
    else:
        print("No tracks found for:", album_name)
        return None
    
    # Uses the URI to play the album on Spotify
    try:
        print("Playing album:", albums[0]['name'])
        sp.start_playback(context_uri=album)
    except spotipy.SpotifyException as e:
        print("Error", e)