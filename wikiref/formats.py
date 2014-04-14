# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import logging
import StringIO as stringio


from hugin.pos import POS_NAMES
from hugin.relsearch import RELATION_NAMES


class Triplet(object):
    """
    Class representing semantic triplet (arguments + relation) with frequency.
    Despite the fact it is called "triplet", the number of arguments can be any.
    """

    def __init__(self, rel_type, args, freq):
        """
        @type rel_type: str \from *RELATION_NAMES*
        @param rel_type: Triplet relation type.

        @type args: [(str, str \from *POS_NAMES*)]
        @param args: Ordered list of tuples word-part_of_speech_tag.

        @type freq: int
        @param freq: Triplet corpus frequency.
        """

        if rel_type is None:
            self.frequency = -1
            self.rel_type = None
            self.arguments = None
            return

        if rel_type in RELATION_NAMES:
            self.rel_type = rel_type
        else:
            raise TypeError("Unknown relation type %r" % rel_type)

        self.arguments = []
        self.frequency = freq
        for arg in args:
            if arg is None:
                self.arguments.append(None)
            else:
                if arg[1] in POS_NAMES:
                    self.arguments.append(arg)
                else:
                    raise TypeError("Unknown part-of-speech tag: %r" % str(args))


    def __len__(self):
        return len(self.arguments)

    def __str__(self):
        string = stringio.StringIO()
        string.write("<")
        string.write(self.rel_type)
        string.write(" ")
        for term_pos in self.arguments:
            if term_pos is None:
                string.write("None")
            else:
                if len(term_pos) == 2:
                    string.write("%s-%s" % (term_pos[0], term_pos[1]))
                else:
                    string.write("%s-%s(%r)" % (term_pos[0], term_pos[1], term_pos[2]))
            string.write(" ")
        string.write(str(self.frequency))
        string.write(">")
        return string.getvalue()


class TripleStoreReader(object):

    CSV_TRIPLE_ARG_DELIMITER = ","
    CSV_TERM_POS_DELIMITER   = "-"

    CSV_EMPTY_TERM_1 = "<NONE>"
    CSV_EMPTY_TERM_2 = "None-<NONE-POS>"
    CSV_IGNORE_TERM = "<->"

    def __init__(self, csv_file_object,
                 csv_triple_arg_delimiter=None,
                 csv_term_pos_delimiter=None):
        self.csv_file_object = csv_file_object
        if csv_triple_arg_delimiter is None:
            self.csv_triple_arg_delimiter = self.CSV_TRIPLE_ARG_DELIMITER
        else:
            self.csv_triple_arg_delimiter = csv_triple_arg_delimiter
        if csv_term_pos_delimiter is None:
            self.csv_term_pos_delimiter = self.CSV_TERM_POS_DELIMITER
        else:
            self.csv_term_pos_delimiter = csv_term_pos_delimiter

    def map_csv_line(self, line):
        """
        Maps CSV lines into list of [(term, term_index_record, ...)]
        CSV should be formed like this:
        `<relation_name>, <term_1>-<pos_1>, ..., <term_k>-<pos_k>, <freq>`

        If term is unknown, use <NONE> marker. For example:
        `subj_verb, речь-NN, идти-VB, <->, <->, <->, 85846`
        `subj_verb, <NONE>, идти-VB, <->, <->, <->, 85846`
        """
        row = line.split(self.csv_triple_arg_delimiter)
        rel_name = row[0]
        frequency = int(row[-1])
        arguments = []
        for i in xrange(1, len(row) - 2):
            if row[i] == self.CSV_EMPTY_TERM_1 or row[i] == self.CSV_EMPTY_TERM_2:
                arguments.append(None)
            elif row[i] == self.CSV_IGNORE_TERM:
                continue
            else:
                term_and_pos = row[i].split(self.csv_term_pos_delimiter)
                pos_name = term_and_pos[-1]
                term = "".join(term_and_pos[0:(len(term_and_pos) - 1)])
                arguments.append((term, pos_name))

        triplet = Triplet(rel_name, arguments, frequency)
        return triplet

    def __iter__(self):
        for line in self.csv_file_object:
            try:
                triplet = self.map_csv_line(line)
            except Exception:
                continue
            yield triplet


class DisambiguatedTripletReader(TripleStoreReader):
    CSV_TERM_NODE_DELIMITER  = "="
    CSV_NODE_NODE_DELIMITER  = ";"
    CSV_NODE_SCORE_DELIMITER = "/"

    def __init__(self, csv_file_object,
                 csv_triple_arg_delimiter=None,
                 csv_term_pos_delimiter=None,
                 csv_term_node_delimiter=None,
                 csv_node_node_delimiter=None,
                 csv_node_score_delimiter=None):

        super(DisambiguatedTripletReader, self).__init__(csv_file_object,
                                                         csv_triple_arg_delimiter,
                                                         csv_term_pos_delimiter)

        if csv_term_node_delimiter is None:
            self.csv_term_node_delimiter = self.CSV_TERM_NODE_DELIMITER
        else:
            self.csv_term_node_delimiter = csv_term_node_delimiter

        if csv_node_node_delimiter is None:
            self.csv_node_node_delimiter = self.CSV_NODE_NODE_DELIMITER
        else:
            self.csv_node_node_delimiter = csv_node_node_delimiter

        if csv_node_score_delimiter is None:
            self.csv_node_score_delimiter = self.CSV_NODE_SCORE_DELIMITER
        else:
            self.csv_node_score_delimiter = csv_node_score_delimiter

    def map_csv_line(self, line):
        """
        """
        row = line.split(self.csv_triple_arg_delimiter)
        rel_name = row[0]
        frequency = int(row[-1])
        arguments = []

        for i in xrange(1, len(row) - 1):
            if row[i] == self.CSV_EMPTY_TERM_1 or row[i] == self.CSV_EMPTY_TERM_2:
                arguments.append(None)
            elif row[i] == self.CSV_IGNORE_TERM:
                continue
            else:
                term_and_pos = row[i].split(self.csv_term_pos_delimiter)
                pos_name = term_and_pos[-1]
                if pos_name.startswith("NN"):
                    pos, nodes = pos_name.split(self.csv_term_node_delimiter)

                    if len(nodes) > 0:
                        nodes = nodes.split(self.csv_node_node_delimiter)
                        w_nodes = []
                        for node_score in nodes:
                            node, score = node_score.split(self.csv_node_score_delimiter)
                            score = float(score)
                            w_nodes.append((node, score))
                        nodes = w_nodes
                    else:
                        nodes = []
                else:
                    nodes = []
                    pos = pos_name

                term = "".join(term_and_pos[0:(len(term_and_pos) - 1)])
                arguments.append((term, pos, nodes))
        triplet = Triplet(rel_name, arguments, frequency)
        return triplet

    def __iter__(self):
        for line_no, line in enumerate(self.csv_file_object):
            line = line.rstrip("\n")
            try:
                triplet = self.map_csv_line(line)
            except Exception:
                import traceback
                traceback.print_exc()
                logging.info((line_no, line))
                exit(0)
            yield triplet, line
