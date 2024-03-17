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


def choose_monkey(options):
    return np.random.choice(options)


def make_grid(env, spacing=30):
    x_space = list(range(150, int(1600 * env.res_mod[0]), spacing))
    y_space = list(range(150, int(1000 * env.res_mod[1]), spacing))
    grid = []
    for x in x_space:
        for y in y_space:
            grid.append((x, y))

    # get the whole map, then locate where the path is
    orig_map = env.take_screenshot(force_hd=False)
    bloon_map = bloon_paths.preprocess_image(orig_map)

    contours = bloon_paths.find_contours(bloon_map)
    filtered_grid = bloon_paths.find_viable_squares(contours, grid)

    fig, ax = plt.subplots()
    ax.imshow(orig_map)
    ax.scatter([x for x, y in filtered_grid], [y for x, y in filtered_grid])

    return filtered_grid


def game_loop(model_file=None, should_save=True):
    # make game the active window
    env = BloonEnv()
    env.clean_click()
    money = int(env.get_money())
    options = prices.get_affordable(money)
    buffer = bloon_buffer.Buffer(len(options), num_rounds=41)
    did_win = False
    epsilon = 0.66
    # call_upgrade_model_thresh = 0.5
    explore_thresh = 0.99
    loc_explore_thresh = 0.99

    loc_model = bloon_loc_model.LocQTable(buffer)

    if model_file is not None:
        print("reading in model")
        model = pd.read_pickle(model_file)
    else:
        model = bloon_model.QTable(buffer, num_rounds=41)

    for epoch in range(50):  # number of times to try winning
        if did_win:
            break
        print(f"start game, attempt {epoch + 1}")
        start_lives = int(env.get_lives())
        num_lives = start_lives
        buffer.reset()
        # game_grid= make_grid(spacing=GRID_SPACING)
        monkey_spots = {}  # key by monkey name, list of all locations

        for j in range(41):
            print("round", j+1)
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
            #            if len(game_grid) > 0:
            print(options)
            monkey_choice = choose_monkey(options)
            #            else:
            #                monkey_choice = 'none'
            loc_options = loc_model.predict(monkey_choice)
            e = np.random.uniform(0, 1)
            if len(loc_options) > 0 and e > loc_explore_thresh:
                loc_idx_choice = np.random.choice(loc_options)
            else:
                loc_idx_choice = np.random.randint(0, len(loc_model.grid) - 1)
            loc_choice = loc_model.grid[loc_idx_choice]

            if monkey_choice.startswith('upgrade_'):
                print("upgrade monkey ", monkey_choice)
                upgrade_choice = '_'.join(monkey_choice.split('_')[1:])
                env.click_upgrade(monkey_spots[upgrade_choice])
            else:
                print("adding monkey ", monkey_choice, loc_choice)
                hotkey_choice = prices.get_key_for_monkey(monkey_choice)

                # choose where to place the monkey
                success, monkey_spot = env.place_monkey_by_key(hotkey_choice, loc_choice)

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

            make_traj = False
            if epoch < 1 and j < 2:
                make_traj = True
            done = env.hit_play(make_trajectory=make_traj)
            print("done", done)
            if done == 1:
                print("Game Over!")
                # lost all remaining lives this round
                buffer.add(action=monkey_choice, reward=-start_lives, is_done=done, loc_action=loc_idx_choice)
                break
            elif done == 2:
                print("Victory!")
                # regardless of any lives lost, give a good reward
                buffer.add(action=monkey_choice, reward=num_lives, is_done=done, loc_action=loc_idx_choice)
                did_win = True
                break
            else:
                # update the reward
                life_str = env.get_lives()
                if len(life_str) > 0:
                    num_lives = int(life_str)
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
        loc_explore_thresh = max(0.1, loc_explore_thresh * epsilon)
        model.update(buffer)
        loc_model.update(buffer)
        if should_save:
            buffer.save("./bloon_buffer_temp.pkl")
            model.save("./bloon_model_tmp.pkl")
            loc_model.save("./bloon_loc_model_tmp.pkl")
        env.restart_game()
    return did_win, model, buffer, loc_model


should_save = True
success, model, buffer, loc_model = game_loop(should_save=should_save)
# success, model, buffer, loc_model = game_loop("./bloon_model.pkl", should_save=should_save)

if success and should_save:
    buffer.save("./bloon_buffer.pkl")
    model.save("./bloon_model.pkl")
    loc_model.save("./bloon_loc_model.pkl")
