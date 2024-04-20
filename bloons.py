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


def master_loop(num_games=1, randomize=False, model_file=None):
    pyautogui.moveTo(300, 300)
    time.sleep(1.0)
    pyautogui.click()

    starter_clicks = [
        (700, 350),
        (1270, 350),
        (1800, 350),
        (700, 750),
        (1270, 750),
        # (1800, 750),
    ]

    names = [
        "meadow",
        "loop",
        "middle_road",
        "tree",
        "town",
        # "one_two_three"
    ]
    for i in range(num_games):
        if randomize:
            game_idx = np.random.choice(len(starter_clicks))
        else:
            game_idx = i

        # start game
        time.sleep(0.5)
        pyautogui.moveTo(1110, 1250)
        pyautogui.click()
        time.sleep(0.5)

        # select the map
        startx = starter_clicks[game_idx][0]
        starty = starter_clicks[game_idx][1]
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

        print(f"map {names[game_idx]}")
        # trajectory_loop(map_name=names[game_idx])
        success, model, buffer = game_loop(should_save=True,
                                           map_name=names[game_idx],
                                           model_file=model_file
                                           )

        # End the game, success or fail
        if success:
            pyautogui.moveTo(1290, 1215)
            pyautogui.click()
            time.sleep(0.5)

            pyautogui.moveTo(945, 1130)
            pyautogui.click()
            time.sleep(2.5)
        elif not success:
            # print("going through defeat reset")
            pyautogui.moveTo(1130, 1080)
            pyautogui.click()
            time.sleep(2.5)
        else: # placeholder condition for trajectory building commands
            # Press escape
            bloon_input.press_key(0x01)
            time.sleep(0.25)
            bloon_input.release_key(0x01)
            time.sleep(0.25)

            # Return home
            pyautogui.moveTo(1140, 1120)
            pyautogui.click()
            time.sleep(2.5)


def choose_monkey(options):
    return np.random.choice(options)


def trajectory_loop(map_name:str):
    # make game the active window
    env = BloonEnv()
    env.clean_click()

    print(f"start game")

    done = env.hit_play(make_trajectory=True)
    print("updating paths")
    env.find_placement_grid_by_trajectories(inplace=True)
    print("saving paths")
    pd.to_pickle(env.path_options, f"path_{map_name}.pkl")

    print("done", done)
    return 0


def game_loop(model_file=None, should_save=True, map_name=None):
    # make game the active window
    env = BloonEnv(map_name)
    env.clean_click()
    money = int(env.get_money())
    options = prices.get_affordable(money)
    buffer = bloon_buffer.Buffer(len(options), num_rounds=41)
    did_win = False
    epsilon = 0.66
    # call_upgrade_model_thresh = 0.5
    explore_thresh = 0.99
    # loc_explore_thresh = 0.99

    # loc_model = bloon_loc_model.LocQTable(buffer)

    if model_file is not None:
        # print("reading in model")
        model = pd.read_pickle(model_file)
    else:
        model = bloon_model.QTable(buffer, num_rounds=41)

    for epoch in range(1):  # number of times to try winning
        if did_win:
            break
        start_lives = int(env.get_lives())
        print(f"start game, attempt {epoch + 1}, with lives {start_lives}")
        num_lives = start_lives
        buffer.reset()
        monkey_spots = {}  # key by monkey name, list of all locations

        for j in range(41):
            # print("round", j+1)
            money_str = env.get_money()
            if len(money_str) > 0:
                money = int(money_str)
            # print("money", money)
            # get all monkeys that are affordable right now

            e = np.random.uniform(0, 1)
            options = prices.get_affordable(money)
            # options += ['upgrade_' + m for m in monkey_spots.keys()]  # add possible upgrade monkeys
            if e > explore_thresh:
                model_options = model.predict(j)
                model_options = [o for o in model_options if o in options]
                if len(model_options) > 0:
                    options = model_options[:]
            # pick one monkey to place, or none
            # print(options)
            monkey_choice = choose_monkey(options)

            # pick where the monkey will go
            # loc_options = loc_model.predict(monkey_choice)
            # e = np.random.uniform(0, 1)
            # if len(loc_options) > 0 and e > loc_explore_thresh:
            #     loc_idx_choice = np.random.choice(loc_options)
            # else:

            if monkey_choice.startswith('upgrade_'):
                # print("upgrade monkey ", monkey_choice)
                upgrade_choice = '_'.join(monkey_choice.split('_')[1:])
                env.click_upgrade(monkey_spots[upgrade_choice])
            else:
                hotkey_choice = prices.get_key_for_monkey(monkey_choice)

                # choose where to place the monkey
                for placement_try in range(30):
                    loc_idx_choice = np.random.randint(0, len(env.path_options) - 1)
                    loc_choice = env.path_options[loc_idx_choice]
                    # print("adding monkey ", monkey_choice, loc_choice, loc_idx_choice)
                    success, monkey_spot = env.place_monkey_by_key(
                        hotkey_choice,
                        loc_choice,
                        num_tries=1,
                        add_noise=False
                    )
                    if success:
                        break
                    elif prices.get_size()[monkey_choice] == 's':
                        env.path_options.pop(loc_idx_choice)

                # keep track of where we've placed monkeys
                if success == 1:
                    if monkey_choice in monkey_spots:
                        monkey_spots[monkey_choice].append(monkey_spot)
                    else:
                        monkey_spots[monkey_choice] = [monkey_spot]
            #                    print("monkey added ")
            #                else:
            #                    print("monkey not added ")

            # end round
            # always try to read the money :)
            money_str = env.get_money()
            if len(money_str) > 0:
                money = int(money_str)

            done = env.hit_play()

            if done > 0:
                im1 = env.take_screenshot(force_hd=True)
                im2 = np.array(im1)
                hash = time.time()
                np.save(f"end_screen_{hash}.npy", im2)
            if done == 1:
                # lost all remaining lives this round
                buffer.add(action=monkey_choice, reward=-start_lives, is_done=done, loc_action=loc_idx_choice)
                print("Game Over!", sum(buffer.rewards))
                break
            elif done == 2:
                # regardless of any lives lost, give a good reward
                buffer.add(action=monkey_choice, reward=200, is_done=done, loc_action=loc_idx_choice)
                print("Victory!", sum(buffer.rewards))
                did_win = True
                break
            else:
                # update the reward
                life_str = env.get_lives()
                if len(life_str) > 0:
                    num_lives = int(life_str)
                    if num_lives > start_lives:
                        print(f"WARNING: num lives too large: {num_lives}. Start: {start_lives}. Setting to 1 less")
                        num_lives = start_lives - 1
                assert num_lives <= start_lives
                assert num_lives >= 0
                reward = num_lives - start_lives
                start_lives = num_lives

                # update the number of options
                money_str = env.get_money()
                if len(money_str) > 0:
                    money = int(money_str)

                buffer.add(action=monkey_choice, reward=reward, is_done=done, loc_action=loc_idx_choice)

        #        fig,ax=plt.subplots()
        #        ax.scatter([x for x,y in game_grid], [y for x,y in game_grid])
        #        plt.show()

        explore_thresh = max(0.1, explore_thresh * epsilon)
        # loc_explore_thresh = max(0.1, loc_explore_thresh * epsilon)
        model.update(buffer)
        # loc_model.update(buffer)
        if should_save:
            buffer.save("./bloon_buffer_temp.pkl")
            model.save("./bloon_model_tmp.pkl")
            np.save(f"path_{map_name}_valid.npy", env.path_options)
            # loc_model.save("./bloon_loc_model_tmp.pkl")
        env.restart_game()
    return did_win, model, buffer#, loc_model


master_loop(1, randomize=True, model_file=None)
master_loop(49, randomize=True, model_file="bloon_model_tmp.pkl")
# should_save = True
# success, model, buffer = game_loop(should_save=should_save, map_name="middle_road")
# # success, model, buffer, loc_model = game_loop("./bloon_model.pkl", should_save=should_save)
#
# if success and should_save:
#     buffer.save("./bloon_buffer.pkl")
#     model.save("./bloon_model.pkl")
#     # loc_model.save("./bloon_loc_model.pkl")
