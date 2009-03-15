# Copyright 2000 by Jeffrey Chang.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

"""
This module provides code to work with the prosite.doc file from
Prosite.
http://www.expasy.ch/prosite/

Tested with:
Release 15.0, July 1998
Release 16.0, July 1999
Release 20.22, 13 November 2007


Functions:
parse              Iterates over entries in a Prodoc file.
index_file         Index a Prodoc file for a Dictionary.
_extract_record    Extract Prodoc data from a web page.


Classes:
Record             Holds Prodoc data.
Reference          Holds data from a Prodoc reference.
Dictionary         Accesses a Prodoc file using a dictionary interface.
RecordParser       Parses a Prodoc record into a Record object.

_Scanner           Scans Prodoc-formatted data.
_RecordConsumer    Consumes Prodoc data to a Record object.
Iterator           Iterates over entries in a Prodoc file; DEPRECATED.
"""

from types import *
import os
import sgmllib
from Bio import File
from Bio import Index
from Bio.ParserSupport import *

def parse(handle):
    import cStringIO
    parser = RecordParser()
    text = ""
    for line in handle:
        text += line
        if line[:5] == '{END}':
            handle = cStringIO.StringIO(text)
            record = parser.parse(handle)
            text = ""
            yield record

def read(handle):
    parser = RecordParser()
    record = parser.parse(handle)
    # We should have reached the end of the record by now
    remainder = handle.read()
    if remainder:
        raise ValueError("More than one Prodoc record found")
    return record


# It may be a good idea to rewrite read(), parse() at some point to avoid
# using the old-style "parser = RecordParser(); parser.parse(handle)" approach.

class Record:
    """Holds information from a Prodoc record.

    Members:
    accession      Accession number of the record.
    prosite_refs   List of tuples (prosite accession, prosite name).
    text           Free format text.
    references     List of reference objects.

    """
    def __init__(self):
        self.accession = ''
        self.prosite_refs = []
        self.text = ''
        self.references = []

class Reference:
    """Holds information from a Prodoc citation.

    Members:
    number     Number of the reference. (string)
    authors    Names of the authors.
    citation   Describes the citation.

    """
    def __init__(self):
        self.number = ''
        self.authors = ''
        self.citation = ''

class Iterator:
    """Returns one record at a time from a Prodoc file.

    Methods:
    next   Return the next record from the stream, or None.

    """
    def __init__(self, handle, parser=None):
        """__init__(self, handle, parser=None)

        Create a new iterator.  handle is a file-like object.  parser
        is an optional Parser object to change the results into another form.
        If set to None, then the raw contents of the file will be returned.

        """
        import warnings
        warnings.warn("Bio.Prosite.Prodoc.Iterator is deprecated; we recommend using the function Bio.Prosite.Prodoc.parse instead. Please contact the Biopython developers at biopython-dev@biopython.org you cannot use Bio.Prosite.Prodoc.parse instead of Bio.Prosite.Prodoc.Iterator.",
              DeprecationWarning)
        if type(handle) is not FileType and type(handle) is not InstanceType:
            raise ValueError("I expected a file handle or file-like object")
        self._uhandle = File.UndoHandle(handle)
        self._parser = parser

    def next(self):
        """next(self) -> object

        Return the next Prodoc record from the file.  If no more records,
        return None.

        """
        lines = []
        while 1:
            line = self._uhandle.readline()
            if not line:
                break
            lines.append(line)
            if line[:5] == '{END}':
                break
            
        if not lines:
            return None
            
        data = "".join(lines)
        if self._parser is not None:
            return self._parser.parse(File.StringHandle(data))
        return data

    def __iter__(self):
        return iter(self.next, None)

class Dictionary:
    """Accesses a Prodoc file using a dictionary interface.

    """
    __filename_key = '__filename'
    
    def __init__(self, indexname, parser=None):
        """__init__(self, indexname, parser=None)

        Open a Prodoc Dictionary.  indexname is the name of the
        index for the dictionary.  The index should have been created
        using the index_file function.  parser is an optional Parser
        object to change the results into another form.  If set to None,
        then the raw contents of the file will be returned.

        """
        self._index = Index.Index(indexname)
        self._handle = open(self._index[Dictionary.__filename_key])
        self._parser = parser

    def __len__(self):
        return len(self._index)

    def __getitem__(self, key):
        start, len = self._index[key]
        self._handle.seek(start)
        data = self._handle.read(len)
        if self._parser is not None:
            return self._parser.parse(File.StringHandle(data))
        return data

    def __getattr__(self, name):
        return getattr(self._index, name)

class ExPASyDictionary:
    """Access PRODOC at ExPASy using a read-only dictionary interface.

    """
    def __init__(self, delay=5.0, parser=None):
        """__init__(self, delay=5.0, parser=None)

        Create a new Dictionary to access PRODOC.  parser is an optional
        parser (e.g. Prodoc.RecordParser) object to change the results
        into another form.  If set to None, then the raw contents of the
        file will be returned.  delay is the number of seconds to wait
        between each query.

        """
        import warnings
        warnings.warn("Bio.Prosite.Prodoc.ExPASyDictionary is deprecated. Please use the function Bio.ExPASy.get_prosite_raw instead.",
              DeprecationWarning)

        self.delay = delay
        self.parser = parser
        self.last_query_time = None

    def __len__(self):
        raise NotImplementedError("Prodoc contains lots of entries")
    def clear(self):
        raise NotImplementedError("This is a read-only dictionary")
    def __setitem__(self, key, item):
        raise NotImplementedError("This is a read-only dictionary")
    def update(self):
        raise NotImplementedError("This is a read-only dictionary")
    def copy(self):
        raise NotImplementedError("You don't need to do this...")
    def keys(self):
        raise NotImplementedError("You don't really want to do this...")
    def items(self):
        raise NotImplementedError("You don't really want to do this...")
    def values(self):
        raise NotImplementedError("You don't really want to do this...")
    
    def has_key(self, id):
        """has_key(self, id) -> bool"""
        try:
            self[id]
        except KeyError:
            return 0
        return 1

    def get(self, id, failobj=None):
        try:
            return self[id]
        except KeyError:
            return failobj

    def __getitem__(self, id):
        """__getitem__(self, id) -> object

        Return a Prodoc entry.  id is either the id or accession
        for the entry.  Raises a KeyError if there's an error.
        
        """
        import time
        from Bio import ExPASy
        # First, check to see if enough time has passed since my
        # last query.
        if self.last_query_time is not None:
            delay = self.last_query_time + self.delay - time.time()
            if delay > 0.0:
                time.sleep(delay)
        self.last_query_time = time.time()

        try:
            handle = ExPASy.get_prodoc_entry(id)
        except IOError:
            raise KeyError(id)
        try:
            handle = File.StringHandle(_extract_record(handle))
        except ValueError:
            raise KeyError(id)
        
        if self.parser is not None:
            return self.parser.parse(handle)
        return handle.read()

class RecordParser(AbstractParser):
    """Parses Prodoc data into a Record object.

    """
    def __init__(self):
        self._scanner = _Scanner()
        self._consumer = _RecordConsumer()

    def parse(self, handle):
        self._scanner.feed(handle, self._consumer)
        return self._consumer.data

class _Scanner:
    """Scans Prodoc-formatted data.

    Tested with:
    Release 15.0, July 1998
    
    """
    def feed(self, handle, consumer):
        """feed(self, handle, consumer)

        Feed in Prodoc data for scanning.  handle is a file-like
        object that contains prosite data.  consumer is a
        Consumer object that will receive events as the report is scanned.

        """
        if isinstance(handle, File.UndoHandle):
            uhandle = handle
        else:
            uhandle = File.UndoHandle(handle)

        while 1:
            line = uhandle.peekline()
            if not line:
                break
            elif is_blank_line(line):
                # Skip blank lines between records
                uhandle.readline()
                continue
            else:
                self._scan_record(uhandle, consumer)
            
    def _scan_record(self, uhandle, consumer):
        consumer.start_record()

        self._scan_accession(uhandle, consumer)
        self._scan_prosite_refs(uhandle, consumer)
        read_and_call(uhandle, consumer.noevent, start='{BEGIN}')
        self._scan_text(uhandle, consumer)
        self._scan_refs(uhandle, consumer)
        self._scan_copyright(uhandle, consumer)
        read_and_call(uhandle, consumer.noevent, start='{END}')

        consumer.end_record()

    def _scan_accession(self, uhandle, consumer):
        read_and_call(uhandle, consumer.accession, start='{PDOC')

    def _scan_prosite_refs(self, uhandle, consumer):
        while attempt_read_and_call(uhandle, consumer.prosite_reference,
                                    start='{PS'):
            pass

    def _scan_text(self, uhandle, consumer):
        while 1:
            line = safe_readline(uhandle)
            if (line[0] == '[' and line[3] == ']' and line[4] == ' ') or \
               line[:5] == '{END}':
                uhandle.saveline(line)
                break
            consumer.text(line)

    def _scan_refs(self, uhandle, consumer):
        while 1:
            line = safe_readline(uhandle)
            if line[:5] == '{END}' or is_blank_line(line):
                uhandle.saveline(line)
                break
            consumer.reference(line)

    def _scan_copyright(self, uhandle, consumer):
        # Cayte Lindner found some PRODOC records with the copyrights
        # appended at the end.  We'll try and recognize these.
        read_and_call_while(uhandle, consumer.noevent, blank=1)
        if attempt_read_and_call(uhandle, consumer.noevent, start='+----'):
            read_and_call_until(uhandle, consumer.noevent, start='+----')
            read_and_call(uhandle, consumer.noevent, start='+----')
        read_and_call_while(uhandle, consumer.noevent, blank=1)

class _RecordConsumer(AbstractConsumer):
    """Consumer that converts a Prodoc record to a Record object.

    Members:
    data    Record with Prodoc data.

    """
    def __init__(self):
        self.data = None
        
    def start_record(self):
        self.data = Record()
        
    def end_record(self):
        self._clean_data()

    def accession(self, line):
        line = line.rstrip()
        if line[0] != '{' or line[-1] != '}':
            raise ValueError("I don't understand accession line\n%s" % line)
        acc = line[1:-1]
        if acc[:4] != 'PDOC':
            raise ValueError("Invalid accession in line\n%s" % line)
        self.data.accession = acc

    def prosite_reference(self, line):
        line = line.rstrip()
        if line[0] != '{' or line[-1] != '}':
            raise ValueError("I don't understand accession line\n%s" % line)
        acc, name = line[1:-1].split('; ')
        self.data.prosite_refs.append((acc, name))
    
    def text(self, line):
        self.data.text = self.data.text + line
    
    def reference(self, line):
        if line[0] == '[' and line[3] == ']':  # new reference
            self._ref = Reference()
            self._ref.number = line[1:3].strip()
            if line[1] == 'E':
                # If it's an electronic reference, then the URL is on the
                # line, instead of the author.
                self._ref.citation = line[4:].strip()
            else:
                self._ref.authors = line[4:].strip()
            self.data.references.append(self._ref)
        elif line[:4] == '    ':
            if not self._ref:
                raise ValueError("Unnumbered reference lines\n%s" % line)
            self._ref.citation = self._ref.citation + line[5:]
        else:
            raise Exception("I don't understand the reference line\n%s" % line)

    def _clean_data(self):
        # get rid of trailing newlines
        for ref in self.data.references:
            ref.citation = ref.citation.rstrip()
            ref.authors = ref.authors.rstrip()
    
def index_file(filename, indexname, rec2key=None):
    """index_file(filename, indexname, rec2key=None)

    Index a Prodoc file.  filename is the name of the file.
    indexname is the name of the dictionary.  rec2key is an
    optional callback that takes a Record and generates a unique key
    (e.g. the accession number) for the record.  If not specified,
    the id name will be used.

    """
    import os
    if not os.path.exists(filename):
        raise ValueError("%s does not exist" % filename)

    index = Index.Index(indexname, truncate=1)
    index[Dictionary._Dictionary__filename_key] = filename

    handle = open(filename)
    records = parse(handle)
    end = 0L
    for record in records:
        start = end
        end = long(handle.tell())
        length = end - start

        if rec2key is not None:
            key = rec2key(record)
        else:
            key = record.accession
            
        if not key:
            raise KeyError("empty key was produced")
        elif key in index:
            raise KeyError("duplicate key %s found" % key)

        index[key] = start, length

# This function can be deprecated once Bio.Prosite.Prodoc.ExPASyDictionary
# is removed.
def _extract_record(handle):
    """_extract_record(handle) -> str

    Extract PRODOC data from a web page.  Raises a ValueError if no
    data was found in the web page.

    """
    # All the data appears between tags:
    # <pre width = 80>ID   NIR_SIR; PATTERN.
    # </PRE>
    class parser(sgmllib.SGMLParser):
        def __init__(self):
            sgmllib.SGMLParser.__init__(self)
            self._in_pre = 0
            self.data = []
        def handle_data(self, data):
            if self._in_pre:
                self.data.append(data)
        def do_br(self, attrs):
            if self._in_pre:
                self.data.append('\n')
        def start_pre(self, attrs):
            self._in_pre = 1
        def end_pre(self):
            self._in_pre = 0
    p = parser()
    p.feed(handle.read())
    data = ''.join(p.data).lstrip()
    if not data:
        raise ValueError("No data found in web page.")
    return data
