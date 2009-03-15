# Copyright 2000 by Andrew Dalke.
# All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

"""Miscellaneous functions for dealing with sequences (obsolete?)."""

import Seq
import Alphabet

from PropertyManager import default_manager

def translate(seq, id = None):
    """Translate a sequence (DEPRECATED)."""
    import warnings
    warnings.warn("Bio.utils.translate() has been deprecated, and we" \
                  +" intend to remove it in a future release of Biopython."\
                  +" Please use the translate method or function in Bio.Seq"\
                  +" instead, as described in the Tutorial.",
                  DeprecationWarning)
    if id is None:
        s = "translator"
    else:
        s = "translator.id.%d" % id
    translator = default_manager.resolve(seq.alphabet, s)
    return translator.translate(seq)

def translate_to_stop(seq, id = None):
    """Translate a sequence up to the first in frame stop codon (DEPRECATED)."""
    import warnings
    warnings.warn("Bio.utils.translate_to_stop() has been deprecated, and we" \
                  +" intend to remove it in a future release of Biopython."\
                  +" Please use the translate method or function in Bio.Seq"\
                  +" instead, as described in the Tutorial.",
                  DeprecationWarning)
    if id is None:
        s = "translator"
    else:
        s = "translator.id.%d" % id
    translator = default_manager.resolve(seq.alphabet, s)
    return translator.translate_to_stop(seq)

def back_translate(seq, id = None):
    """Back-translate a sequence (DEPRECATED)."""
    import warnings
    warnings.warn("Bio.utils.back_translate() has been deprecated, and we" \
                  +" intend to remove it in a future release of Biopython."\
                  +" If you use it, please tell us on the mailing list.",
                  DeprecationWarning)
    if id is None:
        s = "translator"
    else:
        s = "translator.id.%d" % id
    translator = default_manager.resolve(seq.alphabet, s)
    return translator.back_translate(seq)


def transcribe(seq):
    """Transcribe a sequence (DEPRECATED)."""
    import warnings
    warnings.warn("Bio.utils.transcribe() has been deprecated, and we" \
                  +" intend to remove it in a future release of Biopython."\
                  +" Please use the transcribe method or function in"\
                  +" Bio.Seq instead, as described in the Tutorial.",
                  DeprecationWarning)
    transcriber = default_manager.resolve(seq.alphabet, "transcriber")
    return transcriber.transcribe(seq)

def back_transcribe(seq):
    """Back-transcribe a sequence (DEPRECATED)."""
    import warnings
    warnings.warn("Bio.utils.back_transcribe() has been deprecated, and we" \
                  +" intend to remove it in a future release of Biopython."\
                  +" Please use the back_transcribe method or function in"\
                  +" Bio.Seq instead, as described in the Tutorial.",
                  DeprecationWarning)
    transcriber = default_manager.resolve(seq.alphabet, "transcriber")
    return transcriber.back_transcribe(seq)

def ungap(seq):
    """given a sequence with gap encoding, return the ungapped sequence"""
    #TODO - Fix this?  It currently assumes the outmost AlphabetEncoder
    #is for the gap.  Consider HasStopCodon(Gapped(Protein())) as a test case.
    gap = seq.gap_char
    letters = []
    for c in seq.data:
        if c != gap:
            letters.append(c)
    return Seq.Seq("".join(letters), seq.alphabet.alphabet)

def verify_alphabet(seq):
    letters = {}
    for c in seq.alphabet.letters:
        letters[c] = 1
    try:
        for c in seq.data:
            letters[c]
    except KeyError:
        return 0
    return 1

def count_monomers(seq):
    dict = {}
#    bugfix: string.count(s,c) raises an AttributeError. Iddo Friedberg 16 Mar. 04
#    s = buffer(seq.data)  # works for strings and array.arrays
    for c in seq.alphabet.letters:
        dict[c] = seq.data.count(c)
    return dict

def percent_monomers(seq):
    dict2 = {}
    seq_len = len(seq)
    dict = count_monomers(seq)
    for m in dict:
        dict2[m] = dict[m] * 100. / seq_len
    return dict2

def sum(seq, table, zero = 0.0):
    total = zero
    for c in getattr(seq, "data", seq):
        total = total + table[c]
    return total

# For ranged addition
def sum_2ple(seq, table, zero = (0.0, 0.0)):
    x, y = zero
    data = getattr(seq, "data", seq)
    for c in data:
        x2, y2 = table[c]
        x = x + x2
        y = y + y2
    return (x, y)

def total_weight(seq, weight_table = None):
    if weight_table is None:
        weight_table = default_manager.resolve(seq.alphabet, "weight_table")
    return sum(seq, weight_table)

def total_weight_range(seq, weight_table = None):
    if weight_table is None:
        weight_table = default_manager.resolve(seq.alphabet, "weight_range_table")
    return sum_2ple(seq, weight_table)

def reduce_sequence(seq, reduction_table,new_alphabet=None):
   """ given an amino-acid sequence, return it in reduced alphabet form based
       on the letter-translation table passed. Some "standard" tables are in
       Alphabet.Reduced.
       seq: a Seq.Seq type sequence
       reduction_table: a dictionary whose keys are the "from" alphabet, and values
       are the "to" alphabet"""
   if new_alphabet is None:
      new_alphabet = Alphabet.single_letter_alphabet
      new_alphabet.letters = ''
      for letter in reduction_table:
         new_alphabet.letters += letter
      new_alphabet.size = len(new_alphabet.letters)
   new_seq = Seq.Seq('',new_alphabet)
   for letter in seq:
      new_seq += reduction_table[letter]
   return new_seq


