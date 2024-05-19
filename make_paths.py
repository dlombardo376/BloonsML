# -*- coding: utf-8 -*-
"""
Works with full screen
"""
import time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import prices
import buffer as bloon_buffer
import model as bloon_model
import location_model as bloon_loc_model
import pathfinder as bloon_paths
from bloon_env import BloonEnv
import pyautogui
import inputs as bloon_input

def master_loop(skip_maps=0):
    pyautogui.moveTo(300, 300)
    time.sleep(1.0)
    pyautogui.click()

    starter_clicks = [
        (700, 350),
        (1270, 350),
        (1800, 350),
        (700, 750),
        (1270, 750),
        (1800, 750),
    ]

    forward_click = (2189, 574)

    names = [
        "meadow",
        "loop",
        "middle_road",
        "tree",
        "town",
        "one_two_three",
        "scrapyard",
        "cabin",
        "resort",
        "skates",
        "lotus_island",
        "candy_falls",
        "winter_park",
        "carved",
        "park_path",
        "alpine",
        "frozen_over",
        "cubism",
        "four_circles",
        "hedge",
        "end_of_road",
        "logs"
    ]
    for i in range(22):
        if i < skip_maps:
            continue

        # start game
        time.sleep(0.5)
        pyautogui.moveTo(1110, 1250)
        pyautogui.click()
        time.sleep(0.5)

        # if necessary, move to next page
        pages = i // 6
        while pages > 0:
            pyautogui.moveTo(forward_click[0], forward_click[1])
            pyautogui.click()
            time.sleep(0.5)
            pages -= 1

        # select the map
        startx = starter_clicks[i % 6][0]
        starty = starter_clicks[i % 6][1]
        time.sleep(0.5)
        pyautogui.moveTo(startx, starty)
        pyautogui.click()
        time.sleep(0.5)

        # select easy mode
        pyautogui.moveTo(840, 540)
        pyautogui.click()
        time.sleep(0.5)

        # select normal game type
        pyautogui.moveTo(840, 800)
        pyautogui.click()
        time.sleep(0.5)

        # Overwrite save if necessary.
        # If the prompt doesn't show, then it's a harmless click on the load screen.
        pyautogui.moveTo(1510, 970)
        pyautogui.click()
        time.sleep(2.5)

        game_loop(map_name=names[i])

        # press escape
        bloon_input.press_key(0x01)
        time.sleep(0.25)
        bloon_input.release_key(0x01)
        time.sleep(0.25)

        # return home
        pyautogui.moveTo(1140, 1120)
        pyautogui.click()
        time.sleep(2.5)

def game_loop(map_name:str):
    # make game the active window
    env = BloonEnv()
    env.clean_click()

    print(f"start game")
    # for two rounds just watch the bloons
    for epoch in range(2):
        env.hit_play(make_trajectory=True)
        print("updating paths")
        env.find_placement_grid_by_trajectories(inplace=True)
        print("saving paths")
        pd.to_pickle(env.path_options, f"path_{map_name}.pkl")

    # on the third round, check all the options to see which are actually valid
    # warning: didn't work, placing the monkey costs money. Can't check more than few spots.
    # env = BloonEnv(map_name=map_name)
    # env.clean_click()
    # for epoch in range(1):
    #     monkey_choice = "dart"
    #     hotkey_choice = prices.get_key_for_monkey(monkey_choice)
    #     valid_locs = []
    #     for loc_choice in env.path_options[:30]:
    #         success, monkey_spot = env.place_monkey_by_key(hotkey_choice, loc_choice, num_tries=1)
    #         if success:
    #             valid_locs.append(loc_choice)d
    #         env.clean_click()
    #     valid_locs = np.array(valid_locs)
    #     pd.to_pickle(valid_locs, f"path_{map_name}_valid.pkl")
    # print("done")
    return 0


master_loop(skip_maps=6)
