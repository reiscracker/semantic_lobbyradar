from pymongo import MongoClient
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF, XSD
from entity_to_rdf import EntityConvert

# Connect to database and create variables for the collections
client = MongoClient()
db = client.lobbyradar
entities = db.entities
relations = db.relations
# Print some statistics about our database dump
print("Collections in database: " + ", ".join(db.collection_names(include_system_collections=False)))
print("Entities: %s documents" % entities.count())
print("Relations: %s documents" % relations.count())

# Create a graph and prepare by loading ontology and binding prefixes
g = Graph()
converter = EntityConvert(g)

# entity = entities.find_one({'name': 'Rudolf Henke'})
all_entities = entities.find()
for i,e in enumerate(all_entities):
    if (i % (entities.count() / 20) == 0):
        print("%s of %s processed" % (i, entities.count()))
    converter.convert_entity(e)

# Save graph to file
f = open('entities.ttl', 'w')
f.write(converter.g.serialize(format="turtle"))
f.close()
