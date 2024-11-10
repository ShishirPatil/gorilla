import os
import pickle
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

def spotify_add_song_playlist(playlist_name, track_name):
    # Define required scopes for playback
    scope = "playlist-modify-public,playlist-modify-private"

    # Initialization
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id='0322795be61e4903af31ff1c14248eb0',
        client_secret='493439dbbf2143acb9ce28ad6dd62634',
        redirect_uri='http://localhost:8888/callback',  #Change ID, Secret, and redirct uri to match the correct ones
        scope=scope
    ))

    # Find playlist URI from playlist name
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            playlist_id = playlist['id']
            break
    if not playlist_id:
        print('No playlist found')
        return None

    # Find song that you want to add
    track_results = sp.search(q=track_name, type='track', limit=1)
    tracks = track_results['tracks']['items']    
    if not tracks:
        print('No song founf')
        return None
    track_uri = tracks[0]['uri']  

    # Add song to playlist
    try:
        sp.playlist_add_items(playlist_id, [track_uri])
        print(f'{track_name} was added to {playlist_name}')
    except spotipy.SpotifyException as e:
        print('Error', e)       


spotify_add_song_playlist('anay', 'dep gai')