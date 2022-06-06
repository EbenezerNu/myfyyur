#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import time
from dateutil.parser import parse
# from dateutil.tz import gettz
import json
import datetime
from dateutil import parser
from datetime import date as dt
import babel
from pip import List
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import pytz

utc=pytz.UTC
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    website = db.Column(db.String(), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500), nullable=True)
    shows = db.relationship('Show', backref='venue', lazy=True)

   

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    website = db.Column(db.String(), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)
    seeking_venue = db.Column(db.Boolean, nullable=False, default=True)
    seeking_description = db.Column(db.String(500), nullable=True)

    shows = db.relationship('Show', backref='artist', lazy=True)


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime())
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'))


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = parser.parse(value)
    print("The Date value = {}".format(date))
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.

    data = Venue.query.all()    
    for i in range(len(data)): 
        data1 = {
            (v.city+', '+v.state): {
                'city' : v.city, 
                'state' : v.state, 
                'venues': [{
                    'id': i.id, 
                    'name': i.name, 
                    'num_upcoming_shows': len(Show.query.filter(Show.start_time > datetime.now(), Show.venue_id == v.id).all())
                    } for i in Venue.query.filter_by(city=v.city, state=v.state).all() ]
             } for v in Venue.query.distinct((Venue.city +", "+ Venue.state)).all()}
    
    return render_template('pages/venues.html', areas=data1)
    # return jsonify(data1)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    word = request.form.get('search_term')
    keyword = "%{}%".format(word)
    data = Venue.query.filter(or_(Venue.name.ilike(keyword), Venue.city.ilike(keyword), Venue.state.ilike(keyword), func.concat(Venue.city +", ", Venue.state).ilike(keyword))).all()
    response = {
        "count": len(data),
        "data": [{
            "id": d.id,
            "name": d.name,
            "num_upcoming_shows": len(Show.query.filter(Show.start_time > datetime.now(), Show.venue_id == d.id).all()),
        } for d in data]
    }
    return render_template('pages/search_venues.html', results=response, search_term=word)

@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    local_venue = Venue.query.get(venue_id)
    past_shows = Show.query.filter(Show.start_time < datetime.now(), Show.venue_id == local_venue.id).all()
    upcoming_shows = Show.query.filter(Show.start_time > datetime.now(), Show.venue_id == local_venue.id).all()
    data = {
        'id': local_venue.id,
        'name': local_venue.name,
        'address': local_venue.address,
        'city': local_venue.city,
        'state': local_venue.state,
        'phone': local_venue.phone,
        'genres': local_venue.genres,
        'website': local_venue.website,
        'facebook_link': local_venue.facebook_link,
        'seeking_talent': local_venue.seeking_talent,
        'image_link': local_venue.image_link,
        'past_shows': [{
          'artist_id': p.artist_id,
          'artist_name': p.artist.name,
          'artist_image_link': p.artist.image_link,
          'start_time': p.start_time.strftime("%m/%d/%Y, %H:%M")
          } for p in past_shows],
          'upcoming_shows': [{
              'artist_id': u.artist.id,
              'artist_name': u.artist.name,
              'artist_image_link': u.artist.image_link,
              'start_time': u.start_time.strftime("%m/%d/%Y, %H:%M")
          } for u in upcoming_shows],
          'past_shows_count': len(past_shows),
          'upcoming_shows_count': len(upcoming_shows)
      }
    if local_venue.seeking_talent==True:
          data['seeking description'] =  local_venue.seeking_description

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    try:  
        venue = Venue(
            name =request.form.get('name'),
            city =request.form.get('city'),
            state =request.form.get('state'),
            address =request.form.get('address'),
            phone =request.form.get('phone'),
            genres =request.form.getlist('genres'),
            facebook_link =request.form.get('facebook_link'),
            website =request.form.get('website_link'),
            image_link =request.form.get('image_link'),
            seeking_talent =request.form.get('seeking_talent') == 'true',
            seeking_description =request.form.get('seeking_description')
        )
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form.get('name') + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ' + request.form.get('name') + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    # return jsonify(venue.details_with_shows)


@app.route('/venues/<venue_id>/delete')
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        Show.query.filter_by(venue_id=venue_id).delete()
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
        flash('Venue was successfully deleted!')
        return redirect(url_for('index'))
    except:
        db.session.rollback()
        print(sys.exc_info)
        flash('Venue could not be deleted!')
        return redirect(url_for('show_venue', venue_id))
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    local_artists =[{"id": person.id, "name": person.name} for person in Artist.query.with_entities(Artist.id, Artist.name).all()]
    return render_template('pages/artists.html', artists=local_artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    word = request.form.get('search_term')
    data = Artist.query.filter(or_(Artist.name.ilike(keyword), Artist.city.ilike(keyword), Artist.state.ilike(keyword), func.concat(Artist.city +", ", Artist.state).ilike(keyword))).all()
    keyword = "%{}%".format(word)    
    response = {
        "count": len(data),
        "data": [{
            "id": d.id,
            "name": d.name,
            "num_upcoming_shows": len(Show.query.filter(Show.start_time > datetime.now(), Show.artist_id == d.id).all()),
        } for d in data]
    }
    return render_template('pages/search_artists.html', results=response, search_term=word)


@app.route('/artists/<int:_id>')
def show_artist(_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    local_artist = Artist.query.get(_id)
    past_shows = Show.query.filter(Show.start_time < datetime.now(), Show.artist_id == local_artist.id).all()
    upcoming_shows = Show.query.filter(Show.start_time > datetime.now(), Show.artist_id == local_artist.id).all()
    data = {
    'id': local_artist.id,
    'name': local_artist.name,
    'city': local_artist.city,
    'state': local_artist.state,
    'phone': local_artist.phone,
    'genres': local_artist.genres,
    'website': local_artist.website,
    'facebook_link': local_artist.facebook_link,
    'seeking_venue': local_artist.seeking_venue,
    'image_link': local_artist.image_link,
    'past_shows': [{
        'venue_id': p.venue_id,
        'venue_name': p.venue.name,
        'venue_image_link': p.venue.image_link,
        'start_time': p.start_time.strftime("%m/%d/%Y, %H:%M")
        } for p in past_shows],
    'upcoming_shows': [{
        'venue_id': u.venue.id,
        'venue_name': u.venue.name,
        'venue_image_link': u.venue.image_link,
        'start_time': u.start_time.strftime("%m/%d/%Y, %H:%M")
    } for u in upcoming_shows],
    'past_shows_count': len(past_shows),
    'upcoming_shows_count': len(upcoming_shows)
    }
    if local_artist.seeking_venue==True:
        data['seeking description'] =  local_artist.seeking_description

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    local_artist = Artist.query.get(artist_id)
    artist = {
        "id": local_artist.id,
        "name": local_artist.name,
        "genres": local_artist.genres,
        "city": local_artist.city,
        "state": local_artist.state,
        "phone": local_artist.phone,
        "website": local_artist.website,
        "facebook_link": local_artist.facebook_link,
        "seeking_venue": local_artist.seeking_venue,
        "seeking_description": local_artist.seeking_description,
        "image_link": local_artist.image_link
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    try:
        artist = Artist.query.filter_by(id=artist_id).all()[0]
        artist.name=request.form.get('name')
        artist.city=request.form.get('city')
        artist.state=request.form.get('state')
        artist.phone=request.form.get('phone')
        artist.genres=request.form.getlist('genres')
        artist.facebook_link=request.form.get('facebook_link')
        artist.website=request.form.get('website_link')
        artist.image_link=request.form.get('image_link')
        artist.seeking_venue=request.form.get('seeking_venue') == 'True'
        artist.seeking_description=request.form.get('seeking_description')
        db.session.add(artist)
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occurred. Artist could not be updated')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    local_venue = Venue.query.get(venue_id)
    venue = {
        "id": local_venue.id,
        "name": local_venue.name,
        "address": local_venue.address,
        "city": local_venue.city,
        "state": local_venue.state,
        "phone": local_venue.phone,
        "genres": local_venue.genres,
        "website": local_venue.website,
        "facebook_link": local_venue.facebook_link,
        "seeking_talent": local_venue.seeking_talent,
        "seeking_description": local_venue.seeking_description,
        "image_link": local_venue.image_link
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes

    try:
        venue = Venue.query.filter_by(id=venue_id).all()[0]
        venue.name=request.form.get('name')
        venue.city=request.form.get('city')
        venue.state=request.form.get('state')
        venue.address=request.form.get('address')
        venue.phone=request.form.get('phone')
        venue.genres=request.form.getlist('genres')
        venue.facebook_link=request.form.get('facebook_link')
        venue.website=request.form.get('website_link')
        venue.image_link=request.form.get('image_link')
        venue.seeking_talent=request.form.get('seeking_talent') == 'True'
        venue.seeking_description=request.form.get('seeking_description')
        db.session.commit()
        flash('Venue ' + request.form.get('name') + ' has been updated successfuly')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + request.form.get('name') + ' could not be updated')
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    try: 
        artist = Artist(
            name =request.form.get('name'),
            city =request.form.get('city'),
            state =request.form.get('state'),
            phone =request.form.get('phone'),
            genres =request.form.getlist('genres'),
            facebook_link =request.form.get('facebook_link'),
            website =request.form.get('website_link'),
            image_link =request.form.get('image_link'),
            seeking_venue = request.form.get('seeking_venue') == 'true',
            seeking_description =request.form.get('seeking_description')
        )
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form.get('name') + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Artist ' + request.form.get('name') + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    # return jsonify(artist.details_with_shows)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    local_shows = Show.query.all()
    raw = None
    for i in range(len(local_shows)): 
        raw = {s.id : {
            "venue_id": s.venue_id,
            "venue_name": Venue.query.get(s.venue_id).name,
            "artist_id": s.artist_id,
            "artist_name": Artist.query.get(s.artist_id).name,
            "artist_image_link": Artist.query.get(s.artist_id).image_link,
            "start_time": s.start_time.strftime("%m/%d/%Y, %H:%M")
        } for s in local_shows}

    if raw is None:
        data = None
    else:
        data = raw

    return render_template('pages/shows.html', shows=data)
    # return jsonify(raw)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    try:
        artist_check = Artist.query.get(request.form['artist_id'])
        venue_check = Venue.query.get(request.form['venue_id'])
        if((artist_check != None) and (venue_check != None)):
            show = Show(
                start_time =request.form.get('start_time'),
                artist_id =request.form.get('artist_id'),
                venue_id =request.form.get('venue_id')
            )
            db.session.add(show)
            db.session.commit()
            flash('Show was successfully listed!')
        else:
            raise Exception
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
        return redirect(url_for('create_shows'))

        # return render_template('pages/home.html')

    # return jsonify(show=show)
    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
