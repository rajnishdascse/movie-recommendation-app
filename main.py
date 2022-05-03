import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import bs4 as bs
import urllib.request
import pickle
import requests
from datetime import date, datetime
from tmdbsimple import Authentication
from tmdbv3api import TMDb, Movie

from flask import *
from flask import request, flash
from flask import Flask, redirect, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_required, login_user, login_url, LoginManager, logout_user, current_user
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView


# load the nlp model and tfidf vectorizer from disk
filename = 'nlp_model.pkl'
clf = pickle.load(open(filename, 'rb'))
vectorizer = pickle.load(open('tranform.pkl','rb'))
    
# converting list of string to list (eg. "["abc","def"]" to ["abc","def"])
def convert_to_list(my_list):
    my_list = my_list.split('","')
    my_list[0] = my_list[0].replace('["','')
    my_list[-1] = my_list[-1].replace('"]','')
    return my_list

# convert list of numbers to list (eg. "[1,2,3]" to [1,2,3])
def convert_to_list_num(my_list):
    my_list = my_list.split(',')
    my_list[0] = my_list[0].replace("[","")
    my_list[-1] = my_list[-1].replace("]","")
    return my_list

def get_suggestions():
    data = pd.read_csv('main_data.csv')
    return list(data['movie_title'].str.capitalize())

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisisasecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Machine learning/MovieRecommender/database.db'
admin = Admin(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.route("/")
@app.route("/home")
@login_required
def home():
    suggestions = get_suggestions()
    # return render_template('home.html',suggestions=suggestions)
    try:
        tmdb = TMDb()
        tmdb.api_key = '225ac8079ea25738ddc6a4c08757dd89'
        tmdb.language = 'en'
        tmdb.debug = True

        movie = Movie()
        popularr = movie.popular()
        popular=popularr[:7]

        final_popular={}
        for i in range(len(popular)):
            l=[]
            z=popular[i]['id']
            m = movie.details(z)
            l.append(m.title)
            l.append(m.overview[:140])
            # l.append('https://image.tmdb.org/t/p/original//'+m.poster_path)

            final_popular[i]=l

        url="https://api.themoviedb.org/3/movie/top_rated?api_key=225ac8079ea25738ddc6a4c08757dd89&language=en-US&page=1"
        url2="https://api.themoviedb.org/3/movie/upcoming?api_key=225ac8079ea25738ddc6a4c08757dd89&language=en-US&page=1"
        
        # have to show popular movie = https://api.themoviedb.org/3/trending/movie/day?api_key=<<api_key>>
        info = requests.get(url)
        info2 = requests.get(url2)

        json_edit = info.json()

        json_edit2 = info2.json()

        a=json_edit['results']
        b = json_edit2['results']
        
        new_release={}
        new_release2 = {}

        for i in range(7):
            x= a[i]['original_title']
            y='https://image.tmdb.org/t/p/original/'+a[i]['backdrop_path']
            z=a[i]['overview'][:140]
            new_release[i]=[x,y,z]

        for i in range(7):
            x2= b[i]['original_title']
            y2='https://image.tmdb.org/t/p/original/'+b[i]['backdrop_path']
            z2=b[i]['overview'][:140]
            new_release2[i]=[x2,y2,z2]

        # for top_rated movie
        link="https://api.themoviedb.org/3/movie/top_rated?api_key=225ac8079ea25738ddc6a4c08757dd89&language=en-US&page=1"
        details = requests.get(link)
        json_details = details.json()

        link2="https://api.themoviedb.org/3/movie/upcoming?api_key=225ac8079ea25738ddc6a4c08757dd89&language=en-US&page=1"
        details2 = requests.get(link2)
        json_details2 = details2.json()
        
        return render_template('home.html',suggestions= suggestions, final_popular=final_popular,new_release=new_release,json_details=json_details,new_release2=new_release2, json_details2=json_details2)
    except Exception as e:
        print(e)
        return render_template('home.html',e="Something went Wrong! " + str(e))




@app.route("/recommend",methods=["POST"])
def recommend():
    # getting data from AJAX request
    title = request.form['title']
    cast_ids = request.form['cast_ids']
    cast_names = request.form['cast_names']
    cast_chars = request.form['cast_chars']
    cast_bdays = request.form['cast_bdays']
    cast_bios = request.form['cast_bios']
    cast_places = request.form['cast_places']
    cast_profiles = request.form['cast_profiles']
    imdb_id = request.form['imdb_id']
    poster = request.form['poster']
    genres = request.form['genres']
    overview = request.form['overview']
    vote_average = request.form['rating']
    vote_count = request.form['vote_count']
    rel_date = request.form['rel_date']
    release_date = request.form['release_date']
    runtime = request.form['runtime']
    status = request.form['status']
    rec_movies = request.form['rec_movies']
    rec_posters = request.form['rec_posters']
    rec_movies_org = request.form['rec_movies_org']
    rec_year = request.form['rec_year']
    rec_vote = request.form['rec_vote']

    # get movie suggestions for auto complete
    suggestions = get_suggestions()

    # call the convert_to_list function for every string that needs to be converted to list
    rec_movies_org = convert_to_list(rec_movies_org)
    rec_movies = convert_to_list(rec_movies)
    rec_posters = convert_to_list(rec_posters)
    cast_names = convert_to_list(cast_names)
    cast_chars = convert_to_list(cast_chars)
    cast_profiles = convert_to_list(cast_profiles)
    cast_bdays = convert_to_list(cast_bdays)
    cast_bios = convert_to_list(cast_bios)
    cast_places = convert_to_list(cast_places)
    
    # convert string to list (eg. "[1,2,3]" to [1,2,3])
    cast_ids = convert_to_list_num(cast_ids)
    rec_vote = convert_to_list_num(rec_vote)
    rec_year = convert_to_list_num(rec_year)
    
    # rendering the string to python string
    for i in range(len(cast_bios)):
        cast_bios[i] = cast_bios[i].replace(r'\n', '\n').replace(r'\"','\"')

    for i in range(len(cast_chars)):
        cast_chars[i] = cast_chars[i].replace(r'\n', '\n').replace(r'\"','\"') 
    
    # combining multiple lists as a dictionary which can be passed to the html file so that it can be processed easily and the order of information will be preserved
    movie_cards = {rec_posters[i]: [rec_movies[i],rec_movies_org[i],rec_vote[i],rec_year[i]] for i in range(len(rec_posters))}

    casts = {cast_names[i]:[cast_ids[i], cast_chars[i], cast_profiles[i]] for i in range(len(cast_profiles))}

    cast_details = {cast_names[i]:[cast_ids[i], cast_profiles[i], cast_bdays[i], cast_places[i], cast_bios[i]] for i in range(len(cast_places))}

    # web scraping to get user reviews from IMDB site
    sauce = urllib.request.urlopen('https://www.imdb.com/title/{}/reviews?ref_=tt_ov_rt'.format(imdb_id)).read()
    soup = bs.BeautifulSoup(sauce,'lxml')
    soup_result = soup.find_all("div",{"class":"text show-more__control"})

    reviews_list = [] # list of reviews
    reviews_status = [] # list of comments (good or bad)
    for reviews in soup_result:
        if reviews.string:
            reviews_list.append(reviews.string)
            # passing the review to our model
            movie_review_list = np.array([reviews.string])
            movie_vector = vectorizer.transform(movie_review_list)
            pred = clf.predict(movie_vector)
            reviews_status.append('Positive' if pred else 'Negative')

    # getting current date
    movie_rel_date = ""
    curr_date = ""
    if(rel_date):
        today = str(date.today())
        curr_date = datetime.strptime(today,'%Y-%m-%d')
        movie_rel_date = datetime.strptime(rel_date, '%Y-%m-%d')

    # combining reviews and comments into a dictionary
    movie_reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))}     

    # passing all the data to the html file
    return render_template('recommend.html',title=title,poster=poster,overview=overview,vote_average=vote_average,
        vote_count=vote_count,release_date=release_date,movie_rel_date=movie_rel_date,curr_date=curr_date,runtime=runtime,status=status,genres=genres,movie_cards=movie_cards,reviews=movie_reviews,casts=casts,cast_details=cast_details)


# ============User Authentication==========
class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(40), unique=True)
    password = db.Column(db.String(80))
admin.add_view(ModelView(User,db.session))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get((user_id))


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username= username).first()
        if user:
            if check_password_hash(user.password,password):
                login_user(user)
                user.authenticated = True
                flash('Woho!! Logged in successfully!!')
                return redirect(url_for('home'))
        # return "<h1>Invalid credential"
        flash('Invalid credential! Try again..')
    # return render_template('login_register.html')
    return render_template('login.html')



@app.route('/register',methods=["GET","POST"])
def register():
    if request.method =='POST':

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password, method = 'sha256')  #for security purpose password is converted into hash value
        
        if User.query.filter_by(username=username).first():
            flash('Username already exist, Try again!!')
            # return render_template('login_register.html')
            return render_template('signup.html')

        elif User.query.filter_by(email=email).first():
            flash('Email id already has been used! You can log in directly')
            # return render_template('login_register.html')
            return render_template('signup.html')

        
        new_user = User(username=username, email=email, password=hashed_password)
        new_user.authenticated = True
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        new_user.authenticated = True
        flash("Well done! Account created successfully")
        return redirect(url_for('home'))
    # return render_template('login_register.html')
    return render_template('signup.html')



@app.route('/logout')
@login_required
def logout():
    logout_user()
    # flash("Logout sucessfully")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
