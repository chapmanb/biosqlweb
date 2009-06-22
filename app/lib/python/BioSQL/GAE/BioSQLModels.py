"""Database models for the main BioSQL database.

These have as close a relationship as possible to the standard BioSQL schema,
which is documented at: http://biosql.org/wiki/Schema_Overview.

Currently this only represents a subset of the available BioSQL tables.
"""
from google.appengine.ext import db

class Ontology(db.Model):
    name = db.StringProperty(required=True)
    definition = db.TextProperty()

class Term(db.Model):
    name = db.StringProperty(required=True)
    definition = db.TextProperty()
    identifier = db.StringProperty()
    is_obsolete = db.BooleanProperty()
    ontology = db.ReferenceProperty(Ontology,
            collection_name="terms")

class Biodatabase(db.Model):
    name = db.StringProperty(required=True)
    authority = db.IntegerProperty()
    description = db.TextProperty()

class Bioentry(db.Model):
    name = db.StringProperty(required=True)
    accession = db.StringProperty()
    identifier = db.StringProperty()
    division = db.StringProperty()
    description = db.TextProperty()
    version = db.IntegerProperty()
    biodatabase = db.ReferenceProperty(Biodatabase,
            collection_name="bioentries")
    # XXX toDo
    # taxon

class BioentryRelationship(db.Model):
    object_bioentry = db.ReferenceProperty(Bioentry,
            collection_name="object_relationships")
    subject_bioentry = db.ReferenceProperty(Bioentry,
            collection_name="subject_relationships")
    term = db.ReferenceProperty(Term)
    rank = db.IntegerProperty()

class Biosequence(db.Model):
    version = db.IntegerProperty()
    length = db.IntegerProperty()
    alphabet = db.StringProperty()
    seq = db.TextProperty()
    bioentry = db.ReferenceProperty(Bioentry,
            collection_name="seqs")

class BioentryQualifierValue(db.Model):
    term = db.ReferenceProperty(Term)
    bioentry = db.ReferenceProperty(Bioentry,
            collection_name="quals")
    value = db.StringProperty()
    rank = db.IntegerProperty()
