# -*- coding: utf-8 -*-
"""
Created on Sat Feb 26 23:25:00 2022

@author: Danny
"""

def get_base_prices():
    return {
            'dart':170,
            'boomerang':275,
            'cannon':445,
            'spike':240,
            'frozen':425,
            'glue':235,
            'sniper':300,
#            'sub':275,
#            'pirate':425,
            'plane':680,
#            'heli':1360,
            'mortar':640,
            'gatling':720,
            'magic':320,
            'super':2125,
            'ninja':425,
            'alchemist':470,
            'druid':340,
#            'banana':1060,
            'factory':850,
#            'village':1020,
            'engineer':340,
            'none':0
            }


def get_key_for_monkey(monkey):
    hotkeys = {
            'dart':0x10,
            'boomerang':0x11,
            'cannon':0x12,
            'spike':0x13,
            'frozen':0x14,
            'glue':0x15,
            'sniper':0x2C,
            'sub':0x2D,
            'pirate':0x2E,
            'plane':0x2F,
            'heli':0x30,
            'mortar':0x31,
            'gatling':0x32,
            'magic':0x1E,
            'super':0x1F,
            'ninja':0x20,
            'alchemist':0x21,
            'druid':0x22,
            'banana':0x23,
            'factory':0x24,
            'village':0x25,
            'engineer':0x26,
            'none':-1
            }
    return hotkeys[monkey]


def get_affordable(current_money):
    options = []
    prices = get_base_prices()
    for k in prices:
        if prices[k] <= current_money:
            options.append(k)
    return options