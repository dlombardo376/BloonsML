# -*- coding: utf-8 -*-
"""
Created on Fri May 20 22:08:20 2022

@author: Danny
"""

import pandas as pd
import numpy as np


class LocQTable:
    def __init__(self, buffer, num_rows=4, num_cols=4, alpha=0.1, decay=0.99):
        self.qtable = pd.DataFrame(columns=buffer.monkeys, index=range(num_rows*num_cols)).fillna(0)
        self.alpha = alpha
        self.decay = decay
        self.grid = self.make_grid(num_cols, num_rows)

    def update(self,buffer):
        num_rewards = len(buffer.rewards)
        reward_decay = np.zeros(num_rewards)
        next_reward = 0
        # use the same rewards as what we had for the monkey choice model
        for n,r in enumerate(buffer.rewards[::-1]):
            reward_decay[num_rewards-n-1] = r + self.decay * next_reward
            next_reward = reward_decay[num_rewards-n-1]

        for i in range(len(reward_decay)):
            old_reward = self.qtable.loc[buffer.loc_action_ls[i],buffer.action_ls[i]]
            self.qtable.loc[buffer.loc_action_ls[i],buffer.action_ls[i]] += self.alpha * (reward_decay[i] - old_reward)

    def predict(self, monkey_choice):
        t = self.qtable[monkey_choice]
        max_val = t[t != 0].max()
        choices = t[t == max_val].index
        return choices.tolist()

    def save(self, filepath):
        pd.to_pickle(self, filepath)

    def make_grid(self,num_cols=4, num_rows=4):
        x_space = np.linspace(150, 1600, num_cols + 1)
        y_space = np.linspace(150, 1000, num_rows + 1)
        bounds = []
        grid = []
        for x in x_space:
            for y in y_space:
                bounds.append((x,y))

        for i in range(len(bounds)):
            if i + 1 + num_rows < len(bounds):
                x_ = bounds[i][0]
                y_ = bounds[i][1]
                yM = bounds[i +1][1]
                xM = bounds[i + 1 + num_rows][0]
                if yM > y_:
                    grid.append((x_, y_, xM, yM))
            
        return grid
    