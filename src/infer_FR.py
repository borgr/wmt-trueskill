#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division

"""
Implement's Martin Popel's FairRank.
"""

__author__ = "Martin Popel"
__version__ = "0.1"
__usage__ = "cat JUDGEMENTS.csv | python infer_FR.py OUTPUTID(e.g. cs-en-FairRank)"

import sys
import os
import json
import random
import argparse

from scripts import wmt

from csv import DictReader
from collections import defaultdict
from itertools import combinations

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('prefix', help='file prefix (e.g., fr-en0)')
arg_parser.add_argument('-p', dest='dp_pct', type=float, default=1.0,
        help='Percentage of judgements to use (1.0)')
arg_parser.add_argument('-n', dest='replacement', action='store_false', default=True,
        help='Just use all datapoints instead of bootstrap resampling')
args = arg_parser.parse_args()

def compute_fair_rank():
    ### Pairwise result
    win_dict = defaultdict(int)
    tie_dict = defaultdict(int)

    data_points = 0
    all_systems = {}
    if args.replacement:
        dataset = [pw for pw in wmt.parse_csv(sys.stdin)]

        print >> sys.stderr, "Bootstrap resampling %d of %d samples" % (args.dp_pct * len(dataset), len(dataset))
        for i in range(int(args.dp_pct * len(dataset))):
            s1, s2, obs = random.choice(dataset)
            all_systems[s1] = 1
            all_systems[s2] = 1
            if obs == '<':
                data_points += 1
                win_dict[(s1, s2)] += 1
            elif obs == '>':
                win_dict[(s2, s1)] += 1
                data_points += 1
            elif obs == '=':
                tie_dict[(s1,s2)] += 1
                tie_dict[(s2,s1)] += 1

    else:
        for s1, s2, obs in wmt.parse_csv(sys.stdin):
            all_systems[s1] = 1
            all_systems[s2] = 1
            if random.random() < args.dp_pct:
                if obs == '<':
                    data_points += 1
                    win_dict[(s1, s2)] += 1
                elif obs == '>':
                    win_dict[(s2, s1)] += 1
                    data_points += 1
                elif obs == '=':
                    tie_dict[(s1,s2)] += 1
                    tie_dict[(s2,s1)] += 1
                        
    final_rank = {}
    for sys_i in all_systems.keys():
        fr_score = 0
        sum_prob_nonties = 0
        for sys_j in all_systems.keys():
            if sys_i != sys_j:
                wins    = win_dict[(sys_i, sys_j)]
                ties    = tie_dict[(sys_i, sys_j)]
                nonties = wins + win_dict[(sys_j, sys_i)]
                if nonties != 0:
                    direct  = wins / nonties
                    prob_nontie       = nonties / (nonties + ties)
                    sum_prob_nonties += prob_nontie
                    fr_score         += prob_nontie * direct
        final_rank[sys_i] = [fr_score/sum_prob_nonties, 0.001] # 0.001 is a dummy variance
        final_rank['data_points'] = [data_points, args.dp_pct]
    f = open(args.prefix + '_mu_sigma.json', 'w')
    json.dump(final_rank, f)
    f.close()

if __name__ == '__main__':
    compute_fair_rank()

