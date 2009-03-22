import os
import logging
import StringIO
import collections

from google.appengine.api import users
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app
from django.utils import simplejson as json

from mako.template import Template

from Bio import SeqIO

from BioSQL.GAE import BioSeqDatabase

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        tmpl = Template(filename=os.path.join("templates", "main.html"))
        self.response.out.write(tmpl.render(records=self._get_records()))

    def _get_records(self):
        """Retrieve BioSQL records in the database.
        """
        biodb_handler = BiodatabaseHandler()
        bioentries = biodb_handler.get_bioentries()
        records = []
        for bioentry in bioentries:
            b_tmpl = Template(bioentry_template)
            retrieve_url = "rpc?action=bioentry_details&bioentry_key=%s" % (
                    bioentry.key())
            records.append(b_tmpl.render(accession=bioentry.accession,
                description=bioentry.description, retrieve_url=retrieve_url))
        return records

class RPCHandler(webapp.RequestHandler):
    """Handler for Ajax RPC calls, from:

    http://code.google.com/appengine/articles/rpc.html
    """
    def __init__(self):
        webapp.RequestHandler.__init__(self)
        self.methods = BiodatabaseHandler()
 
    def get(self):
        action = self.request.get('action')
        func = self._get_function(action)
        if func:
            params = self._get_params(self.request)
            self._finish(func, params)
    
    def post(self):
        action = self.request.get('action')
        func = self._get_function(action)
        if func:
            params = self._get_params(self.request)
            self._finish(func, params)

    def _get_params(self, request):
        """Retrieve parameters associated with the request.
        """
        ignore_args = ['action']
        params = [(str(a), self.request.get(a)) for a in 
                request.arguments() if a not in ignore_args]
        return dict(params)

    def _get_function(self, action):
        """Access our local function associated with the ajax call.
        """
        func = None
        if action:
            if action[0] == '_':
                self.error(403) # access denied
                return
            else:
                func = getattr(self.methods, action, None)
        if not func:
            self.error(404) # file not found
            return
        return func

    def _finish(self, func, params):
        result = func(**params)
        self.response.out.write(result)
  
class BiodatabaseHandler:
    """Ajax methods for interaction with the web interface.
    """
    def __init__(self):
        self._biodb_name = "gae_testing"

    def genbank_upload(self, *args, **kwargs):
        handle = StringIO.StringIO(kwargs['upload_file'])
        biosql_db = BioSeqDatabase.open_database()
        try:
            biodb = biosql_db[self._biodb_name]
        except KeyError:
            biodb = biosql_db.new_database(self._biodb_name)
        biodb.load(SeqIO.parse(handle, "genbank"))
        return json.dumps(dict())

    def get_bioentries(self, start=0, limit=10):
        """Retreive bioentries associated with the database.
        """
        biosql_db = BioSeqDatabase.open_database()
        try:
            biodb = biosql_db[self._biodb_name]
        except KeyError:
            return []
        biodb = biodb.get_biodatabase()
        return biodb.bioentries[start:start+limit]
    
    def bioentry_details(self, bioentry_key):
        """Retrieve full details for a bioentry based on the internal key.

        This could also use accession numbers or unique identifiers here.
        """
        bioentry = db.get(db.Key(bioentry_key))
        qual_info = collections.defaultdict(list)
        for qual in bioentry.quals:
            qual_info[qual.term.name].append(qual.value)
        qualifiers = [(key, ", ".join(values)) for key, values in
                qual_info.items()]
        qualifiers.sort()
        seq_parts = [bioentry.seqs[0].seq[pos:pos+80] for pos
                in range(0, len(bioentry.seqs[0].seq), 80)]
        tmpl = Template(bioentry_details_template)
        return tmpl.render(qualifiers=qualifiers,
                sequence="<br/>".join(seq_parts))
        
bioentry_template = """
<h3><a href="${retrieve_url}">${accession} ${description}</a></h3>
<div>
</div>
"""

bioentry_details_template = """
<table id="hor-minimalist-a">
% for key, val in qualifiers:
    <tr><td><b>${key}</b></td><td>${val}</td></tr>
% endfor
</table>
<pre>
${sequence}
</pre>
"""


application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/rpc', RPCHandler)],
                                     debug=True)
def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
