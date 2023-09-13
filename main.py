from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
import requests
import os

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Movies.db"
MOVIE_API = os.environ["Api_Key"]
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
Bootstrap5(app)

db = SQLAlchemy()
db.init_app(app)


class NewMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


class MyForm(FlaskForm):
    rating = StringField('Your rating out of 10 for eg:7.5', validators=[DataRequired()])
    review = StringField("Your review", validators=[DataRequired()])
    Go = SubmitField("Done")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()  # convert ScalarResult to Python List
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add():
    newMovie = NewMovie()
    if newMovie.validate_on_submit():
        query = request.form["title"]

        MOVIE_ENDPOINT = f"https://api.themoviedb.org/3/search/movie?"
        response = requests.get(MOVIE_ENDPOINT, params={"api_key": MOVIE_API, "query": query})
        data = response.json()
        if data["total_results"] > 0:
            results = data["results"]

            return render_template("select.html", movies=results)
        else:
            return "There is No movie with this title"
    return render_template("add.html", movie=newMovie)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = MyForm()

    movie_id = request.args.get("movie_id")
    movie = db.get_or_404(Movie, movie_id)

    if form.validate_on_submit():
        movie.rating = request.form["rating"]
        movie.review = request.form["review"]
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", form=form, movie=movie)


@app.route("/delete")
def remove():
    # book_to_delete = db.session.execute(db.select(Movie).where(Movie.movie_id == movie_id)).scalar()
    movie_id = request.args.get("movie_id")
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/find")
def find_movie():
    movie_id = request.args.get("id")
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    response = requests.get(url, params={"api_key": MOVIE_API, "language": "en-US"})
    data = response.json()
    new_movie = Movie(title=data["title"],
                      year=data["release_date"].split("-")[0],
                      description=data["overview"],
                      img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
                      rating=0,
                      ranking=0,
                      review="Nice")

    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit',movie_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
