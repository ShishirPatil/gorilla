import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

def spotify_play_song(song_name):
    # Define required scopes for playback
    scope = "user-modify-playback-state,user-read-playback-state,user-read-currently-playing"

    # Initialize Spotify API client with user authorization
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id='0322795be61e4903af31ff1c14248eb0',
        client_secret='493439dbbf2143acb9ce28ad6dd62634',
        redirect_uri='http://localhost:8888/callback',  #Change ID, Secret, and redirct uri to match the correct ones
        scope=scope
    ))
    # Get list of available devices
    devices = sp.devices()
    if not devices['devices']:
        print("No active devices found")
        return None

    # # Print the available devices for reference
    # print("Available devices:")
    # for i, device in enumerate(devices['devices']):
    #     print(f"{i + 1}. {device['name']} (ID: {device['id']})")

    # Choose the first available device (or specify a preferred one)
    device_id = devices['devices'][0]['id']

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
    try:
        sp.start_playback(device_id=device_id,uris=[song])
        print("Playing")
    except spotipy.SpotifyException as e:
        print("Error", e)

spotify_play_song('dead girl walking')