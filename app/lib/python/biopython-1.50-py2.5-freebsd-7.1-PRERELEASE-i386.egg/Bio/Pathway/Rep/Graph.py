# Copyright 2002 by Tarjei Mikkelsen.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

# get set abstraction for graph representation
from Bio.Pathway.Rep.HashSet import *

class Graph:
    """A directed graph abstraction with labeled edges."""

    def __init__(self, nodes = []):
        """Initializes a new Graph object."""
        self.__adjacency_list = {}    # maps parent -> set of child objects
        for n in nodes:
            self.__adjacency_list[n] = HashSet()
        self.__label_map = {}         # maps label -> set of (parent, child) pairs
        self.__edge_map = {}          # maps (parent, child) pair -> label

    def __eq__(self, g):
        """Returns true if g is equal to this graph."""
        return isinstance(g, Graph) and \
               (self.__adjacency_list == g.__adjacency_list) and \
               (self.__label_map == g.__label_map) and \
               (self.__edge_map == g.__edge_map)

    def __ne__(self, g):
        """Returns true if g is not equal to this graph."""
        return not self.__eq__(g)

    def __repr__(self):
        """Returns an unique string representation of this graph."""
        s = "<Graph: "
        keys = self.__adjacency_list.keys()
        keys.sort()
        for key in keys:
            values = [(x,self.__edge_map[(key,x)]) \
                      for x in self.__adjacency_list[key].list()]
            values.sort()
            s = s + "(" + repr(key) + ": " + ",".join(map(repr, values)) + ")" 
        return s + ">"

    def __str__(self):
        """Returns a concise string description of this graph."""
        nodenum = len(self.__adjacency_list.keys())
        edgenum = reduce(lambda x,y: x+y,
                         map(len, self.__adjacency_list.values()))
        labelnum = len(self.__label_map.keys())
        return "<Graph: " + \
               str(nodenum) + " node(s), " + \
               str(edgenum) + " edge(s), " + \
               str(labelnum) + " unique label(s)>"

    def add_node(self, node):
        """Adds a node to this graph."""
        if node not in self.__adjacency_list:
            self.__adjacency_list[node] = HashSet()

    def add_edge(self, source, to, label = None):
        """Adds an edge to this graph."""
        if source not in self.__adjacency_list:
            raise ValueError("Unknown <from> node: " + str(source))
        if to not in self.__adjacency_list:
            raise ValueError("Unknown <to> node: " + str(to))
        if (source,to) in self.__edge_map:
            raise ValueError(str(source) + " -> " + str(to) + " exists")
        self.__adjacency_list[source].add(to)
        if label not in self.__label_map:
            self.__label_map[label] = HashSet()
        self.__label_map[label].add((source,to))
        self.__edge_map[(source,to)] = label

    def child_edges(self, parent):
        """Returns a list of (child, label) pairs for parent."""
        if parent not in self.__adjacency_list:
            raise ValueError("Unknown <parent> node: " + str(parent))
        return [(x, self.__edge_map[(parent,x)]) \
                for x in self.__adjacency_list[parent].list()]

    def children(self, parent):
        """Returns a list of unique children for parent."""
        return self.__adjacency_list[parent].list()

    def edges(self, label):
        """Returns a list of all the edges with this label."""
        if label not in self.__label_map:
            raise ValueError("Unknown label: " + str(label))
        return self.__label_map[label].list()

    def labels(self):
        """Returns a list of all the edge labels in this graph."""
        return self.__label_map.keys()

    def nodes(self):
        """Returns a list of the nodes in this graph."""
        return self.__adjacency_list.keys()

    def parent_edges(self, child):
        """Returns a list of (parent, label) pairs for child."""
        if child not in self.__adjacency_list:
            raise ValueError("Unknown <child> node: " + str(child))
        parents = []
        for parent in self.__adjacency_list.keys():
            children = self.__adjacency_list[parent]
            for x in children.list():
                if x is child:
                    parents.append((parent, self.__edge_map[(parent, child)]))
        return parents

    def parents(self, child):
        """Returns a list of unique parents for child."""
        s = HashSet([x[0] for x in self.parent_edges(child)])
        return s.list()

    def remove_node(self, node):
        """Removes node and all edges connected to it."""
        if node not in self.__adjacency_list:
            raise ValueError("Unknown node: " + str(node))
        # remove node (and all out-edges) from adjacency list
        del self.__adjacency_list[node]
        # remove all in-edges from adjacency list
        for n in self.__adjacency_list.keys():
            self.__adjacency_list[n] = HashSet(filter(lambda x,node=node: x is not node,
                                                      self.__adjacency_list[n].list()))
        # remove all refering pairs in label map
        for label in self.__label_map.keys():
            lm = HashSet(filter(lambda x,node=node: \
                                (x[0] is not node) and (x[1] is not node),
                                self.__label_map[label].list()))
            # remove the entry completely if the label is now unused
            if lm.empty():
                del self.__label_map[label]
            else:
                self.__label_map[label] = lm
        # remove all refering entries in edge map
        for edge in self.__edge_map.keys():
            if edge[0] is node or edge[1] is node:
                del self.__edge_map[edge]
        
    def remove_edge(self, parent, child, label):
        """Removes edge. -- NOT IMPLEMENTED"""
        # hm , this is a multigraph - how should this be implemented?
        raise NotImplementedError("remove_edge is not yet implemented")



