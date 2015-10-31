def formatRow(row):
    formats = { 2: u"{}: {}", 3: u"{}: {} ({})" }
    row_format = formats.get( len(row), u"{} " * len(row) )
    
    return (row_format.format(*row.values()))


def printCols(iterable, columns=5, spacing=30):
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

    def exists(self,field):
        return '{ %s: {"$exists": 3, "$ne": None} }' % format(field)

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
        
    
def make_pipeline(**kwargs):
    unwind = lambda field: {"$unwind": "$"+field}         
    group = lambda field: {"$group": {"_id": "$"+field, "count": {"$sum": 1}} }
    sort = {"$sort": {"count": -1} }
    min_count = lambda minimum: {"$match": {"count": {"$gt": minimum}}}

    pipeline = []
    if (kwargs.has_key('unwind')): pipeline.append(unwind(kwargs['unwind']))
    if (kwargs.has_key('group')): pipeline.append(group(kwargs['group']))
    if (kwargs.has_key('sort')): pipeline.append(sort)
    if (kwargs.has_key('min_count')): pipeline.append(min_count(kwargs['min_count']))
    return pipeline

# Returns a simple aggregationd directly as list of values
def simple_aggregate(self, group="", unwind=None, sort=True):
    pipeline = make_pipeline(unwind=unwind, group=group, sort=sort)
    return [ "%s: %s" % (d['_id'], d['count']) for d in self.collection.aggregate(pipeline, cursor={}) ]
