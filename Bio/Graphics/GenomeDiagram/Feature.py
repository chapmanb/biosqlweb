# Copyright 2003-2008 by Leighton Pritchard.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.
#
# Contact:       Leighton Pritchard, Scottish Crop Research Institute,
#                Invergowrie, Dundee, Scotland, DD2 5DA, UK
#                L.Pritchard@scri.ac.uk
################################################################################

""" Feature module

    Provides:

    o Feature - class to wrap Bio.SeqFeature objects with drawing information

    For drawing capabilities, this module uses reportlab to define colors:

    http://www.reportlab.com

    For dealing with biological information, the package uses BioPython:

    http://www.biopython.org
"""

# ReportLab imports
from reportlab.lib import colors

# GenomeDiagram imports
from Bio.Graphics.GenomeDiagram.Colors import ColorTranslator

import string

class Feature:
    """ Class to wrap Bio.SeqFeature objects for GenomeDiagram

        Provides:

        Methods:

        o __init__(self, parent=None, feature_id=None, feature=None,
                 color=colors.lightgreen) Called when the feature is
                 instantiated

        o set_feature(self, feature) Wrap the passed feature

        o get_feature(self) Return the unwrapped Bio.SeqFeature object

        o set_color(self, color) Set the color in which the feature will
                be drawn (accepts multiple formats: reportlab color.Color()
                tuple and color.name, or integer representing Artemis color

        o get_color(self) Returns color.Color tuple of the feature's color

        o __getattr__(self, name) Catches attribute requests and passes them to
                the wrapped Bio.SeqFeature object

        Attributes:

        o parent    FeatureSet, container for the object

        o id        Unique id

        o color    color.Color, color to draw the feature

        o hide      Boolean for whether the feature will be drawn or not

        o sigil     String denoting the type of sigil to use for the feature.
                    Currently either "BOX" or "ARROW" are supported.

        o arrowhead_length  Float denoting length of the arrow head to be drawn,
                            relative to the bounding box height.  The arrow shaft
                            takes up the remainder of the bounding box's length.

        o arrowshaft_height  Float denoting length of the representative arrow
                             shaft to be drawn, relative to the bounding box height.
                             The arrow head takes the full height of the bound box.
         
        o name_qualifiers   List of Strings, describes the qualifiers that may
                    contain feature names in the wrapped Bio.SeqFeature object

        o label     Boolean, 1 if the label should be shown

        o label_font    String describing the font to use for the feature label

        o label_size    Int describing the feature label font size

        o label_color  color.Color describing the feature label color

        o label_angle   Float describing the angle through which to rotate the
                    feature label in degrees (default = 45, linear only)

        o label_position    String, 'start', 'end' or 'middle' denoting where
                    to place the feature label (linear only)

        o locations     List of tuples of (start, end) ints describing where the
                    feature and any subfeatures start and end

        o type      String denoting the feature type

        o name      String denoting the feature name

        o strand    Int describing the strand on which the feature is found

    """
    def __init__(self, parent=None, feature_id=None, feature=None,
                 color=colors.lightgreen, label=0, colour=None):
        """ __init__(self, parent=None, feature_id=None, feature=None,
                 color=colors.lightgreen, label=0)

            o parent    FeatureSet containing the feature

            o feature_id    Unique id for the feature

            o feature   Bio.SeqFeature object to be wrapped

            o color    color.Color Color to draw the feature (overridden
                       by backwards compatible argument with UK spelling,
                       colour).  Either argument is overridden if 'color'
                       is found in feature qualifiers

            o label     Boolean, 1 if the label should be shown
        """
        #Let the UK spelling (colour) override the USA spelling (color)
        if colour is not None:
            color = colour

        self._colortranslator = ColorTranslator()
        
        # Initialise attributes
        self.parent = parent
        self.id = feature_id        
        self.color = color            # default color to draw the feature
        self._feature = None            # Bio.SeqFeature object to wrap
        self.hide = 0                   # show by default
        self.sigil = 'BOX'
        self.arrowhead_length = 1.0 # 100% of the box height
        self.arrowshaft_height = 0.4 # 40% of the box height
        self.name_qualifiers = ['gene', 'label', 'name', 'locus_tag', 'product']
        self.label = label
        self.label_font = 'Helvetica'
        self.label_size = 6
        self.label_color = colors.black
        self.label_angle = 45
        self.label_position = 'start'
        
        if feature is not None:
            self.set_feature(feature)

    def set_feature(self, feature):
        """ set_feature(self, feature)

            o feature   Bio.SeqFeature object to be wrapped

            Defines the Bio.SeqFeature object to be wrapped
        """
        self._feature = feature
        self.__process_feature()


    def __process_feature(self):
        """ __process_feature(self)

            Examine the feature to be wrapped, and set some of the Feature's
            properties accordingly
        """
        self.locations = []
        bounds = []
        if self._feature.sub_features == []:
            if '^' in str(self._feature.location._start):
                self.hide = 1       # The GenBank parser doesn't behave properly, so don't show the feature
                #print self._feature.location, dir(self._feature.location)
                start, end = str(self._feature.location._start).split('^')
            else:
                start = str(self._feature.location._start)  # Feature start
                end = str(self._feature.location._end)      # Feature end
            while start[0] not in string.digits:        # Remove extraneous leading chars
                #print start
                start = start[1:]
            while end[0] not in string.digits:
                #print end
                end = end[1:]
            while end[-1] not in string.digits:
                #print end
                end = end[:-1]
            start, end = int(start), int(end)
            #if start > end and self.strand == -1:
            #    start, end = end, start
            self.locations.append((start, end))
            bounds += [start, end]
        else:
            for subfeature in self._feature.sub_features:
                if '^' in str(subfeature.location._start):                    
                    self.hide = 1
                    start, end = str(subfeature.location._start).split('^')
                else:
                    start = str(subfeature.location._start)  # Feature start
                    end = str(subfeature.location._end)      # Feature end
                while start[0] not in string.digits:        # Remove extraneous leading chars
                    #print start
                    start = start[1:]
                while end[0] not in string.digits:
                    #print end
                    end = end[1:]
                try:
                    start, end = int(start), int(end)
                except:
                    #print start, end
                    sys.exit(1)
                #if start > end and self.strand == -1:
                #    start, end = end, start
                self.locations.append((start, end))                
                bounds += [start, end]
        self.type = str(self._feature.type)                     # Feature type
        if self._feature.strand is None :
            #This is the SeqFeature default (None), but the drawing code
            #only expects 0, +1 or -1.
            self.strand = 0
        else :
            self.strand = int(self._feature.strand)                 # Feature strand
        if 'color' in self._feature.qualifiers:                # Artemis color (if present)
            # Artemis color used to be only a single integer, but as of
            # Oct '04 appears to be dot-delimited.  This is a quick fix to
            # allow dot-delimited strings, but only use the first integer
            artemis_color = self._feature.qualifiers['color'][0] # Local copy of string
            if artemis_color.count('.'):                          # dot-delimited
                artemis_color = artemis_color.split('.')[0]      # Use only first integer
            else:                                     # Assume just an integer
                artemis_color = artemis_color       # Use integer
            self.color = self._colortranslator.artemis_color(artemis_color)
        self.name = self.type
        for qualifier in self.name_qualifiers:            
            if qualifier in self._feature.qualifiers:
                self.name = self._feature.qualifiers[qualifier][0]
                break
        self.start, self.end = min(bounds), max(bounds)


    def get_feature(self):
        """ get_feature(self) -> Bio.SeqFeature

            Returns the unwrapped Bio.SeqFeature object
        """
        return self._feature

    def set_colour(self, colour):
        """Backwards compatible variant of set_color(self, color) using UK spelling."""
        color = self._colortranslator.translate(colour)
        self.color = color

    def set_color(self, color):
        """ set_color(self, color)

            o color    The color to draw the feature - either a colors.Color
                       object, an RGB tuple of floats, or an integer
                       corresponding to colors in colors.txt
                           
            Set the color in which the feature will be drawn
        """
        #TODO - Make this into the set method for a color property?
        color = self._colortranslator.translate(color)
        self.color = color

    def __getattr__(self, name):
        """ __getattr__(self, name) -> various

            If the Feature class doesn't have the attribute called for,
            check in self._feature for it
        """
        return getattr(self._feature, name) # try to get the attribute from the feature


    
################################################################################
# RUN AS SCRIPT
################################################################################

if __name__ == '__main__':

    # Test code
    gdf = Feature()
