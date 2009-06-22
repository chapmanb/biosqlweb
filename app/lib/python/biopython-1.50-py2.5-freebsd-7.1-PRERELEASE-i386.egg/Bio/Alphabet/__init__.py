# Copyright 2000-2002 by Andrew Dalke.
# Revisions copyright 2007-2008 by Peter Cock.
# All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

"""Alphabets used in Seq objects etc to declare sequence type and letters.

This is used by sequences which contain a finite number of similar words.
"""

class Alphabet:
    size = None     # no fixed size for words
    letters = None  # no fixed alphabet; implement as a list-like
                    # interface,
    def __repr__(self):
        return self.__class__.__name__ + "()"

    def contains(self, other):
        """Does this alphabet 'contain' the other (OBSOLETE?).

        Returns a boolean.  This relies on the Alphabet subclassing
        hierarchy only, and does not check the letters property.
        This isn't ideal, and doesn't seem to work as intended
        with the AlphabetEncoder classes."""
        return isinstance(other, self.__class__)

generic_alphabet = Alphabet()

class SingleLetterAlphabet(Alphabet):
    size = 1
    letters = None   # string of all letters in the alphabet

single_letter_alphabet = SingleLetterAlphabet()

########### Protein

class ProteinAlphabet(SingleLetterAlphabet):
    pass

generic_protein = ProteinAlphabet()

########### DNA
class NucleotideAlphabet(SingleLetterAlphabet):
    pass

generic_nucleotide = NucleotideAlphabet()

class DNAAlphabet(NucleotideAlphabet):
    pass

generic_dna = DNAAlphabet()


########### RNA

class RNAAlphabet(NucleotideAlphabet):
    pass

generic_rna = RNAAlphabet()



########### Other per-sequence encodings

class SecondaryStructure(SingleLetterAlphabet):
    letters = "HSTC"

class ThreeLetterProtein(Alphabet):
    size = 3
    letters = [
        "Ala", "Asx", "Cys", "Asp", "Glu", "Phe", "Gly", "His", "Ile",
        "Lys", "Leu", "Met", "Asn", "Pro", "Gln", "Arg", "Ser", "Thr",
        "Sec", "Val", "Trp", "Xaa", "Tyr", "Glx",
        ]
        
###### Non per-sequence modifications

# (These are Decorator classes)

class AlphabetEncoder:
    def __init__(self, alphabet, new_letters):
        self.alphabet = alphabet
        self.new_letters = new_letters
        if alphabet.letters is not None:
            self.letters = alphabet.letters + new_letters
        else:
            self.letters = None
    def __getattr__(self, key):
        if key[:2] == "__" and key[-2:] == "__":
            raise AttributeError(key)
        return getattr(self.alphabet, key)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.alphabet,
                               self.new_letters)

    def contains(self, other):
        """Does this alphabet 'contain' the other (OBSOLETE?).

        This is isn't implemented for the base AlphabetEncoder,
        which will always return 0 (False)."""
        return 0
    
class Gapped(AlphabetEncoder):
    def __init__(self, alphabet, gap_char = "-"):
        AlphabetEncoder.__init__(self, alphabet, gap_char)
        self.gap_char = gap_char

    def contains(self, other):
        """Does this alphabet 'contain' the other (OBSOLETE?).

        Returns a boolean.  This relies on the Alphabet subclassing
        hierarchy, and attempts to check the gap character.  This fails
        if the other alphabet does not have a gap character!
        """
        return other.gap_char == self.gap_char and \
               self.alphabet.contains(other.alphabet)
               
class HasStopCodon(AlphabetEncoder):
    def __init__(self, alphabet, stop_symbol = "*"):
        AlphabetEncoder.__init__(self, alphabet, stop_symbol)
        self.stop_symbol = stop_symbol
        
    def __cmp__(self, other):
        x = cmp(self.alphabet, other.alphabet)
        if x == 0:
            return cmp(self.stop_symbol, other.stop_symbol)
        return x

    def contains(self, other):
        """Does this alphabet 'contain' the other (OBSOLETE?).

        Returns a boolean.  This relies on the Alphabet subclassing
        hierarchy, and attempts to check the stop symbol.  This fails
        if the other alphabet does not have a stop symbol!
        """
        return other.stop_symbol == self.stop_symbol and \
               self.alphabet.contains(other.alphabet)

def _get_base_alphabet(alphabet) :
    """Returns the non-gapped non-stop-codon Alphabet object (PRIVATE)."""
    a = alphabet
    while isinstance(a, AlphabetEncoder) :
        a = a.alphabet
    assert isinstance(a, Alphabet), \
           "Invalid alphabet found, %s" % repr(a)
    return a
    
def _consensus_base_alphabet(alphabets) :
    """Returns a common but often generic base alphabet object (PRIVATE).

    This throws away any AlphabetEncoder information, e.g. Gapped alphabets.

    Note that DNA+RNA -> Nucleotide, and Nucleotide+Protein-> generic single
    letter.  These DO NOT raise an exception!"""
    common = None
    for alpha in alphabets :
        a = _get_base_alphabet(alpha)
        if common is None :
            common = a
        elif common == a :
            pass
        elif isinstance(a, common.__class__) :
            pass
        elif isinstance(common, a.__class__) :
            common = a
        elif isinstance(a, NucleotideAlphabet) \
        and isinstance(common, NucleotideAlphabet) :
            #e.g. Give a mix of RNA and DNA alphabets
            common = generic_nucleotide
        elif isinstance(a, SingleLetterAlphabet) \
        and isinstance(common, SingleLetterAlphabet) :
            #This is a pretty big mis-match!
            common = single_letter_alphabet
        else :
            #We have a major mis-match... take the easy way out!
            return generic_alphabet
    if common is None :
        #Given NO alphabets!
        return generic_alphabet
    return common

def _consensus_alphabet(alphabets) :
    """Returns a common but often generic alphabet object (PRIVATE).

    Note that DNA+RNA -> Nucleotide, and Nucleotide+Protein-> generic single
    letter.  These DO NOT raise an exception!
    
    This is aware of Gapped and HasStopCodon and new letters added by
    other AlphabetEncoders.  This WILL raise an exception if more than
    one gap character or stop symbol is present."""
    base = _consensus_base_alphabet(alphabets)
    gap = None
    stop = None
    new_letters = ""
    for alpha in alphabets :
        #Gaps...
        if not hasattr(alpha, "gap_char") :
            pass
        elif gap is None :
            gap = alpha.gap_char
        elif gap == alpha.gap_char :
            pass
        else :
            raise ValueError("More than one gap character present")
        #Stops...
        if not hasattr(alpha, "stop_symbol") :
            pass
        elif stop is None :
            stop = alpha.stop_symbol
        elif stop == alpha.stop_symbol :
            pass
        else :
            raise ValueError("More than one stop symbol present")
        #New letters...
        if hasattr(alpha, "new_letters") :
            for letter in alpha.new_letters :
                if letter not in new_letters \
                and letter != gap and letter != stop :
                    new_letters += letter

    alpha = base
    if new_letters :
        alpha = AlphabetEncoder(alpha, new_letters)
    if gap :
        alpha = Gapped(alpha, gap_char=gap)
    if stop :
        alpha = HasStopCodon(alpha, stop_symbol=stop)
    return alpha

def _check_type_compatible(alphabets) :
    """Returns True except for DNA+RNA or Nucleotide+Protein (PRIVATE).

    This relies on the Alphabet subclassing hierarchy.  It does not
    check things like gap characters or stop symbols."""
    dna, rna, nucl, protein = False, False, False, False
    for alpha in alphabets :
        a = _get_base_alphabet(alpha)
        if isinstance(a, DNAAlphabet) :
            dna = True
            nucl = True
            if rna or protein : return False
        elif isinstance(a, RNAAlphabet) :
            rna = True
            nucl = True
            if dna or protein : return False
        elif isinstance(a, NucleotideAlphabet) :
            nucl = True
            if protein : return False
        elif isinstance(a, ProteinAlphabet) :
            protein = True
            if nucl : return False
    return True
