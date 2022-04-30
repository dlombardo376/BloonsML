# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 22:54:43 2022

@author: Danny
"""
import pandas as pd
import numpy as np

class QTable():
    def __init__(self,buffer,num_rounds=41,alpha=0.1,decay=0.9):
        self.qtable = pd.DataFrame(columns=buffer.monkeys, index=range(41)).fillna(0)
        self.alpha = alpha


    def update(self,buffer):
        num_rewards = len(buffer.rewards)
        reward_decay = np.zeros(num_rewards)
        decay = 0.99
        next_reward = 0
        for n,r in enumerate(buffer.rewards[::-1]):
            reward_decay[num_rewards-n-1] = r + decay * next_reward
            next_reward = reward_decay[num_rewards-n-1]

        for i in range(len(reward_decay)):
            old_reward = self.qtable.loc[i,buffer.action_ls[i]]
            self.qtable.loc[i,buffer.action_ls[i]] += self.alpha * (reward_decay[i] - old_reward)


    def predict(self,round_num):
        choices = self.qtable.loc[round_num][self.qtable.loc[round_num] == self.qtable.loc[round_num].max()].index
        return choices


    def save(self):
        pd.to_pickle(self,"bloon_model.pkl")
    