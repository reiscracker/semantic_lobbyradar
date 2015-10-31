from pymongo import MongoClient
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF, XSD

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
# g.parse("../ontology/ontology.owl")
# g.bind("lobbyradar", u'https://studi.f4.htw-berlin.de/~s0539710/lobbyradar#')
# g.bind("rdf", RDF)
# g.bind("foaf", FOAF)
lobbyFacts = Namespace('https://studi.f4.htw-berlin.de/~s0539710/lobbyradar#')
lobbyOntology = Namespace('https://studi.f4.htw-berlin.de/~s0539710/lobbyradar/ontology#')
org = Namespace('http://www.w3.org/ns/org#')
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
vcard = Namespace('http://www.w3.org/2006/vcard/ns#')
        
entity = entities.find_one({'data.desc': 'Adresse'})

# First important thing is to define a URI. This will be the name stripped of whitespaces (with our namespaces added)
e = lobbyFacts.term(entity.get('name').replace(' ', '_'))
# And define a type based on the type attribute
entityType = FOAF.Person if entity['type'] is "person" else org.Organization
g.add((e, RDF.type, entityType))

# Mongo ID
g.add((e, lobbyOntology.mongo_id, Literal(entity['_id'])))
# Bag of aliases (why is Bag in RDF namespace, not RDFS?)
aliases = BNode()
g.add((aliases, RDF.type, RDF.Bag))
for i, alias in enumerate(entity['aliases'], 1):
    g.add((aliases, rdf.term("_%s" % i), Literal(alias)))
g.add((e, lobbyOntology.alias, aliases))
# Name
g.add((e, FOAF.name, Literal(entity['name'])))

# Data now is a little more complicated. Each piece of information in this array could contain a completely different information
# The information is primariliy described by the data.desc field
def make_title(title):
    print("Title: %s" % title)
    return (FOAF.title, Literal(title))
def make_address(address):
    print("Address: %s" % address)
    addressObject = BNode()
    g.add((addressObject, vcard.term('country-name'), Literal(address['country'], datatype=XSD.string)))
    g.add((addressObject, vcard.locality, Literal(address['city'], datatype=XSD.string)))
    g.add((addressObject, vcard.term('postal-code'), Literal(address['postcode'], datatype=XSD.string)))
    g.add((addressObject, vcard.term('street-address'), Literal(address['street'], datatype=XSD.string)))
    return (vcard.hasAddress, addressObject)
mapping = {
    "Titel": make_title,
    "Adresse": make_address
}

for d in entity['data']:
    desc = d['desc']
    print("Desc: %s" % desc)
    if mapping.has_key(desc):
        p, o = mapping[desc](d['value'])
        g.add((e, p, o))


#     if d['desc'] == "Titel":
#         p, o = make_title(d['value']) 
#     elif d['desc'] == "Adresse":
#         p, o = make_address(d['value'])
#         g.add((e, p, o))

print(g.serialize(format="turtle"))
