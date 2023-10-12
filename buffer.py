# -*- coding: utf-8 -*-
"""
Created on Sun Feb 27 17:02:34 2022

@author: Danny
"""
import numpy as np
import pandas as pd

class Buffer():
    def __init__(self, num_first_options:int, num_rounds:int=40):
#        self.option_bins = ['0-16','16-32']
#        self.count_bins = ['0-2','3+']
        self.monkeys = ['dart',
            'boomerang', 'cannon', 'spike', 'frozen', 'glue', 'sniper',
            'plane', 'mortar', 'gatling',
            'magic',  'super',  'ninja',  'alchemist', 'druid',
            'factory', 'engineer', 'none',
        ]

        self.monkeys += ['upgrade_' + c for c in self.monkeys if c != 'none']
        # each state is the bin for each monkey name, and the number of options
        # (23 + 1) values. Each value has 5 possibilities. 5^24 = a bad idea
        # so at least exclude the option bins
        # also removed the village and farm, reducing from 8M to 2M combinations
        # but then multiply by number of actions and we're up to 40M
        # so the only possibily for quick results is just use the round number as the state
        # next step up is maybe logistic regression
        
        self.reset()

    def add(self, action:str, reward:float, is_done:int, loc_action:int):
        # update the raw counts with the selected monkey action
        # self.raw_counts[action] += 1
        # new_bin = 0 if self.raw_counts[action] < 3 else 1
        
        # how many options in the next state?
        # option_bin = int(np.round(num_options / 2))
        # option_bin = min(option_bin, 4)
        
        # update the reward and action
        self.rewards.append(reward)
        self.action_ls.append(action)
        self.loc_action_ls.append(loc_action)
        # update the next state
        # state = self.state_ls[-1].copy()
        # state[action] = self.count_bins[new_bin]
        # next_state = {x:state[x] for x in self.monkeys}
        # next_state.update({'num_options':self.option_bins[option_bin]})
        # self.next_state_ls.append(next_state)
        self.done_ls.append(is_done)
        
        # change the current state to the next state
        # self.state_ls.append(next_state.copy())

    def save(self, filepath):
        pd.to_pickle(self, filepath)

    def reset(self):
        # self.state_ls = [] # list of dictionary of current states
        self.rewards = []  # list of all rewards
        self.action_ls = []  # list of all actions, which monkey to place per round
        self.loc_action_ls = []  # list of all actions for selection the location of the monkey
        # self.next_state_ls = []  # list of dictionary of next state
        self.done_ls = []

        # self.raw_counts = {x:0 for x in self.monkeys}
        # first_state = {x: self.count_bins[0] for x in self.monkeys}
        # option_bin = int(np.round(num_first_options / 2))
        # option_bin = min(option_bin, 4)
        # first_state.update({'num_options':self.option_bins[option_bin]})
        # self.state_ls.append(first_state)
        # self.iter = 0