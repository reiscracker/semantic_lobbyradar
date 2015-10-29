

# Imports for using and connecting to mongodb

# import pymongo
# from pymongo import MongoClient
# from pprint import pprint, pformat, PrettyPrinter
# from bson.son import SON
# from bson.objectid import ObjectId
# from os.path import exists
# import json
# from ipy_table import *

# Connect to database and create variables for the collections
# client = MongoClient()
# db = client.lobbyradar
# entities, relations = db.entities, db.relations

#
# Some format strings and helpers
#

def formatRow(self, row):
    formats = { 2: u"{}: {}", 3: u"{}: {} ({})" }
    row_format = formats.get( len(row), u"{} " * len(row) )
    
    return (row_format.format(*row.values()))


def printCols(self, iterable, columns=5, spacing=30):
    """ Prints an iterable structure in columns instead of many newlines """
    formatElement = u"{:<%s}" % spacing
    
    row_format =  formatElement * columns
    for chunk in zip(*[iter(iterable)]*columns):
        print(row_format.format(*chunk))
        
    # Splitting might be uneven and we could have some elements left, so print those too
    # The missing elements are those with an index in range of iterable % columns at the end 
    rest=iterable[len(iterable) - (len(iterable) % columns):]
    print( (formatElement * len(rest)).format(*rest) )
    

class Query:
    query_formats = {
            "exists": '',
    }

    def exists(self,field):
        return '{ %s: {"$exists": 1, "$ne": None} }' % format(field)

    def id(self, objId):
        return '{ "_id": %s }' % objId
query = Query()




class MongoHelper:

    def __init__(self, collection):
        self.collection = collection

    def find_if_exists(self, field, mask=None):
        return self.collection.find_one({ field: {"$exists": 1, "$ne": None} }, mask)


    def lookup_entity(self, entity_id, queryMask=None):
        return self.collection.find_one({ "_id": entity_id }, queryMask)

    def lookup_relation(self, relation_id, queryMask=None):
        return self.collection.find_one({ "_id": relation_id }, queryMask)
        
    def get_relation_entity_ids(self, relation_id): 
        # Look up the entity ids of a relation with provided id
        relation = self.lookup_relation(relation_id, {'_id': 0, 'data.desc': 1, 'entities': 1})
        return self.collection['entities']
        
    
        # Find all those entities in the entities collection
#        (entity1, entity2) = [ self.lookup_entity(e_id) for e_id in  ]
#        return (entity1, entity2)

class Pipeline:
    stage_formats = {
     "unwind" : '{{ "$unwind": "${}" }}',
     "group" : '{{ "$group": {{ "_id": "${}" }}, "count": {{"$sum": 1}} }}',
     "sort" : '{ "$sort": { "count": -1 } }',
     "min_count" : '{{ "$match": {{ "count": {{ "$gt": {} }} }} }}'
     }

    def __init__(self):
        self.pipeline = []

    def unwind(self,x):
        self.pipeline.append({ "$unwind": "${%s}" % x })
        return self

    def group(self,x):
        g = [ { "$group": { "_id": "x", "count": {"$sum": 1} }}


    def sort(self):
        self.pipeline.append({ "$sort": { "count": -1 } })
        return self

    def min_count(self, x):
        self.pipeline.append({ "$match": { "count": { "$gt": x } } })
        return self
    
    def get(self):
        return self.pipeline






#     def make_pipeline(self, **kwargs):
#         unwind = lambda field:         group = lambda field: {"$group": {"_id": "$"+field, "count": {"$sum": 1}} }
#         sort = {"$sort": {"count": -1} }
#         min_count = lambda minimum: {"$match": {"count": {"$gt": minimum}}}
# 
#         pipeline = []
#         if (kwargs.has_key('unwind')): pipeline.append(unwind(kwargs['unwind']))
#         if (kwargs.has_key('group')): pipeline.append(group(kwargs['group']))
#         if (kwargs.has_key('sort')): pipeline.append(sort)
#         if (kwargs.has_key('min_count')): pipeline.append(min_count(kwargs['min_count']))
#         return pipeline
# 
#     # Returns a simple aggregationd directly as list of values
#     def simple_aggregate(self, group="", unwind=None, sort=True):
#         pipeline = make_pipeline(unwind=unwind, group=group, sort=sort)
#         return [ "%s: %s" % (d['_id'], d['count']) for d in self.collection.aggregate(pipeline, cursor={}) ]
