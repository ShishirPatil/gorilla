import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

def spotify_queue(song_name):
    # Define scope
    scope = "user-modify-playback-state"

    # Initialization
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id='0322795be61e4903af31ff1c14248eb0',
        client_secret='493439dbbf2143acb9ce28ad6dd62634',
        redirect_uri='http://localhost:8888/callback',  #Change ID, Secret, and redirct uri to match the correct ones
        scope=scope
    ))

    # Get track uri from the song name
    # searches song name and finds the most popular match and then provides the URI from that
    results = sp.search(q=song_name, type='track', limit=1)
    tracks = results['tracks']['items']
    if tracks:
        song = tracks[0]['uri'] 
    else:
        print("No tracks found")
        return None
    # Uses the URI to add the song to queue on Spotify
    try:
        sp.add_to_queue(song)
        print(tracks[0]['name'], "added to queue:")
    except spotipy.SpotifyException as e:
        print('Error', e)