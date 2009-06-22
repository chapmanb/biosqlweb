"""Load biopython objects into a BioSQL Google App Engine datastore.
"""
from google.appengine.ext import db

from Bio import Alphabet

from BioSQL.GAE import BioSQLModels as biosql

class GAEDatabaseLoader:
    """Load Biopython SeqRecord objects into the datastore.
    """
    def __init__(self, biodb):
        self._biodb = biodb

    def load_seqrecord(self, rec):
        """Load a Biopython SeqRecord object; mimics the standard interface.
        """
        bioentry = self._load_bioentry(rec)
        self._load_biosequence(rec, bioentry)
        self._load_annotations(rec, bioentry)

    def _get_ontology(self, ontology_name):
        """Retrieve an existing or generate a new ontology with the given name
        """
        ontology = biosql.Ontology.all().filter('name =', ontology_name
                ).get()
        if not ontology:
            ontology = biosql.Ontology(name=ontology_name)
            ontology.put()
        return ontology

    def _get_term(self, term_name, ontology):
        """Retrieve a Term with the given key name and ontology.
        """
        term = biosql.Term.all().filter('name =', term_name
                ).filter("ontology =", ontology).get()
        if not term:
            term = biosql.Term(name=term_name, ontology=ontology)
            term.put()
        return term
    
    def _load_annotations(self, record, bioentry):
        """Record a SeqRecord's misc annotations in the database.

        The annotation strings are recorded in the bioentry_qualifier_value
        table, except for special cases like the reference, comment and
        taxonomy which are handled with their own tables.
        """
        #Handled separately
        separate_tags = ["references", "comment", "ncbi_taxid"]
        tag_ontology = self._get_ontology('Annotation Tags')
        for key, value in record.annotations.items():
            if key not in separate_tags:
                term = self._get_term(key, tag_ontology)
                if not isinstance(value, list):
                    value = [value]
                for index, entry in enumerate(value):
                    cur_qual_val = biosql.BioentryQualifierValue(term=term,
                            value=str(entry), bioentry=bioentry, rank=index)
                    cur_qual_val.put()

    def _load_biosequence(self, record, bioentry):
        """Record a SeqRecord's sequence and alphabet in the database.
        """
        # determine the string representation of the alphabet
        if isinstance(record.seq.alphabet, Alphabet.DNAAlphabet):
            alphabet = "dna"
        elif isinstance(record.seq.alphabet, Alphabet.RNAAlphabet):
            alphabet = "rna"
        elif isinstance(record.seq.alphabet, Alphabet.ProteinAlphabet):
            alphabet = "protein"
        else:
            alphabet = "unknown"
        cur_bioseq = biosql.Biosequence(version=0, length=len(record.seq),
                seq=str(record.seq), alphabet=alphabet, bioentry=bioentry)
        cur_bioseq.put()

    def _load_bioentry(self, record):
        """Load the high level bioentry object for this record.
        """
        if record.id.count(".") == 1: # try to get a version from the id
            #This assumes the string is something like "XXXXXXXX.123"
            accession, version = record.id.split('.')
            try :
                version = int(version)
            except ValueError :
                accession = record.id
                version = 0
        else: # otherwise just use a version of 0
            accession = record.id
            version = 0

        if ("accessions" in record.annotations 
                and isinstance(record.annotations["accessions"],list)
                and record.annotations["accessions"]):
            #Take the first accession (one if there is more than one)
            accession = record.annotations["accessions"][0]
        
        # XXX To Do -- taxon

        if "gi" in record.annotations :
            identifier = record.annotations["gi"]
        else :
            identifier = record.id

        #Allow description and division to default to NULL as in BioPerl.
        description = getattr(record, 'description', None)
        division = record.annotations.get("data_file_division", None)

        cur_bioentry = biosql.Bioentry(name=record.name, accession=accession,
                identifier=identifier, division=division,
                description=description, version=version,
                biodatabase=self._biodb)
        cur_bioentry.put()
        return cur_bioentry
