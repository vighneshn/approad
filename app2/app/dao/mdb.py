from pymongo import MongoClient
from bson.objectid import ObjectId
import sys

#TODO: Have to change the way dao is defined, as multiple instances arent allowed. In progress.
#NOTE:IMPORTANT NOTE: Change the db address in this file.

###
# Dao or Data Access Object 
# Used to interface with the database using this object.
# 
# The data parameter is a dict following json format I guess. Format for the data depends on the 
# 
# This is an implementation of this design pattern to smoothen the process.
###
class DaoImpl:
	__client = None
        __instance = None
	
        @staticmethod
        def getInstance():
            """Static Access Method. """
            if DaoImpl.__instance is None:
                DaoImpl()
            return DaoImpl.__instance

        def __init__(self):
            """Virtually private constructor."""
            if DaoImpl.__instance is not None:
                raise Exception("This class is a singleton!")
            else:
                DaoImpl.__instance = self

	#link can be hardcoded when we have a link.
	#def __init__(self, link, db_name, collection_name):
        #   self.__client = MongoClient(link)
        def get_collection(self, db_name, collection_name):
            if self.__client is None:
                self.__client = MongoClient("mongodb://localhost:27017")
            return self.__client[db_name][collection_name]

	def obj_id_as_string(self, objid=None):
		if objid==None:
			return ObjectId()
                else:
		        return ObjectId(objid)

	
	def count(self, db_name, collection_name, query, options=None):
        	return self.get_collection(db_name,collection_name).find(query, options).count()

	####
	# All names are self explanatory of the action.
	####
	# Supply the appropriate query/data in the parameters, as per the query language/aggregation framework. 
	# I think find and aggregate functions can be used similarly. But find is the query language, aggregate uses the aggregation_framework. Though both can be used, aggregation
	# framework allows for renaming and introducing new fields in the project stage, far more powerful than find, though may require more time to execute at times.
	# The options parameters refers to the projection required ie what fields we want as output.
	####
    	def find_one(self, db_name, collection_name, query, options=None):
        	return self.get_collection(db_name, collection_name).find_one(query, options)

   	def find_all(self, db_name, collection_name, query, skip=None, limit=None, sort=None, options=None):
        	cursor = self.get_collection(db_name, collection_name).find(query, options)
        	if limit is not None:
        	    cursor = cursor.limit(int(limit))
        	if skip is not None:
        	    cursor = cursor.skip(int(skip))
        	if sort is not None:
        	    cursor = cursor.sort(sort)
        	total = cursor.count()
        	# data =list(cursor)
        	data=[]
        	for item in cursor:
        	    item['_id'] = str(item['_id'])
        	    data.append(item)
	
	        return total, data
	
	def insert_one(self, db_name, collection_name, data, options=None):
		return self.get_collection(db_name, collection_name).insert_one(data, options)

	def insert_many(self, db_name, collection_name, data, options=None):
		return self.get_collection(db_name, collection_name).insert_many(data, options)

    	def update_one(self, db_name, collection_name, query, doc, options=None):
        	return self.get_collection(db_name, collection_name).update_one(query, doc, options)

    	def update_many(self, db_name, collection_name, query, doc, options=None):
        	return self.get_collection(db_name, collection_name).update_many(query, doc, options)

    	def delete_one(self, db_name, collection_name, query, options=None):
        	return self.get_collection(db_name, collection_name).deleteOne(query, options)
	
	##
	# To process and shape the data we have for useage in ML tasks or other big data tasks. Powerful function.
	##
    	def aggregate(self, db_name, collection_name, query, options=None):
        	return self.get_collection(db_name, collection_name).aggregate(query, options)

        ##
        # Create index for geospatial queries
        ##
        def createIndex_find(self, db_name, collection_name, index_name, index_type, query, skip=None, limit=None, sort=None, options=None):
                self.get_collection(db_name, collection_name).ensure_index([(index_name, index_type)])
                return self.find_all(db_name, collection_name, query, skip, limit, sort, options)
