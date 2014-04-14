# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import collections


class StatCollector(object):

    def __init__(self):

        self.conceptnet_total_found = 0
        self.conceptnet_total_missed = 0
        self.conceptner_arg_found = collections.Counter()
        self.conceptner_arg_missed = collections.Counter()

        self.total_reltype = 0
        self.total_reltype_handled = 0
        self.total_reltype_missed = 0
        self.total_args = 0
        self.total_args_missed = 0
        self.total_args_handled = 0

        self.reltype_stat = collections.Counter()
        self.reltype_handled_stat = collections.Counter()
        self.reltype_missed_stat = collections.Counter()

        self.arg_stat = collections.Counter()
        self.arg_handled_stat = collections.Counter()
        self.arg_missed_stat = collections.Counter()

    def update_conceptnet(self, concept_lemma, found):
        if found:
            self.conceptner_arg_found[concept_lemma] += 1
            self.conceptnet_total_found += 1
        else:
            self.conceptner_arg_missed[concept_lemma] += 1
            self.conceptnet_total_missed += 1

    def update_arg(self, arg, found):
        self.total_args += 1
        self.arg_stat[arg] += 1
        if found:
            self.total_args_handled += 1
            self.arg_handled_stat[arg] += 1
        else:
            self.total_args_missed += 1
            self.arg_missed_stat[arg] += 1

    def update_rel(self, reltype, found):
        self.total_reltype += 1
        self.reltype_stat[reltype] += 1
        if found:
            self.total_reltype_handled += 1
            self.reltype_handled_stat[reltype] += 1
        else:
            self.total_reltype_missed += 1
            self.reltype_missed_stat[reltype] += 1

    def save(self, to_filename):
        main_stat_fl = open("%s.stat.main.txt" % to_filename, "w")
        arg_stat_fl = open("%s.stat.arg.all.txt" % to_filename, "w")
        arg_missed_stat_fl = open("%s.stat.arg.missed.txt" % to_filename, "w")
        arg_handled_stat_fl = open("%s.stat.arg.handled.txt" % to_filename, "w")
        conceptnet_found_stat_fl = open("%s.stat.concept.found.txt" % to_filename, "w")
        conceptnet_missed_stat_fl = open("%s.stat.concept.missed.txt" % to_filename, "w")

        main_stat_fl.write("Total triples: %d\n" % self.total_reltype)
        main_stat_fl.write("Total triples handled: %d\n" % self.total_reltype_handled)
        main_stat_fl.write("Total triples missed: %d\n" % self.total_reltype_missed)
        main_stat_fl.write("Conceptnet improved args: %d\n" % self.conceptnet_total_found)
        main_stat_fl.write("Conceptnet not improved args: %d\n" % self.conceptnet_total_missed)

        main_stat_fl.write("\nTotal args: %d\n" % self.total_args)
        main_stat_fl.write("Total args handled: %d\n" % self.total_args_handled)
        main_stat_fl.write("Total args missed: %d\n" % self.total_args_missed)

        main_stat_fl.write("\nBy reltype (total):\n")
        for rel_type, freq in self.reltype_stat.most_common():
            main_stat_fl.write("%s:\t%d\n" % (rel_type, freq))

        main_stat_fl.write("\nBy reltype (handled):\n")
        for rel_type, freq in self.reltype_handled_stat.most_common():
            main_stat_fl.write("%s:\t%d\n" % (rel_type, freq))

        main_stat_fl.write("\nBy reltype (missed):\n")
        for rel_type, freq in self.reltype_missed_stat.most_common():
            main_stat_fl.write("%s:\t%d\n" % (rel_type, freq))

        main_stat_fl.write("\n")

        for arg, freq in self.arg_stat.most_common():
            arg_stat_fl.write(("%s\t%d\n" % (arg, freq)).encode("utf-8"))

        for arg, freq in self.arg_handled_stat.most_common():
            arg_handled_stat_fl.write(("%s\t%d\n" % (arg, freq)).encode("utf-8"))

        for arg, freq in self.arg_missed_stat.most_common():
            arg_missed_stat_fl.write(("%s\t%d\n" % (arg, freq)).encode("utf-8"))

        for arg, freq in self.conceptner_arg_found.most_common():
            conceptnet_found_stat_fl.write(("%s\t%d\n" % (arg, freq)).encode("utf-8"))

        for arg, freq in self.conceptner_arg_missed.most_common():
            conceptnet_missed_stat_fl.write(("%s\t%d\n" % (arg, freq)).encode("utf-8"))

        main_stat_fl.close()
        arg_stat_fl.close()
        arg_missed_stat_fl.close()
        arg_handled_stat_fl.close()
        conceptnet_found_stat_fl.close()
        conceptnet_missed_stat_fl.close()