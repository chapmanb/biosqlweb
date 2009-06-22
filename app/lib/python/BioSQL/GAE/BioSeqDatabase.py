"""Model BioSeqDatabase interface of Biopython BioSQL with Google App Engine.
"""

from BioSQL.GAE import BioSQLModels as biosql
from BioSQL.GAE import Loader

def open_database(*args, **kwargs):
    return DBServer()

class DBServer:
    def __init__(self):
        pass

    def __getitem__(self, db_name):
        biodb = biosql.Biodatabase.all().filter('name =', db_name
                ).get()
        if not biodb:
            raise KeyError("No biodatabase found: %s" % db_name)
        return BioSeqDatabase(biodb)

    def keys(self):
        biodb = biosql.Biodatabase.all()
        return [d.name for d in biodb]

    def remove_database(self, db_name):
        raise NotImplementedError

    def new_database(self, db_name, authority=None, description=None):
        new_biodb = biosql.Biodatabase(name=db_name, authority=authority,
                description=description)
        new_biodb.put()
        return self[db_name]

class BioSeqDatabase:
    """Provide layer on top of BioSQL Biodatabases for record access.
    """
    def __init__(self, biodb):
        self._biodb = biodb
    
    def load(self, record_iterator, fetch_NCBI_taxonomy=False):
        """Load a set of SeqRecords into the BioSQL database.
        """
        db_loader = Loader.GAEDatabaseLoader(self._biodb)
        num_records = 0
        for cur_record in record_iterator:
            num_records += 1
            db_loader.load_seqrecord(cur_record)
        return num_records

    def get_biodatabase(self):
        return self._biodb
