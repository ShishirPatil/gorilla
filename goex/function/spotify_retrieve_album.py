import spotipy
from spotify_api_details import sp

def get_album_info(album_name):

    # search for the album
    results = sp.search(q=album_name, type='album', limit=1)
    albums = results['albums']['items']
    
    if not albums:
        print("No album found")
        return None

    # Choose the most popular album
    album = albums[0]['uri'] 
    albuminfo = sp.album(album)

    # Find the tracks in the album
    tracks = sp.album_tracks(album)['items']

    album_info = {
        'name': albuminfo['name'],
        'release_date': albuminfo['release_date'],
        'total_tracks': albuminfo['total_tracks'],
        'artists': [artist['name'] for artist in albuminfo['artists']],
        'tracks': [track['name'] for track in tracks]
    }
    print(album_info)
    return album_info
