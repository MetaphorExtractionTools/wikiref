# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

# coding: utf-8

import sys
import logging
import collections
import itertools
try:
    import numpy as np
except ImportError:
    import numpypy as np


from wikiref.semadata import SemanticNodeSet

CLASS_SCORE_AWARD = 0.1

class MinClassDisambigSolver(object):
    EMPTY_SET = SemanticNodeSet([], [])
    PERSON_NODE = [("<wordnet_person_100007846>", 1.0)]

    def __init__(self,
                 class_dict,
                 class_search,
                 taxonomy,
                 types,
                 names=set()):
        self.class_dict = class_dict
        self.class_search = class_search
        self.taxonomy = taxonomy
        self.types = types
        self.names = names

    def bin_sets(self, node_sets, debug=False):
        sets = []
        for i, ns in enumerate(node_sets):

            sets.append((
                i,
                ns.lemmas,
                set(ns.wclasses()),
                set(ns.generalize(self.types, self.taxonomy, levels=1).wclasses()),
            ))
        if debug:
            for i, lemmas, classes, inst_classes in sets:
                sys.stderr.write("\t\t\t bin(%d) %s\n" % (i, " ".join(lemmas)))
                for cl in classes:
                    sys.stderr.write("\t\t\t\t c %s\n" % cl)
                for cl in inst_classes:
                    sys.stderr.write("\t\t\t\t i %s\n" % cl)
        return sets

    @staticmethod
    def sort_sets(binned_node_sets, debug=False):
        sorted_sets = []

        for class_bin_index, lemmas, classes, self_instance_classes in binned_node_sets:
            bin_weighted_nodes = dict()
            all_classes = self_instance_classes | classes
            for cl in all_classes:

                if cl not in bin_weighted_nodes:
                    if cl in classes:
                        bin_weighted_nodes[cl] = [1.0 / len(classes) + CLASS_SCORE_AWARD, []]
                    if cl in self_instance_classes:
                        bin_weighted_nodes[cl] = [1.0 / len(self_instance_classes), []]

                for instance_bin_index, instance_lemmas, _, instance_classes in binned_node_sets:
                    if class_bin_index != instance_bin_index and cl in instance_classes:

                        bin_weighted_nodes[cl][0] += 1
                        bin_weighted_nodes[cl][1].append(" ".join(instance_lemmas))

            # if debug:
            #     print "W", bin_weighted_nodes
            #     exit()
            sorted_sets.append((class_bin_index, lemmas, bin_weighted_nodes))

        if debug:
            sys.stderr.write("\t\t----------\n")
            for class_bin_index, lemmas, bin_weighted_nodes in sorted_sets:
                sys.stderr.write("\t\t\t sorted_bin(%d) %s\n" % (class_bin_index, " ".join(lemmas)))
                for cl, (cl_weight, cl_lemmas) in bin_weighted_nodes.iteritems():
                    cl_lemmas = ";".join(cl_lemmas)
                    sys.stderr.write("\t\t\t\t c %.3f %s in  %s\n" % (cl_weight, cl, cl_lemmas))

        sorted_nodes = collections.Counter()
        for _, _, bin_weighted_nodes in sorted_sets:
            for cl, (cl_weight, _) in bin_weighted_nodes.iteritems():
                sorted_nodes[cl] += cl_weight

        return sorted_nodes

    def transitive(self, w_class):
        if w_class is None:
            return []
        last_parent = w_class
        path = []
        while True:
            parent = self.taxonomy[last_parent]
            if parent is None:
                return path
            path.append(parent)
            last_parent = parent
            # print last_parent
        return path

    def apply_lca(self, node_set, depth=1, debug=False):
        """

        """

        # If node set has classes, return.
        if node_set.class_count() > 0:
            return node_set
        else:
            # Otherwise get list of classes for instances from @depth levels.
            all_classes = node_set.generalize(self.types, self.taxonomy, levels=depth).nodes

        if debug:
            sys.stderr.write("\t\tinstance_classes={%s}\n" % ", ".join(all_classes))

        # For each class, get list of all its parenrs (transitive).
        classes_with_parents = []
        for cl in all_classes:
            trans = self.transitive(cl)
            classes_with_parents.append((cl, trans))
            # print cl, "=>", len(trans), trans


        # Create taxonomy tree and count total numbers of leaves for each node.
        tree = dict()
        for cl in all_classes:
            tree[cl] = [cl, dict(), 1]
        for cl, parents in classes_with_parents:
            child = cl
            for p in parents:
                child_node = tree[child]
                if p not in tree:
                    children = {child: child_node[2]}
                    total_children = child_node[2]
                    tree[p] = [p, children, total_children]
                else:
                    children = tree[p][1]
                    total_children = tree[p][2]
                    if child in children:
                        # print children[child], "=>", child_node[2]
                        total_children -= children[child]
                        total_children += child_node[2]
                        children[child] = child_node[2]
                    else:
                        total_children += child_node[2]
                        children[child] = child_node[2]
                    tree[p][2] = total_children
                child = p

        if len(tree) <= 1:
            return SemanticNodeSet(lemmas=[], nodes=[])

        # Sort all nodes by total number of leaves.
        sorted_tree = sorted(tree.itervalues(), key=lambda node: -node[2])

        if debug:
            sys.stderr.write("\t\t\tsorted_node_subtree[%s]:" % ", ".join(node_set.lemmas))
            for node in sorted_tree:
                sys.stderr.write("\t\t\t\tnode=%s (%d)" % (node[0], node[2]))

        # Cross fingers and return nodes, selected by Ziph magic rule.
        total = len(sorted_tree)
        bottom_thr = int(len(sorted_tree) / 5.0)
        if bottom_thr == 0:
            bottom_thr = 1
        top_thr = int(len(sorted_tree) / 5.0 * 2) + 1
        nodes = [node[0] for node in sorted_tree[bottom_thr:top_thr]]
        return SemanticNodeSet(lemmas=node_set.lemmas, nodes=nodes)

    def disambiguate(self, lemmas, depth=1, return_size=1, debug=False, try_lca=False):

        if len(lemmas) == 0:
            return []

        best_set = None
        best_len = np.inf

        # Initially, use all lemmas to find best node set.
        active_lemmas = set(lemmas)

        # Try all possible combination of lemmas starting from the longest (the less ambiguate).
        #if try_lca:
        comb_sizes = range(len(lemmas), 0, -1)
        #else:
        #    comb_sizes = [1]

        # Store found results in this list.
        found_node_sets = []

        for comb_size in comb_sizes:

            # Checking all combibations of lemmas starting from the longest.
            combinations = itertools.combinations(active_lemmas, comb_size)


            for lemm_combination in combinations:

                if debug:
                    sys.stderr.write("\tchecking: (%d) [%s] \n" % (comb_size, ",".join(lemm_combination)))

                # If number of lemmas in combination is more than one, just do partial search.
                if comb_size > 1:

                    # try all to concatinate all permutations
                    # else use search

                    for permutation in itertools.permutations(lemm_combination):
                        perm_str = " ".join(permutation)
                        node_set = self.class_dict.get(perm_str, self.EMPTY_SET)
                        if not node_set.isempty(self.types):
                            break

                    if node_set.isempty(self.types):
                        node_set = self.class_search.search(lemm_combination, self.EMPTY_SET)

                # Othewise, first try to find exact lemma = label match.
                else:

                    # Exact search.
                    term = lemm_combination[0]
                    node_set = self.class_dict.get(term, self.EMPTY_SET)

                    # If result is empty, try to do partial search.
                    if node_set.isempty(self.types) and try_lca:
                        node_set = self.class_search.search(lemm_combination, self.EMPTY_SET)

                        # Use (L)east (C)ommon (A)ncestor to find better instance nodes.
                        node_set = self.apply_lca(node_set, debug)

                # If we found something, removed used lemmas from list of lemmas for next combination.
                if not node_set.isempty(self.types):
                    if debug:
                        sys.stderr.write("\t\tfound_nodeset=%r\n" % node_set)
                    found_node_sets.append(node_set)
                    for lemma in lemm_combination:
                        try:
                            active_lemmas.remove(lemma)
                        except: pass
                elif debug:
                    sys.stderr.write("\t\tfound_nodeset=EMPTY\n")

        if len(found_node_sets) == 1 \
           and len(found_node_sets[0].lemmas) == 1 \
           and found_node_sets[0].lemmas[0] in self.names:
            return self.PERSON_NODE

        if len(found_node_sets) == 0:
            for lemma in lemmas:
                if lemma in self.names:
                    return self.PERSON_NODE

        binned_sets = self.bin_sets(found_node_sets, debug=debug)
        sorted_nodes = self.sort_sets(binned_sets, debug=debug)
        total_score = sum(sorted_nodes.itervalues())

        for k in sorted_nodes.iterkeys():
            sorted_nodes[k] /= total_score

        if len(sorted_nodes) > 0:

            max_score = max(sorted_nodes.itervalues())
            selected_nodes = list(filter(lambda node_score: node_score[1] == max_score, sorted_nodes.iteritems()))

            # if debug:
            #     print selected_nodes

            return selected_nodes
        else:
            return []