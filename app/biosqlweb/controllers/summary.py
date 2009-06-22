"""Provide a controller to display a list summary view of loaded records.
"""
import os
import logging
import StringIO
import collections
import simplejson as json

from google.appengine.ext import db
from mako.template import Template
from pylons import request, config, response
from pylons.templating import render_mako as render
from biosqlweb.lib.base import BaseController

from Bio import SeqIO
from BioSQL.GAE import BioSeqDatabase

log = logging.getLogger(__name__)

class SummaryController(BaseController):
    """Simple list view of records loaded in the BioSQL database.
    """
    def index(self):
        biodb_name = config.get("biosql_biodb_name")
        return render("/summary.html",
                extra_vars=dict(records=self._get_records(biodb_name)))

    def _get_records(self, biodb_name):
        """Retrieve BioSQL records in the database.
        """
        bioentries = self._get_bioentries(biodb_name)
        records = []
        for bioentry in bioentries:
            b_tmpl = Template(bioentry_template)
            retrieve_url = "bioentry_details?bioentry_key=%s" % (
                    bioentry.key())
            records.append(b_tmpl.render(accession=bioentry.accession,
                description=bioentry.description, retrieve_url=retrieve_url))
        return records
    
    def _get_bioentries(self, biodb_name, start=0, limit=10):
        """Retreive bioentries associated with the database.
        """
        start = int(request.params.get('start', start))
        limit = int(request.params.get('limit', limit))
        biosql_db = BioSeqDatabase.open_database()
        try:
            biodb = biosql_db[biodb_name]
        except KeyError:
            return []
        biodb = biodb.get_biodatabase()
        return biodb.bioentries[start:start+limit]
   
    def genbank_upload(self, *args, **kwargs):
        # XXX hack for os.linesep not being present; where did it go?
        os.linesep = "\n"
        biodb_name = config.get("biosql_biodb_name")
        biosql_db = BioSeqDatabase.open_database()
        try:
            biodb = biosql_db[biodb_name]
        except KeyError:
            biodb = biosql_db.new_database(biodb_name)
        handle = request.params['upload_file'].file
        biodb.load(SeqIO.parse(handle, "genbank"))
        handle.close()
        response.headers['content-type'] = 'text/javascript'
        return json.dumps(dict())
    
    def bioentry_details(self):
        """Retrieve full details for a bioentry based on the internal key.

        This could also use accession numbers or unique identifiers here.
        """
        bioentry_key = request.params.get('bioentry_key', '')
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
