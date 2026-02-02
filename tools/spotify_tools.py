import spotipy
from spotipy.oauth2 import SpotifyOAuth
from langchain_core.tools import tool
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

# authentication to Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri="http://localhost:8888/callback",
    scope="user-modify-playback-state user-read-playback-state",
    open_browser=False
))

@tool
def play_music(query: str):
    """
    Spelar musik på Spotify. 
    Används när användaren säger 'spela jazz', 'spela Avicii', etc.
    Input ska vara söktermen (t.ex. 'Jazz', 'Rock', 'Artistnamn').
    """
    try:

        # check if spotify is running
        devices = sp.devices()
        if not devices or not devices['devices']:
            return "Spotify verkar inte vara igång. Öppna Spotify först."

        
        # search for track/playlist
        results = sp.search(q=query, limit=1, type='track,playlist')
        
        if results['tracks']['items']:
            uri = results['tracks']['items'][0]['uri']
            sp.start_playback(uris=[uri])
            return f"Spelar '{query}' på Spotify."
        else:
            return f"Hittade inget som matchade '{query}'."

    except Exception as e:
        return f"Kunde inte spela musik. Se till att Spotify är igång och inloggat. Fel: {e}"