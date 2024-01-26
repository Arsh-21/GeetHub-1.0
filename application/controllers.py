import os
from flask import Flask, render_template, redirect, request, url_for, flash
from flask import current_app as app
from application.models import *
from sqlalchemy import or_,and_
 
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user:
            flash('User already exists. Kindly login')
        else:
            a = User (username=username,password=password)
            db.session.add(a)
            db.session.commit()
            flash ('User Created')
            return redirect(url_for('user_login')) 


@app.route("/user_login", methods=['GET','POST'])
def user_login():
    if request.method == 'GET':
        return render_template("user_login.html")

    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Kindly Check you user name or password')
            return redirect(url_for('user_login'))
        
        if not (user.password == password):
            flash("Kindly Check you user name or password")
            return redirect(url_for('user_login'))

        if user.user_type == 'admin':
            flash('Not a user')
            return redirect(url_for('home'))    
        redirect_url_with_un = "/"+username+"/user_home_page"
        return redirect(redirect_url_with_un)


@app.route("/admin_login", methods = ['GET','POST'])
def admin_login():
    if request.method == 'GET':
        return render_template("admin_login.html")

    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username = username).first()
        
        if user is None:
            flash("Check username")
            return redirect(url_for('admin_login'))

        if user.user_type != "admin":
            flash("You are not an admin")
            return redirect(url_for('admin_login'))
       
        elif not (user.password == password):
            flash("Kindly check your password")
            return redirect(url_for('admin_login'))
        redirect_url_with_un = "/"+username+"/admin_dashboard"
        return redirect(redirect_url_with_un)
   

@app.route("/<string:username>/user_home_page")
def user_home_page(username):
    recommended_Song_rating = db.session.query(Rating).join(Song).filter(
        and_(Song.flagged == False, Rating.song_id == Song.song_id)
    ).order_by(Rating.rating.desc()).all()

    
    rating={}
    for i in recommended_Song_rating:
        current_song = Song.query.filter_by(song_id=i.song_id).first() 
        if i.song_id in list(rating.keys()):
            song_rating_sum = rating[i.song_id][1]
            count = rating[i.song_id][2]
            rating[i.song_id] = [current_song.song_name,song_rating_sum+i.rating,count+1,i.song_id]
        else:
            rating[i.song_id] = [current_song.song_name,i.rating,1,i.song_id]
    
    for i in list(rating.keys()):
        rating[i] = [rating[i][0],rating[i][1],rating[i][2],rating[i][1]/rating[i][2],rating[i][3],username]

    rating_list = list(rating.values())[:10]

    user = User.query.filter_by(username = username).first() 
    user_id = user.user_id
    playlist_data = Playlist.query.filter_by(user_id = user_id)

    playlist_user_list = []
    for i in playlist_data:
        playlist_songs = PlaylistSong.query.filter_by(playlist_id = i.playlist_id)
        num_playlist = len(list(playlist_songs))
        playlist_user_list.append((i.playlist_id,i.playlist_name,num_playlist))

    album_data=Album.query.all()
    genre_data={}
    for i in album_data:
        song_data=Song.query.filter_by(album_id=i.album_id, flagged = False)
        album_song_data_list=[]
        for j in song_data:
            song_data= Song.query.filter_by(song_id=j.song_id, flagged = False).first()
            album_data= Album.query.filter_by(album_id=song_data.album_id).first()
            creator_data = Creator.query.filter_by(creator_id=album_data.artist).first()
            artist_data=User.query.filter_by(user_id=creator_data.user_id).first()
            song=[j.song_id,j.song_name,artist_data.username]
            album_song_data_list.append(song)
        if i.genre in genre_data.keys():
            genre_data[i.genre]=genre_data[i.genre]+album_song_data_list
        else:
            genre_data[i.genre]=album_song_data_list

    genre_data_list=list(genre_data.items())
    return render_template("user_home_page.html",username = username, recommended_data = rating_list, playlist_data = playlist_user_list,genre_data=genre_data_list)

@app.route("/<string:username>/song/<int:song_id>", methods = ["GET","POST"])
def song_details(song_id,username):
    song_data= Song.query.filter_by(song_id=song_id, flagged = False).first()
    album_data= Album.query.filter_by(album_id=song_data.album_id).first()
    creator_data = Creator.query.filter_by(creator_id=album_data.artist).first()
    artist_data=User.query.filter_by(user_id=creator_data.user_id).first()
    song_data_list=[song_data.song_name,song_data.lyrics,song_data.duration,str(song_data.date_created)[:4],song_data.album_id,song_data.ratings,song_data.playlists,artist_data.username,album_data.album_name,username]
    if request.method == "GET":
        return render_template("song.html", song = song_data_list, username = username,song_id = song_id)
    
    if request.method == "POST":
        rating = int(request.form.get('rating'))
        user = User.query.filter_by(username = username).first()
        ratings = Rating.query.all()
        for x in ratings:
            if (x.user_id == user.user_id) and (x.song_id == song_id):
                x.rating = rating
                db.session.commit()
                return render_template("song.html", song = song_data_list, username = username,song_id = song_id)

        a = Rating(user_id = user.user_id, song_id = song_id, rating = rating)
        db.session.add(a)
        db.session.commit()
        return render_template("song.html", song = song_data_list, username = username,song_id = song_id)


@app.route("/<string:username>/playlist/<int:playlist_id>")
def playlist_page(username,playlist_id):
    details = []
    playlist_data = Playlist.query.filter_by(playlist_id = playlist_id).first()
    playlist_songs = PlaylistSong.query.filter_by(playlist_id = playlist_id)
    for i in playlist_songs:
        song_detail = Song.query.filter_by(song_id = i.song_id, flagged = False).first()
        album_detail = Album.query.filter_by(album_id = song_detail.album_id).first()
        creator_detail = Creator.query.filter_by(creator_id = album_detail.artist).first()
        x = User.query.filter_by(user_id = creator_detail.user_id).first()
        details.append((song_detail.song_name, song_detail.duration, x.username ,album_detail.album_name,song_detail.song_id,album_detail.album_id))
    return render_template("playlist.html",username=username, details = details,name = playlist_data.playlist_name, playlist_id = playlist_id)

@app.route("/<string:username>/create_playlist", methods = ["GET","POST"])
def create_playlist(username):
    if request.method == "GET":
        return render_template("create_playlist.html",username=username)
    
    if request.method == "POST":
        user = User.query.filter_by(username = username).first()
        playlist_name = request.form.get("playlist_name")
        if playlist_name != '':
            a = Playlist(playlist_name = playlist_name, user_id = user.user_id)
            db.session.add(a)
            db.session.commit()
            return redirect(url_for("edit_playlist", username=username, playlist_id=a.playlist_id))
        else:
            flash("Enter playlist name")
            return render_template("create_playlist.html",username=username)    

    # songs = []
    # song_details = Song.query.all()
    # for i in song_details:
    #     songs.append(i.song_name)
    # # continue
        
    

@app.route("/<string:username>/edit_playlist/<int:playlist_id>", methods = ["GET","POST"])
def edit_playlist(username,playlist_id):
    if request.method == "GET":
        x = Playlist.query.filter_by(playlist_id = playlist_id).first()
        playlist = x.playlist_name
        all_songs = []
        song_details = Song.query.filter_by(flagged = False)
        for i in song_details:
            all_songs.append((i.song_id,i.song_name))
        song_in_playlist = PlaylistSong.query.filter_by(playlist_id = playlist_id)
        songs_in_playlist = []
        for song in song_in_playlist:
            songs_in_playlist.append(song.song_id)
        return render_template("edit_playlist.html",username=username,playlist_name = playlist,songs = all_songs,playlist_id = playlist_id, songs_in_playlist = songs_in_playlist)
    
    if request.method == "POST":
        song_id = request.form.get("song_id")
        action = request.form.get("action") 
        if action == "add":
            playlist_song = PlaylistSong(playlist_id=playlist_id, song_id=song_id)
            db.session.add(playlist_song)
            db.session.commit()
            
        elif action == "remove":
            song_to_remove = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song_id).first()
            db.session.delete(song_to_remove)
            db.session.commit()
        return redirect(url_for("edit_playlist", username=username, playlist_id=playlist_id))

@app.route("/<string:username>/album/<int:album_id>")
def album(username,album_id):
    album_data=Album.query.filter_by(album_id=album_id).first()
    song_data=Song.query.filter_by(album_id=album_id, flagged = False)
    creator_data=Creator.query.filter_by(creator_id=album_data.artist).first()
    username_artist=User.query.filter_by(user_id=creator_data.user_id).first()
    album_song_data_list=[]
    for i in song_data:
        song=[i.song_id,i.song_name]
        album_song_data_list.append(song)
    album_data_list=[album_data.album_name,album_data.genre,album_data.artist,len(album_song_data_list),album_song_data_list,username_artist.username]
    return render_template("album.html",album=album_data_list,username=username)

@app.route("/<string:username>/creator_register", methods = ["GET","POST"])
def creator_register(username):
    if request.method == "GET":
        return render_template("creator_register.html",username=username)
    elif request.method == "POST":
        user = User.query.filter_by(username=username).first()
        user.user_type="creator"
        db.session.commit()
        a =  Creator(user_id=user.user_id)
        db.session.add(a)
        db.session.commit()
        return render_template("creator_home.html",username=username)

@app.route("/<string:username>/creator_home")
def creator_home(username):
    user_data=User.query.filter_by(user_type="creator")
    user_data_list=[]
    for i in user_data:
        user_data_list.append(i.username)
    if username in user_data_list:
        return render_template("creator_home.html",username=username)
    else:
        url_string="/"+username+"/creator_register"
        return redirect(url_string)

from datetime import datetime

@app.route("/<string:username>/upload_song/<int:album_id>" ,methods = ['GET','POST'])
def upload_song(username,album_id):
    if request.method == 'GET':
        return render_template("upload_song.html",username=username,album_id = album_id)

    elif request.method=='POST':
        title = request.form.get('title')
        duration = request.form.get('duration')
        releaseDate = request.form.get('releaseDate')
        date_created = datetime.strptime(releaseDate, '%Y-%m-%d')
         
        lyrics = request.form.get('lyrics')
        a = Song(song_name = title, lyrics = lyrics , duration = duration, date_created = date_created, album_id = album_id)
        db.session.add(a)
        db.session.commit()
        return render_template("creator_home.html",username = username)


@app.route("/<string:username>/add_song_from_album")
def add_song_from_album(username):
    album_info=[]
    user = User.query.filter_by(username=username).first()
    creator = Creator.query.filter_by(user_id=user.user_id).first()
    album = Album.query.filter_by(artist = creator.creator_id) 
    for i in album:
        album_info.append((i.album_id,i.album_name,i.genre,username))
    return render_template("add_song_from_album.html", username=username, album_info=album_info)

@app.route("/<string:username>/delete_album/<int:album_id>", methods=["POST"])
def delete_album(username, album_id):
    # Get the album to delete
    album_to_delete = Album.query.get(album_id)

    if album_to_delete:
        # Perform deletion
        db.session.delete(album_to_delete)
        db.session.commit()
        flash('Album deleted successfully', 'success')
    else:
        flash('Album not found', 'error')

    return redirect(url_for('add_song_from_album', username=username))

    

@app.route("/<string:username>/create_album", methods = ["GET","POST"])
def create_album(username):
    if request.method == 'GET':
        return render_template("create_album.html",username=username)

    elif request.method=='POST':
        name = request.form.get('name')
        genre = request.form.get('genre')
        x = User.query.filter_by(username=username).first()
        y = Creator.query.filter_by(user_id = x.user_id).first()
        a = Album(album_name = name, genre = genre, artist = y.creator_id)
        db.session.add(a)
        db.session.commit()
        return render_template("creator_home.html",username=username)

@app.route("/<string:username>/edit_song/<int:song_id>", methods = ["GET","POST"])
def edit_song(username,song_id):
    song_details = Song.query.filter_by(song_id = song_id).first()
    song_detail = [song_details.song_id,song_details.song_name, song_details.lyrics, song_details.duration, song_details.date_created, song_details.album_id]
    if request.method == 'GET':   
        return render_template("edit_song.html",username=username,song_detail = song_detail, song_id = song_id)
    
    elif request.method=='POST':
        title = request.form.get('title')
        duration = request.form.get('duration')
        releaseDate = request.form.get('releaseDate')
        date_created = datetime.strptime(releaseDate, '%Y-%m-%d')
        lyrics = request.form.get('lyrics')
        song_details.song_name = title
        song_details.duration = duration
        song_details.date_created = date_created
        song_details.lyrics = lyrics
        db.session.commit()
        return render_template("creator_home.html",username = username)

@app.route("/<string:username>/edit_album/<int:album_id>", methods = ["GET","POST"])
def edit_album(username,album_id):
    album_details = Album.query.filter_by(album_id = album_id).first()
    album_detail = [album_details.album_id, album_details.album_name, album_details.genre, album_details.artist]
    print(album_detail)   
    if request.method == 'GET':
        return render_template("edit_album.html", album_name = album_details.album_name, username=username,album_detail = album_detail, album_id = album_id)
    elif request.method=='POST':
        name = request.form.get('name')
        genre = request.form.get('genre')
        album_details.album_name = name
        album_details.genre = genre
        db.session.commit()
        return render_template("creator_home.html",username = username)


@app.route("/<string:username>/creator_dashboard", methods = ["GET","POST"])
def creator_dashboard(username):
    if request.method == "GET":
        user = User.query.filter_by(username = username).first()
        creator = Creator.query.filter_by(user_id = user.user_id).first()
        albums = Album.query.filter_by(artist = creator.creator_id)
        album_data = []
        song_data = []
        album_count = 0
        song_count = 0
        ratings = []
        for album in albums:
            album_count +=1
            album_data.append((album.album_id,album.album_name, album.genre))
            songs = Song.query.filter_by(album_id = album.album_id)
            for song in songs:
                rating_data = Rating.query.filter_by(song_id = song.song_id)
                for i in rating_data:
                    ratings.append(i.rating)
                
                song_count+=1
                song_data.append((song.song_id,song.song_name,song.duration,str(song.date_created)[:11],album.album_name, song.flagged))
        if len(ratings)==0:
            data = ["--",song_count,album_count]
        else:
            data = [sum(ratings)/len(ratings),song_count,album_count]
        return render_template("creator_dashboard.html",username=username,album_data = album_data, song_data = song_data, data = data)
    
    elif request.method == "POST":
        entry_type = request.form.get("entry_type")
        entry_id = request.form.get("entry_id")
        if entry_type == "song":
            song = Song.query.get(entry_id)
            # delete playlist entries of that song first
            temps = PlaylistSong.query.filter_by(song_id = entry_id)
            for temp in temps:
                db.session.delete(temp)
                db.session.commit()
            db.session.delete(song)
            db.session.commit()
            
        elif entry_type == "album":
            album = Album.query.get(entry_id)
            songs = Song.query.filter_by(album_id = entry_id) 
            for song in songs:
                temps = PlaylistSong.query.filter_by(song_id = song.song_id)
                for temp in temps:
                    db.session.delete(temp)
                    db.session.commit()
            db.session.delete(album)
            db.session.commit()
        return redirect(url_for("creator_dashboard", username=username))

@app.route("/<string:username>/admin_dashboard")
def admin_dashboard(username):
    user = User.query.filter_by(username = username).first()
    if user.user_type != 'admin':
        flash('Not accessible to user')
        return redirect(url_for("home"))
    temp = []
    normal_users = User.query.filter_by(user_type = "user")
    creators = User.query.filter_by(user_type = "creator")
    num1=0
    for i in normal_users:
        num1+=1   
    creators = User.query.filter_by(user_type = "creator")
    num2=0
    for i in creators:
        num2+=1
    temp.append(num1+num2)
    temp.append(num2) 
    songs = Song.query.filter_by(flagged = False)
    num3=0
    for i in songs:
        num3+=1
    temp.append(num3) 
    albums = Album.query.all()
    num4=0
    genres=[]
    for i in albums:
        num4+=1
        if i.genre not in genres:
            genres.append(i.genre)
    temp.append(num4) 
    temp.append(len(genres))

    # Top 5 Songs based on rating
    song_rating = {}
    for song in songs:
        ratings = Rating.query.filter_by(song_id=song.song_id).all()
        if ratings:
            total_rating = sum(r.rating for r in ratings)
            if len(ratings) != 0: 
                avg_rating = total_rating / len(ratings)
                avg_rating = 0
            song_rating[song.song_name] = avg_rating

    top_songs = sorted(song_rating.items(), key=lambda x: x[1], reverse=True)[:3]

    # Top 5 Albums based on average song ratings
    album_rating = {}
    for album in albums:
        album_songs = Song.query.filter_by(album_id=album.album_id,flagged = False).all()
        if album_songs:
            if len(album_songs) != 0:
                total_album_rating = sum(song_rating.get(s, 0) for s in album_songs) / len(album_songs)
            album_rating[album.album_name] = total_album_rating

    top_albums = sorted(album_rating.items(), key=lambda x: x[1], reverse=True)[:3]

    # Top 5 Creators based on average album ratings
    creator_rating = {}
    Creators = Creator.query.all()
    for c in Creators:
        u = User.query.filter_by(user_id = c.user_id).first()
        c_name = u.username
        creator_albums = Album.query.filter_by(artist=c.creator_id).all()
        if creator_albums:
            if len(creator_albums) != 0:
                total_creator_rating = sum(album_rating.get(a, 0) for a in creator_albums) / len(creator_albums)
            creator_rating[c_name] = total_creator_rating

    top_creators = sorted(creator_rating.items(), key=lambda x: x[1], reverse=True)[:3]

    return render_template("admin_dashboard.html", username=username, temp=temp,
                           top_songs=top_songs, top_albums=top_albums, top_creators=top_creators)

@app.route("/<string:username>/admin_tracks", methods = ["GET","POST"])
def admin_tracks(username):
    if request.method == 'GET':
        user = User.query.filter_by(username = username).first()
        if user.user_type != 'admin':
            flash('Not accessible to user')
            return redirect(url_for("home"))
        track_info = []
        tracks = Song.query.all()
        for i in tracks:
            x1 = Album.query.filter_by(album_id = i.album_id).first()
            x2 = Creator.query.filter_by(creator_id=x1.artist).first()
            x3 = User.query.filter_by(user_id=x2.user_id).first()
            track_info.append((i.song_id,i.song_name,i.duration,str(i.date_created)[:11],x1.album_name,x3.username,i.flagged))
        return render_template("admin_tracks.html",username=username, track_info = track_info)
    
    elif request.method == 'POST':
        song_id = request.form['song_id']
        song_to_delete = Song.query.filter_by(song_id = song_id).first()
        delete_from_playlist = PlaylistSong.query.filter_by(song_id = song_id)    
        # delete_from_rating = Rating.query.filter_by(song_id = song_id)  
        for x in delete_from_playlist:
            db.session.delete(x)
            db.session.commit()
        db.session.delete(song_to_delete)
        db.session.commit()
        # for x in delete_from_rating:
        #     db.session.delete(x)
        #     db.session.commit()
        url = "/"+username+"/admin_tracks"
        return redirect(url_for(url))
            


@app.route("/<string:username>/admin_albums", methods = ["GET","POST"])
def admin_albums(username):
    if request.method == 'GET':
        user = User.query.filter_by(username = username).first()
        if user.user_type != 'admin':
            flash('Not accessible to user')
            return redirect(url_for("home"))
        album_info=[]
        album = Album.query.all() 
        for i in album:
            x1 = Creator.query.filter_by(creator_id=i.artist).first()
            x2 = User.query.filter_by(user_id=x1.user_id).first()
            album_info.append((i.album_id,i.album_name,i.genre,x2.username))
        return render_template("admin_albums.html",username=username, album_info = album_info)
    
    elif request.method == 'POST':
        album_id = request.form['album_id']
        album_to_delete = Album.query.filter_by(album_id = album_id).first()
        songs_in_album = Song.query.filter_by(album_id = album_id)
        for song in songs_in_album:
            delete_from_playlist = PlaylistSong.query.filter_by(song_id = song.song_id)    
            for x in delete_from_playlist:
                db.session.delete(x)
                db.session.commit()
        db.session.delete(album_to_delete)
        db.session.commit()
        # url = "/"+username+"/admin_albums"
        return redirect(request.referrer) 
        # # some error
        # return None
        

@app.route("/<string:username>/admin_creators")
def admin_creators(username):
    user = User.query.filter_by(username = username).first()
    if user.user_type != 'admin':
        flash('Not accessible to user')
        return redirect(url_for("home"))
    # thinking of removing
    return render_template("admin_creators.html",username=username)


# @app.route("/<string:username>/album_creator_view/<int:album_id>") # why error??
# def album_creator_view(username):
#     album_data=Album.query.filter_by(album_id=album_id).first()
#     song_data=Song.query.filter_by(album_id=album_id)
#     creator_data=Creator.query.filter_by(creator_id=album_data.artist).first()
#     username_artist=User.query.filter_by(user_id=creator_data.user_id).first()
#     album_song_data_list=[]
#     for i in song_data:
#         song=[i.song_id,i.song_name]
#         album_song_data_list.append(song)
#     album_data_list=[album_data.album_name,album_data.genre,album_data.artist,len(album_song_data_list),album_song_data_list,username_artist.username]
#     return render_template("album_creator_view.html",username=username,album = album_data_list)   

@app.route('/<string:username>/<string:category>/search', methods=['GET', 'POST'])
def search(username, category):
    if request.method == 'POST':
        searchstring = request.form.get('searchstring')
        username = request.form.get('username')
        user = User.query.filter_by(username = username).first()
        if category=='album' and user.user_type in ['user','creator']:
            album = Album.query \
                .join(Creator, Album.artist == Creator.creator_id) \
                .join(User, Creator.user_id == User.user_id) \
                .filter(
                    or_(
                        Album.album_name.ilike(f'%{searchstring}%'),
                        Album.genre.ilike(f'%{searchstring}%'),
                        User.username.ilike(f'%{searchstring}%')
                    )
                ) \
                .all()
            album_info=[]
            for i in album:
                x1 = Creator.query.filter_by(creator_id=i.artist).first()
                x2 = User.query.filter_by(user_id=x1.user_id).first()
                album_info.append((i.album_id,i.album_name,i.genre,x2.username))
            return render_template("user_albums.html",username=username, album_info = album_info)
        
        elif category=='song' and user.user_type in ['user','creator']:
            user = User.query.filter_by(username = username).first()
            track_info = []
            tracks = Song.query \
            .join(Album, Song.album_id == Album.album_id) \
            .join(Creator, Album.artist == Creator.creator_id) \
            .join(User, Creator.user_id == User.user_id) \
            .filter(
                or_(
                    Song.song_name.ilike(f'%{searchstring}%'),
                    Album.album_name.ilike(f'%{searchstring}%'),
                    Album.genre.ilike(f'%{searchstring}%'),
                    User.username.ilike(f'%{searchstring}%') 
                )
            ) \
            .all()
            for i in tracks:
                x1 = Album.query.filter_by(album_id = i.album_id).first()
                x2 = Creator.query.filter_by(creator_id=x1.artist).first()
                x3 = User.query.filter_by(user_id=x2.user_id).first()
                track_info.append((i.song_id,i.song_name,i.duration,str(i.date_created)[:11],x1.album_name,x3.username))
            return render_template("user_tracks.html",username=username, track_info = track_info)
        
        elif category=='song' and user.user_type == 'admin':
            user = User.query.filter_by(username = username).first()
            track_info = []
            tracks = Song.query \
            .join(Album, Song.album_id == Album.album_id) \
            .join(Creator, Album.artist == Creator.creator_id) \
            .join(User, Creator.user_id == User.user_id) \
            .filter(
                or_(
                    Song.song_name.ilike(f'%{searchstring}%'),
                    Album.album_name.ilike(f'%{searchstring}%'),
                    Album.genre.ilike(f'%{searchstring}%'),
                    User.username.ilike(f'%{searchstring}%') 
                )
            ) \
            .all()
            for i in tracks:
                x1 = Album.query.filter_by(album_id = i.album_id).first()
                x2 = Creator.query.filter_by(creator_id=x1.artist).first()
                x3 = User.query.filter_by(user_id=x2.user_id).first()
                track_info.append((i.song_id,i.song_name,i.duration,str(i.date_created)[:11],x1.album_name,x3.username))
            return render_template("admin_tracks.html",username=username, track_info = track_info)
        
        elif category=='album' and user.user_type == 'admin':
            album = Album.query \
                .join(Creator, Album.artist == Creator.creator_id) \
                .join(User, Creator.user_id == User.user_id) \
                .filter(
                    or_(
                        Album.album_name.ilike(f'%{searchstring}%'),
                        Album.genre.ilike(f'%{searchstring}%'),
                        User.username.ilike(f'%{searchstring}%')
                    )
                ) \
                .all()
            album_info=[]
            for i in album:
                x1 = Creator.query.filter_by(creator_id=i.artist).first()
                x2 = User.query.filter_by(user_id=x1.user_id).first()
                album_info.append((i.album_id,i.album_name,i.genre,x2.username))
            return render_template("admin_albums.html",username=username, album_info = album_info)


@app.route("/<string:username>/user_profile")
def user_profile(username):
    user = User.query.filter_by(username = username).first() 
    user_id = user.user_id
    playlist_data = Playlist.query.filter_by(user_id = user_id)
    playlist_user_list = []
    for i in playlist_data:
        playlist_user_list.append((i.playlist_id, i.playlist_name))
    return render_template("user_profile.html",username=username,pl_data1 = playlist_user_list) 

@app.route("/<string:username>/user_tracks")
def user_tracks(username):
    
    user = User.query.filter_by(username = username).first()
    track_info = []
    tracks = Song.query.filter_by(flagged = False)
    for i in tracks:
        x1 = Album.query.filter_by(album_id = i.album_id).first()
        x2 = Creator.query.filter_by(creator_id=x1.artist).first()
        x3 = User.query.filter_by(user_id=x2.user_id).first()
        track_info.append((i.song_id,i.song_name,i.duration,str(i.date_created)[:11],x1.album_name,x3.username))
    return render_template("user_tracks.html",username=username, track_info = track_info)

@app.route("/<string:username>/user_albums")
def user_albums(username):
    
    user = User.query.filter_by(username = username).first()
    album_info=[]
    album = Album.query.all() 
    for i in album:
        x1 = Creator.query.filter_by(creator_id=i.artist).first()
        x2 = User.query.filter_by(user_id=x1.user_id).first()
        album_info.append((i.album_id,i.album_name,i.genre,x2.username))
    return render_template("user_albums.html",username=username, album_info = album_info)


@app.route("/<username>/flag_track", methods=["POST"])
def flag_track(username):
    song_id = request.form.get("song_id")
    song = Song.query.filter_by(song_id = song_id).first()
    song.flagged = True
    db.session.commit()
    # Perform actions to flag the track in the database
    # Add code to update the track status or take other actions
    
    # Redirect to the admin_tracks page or perform any other necessary action
    return redirect(f"/{username}/admin_tracks")


@app.route("/<string:username>/toggle_flag", methods=["POST"])
def toggle_flag(username):
    song_id = request.form['song_id']
    flag_action = request.form['flag_action']
    
    song = Song.query.filter_by(song_id=song_id).first()
    if flag_action == 'flag':
        song.flagged = True
    elif flag_action == 'unflag':
        song.flagged = False
    
    db.session.commit()
    
    return redirect(url_for('admin_tracks', username=username))


