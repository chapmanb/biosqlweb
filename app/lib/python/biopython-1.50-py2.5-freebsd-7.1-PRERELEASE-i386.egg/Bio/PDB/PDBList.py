#!/usr/bin/env python
#
# PDBList.py
#
# A tool for tracking changes in the PDB Protein Structure Database.
#
# Version 2.0
#
# (c) 2003 Kristian Rother
# This work was supported by the German Ministry of Education
# and Research (BMBF). Project http://www.bcbio.de
# 
# Contact the author
#    homepage : http://www.rubor.de/bioinf
#    email    : krother@genesilico.pl
#
#
# This Code is released under the conditions of the Biopython license.
# It may be distributed freely with respect to the original author.
# Any maintainer of the BioPython code may change this notice
# when appropriate.
#
# Last modified on Fri, Oct 24th 2006, Warszawa
#
# Removed 'write' options from retrieve_pdb_file method: it is not used.
# Also added a 'dir' options (pdb file is put in this directory if given),
# and an 'exist' option (test if the file is already there). This method
# now returns the name of the downloaded uncompressed file.
#
# -Thomas, 1/06/04
#
#
# Including bugfixes from Sunjoong Lee (9/2006)
#

__doc__="Access the PDB over the internet (for example to download structures)."

import urllib, re, os, sys

class PDBList:
    """
    This class provides quick access to the structure lists on the
    PDB server or its mirrors. The structure lists contain
    four-letter PDB codes, indicating that structures are
    new, have been modified or are obsolete. The lists are released
    on a weekly basis.

    It also provides a function to retrieve PDB files from the server.
    To use it properly, prepare a directory /pdb or the like,
    where PDB files are stored.

    If You want to use this module from inside a proxy, add
    the proxy variable to Your environment, e.g. in Unix
    export HTTP_PROXY='http://realproxy.charite.de:888'    
    (This can also be added to ~/.bashrc)
    """
    
    PDB_REF="""
    The Protein Data Bank: a computer-based archival file for macromolecular structures.
    F.C.Bernstein, T.F.Koetzle, G.J.B.Williams, E.F.Meyer Jr, M.D.Brice, J.R.Rodgers, O.Kennard, T.Shimanouchi, M.Tasumi
    J. Mol. Biol. 112 pp. 535-542 (1977)
    http://www.pdb.org/.
    """

    alternative_download_url = "http://www.rcsb.org/pdb/files/"
    # just append PDB code to this, and then it works.
    # (above URL verified with a XXXX.pdb appended on 2 Sept 2008)
    
    def __init__(self,server='ftp://ftp.wwpdb.org', pdb=os.getcwd(), obsolete_pdb=None):
        """Initialize the class with the default server or a custom one."""
        # remote pdb server
        self.pdb_server = server

        # local pdb file tree
        self.local_pdb = pdb

        # local file tree for obsolete pdb files
        if obsolete_pdb:
            self.obsolete_pdb = obsolete_pdb
        else:
            self.obsolete_pdb = self.local_pdb + os.sep + 'obsolete'
            if not os.access(self.obsolete_pdb,os.F_OK):
                os.makedirs(self.obsolete_pdb)

        # variables for command-line options
        self.overwrite = 0
        self.flat_tree = 0


    def get_status_list(self,url):
        """Retrieves a list of pdb codes in the weekly pdb status file
        from the given URL. Used by get_recent_files.
        
        Typical contents of the list files parsed by this method;
-rw-r--r--   1 rcsb     rcsb      330156 Oct 14  2003 pdb1cyq.ent
-rw-r--r--   1 rcsb     rcsb      333639 Oct 14  2003 pdb1cz0.ent
        """
        url = urllib.urlopen(url)
        file = url.readlines()
        list = []

        # added by S. Lee
        list = map(lambda x: x[3:7], \
                   filter(lambda x: x[-4:] == '.ent', \
                          map(lambda x: x.split()[-1], file)))
        return list


    def get_recent_changes(self):
        """Returns three lists of the newest weekly files (added,mod,obsolete).
        
        Reads the directories with changed entries from the PDB server and
        returns a tuple of three URL's to the files of new, modified and
        obsolete entries from the most recent list. The directory with the
        largest numerical name is used.
        Returns None if something goes wrong.
        
        Contents of the data/status dir (20031013 would be used);
drwxrwxr-x   2 1002     sysadmin     512 Oct  6 18:28 20031006
drwxrwxr-x   2 1002     sysadmin     512 Oct 14 02:14 20031013
-rw-r--r--   1 1002     sysadmin    1327 Mar 12  2001 README


        """     
        url = urllib.urlopen(self.pdb_server+'/pub/pdb/data/status/')
        file = url.readlines()

        try:
            # added by S.Lee
            recent = filter(lambda x: x.isdigit(), \
                            map(lambda x: x.split()[-1], file))[-1]
            
            path = self.pdb_server+'/pub/pdb/data/status/%s/'%(recent)
            # retrieve the lists
            added = self.get_status_list(path+'added.pdb')
            modified = self.get_status_list(path+'modified.pdb')
            obsolete = self.get_status_list(path+'obsolete.pdb')
            return [added,modified,obsolete]
        except:
            return None



    def get_all_entries(self):
        """Retrieves a big file containing all the 
        PDB entries and some annotation to them. 
        Returns a list of PDB codes in the index file.
        """
        entries = []
        print "retrieving index file. Takes about 5 MB."
        url = urllib.urlopen(self.pdb_server+'/pub/pdb/derived_data/index/entries.idx')
        # extract four-letter-codes
        entries = map(lambda x: x[:4], \
                      filter(lambda x: len(x)>4, url.readlines()[2:]))
                      
        return entries



    def get_all_obsolete(self):
        """Returns a list of all obsolete entries ever in the PDB.

        Returns a list of all obsolete pdb codes that have ever been
        in the PDB.
        
        Gets and parses the file from the PDB server in the format
        (the first pdb_code column is the one used).
 LIST OF OBSOLETE COORDINATE ENTRIES AND SUCCESSORS
OBSLTE     30-SEP-03 1Q1D      1QZR
OBSLTE     26-SEP-03 1DYV      1UN2    
        """
        url = urllib.urlopen(self.pdb_server+'/pub/pdb/data/status/obsolete.dat')
        # extract pdb codes
        obsolete = map(lambda x: x[21:25].lower(),
                       filter(lambda x: x[:6] == 'OBSLTE', url.readlines()))

        return obsolete



    def retrieve_pdb_file(self,pdb_code, obsolete=0, compression='.gz', 
            uncompress="gunzip", pdir=None):
        """Retrieves a PDB structure file from the PDB server and
        stores it in a local file tree.
        The PDB structure is returned as a single string.
        If obsolete is 1, the file will be by default saved in a special file tree.
        The compression should be '.Z' or '.gz'. 'uncompress' is
        the command called to uncompress the files.

        @param pdir: put the file in this directory (default: create a PDB-style directory tree) 
        @type pdir: string

        @return: filename
        @rtype: string
        """
        # get the structure
        code=pdb_code.lower()
        filename="pdb%s.ent%s"%(code,compression)
        if not obsolete:
            url=(self.pdb_server+
                 '/pub/pdb/data/structures/divided/pdb/%s/pdb%s.ent%s'
                 % (code[1:3],code,compression))
        else:
            url=(self.pdb_server+
                 '/pub/pdb/data/structures/obsolete/pdb/%s/pdb%s.ent%s'
                 % (code[1:3],code,compression))
            
        # in which dir to put the pdb file?
        if pdir is None:
            if self.flat_tree:
                if not obsolete:
                    path=self.local_pdb
                else:
                    path=self.obsolete_pdb
            else:
                # Put in PDB style directory tree
                if not obsolete:
                    path=self.local_pdb+os.sep+code[1:3]
                else:
                    path=self.obsolete_pdb+os.sep+code[1:3]
        else:
            # Put in specified directory
            path=pdir
            
        if not os.access(path,os.F_OK):
            os.makedirs(path)
            
        filename=path+os.sep+filename
        # the final uncompressed file
        final_file=path+os.sep+"pdb%s.ent" % code

        # check whether the file exists
        if not self.overwrite:
            if os.path.exists(final_file):
                print "file exists, not retrieved",final_file
                return final_file

        # Retrieve the file
        print 'retrieving',url                    
        lines=urllib.urlopen(url).read()
        open(filename,'wb').write(lines)
        # uncompress the file
        os.system("%s %s" % (uncompress, filename))

        return final_file

            

    def update_pdb(self):
        """
        I guess this is the 'most wanted' function from this module.
        It gets the weekly lists of new and modified pdb entries and
        automatically downloads the according PDB files.
        You can call this module as a weekly cronjob.
        """
        changes  = self.get_recent_changes()
        new      = changes[0]
        modified = changes[1]
        obsolete = changes[2]

        for pdb_code in new+modified:
            try:
                print 'retrieving %s'%(pdb_code)            
                self.retrieve_pdb_file(pdb_code)
            except:
                print 'error %s'%(pdb_code)
                # you can insert here some more log notes that
                # something has gone wrong.            

        # move the obsolete files to a special folder
        for pdb_code in obsolete:
            if self.flat_tree:
                old_file = self.local_pdb + os.sep + 'pdb%s.ent'%(pdb_code)
                new_file = self.obsolete_pdb + os.sep + 'pdb%s.ent'%(pdb_code)
            else:
                old_file = self.local_pdb + os.sep + pdb_code[1:3] + os.sep + 'pdb%s.ent'%(pdb_code)
                new_file = self.obsolete_pdb + os.sep + pdb_code[1:3] + os.sep + 'pdb%s.ent'%(pdb_code)
        os.cmd('mv %s %s'%(old_file,new_file))


    def download_entire_pdb(self,listfile=None):
        """Retrieves all PDB entries not present in the local PDB copy.
        Writes a list file containing all PDB codes (optional, if listfile is given).
        """ 
        entries = self.get_all_entries()
        for pdb_code in entries: self.retrieve_pdb_file(pdb_code)

        # write the list
        if listfile:
            open(listfile,'w').writelines(map(lambda x: x+'\n',entries))


    def download_obsolete_entries(self,listfile=None):

        """Retrieves all obsolete PDB entries not present in the local obsolete PDB copy.
        Writes a list file containing all PDB codes (optional, if listfile is given).
        """ 
        entries = self.get_all_obsolete()
        for pdb_code in entries: self.retrieve_pdb_file(pdb_code,obsolete=1)

        # write the list
        if listfile:
            open(listfile,'w').writelines(map(lambda x: x+'\n',entries))            



    #
    # this is actually easter egg code not used by any of the methods
    # maybe someone will find it useful.
    #    
    def get_seqres_file(self,savefile='pdb_seqres.txt'):
        """Retrieves a (big) file containing all the sequences 
        of PDB entries and writes it to a file."""
        print "retrieving sequence file. Takes about 15 MB."
        url = urllib.urlopen(self.pdb_server+'/pub/pdb/derived_data/pdb_seqres.txt')        
        file = url.readlines()
        open(savefile,'w').writelines(file)
        


if __name__ == '__main__':
    doc = """PDBList.py
    (c) Kristian Rother 2003, Contributed to BioPython

    Usage:
    PDBList.py update <pdb_path> [options]   - write weekly PDB updates to
                                               local pdb tree.
    PDBList.py all    <pdb_path> [options]   - write all PDB entries to
                                               local pdb tree.
    PDBList.py obsol  <pdb_path> [options]   - write all obsolete PDB
                                               entries to local pdb tree.
    PDBList.py <PDB-ID> <pdb_path> [options] - retrieve single structure

    Options:
       -d   A single directory will be used as <pdb_path>, not a tree.
       -o   Overwrite existing structure files.
    """
    print doc

    if len(sys.argv)>2:
        pdb_path = sys.argv[2]
        pl = PDBList(pdb=pdb_path)
        if len(sys.argv)>3:
            for option in sys.argv[3:]:
                if option == '-d': pl.flat_tree = 1
                elif option == '-o': pl.overwrite = 1

    else:
        pdb_path = os.getcwd()
        pl = PDBList()
        pl.flat_tree = 1        

    if len(sys.argv) > 1:   
        if sys.argv[1] == 'update':
            # update PDB
            print "updating local PDB at "+pdb_path 
            pl.update_pdb()

        elif sys.argv[1] == 'all':
            # get the entire PDB
            pl.download_entire_pdb()

        elif sys.argv[1] == 'obsol':
            # get all obsolete entries
            pl.download_obsolete_entries(pdb_path)

        elif re.search('^\d...$',sys.argv[1]):
            # get single PDB entry
            pl.retrieve_pdb_file(sys.argv[1],pdir=pdb_path)
        

        

