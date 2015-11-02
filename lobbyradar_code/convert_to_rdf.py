# -*- coding: utf-8 -*-
from pymongo import MongoClient
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF, XSD
from entity_to_rdf import EntityConvert

lobbyFacts = Namespace('https://studi.f4.htw-berlin.de/~s0539710/lobbyradar#')
lobbyOntology = Namespace('https://studi.f4.htw-berlin.de/~s0539710/lobbyradar/ontology#')
org = Namespace('http://www.w3.org/ns/org#')
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
vcard = Namespace('http://www.w3.org/2006/vcard/ns#')

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
relationGraph = Graph()
converter = EntityConvert(g)

entity = entities.find_one({'name': 'Rudolf Henke'})
all_entities = entities.find()
for i,e in enumerate(all_entities):
    if (i % (entities.count() / 20) == 0):
        print("%s of %s processed" % (i, entities.count()))
    converter.convert_entity(e)

def get_uri_by_object_id(objectId):
    g.bind("lobbyOntology", 'https://studi.f4.htw-berlin.de/~s0539710/lobbyradar/ontology#')
    result = g.query("SELECT ?uri ?type WHERE { ?uri lobbyOntology:mongo_id '%s' ; <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?type }" % str(objectId))
    for row in result:
        return { 'uri': row['uri'], 'type': row['type'] }


positions_map = {
    u"Vorstand": lobbyOntology.term("executiveOf"),
    u"Mitglied": org.term("memberOf"),
    u"Ordentliches Mitglied": lobbyOntology.term("fullMemberOf"),
    u"Stellvertretendes Mitglied": lobbyOntology.term("deputyMemberOf"),
    u"Arbeitsverh\xe4ltnis": lobbyOntology.term("employeeOf"),
    u"Aufsichtsratsmitglied": lobbyOntology.term("supervisoryMemberOf"),
    u"Mitglied des Aufsichtsrates": lobbyOntology.term("supervisoryMemberOf"),
    u"Mitglied des Aufsichtsrats": lobbyOntology.term("supervisoryMemberOf"),
    u"Mitglied des Kuratoriums": lobbyOntology.term("kuratoriumMemberOf"),
    u"Mitglied des Stiftungsrates": lobbyOntology.term("kuratoriumMemberOf"),
    u"Mitglied des Beirates": lobbyOntology.term("advisoryMemberOf"),
    u"Mitglied des Vorstandes": lobbyOntology.term("executiveOf"),
    u"Vorstandsmitglied": lobbyOntology.term("executiveOf"),
    u"Staatssekret\xe4r": lobbyOntology.term("secretaryOf"),
    u'Parlamentarischer Staatssekret\xe4r': lobbyOntology.term("secretaryOf"),
    u"Mitglied im Rundfunkrat": lobbyOntology.term("mediaAdvisoryMemberOf"),
    u"Mitglied des Kreistages": lobbyOntology.term("countyCouncilMemberOf"),
    u"Parlamentarischer Staatssekretär": lobbyOntology.term("secretaryOf"),
    u"Vorsitzender": lobbyOntology.term("president"),
}
# Convert the relations next
all_relations = relations.find()
for i, relation in enumerate(all_relations):
    if (i % (relations.count() / 20) == 0):
        print("%s of %s processed" % (i, relations.count()))

    # Find the two related entities by sparqling
    objectIds = relation['entities']
    related_entities = (get_uri_by_object_id(objectIds[0]), get_uri_by_object_id(objectIds[1]))

    # Get the type of the relation
    for single_relation in relation['data']:
        relation_desc = single_relation['desc']

        if relation_desc == "Verbindung":
            """ For "Verbindung" we will need to know which of the entities is a Person for the relations direction """
            if related_entities[1]['type'] == FOAF.Person:
                s, o = related_entities[1]['uri'], related_entities[0]['uri']
            else:
                s, o = related_entities[0]['uri'], related_entities[1]['uri']
            position = single_relation['value']['position'] if single_relation['value'].has_key('position') else "Mitglied"
            if positions_map.has_key(position):
                relationGraph.add((s, positions_map[position], o))

        elif relation_desc == "Parteispende":
            # print("Parteispende-------------------")
            if related_entities[1]['type'] == lobbyOntology.term("PoliticalParty"):
                s, o = related_entities[0]['uri'], related_entities[1]['uri']
            else:
                s, o = related_entities[1]['uri'], related_entities[0]['uri']

            donation = BNode()
            amount = single_relation['value']['amount']
            year = "%s-00-00T00:00:00" % single_relation['value']['year']
            relationGraph.add((donation, RDF.type, lobbyOntology.Donation))
            relationGraph.add((donation, lobbyOntology.amount, Literal(amount, datatype=XSD.float)))
            if year: relationGraph.add((donation, lobbyOntology.year, Literal(year, datatype=XSD.dateTime)))
            relationGraph.add((s, lobbyOntology.donated, donation))
            relationGraph.add((o, lobbyOntology.received, donation))

# Save graph to file
# f = open('entities.ttl', 'w')
# f.write(converter.g.serialize(format="turtle"))
# f.close()
f = open('entities.ttl', 'w')
f.write(converter.g.serialize(format="turtle"))
f.close()
f = open('entities.xml', 'w')
f.write(converter.g.serialize())
f.close()

f = open('relations.ttl', 'w')
f.write(relationGraph.serialize(format="turtle"))
f.close()
f = open('relations.xml', 'w')
f.write(relationGraph.serialize())
f.close()
