# -*- coding: utf-8 -*-
"""
Created on Sun Feb 27 17:02:34 2022

@author: Danny
"""
import numpy as np

class Buffer():
    def __init__(self, num_first_options:int, num_rounds:int=40):
        self.option_bins = ['0-2','2-4','4-8','8-16','16-32']
        self.count_bins = ['0','1','2','3','4+']
        self.monkeys = ['dart',
            'boomerang', 'cannon', 'spike', 'frozen', 'glue', 'sniper'
            'sub',  'pirate', 'plane',  'heli', 'mortar', 'gatling',
            'magic',  'super',  'ninja',  'alchemist', 'druid',
            'banana', 'factory', 'village', 'engineer', 'none'
        ]
        
        #each state is the bin for each monkey name, and the number of options
        #(23 + 1) values. Each value has 5 possibilities. 24*5 = 120 possible states
        #if we wanted to include the round number, then 120*40 = 4800. Still kinda doable?
        
        self.state_ls = [] #list of dictionary of current states
        self.rewards = np.zeros(num_rounds) #list of all rewards
        self.acton_ls = [] #list of all actions, which monkey to place per round
        self.next_state_ls = [] #list of dictionary of next state
       
        self.raw_counts = {x:0 for x in self.monkeys}
        first_state = {x: self.count_bins[0] for x in self.monkeys}
        option_bin = int(np.round(num_first_options / 2))
        option_bin = min(option_bin, 4)
        first_state.upadate({'num_options':self.option_bins[option_bin]})
        self.state_ls.append(first_state)


    def add(self,action:str, reward:float, num_options:int):
        #update the raw counts with the selected monkey action
        self.raw_counts[action] += 1
        new_bin = min(self.raw_counts[action], 4)
        
        #how many options in the next state?
        option_bin = int(np.round(num_options / 2))
        option_bin = min(option_bin, 4)
        
        #update the reward and action
        self.rewards.append(reward)
        self.action_ls.append(action)
        
        #update the next state
        state = self.state_ls[-1].copy()
        state[action] = self.count_bins[new_bin]
        next_state = {x:state[x] for x in self.monkeys}
        next_state.update({'num_options':self.option_bins[option_bin]})
        self.next_state_ls.append(next_state)
        
        #change the curret state to the next state
        self.state_ls.append(next_state.copy())

        
        
        
        