import spotipy
from spotify_api_details import sp

def get_album_info(album_id):
    album = sp.album(album_id)

    album_info = {
        'name': album['name'],
        'release_date': album['release_date'],
        'total_tracks': album['total_tracks'],
        'artists': [artist['name'] for artist in album['artists']],
        'tracks': [track['name'] for track in album['tracks']['items']]
    }
    return album_info

album_id = "4aawyAB9vmqN3uQ7FjRGTy"
print(get_album_info(album_id))
