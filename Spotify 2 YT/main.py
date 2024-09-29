import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
import yt_dlp
import re
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QMessageBox, QProgressBar, QHBoxLayout)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt

# Spotify API Credentials
SPOTIPY_CLIENT_ID = '70d6f50dfbbb4f82943152674b35a479'
SPOTIPY_CLIENT_SECRET = 'c559d58046e94a73b50aac6947d3091a'
SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'
SCOPE = 'playlist-read-private'
YOUTUBE_API_KEY = 'AIzaSyAD6d0XbOm3XfT8vOKD4gtnae3uqnnTCdc'

# Initialize Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE
))


def extract_playlist_id(url):
    pattern = r'(?<=playlist/)([^?]*)'
    match = re.search(pattern, url)
    return match.group(0) if match else None

def get_playlist_tracks(playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = []
    while results:
        for item in results['items']:
            track = item['track']
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            tracks.append(f"{track_name} - {artist_name}")
        results = sp.next(results) if results['next'] else None
    return tracks

def search_youtube(query):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=query,
        part='snippet',
        maxResults=1
    )
    response = request.execute()
    if response['items']:
        video_id = response['items'][0]['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return video_url
    else:
        return None

def download_youtube_video_as_mp3(video_url, progress_bar):
    def progress_hook(d):
        if d['status'] == 'downloading':
            if d['total_bytes'] > 0:  # Ensure total_bytes is not zero
                progress_value = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
                progress_bar.setValue(progress_value)

    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': '/opt/homebrew/bin/ffmpeg',
        'progress_hooks': [progress_hook],  # Add progress hook
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

def process_playlist(playlist_url, progress_bar):
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        QMessageBox.critical(None, "Error", "Invalid playlist URL.")
        return

    tracks = get_playlist_tracks(playlist_id)
    progress_bar.setMaximum(len(tracks))

    for track in tracks:
        video_url = search_youtube(track)
        if video_url:
            download_youtube_video_as_mp3(video_url, progress_bar)
            progress_bar.setValue(progress_bar.value() + 1)
            QMessageBox.information(None, "Download Complete", f"Downloaded: {track}")

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Spotify to YouTube Downloader")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: #2c2f33; color: white;")  # Background color

        layout = QVBoxLayout()

        self.label = QLabel("Enter Spotify Playlist URL:")
        layout.addWidget(self.label)

        self.url_input = QLineEdit(self)
        layout.addWidget(self.url_input)

        self.download_button = QPushButton("Download MP3s", self)
        self.download_button.setIcon(QIcon("download_icon.png"))  # Set the download icon
        self.download_button.setStyleSheet("background-color: #7289da; color: white;")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def start_download(self):
        playlist_url = self.url_input.text()
        process_playlist(playlist_url, self.progress_bar)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())