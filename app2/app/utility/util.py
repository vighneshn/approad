####
# By Vighnesh N, 19/1/19
# Comments format: function description right above the function, basic explanation of the func and my thinking behind the steps.
# Name: util.py
# Code to provide all the back-end utilities, perform the aggregations and queries, and return the results to the supporting code/server.
# Inprogress
# Need to fill in values for db_name, collection_name and link, need to hardcode it somewhere obviously, cant leave it hanging throughout to the front end obviously.
####

##
# Current Pattern requires us to parse db_name and collection_name to every function. May be better to store those two within the dao class itself.
# Simple change, can worry about it later, may be tedious to fix, as will have to change many functions
##

import sys
sys.path.insert(0,'../dao')

#from dao import mdb
import mdb
import pymongo
from bson.objectid import ObjectId
from bson import SON
from datetime import datetime, timedelta
from flask import jsonify

##
# Function, adds an id to each of the objects to be inserted. Returns the operation status.
##
def insert_data(link, db_name, collection_name, inputs):
	#db = mdb.DaoImpl(link, db_name, collection_name)
        db = mdb.DaoImpl.getInstance()
	for item in inputs:
		item['_id'] = db.obj_id_as_string()

	return db.insert_many(db_name, collection_name, inputs)


##
# The time a user registers, we need to initialize all the values before recording the data. after that, we insert to the ratings field
# using that, we adjust the other values like num ratings n stuff
##
def register_user(link, db_name, collection_name, user):
        #db = mdb.DaoImpl(link, db_name, collection_name)
        db = mdb.DaoImpl.getInstance()
	##
	# Rest of the fields are expected to come along with parameter user, like name, emailid, password_hash, isgovt etc
	# There will be a better way to initialize these fields, to explore and change this.
	# Currently, I dont like using the name user too many times.
	##

	## using username as _id for now. need to be flexible to change to email id also.
	#user['_id'] = db.obj_id_as_string()
	user['ratings'] = []
	user['credibility'] = 5
	user['num_ratings'] = 0
	user['avg_rating'] = 0
	user['last_rating_info'] = []
	user['isgovt'] = False
	user['friends'] = []
	
	return db.insert_one(db_name, collection_name, user)

##
# Function for login, only need to verify username/email id and password
# So can just project these two using  function
##
def login(link, db_name, collection_name, username):
	#db = mdb.DaoImpl(link, db_name, collection_name)
        db = mdb.DaoImpl.getInstance()

	query = {
		"username":username,
	}
	query_project = {
	                "username":1,	
			"password":1
		
	}
	
	return db.find_one(db_name, collection_name, query, query_project)



##
# User adds the reviews. Since user name may be ambiguous, passing user_id also.
# Modifies the dependant parameters/entries 
# Format for review:
# 	area: string
# 	category: string
# 	coord_list: array of geospatial coordinates(GeoJSON)
# 	rating: int
#	comments: string
#	public: bool
##
# user_id is th username
##
def add_review(link, db_name, collection_name, user_id, review):
	#db = mdb.DaoImpl(link, db_name, collection_name)
        db = mdb.DaoImpl.getInstance()

	##
	# I think this part will be buggy, not sure if query_update will act on only the found query or all data.
	# Have to test to find out
	##
        #print(ObjectId.is_valid(user_id))
        print(user_id)
	query_find = {
			"username":user_id
		}
        '''
	query_update = [
		{
			"$push":{"ratings":review}
		},
		{
			"$set":{
				"avg_rating":{"$avg":{"ratings.rating"}},
				"$inc":{"num_ratings":1}
			}
		}
		]
        '''
        query_update = {
                        "$push":{"ratings":review},
                        #"$set":{
                        #        "avg_rating":{"$avg":"ratings.rating"},
                        #    },
                        "$inc":{"num_ratings":1}
                        
                }

        return db.update_one(db_name, collection_name, query_find, query_update, True)

##
# Now to get the part where the user views his own data
# I guess a simple find of the user id and returning should suffice.
# This returns only the reviews.
# NOTE: This loads the friends entire data, not just the data around the screen
# For entire user data, can check the final part of the code, after the long dashed line  
##
# user_id is username
def user_view_reviews(link, db_name, collection_name, user_id):
	#db = mdb.DaoImpl(link, db_name, collection_name)
        db = mdb.DaoImpl.getInstance()

	query_find_user_data = {
			"username": user_id
		}
	project_data = {
		
			"_id":0,
			"ratings":1
		
	}
	return db.find_one(db_name, collection_name, query_find_user_data, project_data)

##
# Function to view the overall averaged out and aggregated reviews of the places from all users.
# This function is a bit more complex.
# Need to use the scale of the map to read out only appropriate amount of data around the center of the map region that is being displayed-
# not everything as there may be too much to read.
# So based on scale, determine a radius and read points and reviews only within that radius. Note: each review consists of an array of points, so shall consider if the average-
# of the coordinates are within the radius
# Then need to probably cluster nearby reviews to clusters of regions on the road to display better. This will be tricky I guess.
#
# Will need to use the geospatial query thing of mongodb to facilitate these requirements, like getting all points with a radius etc.
# GeoJSON
##
def view_overall_reviews(link, db_name, collection_name, scale, center_of_screen_gps_coords, categories):
	#db = mdb.DaoImpl(link, db_name, collection_name)
        db = mdb.DaoImpl.getInstance()

	## Create an index?
        
	#db.createIndex({"ratings.coords_list": "2d"})
        '''
	geo_near_query = {
			"$geoNear":{
				"near": center_of_screen_gps_coords,
				"spherical": False,
				##
				# The max distance parameter depends if GeoJSON or legacy coordinates, right now assuming GeoJSON, which needs metres, other one needs in radians
				# Source for creeping up error
				# NOTE: Arbitrary value for maxDistance for now
				##
				"maxDistance": 20*scale,
				"query":{"category":{"$in":categories}},
				"distanceField": "calcDistance"
			}
		}
		
        
        geo_near_query = {
                "ratings.coords_list":{
                        #"$near": {
                        #    "$geometry":{"type":"Point", "coordinates":center_of_screen_gps_coords},
                        #    "$maxDistance":1000*scale
                        #}
                        "$near":center_of_screen_gps_coords,
                        #"$maxDistance":0.*scale
                    }
                }
        '''
        geo_near_query = {
                "ratings.coords_list": SON([("$near",center_of_screen_gps_coords), ("$maxDistance",1.1*scale)])
                }
        
        #geo_near_query2 = {
        #        "ratings.coords_list.0":{
        #                "$lt":20*scale
        #            }
        #        "ratings.coords_list.1":{
        #                "$lt":20*scale
        #            }
        #        }
        #return db.find_all(db_name, collection_name, geo_near_query2)
        return jsonify(db.createIndex_find(db_name, collection_name, "ratings.coords_list", pymongo.GEO2D, geo_near_query))
        '''
	coords_in_frame = db.aggregate(db_name, collection_name, geo_near_query)

	##
	# Do we cluster the coords found to certain key points for better display or not?
	##
	return coords_in_frame
        '''
	
##
# Function to return info of a point by touching the screen
# Need to map the touch to the closest point, and if the distance is less than a threshold, return it. Else return null.
# This is to help the user view details of a point on the screen.
# Do we need another table(collection)? for this and the above one, cluster coords to certain key points?
# As we need to display the statistics of the point displayed.
# Or can i think of a good enough aggregation function?? :D
##
def view_closest_point_stats(link, db_name, collection_name, scale, point_selected, category):
	#db = mdb.DaoImpl(link, db_name, collection_name)
        db = mdb.DaoImpl.getInstance()

        '''
	db.createIndex({"ratings.coordinates":"2d"})
	
	query = [
			{
				"$geoNear":{
					near: point_selected,
					spherical: False,
					#NOTE: Arbitrary value for maxDistance for now
					maxDistance: scale*2,
					distanceField: "Distance"
				}
			},
			{
				"$sort":{"Distance":1}
			},
			{
				"$limit":1
			}
		]

	return db.aggregate(db_name, collection_name, query)
        '''
        geo_near_query = {
                                "ratings.coords_list": SON([("$near",point_selected), ("$maxDistance",1.1*scale)])
                        }
        return jsonify(db.createIndex_find(db_name, collection_name, "ratings.coords_list", pymongo.GEO2D, geo_near_query, limit = 1)[1])

####
# The above function returns the data of a single point.
# But if we want the aggregate statistics of a region, we need a different aggregation query, the below few(in this case 2) functions returns the aggregate results of data
# Like: Number of 5 star, num of 4 star etc, num who voted in each category
####
def num_reviews_for_each_star_count_around_selected_area(link, db_name, collection_name, scale, point_selected):
        #db = mdb.DaoImpl(link, db_name, collection_name)
        db = mdb.DaoImpl.getInstance()

        '''
        db.createIndex({"ratings.coordinates":"2d"})
	
	query = [
			{
				"$geoNear":{
					"near": point_selected,
					"spherical": False,
					#NOTE: Arbitrary value for maxDistance for now, need to find out its relation to the scale
					"maxDistance": scale*5,
					"distanceFiels": "Distance"
				}
			},
			{
				"$group":{
					"_id":"ratings.rating",
					"count":{"$sum":1}
				}
			}
		]
        '''
        query = {
                        "ratings.coords_list": SON([("$near",point_selected), ("$maxDistance",1.1*scale)])
                }
        options = {
                    '_id':1,
                    "ratings.rating":1
                }
        data =  db.createIndex_find(db_name, collection_name, "ratings.coords_list", pymongo.GEO2D, query, options = options)[1]
        data = [j['rating'] for i in data for j in i['ratings']]
        return data

def num_reviews_for_each_category_around_selected_area(link, db_name, collection_name, scale, point_selected):
        #db = mdb.DaoImpl(link, db_name, collection_name)
        db = mdb.DaoImpl.getInstance()

        db.createIndex({"ratings.coordinates":"2d"})

	# This query will have a bug, need to change the $group stage
	# Still not sure of the index part i wrote
        '''
        query = [
                        {
                                "$geoNear":{
                                        near: point_selected,
                                        spherical: False,
                                        #NOTE: Arbitrary value for maxDistance for now, Need to find out its relation to the scale.
                                        maxDistance: scale*5,
                                        distanceFiels: "Distance"
                                }
                        },
                        {
                                "$group":{
                                        "_id":"ratings.category",
                                        "count":{"$sum":1}
                                }
                        }
                ]

        return db.aggregate(db_name, collection_name, query)
        '''
        query = {
                        "ratings.coords_list": SON([("$near",point_selected), ("$maxDistance",1.1*scale)])
                }
        options = {
                    "_id":0,
                    "ratings.category":1
                }
        data =  db.createIndex_find(db_name, collection_name, "ratings.coords_list", pymongo.GEO2D, query, options = options)[1]
        return data

##
# Now to add a function which'll enable the user to view data of his friends. Ignoring public parameter for now, just displaying everything.
# Returns the friends reviews only
# NOTE: This loads the friends entire data, not just the data around the screen
# TODO: The user can choose to make some reviews/categories private
##
def view_friends_reviews(link, db_name, collection_name, friend_username):
	#db = mdb.DaoImpl(link, db_name, collection_name)
        db = mdb.DaoImpl.getInstance()

	query_find_friend_data = {
                "username": friend_username
        }

        project_data = {
                        "_id":0,
                        "username":1,
                        "ratings":1
        }
	
	friend_data = db.find_one(db_name, collection_name, query_find_friend_data, project_data)
	return jsonify(friend_data)

	
def add_friend(link, db_name, collection_name, username, friend_username):
        db = mdb.DaoImpl.getInstance()
        #Verify if the given username is already in db
        verify = db.find_one(db_name, collection_name, {"username":friend_username})
        verify_if_already_friend = db.find_one(db_name, collection_name, {"username":username},{"_id":0, "friends":1})
        print verify_if_already_friend
        if verify != None and friend_username not in verify_if_already_friend['friends']:
                    query_find = {
                            "username":username
                                }
                    query_update = {
                            "$push":{"friends":friend_username}
                                }
                    return db.update_one(db_name, collection_name, query_find, query_update, True)
        else:
            return None


def view_friends_names(link, db_name, collection_name, username):
        db = mdb.DaoImpl.getInstance()
        query_find = {
                        "username":username
                    }
        query_project = {
                        "_id":0,
                        "friends":1
                    }
        return db.find_one(db_name, collection_name, query_find, query_project)['friends']





###################

##
# Have written the core functions above. Now can write the basic functions like returning the entire data of an ObjectId()
##

def view_obj_data(link, db_name, collection_name, scale, obj_id):
        #db = mdb.DaoImpl(link, db_name, collection_name)
        db = mdb.DaoImpl.getInstance()

        query_find_obj_id = {
                "_id": obj_id
        }

        obj_data = db.find_one(db_name, collection_name, query_find_obj_id)
        return obj_data

##
# Function to add a friend to a user
##















