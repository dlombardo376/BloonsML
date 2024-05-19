# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 22:54:43 2022

@author: Danny
"""
import pandas as pd
import numpy as np


class QTable:
    def __init__(self, buffer, num_rounds=41, alpha=0.1, decay=0.99, num_grid=9):
        cols = []
        for monkey in buffer.monkeys:
            for i in range(num_grid):
                cols.append(f"{monkey}_{i}")
        self.qtable = pd.DataFrame(columns=cols, index=range(num_rounds)).fillna(0)
        self.alpha = alpha
        self.decay = decay
        self.num_grid = num_grid

    def update(self, buffer):
        num_rewards = len(buffer.rewards)
        reward_decay = np.zeros(num_rewards)
        next_reward = 0
        for n, r in enumerate(buffer.rewards[::-1]):
            reward_decay[num_rewards-n-1] = r + self.decay * next_reward
            next_reward = reward_decay[num_rewards-n-1]

        for i in range(len(reward_decay)):
            old_reward = self.qtable.loc[i, buffer.action_ls[i]]
            self.qtable.loc[i, buffer.action_ls[i]] += self.alpha * (reward_decay[i] - old_reward)

    def predict(self, round_num):
        t = self.qtable.loc[round_num]
        maxval = t[t != 0].max()
        choices = t[t == maxval].index
        return choices

    def save(self, filepath):
        pd.to_pickle(self, filepath)
    