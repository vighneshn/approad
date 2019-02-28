#############
# By Vighnesh N, 25/1/19
# _server.pyi
# Comments format: function description right above the function, basic explanation of the func and my thinking behind the steps.
# Basic server to test out the functionality of util.py and debug that.
# In progress
#############

import sys
#from os import path
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '../utility')))

from flask import Flask, jsonify, request, redirect, url_for, session, render_template, flash
from passlib.hash import sha256_crypt
from functools import wraps
from wtforms import Form, StringField, IntegerField, TextAreaField, PasswordField, validators, DecimalField

#from utility import util
import util

app = Flask(__name__)

'''
Link is no longer needed, just passing it, shall remove it later.
Directly keeping the link with the dao object.
'''

link = "mongodb://localhost:27017"
db_name = "test"
collection_name = "road_app_test"


@app.route('/')
def index():
	## jsonify?
	return render_template('home.html')

##
# About the app
##
@app.route('/about')
def about():
    return render_template('about.html')

##
# more, if anything more is there to add, i'll use this link, just dummy/test for now
##
@app.route('/More')
def more():
    return "Dummy page, for testing. Go back to Home page"
##Create Registration form
# Register Form Class
class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
        validators.DataRequired(),
	validators.EqualTo('confirm', message='Passwords do not match')
	])
	confirm = PasswordField('Confirm Password')

##Currently setting the username as _id for mongo, need to debug and fix this wherever errors come up
@app.route('/register', methods=['GET','POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		##Insert into db using util.py(mongo)
		user = {
			'name':name,
			'emailid':email,
			'username':username,
			'password':password,
			'isgovt':False
		}
		util.register_user(link, db_name, collection_name, user)

		#See how to send the flash message
		flash('You are now registered and can log in', 'success')

		return redirect(url_for('login'))

	return render_template('register.html', form=form)		

##
# Need to add methods(html) to support the flash messages and everything else.
##
@app.route('/login', methods = ['GET','POST'])
def login():
	print('HIJIJIJI')
	if request.method=='POST':
		username = request.form['username']
		password_candidate = request.form['password']

		usr_pwd = util.login(link, db_name, collection_name, username)
		if usr_pwd['username'] and usr_pwd['password']:
			if sha256_crypt.verify(password_candidate, usr_pwd['password']):
				# Passed 
				# Login credentials are valid
				session['logged_in'] = True
				session['username'] = usr_pwd['username']

				#print(request.headers.items())
				print('HIII ',session['username'])
				#print(request.form)
				flash('You have logged in', 'success')
				
				## For mobile app
				#return jsonify({'message':'logged in'})
				return redirect(url_for('dashboard'))
			else:
				# Failed
				flash('Invalid login')
				error_msg = 'Invalid login'
				return render_template('login.html', error=error_msg)
		else:
			flash('Username not found')
			error_msg = 'Username not found'
			return render_template('login.html', error=error_msg)
	return render_template('login.html')


## TODO: Have to add the feature where login is required for these, just have to wrap these functions checking if the session is logged in, thats it
##
# Dashboard contains buttens to insert data and view it in different ways. Users and aggregate data.
# Create this after registering, login, inserting a users data and viewing only his data. After this, can check the rest of the functionality.
# No UI for now, basic table inserting data and just printing any retrieved data when the button on dashboard is clicked.
# Basics with render_template, not too much
##

##
# Code to create wrapper for functions that shall display only if logged in.
##

def is_logged_in(f):
        @wraps(f)
        def wrap(*args, **kwargs):
                if 'logged_in' in session:
                        return f(*args, **kwargs)
                else:
                        flash('Unauthorized, Please login', 'danger')
                        return redirect(url_for('login'))
        return wrap

@app.route('/dashboard', methods = ['GET','POST'])
@is_logged_in
def dashboard():
	##
	# Buttons for:
	# 	- insert data(add a review)
	# 	- retrieve only his data
	#	- retrive aggregate data, only coords I guess
	# 	- retrive aggregate info about neighbourhood of a surrounding point
	# 	- view closest review to a touch
	# 	- retrive info about a friend
	##
	#return jsonify({'message':'logged in'})
	return render_template('dashboard.html')

##
# Separate form when adding a review, of just the required fields.
# For latitudes and longitudes, for now, taking a string of each, comma separated. eg: lat = (lat1,lat2,lat3...latn), long = (long1,long2,long3...longn).
# Then i extract [(lat1,long1),(lat2,long2)...(latn,longn)] from this
##
class reviewForm(Form):
	area = StringField('Area', [validators.Length(min=1, max=200)])
	category = StringField('Category', [validators.Length(min=1, max=200)])
	## Need to see how to handle coords_list for now
	latitude_list = StringField('List of Latitudes', [validators.Length(min=1)])
	longitude_list = StringField('List of Longitudes', [validators.Length(min=1)])
	rating = IntegerField('Rating')
	comments = TextAreaField('Comments')
	# All are public for now.

@app.route('/add_review', methods = ['GET','POST'])
@is_logged_in
def add_review():
	form = reviewForm(request.form)
	if request.method == 'POST' and form.validate():
		area = form.area.data
		category = form.category.data
		latitude_list = form.latitude_list.data
		longitude_list = form.longitude_list.data
		# Create a derived field called coords_list from this, so that it can work with geo json. For the geoNear commands to work.
		lat_split = latitude_list.split(',')
		long_split = longitude_list.split(',')
		rating = form.rating.data
		comments = form.comments.data

		assert len(lat_split)==len(long_split),"Enter Same number of lats and longs"
		coords_list = [[float(lat_split[i]),float(long_split[i])] for i in range(len(lat_split))]
		
		review = {
				'area':area,
				'category':category,
                                'coords_list':coords_list,
				#'coords_list':{
                                #    'type':'MultiPoint',
                                #    'coordinates':coords_list},
				'rating':rating,
				'comments':comments	
			}

		util.add_review(link, db_name, collection_name, session['username'], review)
		flash('Review Updated', 'success')

		return redirect(url_for('dashboard'))
	return render_template('add_review.html', form = form)

##
# Get the entire review of the user
##
@app.route('/user_view_data', methods = ['GET','POST'])
@is_logged_in
def user_view_data():
	## A form to retrive only particular review, or just return the entire thing. For now entire thing.
	data = util.user_view_reviews(link, db_name, collection_name, session['username'])
	## TRY: data or jsonify(data)?? Try both
	return data

##
# To return the aggregate data
##
class AggForm(Form):
	category = StringField('Category', [validators.Length(min=1, max=200)])
	scale = DecimalField('Scale')
	longi = DecimalField('current Longitude')
	lati = DecimalField('current Latitude')
	# All are public for now.

@app.route('/view_aggregate_data', methods = ['GET','POST'])
@is_logged_in
def view_agg_data():
    #data = util.view_overall_reviews(link, db_name, collection_name)
    form = AggForm(request.form)
    if request.method == 'POST' and form.validate():
        scale = float(form.scale.data)
        lati = float(form.lati.data)
        longi = float(form.longi.data)
        category = form.category.data

        data = util.view_overall_reviews(link, db_name, collection_name, scale, [longi, lati], category)
        return data
    return render_template('agg_data.html', form = form)

##
# User needs to view aggregate stats around a region, say after a long press.
##
class StatsForm(Form):
	scale = DecimalField('Scale')
	longi = DecimalField('current Longitude')
	lati = DecimalField('current Latitude')
@app.route('/view_stats_around_point', methods = ['GET','POST'])
@is_logged_in
def view_stats_around_point():
    form = StatsForm(request.form)
    if request.method == 'POST' and form.validate():
        lati = float(form.lati.data)
        longi = float(form.longi.data)
        scale = float(form.scale.data)

        data = util.num_reviews_for_each_star_count_around_selected_area(link, db_name, collection_name, scale, [longi,lati])
        return jsonify(data)
    return render_template('stats_around_point.html', form = form)



##
# When a user touches the screen, we show him stats of the nearest point. This function does just that
##
class ClosestPointForm(Form):
	category = StringField('Category', [validators.Length(min=1, max=200)])
	scale = DecimalField('Scale')
	longi = DecimalField('current Longitude')
	lati = DecimalField('current Latitude')

@app.route('/view_closest_point', methods = ['GET','POST'])
@is_logged_in
def view_closest_point_stats():
    form = ClosestPointForm(request.form)
    if request.method == 'POST' and form.validate():
        category = form.category.data
        scale = float(form.scale.data)
        lati = float(form.lati.data)
        longi = float(form.longi.data)

        data = util.view_closest_point_stats(link, db_name, collection_name, scale, (longi, lati), category)
        return data
    return render_template('closest_point.html', form = form)


###Handling friends, adding and viewing. For now no policy where the other person has to accept being a friend
#To add that
class FriendForm(Form):
	username = StringField('Username', [validators.Length(min=1, max=200)])

@app.route('/add_friend', methods = ['GET','POST'])
@is_logged_in
def add_friend():
    form = FriendForm(request.form)
    curr_friends = util.view_friends_names(link, db_name, collection_name, session['username'])
    if request.method == 'POST' and form.validate():
        username = form.username.data

        data = util.add_friend(link, db_name, collection_name, session['username'], username)
        if data:
            flash('Review Updated', 'success')
        else:
            flash('User does not exist or this person is already your friend', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('add_friend.html', form = form, curr_friends = curr_friends)

@app.route('/view_friend', methods = ['GET','POST'])
@is_logged_in
def view_friend_stats():
    form = FriendForm(request.form)
    curr_friends = util.view_friends_names(link, db_name, collection_name, session['username'])
    if request.method == 'POST' and form.validate():
        username = form.username.data

        data = util.view_friends_reviews(link, db_name, collection_name, username)
        return data
    return render_template('/view_friend.html', form = form, curr_friends = curr_friends)


@app.route('/logout')
@is_logged_in
def logout():
        session.clear()
        flash('You are now logged out', 'success')
        return redirect(url_for('login'))

if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(host='0.0.0.0', debug=True)
