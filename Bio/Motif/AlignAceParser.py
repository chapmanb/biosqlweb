# Copyright 2003 by Bartek Wilczynski.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.
"""
Classes for pparsing AlignAce and CompareACE files
"""
#changed string.atof to float, for compatibility with python 2.6 and 3k, BW

from Bio.ParserSupport import *
from Motif import Motif
from Bio.Alphabet import IUPAC
from Bio.Seq import Seq


class AlignAceConsumer:
    """
    The general purpose consumer for the AlignAceScanner.

    Should be passed as the consumer to the feed method of the AlignAceScanner. After 'consuming' the file, it has the list of motifs in the motifs property.
    """
    def __init__(self):
        self.motifs=[]
        self.current_motif=None
        self.param_dict = None
    
    def parameters(self,line):
        self.param_dict={}

    def parameter(self,line):
        par_name = line.split("=")[0].strip()
        par_value = line.split("=")[1].strip()
        self.param_dict[par_name]=par_value
        
    def sequences(self,line):
        self.seq_dict=[]
        
    def sequence(self,line):
        seq_name = line.split("\t")[1]
        self.seq_dict.append(seq_name)
        
    def motif(self,line):
        self.current_motif = Motif()
        self.motifs.append(self.current_motif)
        self.current_motif.alphabet=IUPAC.unambiguous_dna
        
    def motif_hit(self,line):
        seq = Seq(line.split("\t")[0],IUPAC.unambiguous_dna)
        self.current_motif.add_instance(seq)
        
    def motif_score(self,line):
        self.current_motif.score = float(line.split()[-1])
        
    def motif_mask(self,line):
        self.current_motif.set_mask(line.strip("\n\c"))

    def noevent(self,line):
        pass
        
    def version(self,line):
        self.ver = line
        
    def command_line(self,line):
        self.cmd_line = line
    
class AlignAceParser(AbstractParser):
    """Parses AlignAce data into a sequence of Motifs.
    """
    def __init__(self):
        """__init__(self)"""
        self._scanner = AlignAceScanner()
        self._consumer = AlignAceConsumer()

    def parse(self, handle):
        """parse(self, handle)"""
        self._scanner.feed(handle, self._consumer)
        return self._consumer

class AlignAceScanner:
    """Scannner for AlignACE output

    Methods:
    feed     Feed data into the scanner.

    The scanner generates (and calls the consumer) the following types of events:

    noevent - blank line

    version - AlignACE version number
    command_line - AlignACE command line string
    parameters - the begining of the parameters
    parameter - the line containing a parameter
    sequences - the begining of the sequences list
    sequence - line containing the name of the input sequence (and a respective number)
    motif - the begining of the motif (contains the number)
    motif_hit - one hit for a motif
    motif_mask - mask of the motif (space - gap, asterisk - significant position)
    motif_score - MAP score of the motif - approx. N * log R, where R == (num. of actual occur.) / (num. of occur. expected by random.)
    
    """
    def feed(self, handle, consumer):
        """S.feed(handle, consumer)

        Feed in a AlignACE report for scanning.  handle is a file-like
        object that contains the AlignACE report.  consumer is a Consumer
        object that will receive events as the report is scanned.
        """
        consumer.version(handle.readline())
        consumer.command_line(handle.readline())
        for line in handle:
            if line.strip() == "":
                consumer.noevent(line)
            elif line[:4]=="Para":
                consumer.parameters(line)
            elif line[0]=="#":
                consumer.sequence(line)
            elif "=" in line:
                consumer.parameter(line)
            elif line[:5]=="Input":
                consumer.sequences(line)
            elif line[:5]=="Motif":
                consumer.motif(line)
            elif line[:3]=="MAP":
                consumer.motif_score(line)
            elif len(line.split("\t"))==4:
                consumer.motif_hit(line)
            elif "*" in line:
                consumer.motif_mask(line)
            else:
                raise ValueError(line)

class CompareAceScanner:
    """Scannner for CompareACE output

    Methods:
    feed     Feed data into the scanner.

    The scanner generates (and calls the consumer) the following types of events:

    motif_score - CompareACE score of motifs

    ###### TO DO #############3
    extend the scanner to include other, more complex outputs.
    """
    def feed(self, handle, consumer):
        """S.feed(handle, consumer)

        Feed in a CompareACE report for scanning.  handle is a file-like
        object that contains the CompareACE report.  consumer is a Consumer
        object that will receive events as the report is scanned.
        """
        consumer.motif_score(handle.readline())


class CompareAceConsumer:
    """
    The general purpose consumer for the CompareAceScanner.

    Should be passed as the consumer to the feed method of the CompareAceScanner. After 'consuming' the file, it has the list of motifs in the motifs property.
    """
    def __init__(self):
        pass
    def motif_score(self,line):
        self.data = float(line.split()[-1])
    
class CompareAceParser(AbstractParser):
    """Parses CompareAce output to usable form

    ### so far only in a very limited way
    """
    def __init__(self):
        """__init__(self)"""
        self._scanner = CompareAceScanner()
        self._consumer = CompareAceConsumer()

    def parse(self, handle):
        """parse(self, handle)"""
        self._scanner.feed(handle, self._consumer)
        return self._consumer.data
