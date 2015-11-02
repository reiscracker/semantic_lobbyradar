__author__ = 'reiscracker'
# coding: utf-8
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF, XSD, RDFS

lobbyFacts = Namespace('https://studi.f4.htw-berlin.de/~s0539710/lobbyradar#')
lobbyOntology = Namespace('https://studi.f4.htw-berlin.de/~s0539710/lobbyradar/ontology#')
org = Namespace('http://www.w3.org/ns/org#')
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
vcard = Namespace('http://www.w3.org/2006/vcard/ns#')

class EntityConvert:
    def __init__(self, graph):
        self.g = graph

    def convert_entity(self, entity):
        # First important thing is to define a URI.
        s = self.make_URI(entity['name'])
        # And define a type based on the type and tag attribute
        self.g.add((s, RDF.type, self.make_type(entity['type'], entity['tags'])))
        # Add the mongo id
        self.g.add((s, lobbyOntology.mongo_id, Literal(entity['_id'])))
        # Add aliases
        self.g.add((s, lobbyOntology.alias, self.make_aliases(entity['aliases'])))
        # Add name
        self.g.add((s, FOAF.name, Literal(entity['name'])))
        # Data
        for d in entity['data']:
            self.add_data(s, d)


    def make_URI(self, name):
        """
        URI will be the name stripped of whitespaces (with our namespaces added)
        """
        from urllib import quote_plus
        return lobbyFacts.term(quote_plus(name.encode("ascii", "ignore")))
    def make_type(self, type, tags):
        """
        Type is either Person, Political Party or, more general, Organization
        An Agent is a party when it has the party tag.
        """
        type_map = {
            "partei": lobbyOntology.term("PoliticalParty"),
            "lobbyorganisation": lobbyOntology.term("LobbyOrganization"),
            "ruestung": lobbyOntology.term("ArmsCorporation"),
            "Bau": lobbyOntology.term("ConstructionCorporation"),
            "Finanzen": lobbyOntology.term("FinancialCorporation"),
            "Banken / Versicherungen": lobbyOntology.term("FinancialCorporation"),
            "bank": lobbyOntology.term("FinancialCorporation"),
            "akademisch": lobbyOntology.term("EducationalOrganization"),
            "Energie / Wasser / Versorgung": lobbyOntology.term("InfrastructureOrganization"),
            "energie": lobbyOntology.term("InfrastructureOrganization"),
            "Gesundheit": lobbyOntology.term("HealthOrganization"),
            "gesundheit": lobbyOntology.term("HealthOrganization"),
            "Immobilien": lobbyOntology.term("RealEstateCorporation"),
            "Handel": lobbyOntology.term("TradingCorporation"),
            "Religion": lobbyOntology.term("ReligionOrganization"),
            "medien": lobbyOntology.term("MediaCorporation"),
            "Industrie": lobbyOntology.term("ManufactureCorporation"),
            "industrie": lobbyOntology.term("ManufactureCorporation")
        }
        # Type could either be Person
        if type == "person":
            return FOAF.Person
        # Or we find a tag that indicates the type of the organization
        for tag in tags:
            if type_map.has_key(tag):
                return type_map[tag]
        # Eventually, if we didn't find any tag, return org.Organization
        return org.Organization

    def make_aliases(self, aliases):
        # Bag of aliases (why is Bag in RDF namespace, not RDFS?)
        aliasBag = BNode()
        self.g.add((aliasBag, RDF.type, RDF.Bag))
        for i, alias in enumerate(aliases, 1):
            self.g.add((aliasBag, rdf.term("_%s" % i), Literal(alias)))
        return aliasBag

    def add_data(self, s, dataElement):
        """
        Data now is a little more complicated. Each piece of information in this array could contain a completely different information
        The information is primariliy described by the data.desc field
        """
        data_desc_mapping = {
            "Titel": self.data_make_title,
            "Adresse": self.data_make_address,
            "Link": self.data_add_link,
            "Nachname": self.data_add_lastname,
            "Vornamen": self.data_add_firstname,
            "Foto": self.data_add_image,
            "Beschreibungstext": self.data_add_comment
        }
        desc = dataElement['desc']
        if data_desc_mapping.has_key(desc):
            p, o = data_desc_mapping[desc](dataElement['value'])
            self.g.add((s, p, o))


    def data_make_title(self, title):
        return (FOAF.title, Literal(title))

    def data_make_address(self, address):
        addressTermsMap = {
            "addr": RDFS.term("label"),
            "city": vcard.locality,
            "country": vcard.term("country-name"),
            "county": vcard.term("country-name"),
            "email": vcard.term("hasEmail"),
            "name": vcard.term("hasFN"),
            "postcode": vcard.term("postal-code"),
            "street": vcard.term("street-address"),
            "tel": vcard.term("hasTelephone")
        }
        addressObject = BNode()
        # Address has either type Home or Work
        if address.has_key('addr') and address['addr'] is not None:
            self.g.add((addressObject, RDF.type, vcard.term("Work")))
        else:
            self.g.add((addressObject, RDF.type, vcard.term("Home")))
        # Add the address values
        for key, val in address.iteritems():
            if addressTermsMap.has_key(key):
                self.g.add((addressObject, addressTermsMap[key], Literal(val)))
        return (vcard.hasAddress, addressObject)

    def data_add_link(self, link):
        import urllib
        return (RDFS.seeAlso, URIRef(urllib.quote_plus(link['url'].encode("ascii", "ignore"))))

    def data_add_firstname(self, firstname):
        return (FOAF.givenName, Literal(firstname, datatype=XSD.string))

    def data_add_lastname(self, lastname):
        return (FOAF.familyName, Literal(lastname, datatype=XSD.string))

    def data_add_image(self, image):
        imageNode = URIRef(image['url'])
        self.g.add((imageNode, RDF.type, FOAF.Image))
        return (FOAF.depiction, imageNode)

    def data_add_comment(self, comment):
        return (RDFS.comment, Literal(comment))
