from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(10), nullable=False, default='user')
    playlists = db.relationship('Playlist', backref='owner', foreign_keys='Playlist.user_id', cascade = 'delete')
    ratings = db.relationship('Rating', backref='user', foreign_keys='Rating.user_id', cascade = 'delete')

class Creator(db.Model):
    __tablename__ = "creator"
    creator_id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    albums = db.relationship('Album', backref='creator', foreign_keys='Album.artist', cascade = 'delete')

class Song(db.Model):
    __tablename__ = "song"
    song_id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    song_name = db.Column(db.String(100), nullable=False)
    lyrics = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.album_id'), nullable=False)
    ratings = db.relationship('Rating', backref='song', foreign_keys='Rating.song_id', cascade = 'delete')
    playlists = db.relationship('PlaylistSong', backref='song', foreign_keys='PlaylistSong.song_id')
    flagged = db.Column(db.Boolean, nullable=False, default=False)

class Rating(db.Model):
    __tablename__ = "rating"
    rating_id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.song_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

class Album(db.Model):
    __tablename__ = "album"
    album_id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    album_name = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    artist = db.Column(db.Integer, db.ForeignKey('creator.creator_id'), nullable=False)
    songs = db.relationship('Song', backref='album', foreign_keys='Song.album_id', cascade = 'delete')

class Playlist(db.Model):
    __tablename__ = "playlist"
    playlist_id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    playlist_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    songs = db.relationship('PlaylistSong', backref='playlist', foreign_keys='PlaylistSong.playlist_id')

class PlaylistSong(db.Model):
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.playlist_id'), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.song_id'), primary_key=True)
