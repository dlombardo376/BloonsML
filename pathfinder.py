# -*- coding: utf-8 -*-
"""
Created on Sat Apr 30 19:14:08 2022

@author: Danny
"""

from skimage import measure
import numpy as np

def preprocess_image(bloon_map):
    ratio = 1
    for thresh in [0.1,0.2,0.3,.4,.5,.6,.7,.8,.9]:
        new_map = (np.array(bloon_map.convert('L')) / 255. > thresh).astype(float)[100:-100,100:1650]
        ratio = new_map.sum() / (new_map.shape[0]*new_map.shape[1])
        if ratio < 0.7:
            return new_map
        
    return None


def find_contours(bloon_map, min_length=500):
    contours = measure.find_contours(bloon_map, 0.8)
    long_cons = []
    for c in contours:
        if c.shape[0] > min_length:
            long_cons.append(c)
    return np.concatenate(long_cons)


def find_viable_squares(contours, grid_options):
   path_options =[]
   for g in grid_options:
       d = np.sqrt((np.power(contours[:,1] + 100 - g[0],2) + np.power(contours[:,0] + 100 - g[1],2))).min()
       if d < 80 and d > 20:
           path_options.append(g) 
   return path_options
