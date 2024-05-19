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

# TODO: add location as part of the actions. Maybe 9 general locations per monkey? But try making it a single model.
# Note: model will be specific to the map with this implementation.
# Note: Make it a dual agent model. Location isn't really dependent on level, it's dependent on monkey choice.


def master_loop(num_games=1, randomize=False, model_file=None, explore_thresh=0.99, subset=None):
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

    track_ls=[]
    for i in range(num_games):
        if subset is None:
            if randomize:
                game_idx = np.random.choice(len(names))
            else:
                game_idx = i % len(names)
        else:
            if randomize:
                sub_idx = np.random.choice(len(subset))
            else:
                sub_idx = i % len(subset)
            game_idx = next(
                idx
                for idx, name
                in enumerate(names)
                if name == subset[sub_idx]
            )

        start_idx = game_idx % 6
        startx = starter_clicks[start_idx][0]
        starty = starter_clicks[start_idx][1]
        game_name = names[game_idx]

        # start game
        time.sleep(0.5)
        pyautogui.moveTo(1110, 1250)
        pyautogui.click()
        time.sleep(0.5)

        # if necessary, move to next page
        pages = game_idx // 6
        while pages > 0:
            pyautogui.moveTo(forward_click[0], forward_click[1])
            pyautogui.click()
            time.sleep(0.5)
            pages -= 1

        # select the map
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

        print(f"map {game_name}")
        # trajectory_loop(map_name=names[game_idx])
        success, model, buffer = game_loop(should_save=True,
                                           map_name=game_name,
                                           model_file=model_file,
                                           explore_thresh=explore_thresh
                                           )

        track_ls.append({
            "success": success,
            "reward": sum(buffer.rewards),
            "map": game_name,
            "num_rounds": len(buffer.rewards),
            "explore_thresh": explore_thresh
        })
        # End the game, success or fail
        if success == 1:
            pyautogui.moveTo(1290, 1215)
            pyautogui.click()
            time.sleep(0.5)

            pyautogui.moveTo(945, 1130)
            pyautogui.click()
            time.sleep(2.5)
        elif success == 0:
            # print("going through defeat reset")
            pyautogui.moveTo(830, 1080)
            pyautogui.click()
            time.sleep(2.5)
        elif success == -1:
            # Press escape
            bloon_input.press_key(0x01)
            time.sleep(0.25)
            bloon_input.release_key(0x01)
            time.sleep(0.25)

            # Return home
            pyautogui.moveTo(1140, 1120)
            pyautogui.click()
            time.sleep(2.5)
        else:
            # placeholder condition for trajectory building commands
            # Press escape
            bloon_input.press_key(0x01)
            time.sleep(0.25)
            bloon_input.release_key(0x01)
            time.sleep(0.25)

            # Return home
            pyautogui.moveTo(1140, 1120)
            pyautogui.click()
            time.sleep(2.5)
    return track_ls


def choose_monkey(options):
    choice = np.random.choice(options)
    return choice


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


def game_loop(model_file=None, should_save=True, map_name=None, explore_thresh=0.99):
    # make game the active window
    env = BloonEnv(map_name)
    env.clean_click()
    money = int(env.get_money())
    options = prices.get_affordable(money)
    buffer = bloon_buffer.Buffer(len(options), num_rounds=41)
    did_win = False
    # call_upgrade_model_thresh = 0.5

    if model_file is not None:
        # print("reading in model")
        model = pd.read_pickle(model_file)
    else:
        model = bloon_model.QTable(buffer, num_rounds=41, num_grid=env.grid_spacing**2)

    num_games = 1
    for epoch in range(num_games):  # number of times to try winning
        if did_win:
            break
        start_lives = int(env.get_lives())
        print(f"start game, attempt {epoch + 1}, with lives {start_lives}")
        num_lives = start_lives
        buffer.reset()
        monkey_spots = {}  # key by monkey name, list of all locations

        placement_coords = []
        for j in range(41):
            # print("round", j+1)
            money_str = env.get_money()
            if len(money_str) > 0:
                money = int(money_str)
            # print("money", money)
            # get all monkeys that are affordable right now

            e = np.random.uniform(0, 1)
            options = []
            monkey_options = prices.get_affordable(money)  # get affordable monkeys
            for monkey in monkey_options:
                for mng in range(model.num_grid):
                    options.append(f"{monkey}_{mng}")
            # options += ['upgrade_' + m for m in monkey_spots.keys()]  # add possible upgrade monkeys
            if e > explore_thresh:
                model_options = model.predict(j)
                model_options = [o for o in model_options if o in options]
                if len(model_options) > 0:
                    options = model_options[:]
            # pick one monkey to place, or none
            # print(options)
            choice = choose_monkey(options)
            monkey_choice = choice.split("_")[0]
            grid_idx = int(choice.split("_")[1])

            if monkey_choice.startswith('upgrade_'):
                # print("upgrade monkey ", monkey_choice)
                upgrade_choice = '_'.join(monkey_choice.split('_')[1:])
                env.click_upgrade(monkey_spots[upgrade_choice])
            else:
                hotkey_choice = prices.get_key_for_monkey(monkey_choice)

                # choose where to place the monkey
                grid_options = env.get_grid_box_options(grid_idx, np.array(env.path_options))
                for placement_try in range(15):
                    loc_idx = np.random.randint(0, len(grid_options) - 1)
                    loc_choice = grid_options[loc_idx]
                    # print("adding monkey ", monkey_choice, loc_choice, loc_idx_choice)
                    success, monkey_spot = env.place_monkey_by_key(
                        hotkey_choice,
                        loc_choice,
                        num_tries=1,
                        add_noise=False
                    )
                    if success:
                        placement_coords.append(loc_choice)
                        break
                    # elif len(env.path_options) < 40:
                    #     np.save(f"bad_path_{map_name}_valid.npy", env.path_options)
                    #     print("WARNING: not enough path options")
                    #     return -1, model, buffer

                # keep track of where we've placed monkeys
                # if success == 1 and monkey_spot is not None:
                #     if monkey_choice in monkey_spots:
                #         monkey_spots[monkey_choice].append(monkey_spot)
                #     else:
                #         monkey_spots[monkey_choice] = [monkey_spot]
            #                    print("monkey added ")
            #                else:
            #                    print("monkey not added ")

            # end round
            # always try to read the money :)
            money_str = env.get_money()
            if len(money_str) > 0:
                money = int(money_str)

            done = env.hit_play()

            # if done > 0:
                # im1 = env.take_screenshot(force_hd=True)
                # im2 = np.array(im1)
                # hash = time.time()
                # np.save(f"end_screen_{hash}.npy", im2)
            if done == 1:
                # lost all remaining lives this round
                buffer.add(action=choice, reward=-start_lives, is_done=done, loc_action=grid_idx)
                print("Game Over!", sum(buffer.rewards))
                break
            elif done == 2:
                # regardless of any lives lost, give a good reward
                buffer.add(action=choice, reward=200, is_done=done, loc_action=grid_idx)
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
                if num_lives > start_lives or num_lives < 0:
                    print("WARNING: num lives does not make sense. Exiting.")
                    return -1, model, buffer
                reward = num_lives - start_lives
                start_lives = num_lives

                # update the number of options
                money_str = env.get_money()
                if len(money_str) > 0:
                    money = int(money_str)

                buffer.add(action=choice, reward=reward, is_done=done, loc_action=grid_idx)

        #        fig,ax=plt.subplots()
        #        ax.scatter([x for x,y in game_grid], [y for x,y in game_grid])
        #        plt.show()

        model.update(buffer)
        if should_save:
            buffer.save(f"./bloon_buffer_temp_{map_name}.pkl")
            model.save(f"./bloon_model_tmp_{map_name}.pkl")
            np.save(f"path_{map_name}_valid.npy", env.path_options)

        if epoch < num_games - 1:
            # we are playing again :)
            env.restart_game()
    return did_win, model, buffer


map_name = "scrapyard"
model_file = f"bloon_model_tmp_{map_name}.pkl"
result_file = f"results_qlearn_temp_{map_name}.csv"

try:
    track_ls = pd.read_csv(result_file)
    track_ls = track_ls.to_dict("records")
    print("Loaded results file, resuming training.")
except:
    print("Couldn't find a result file. Check location or make a new one.")

# explore_thresh = 0.99
# track_ls = master_loop(1, randomize=True, model_file=None, explore_thresh=explore_thresh, subset=[map_name])
explore_thresh = 0.5
for i in range(1):
    track_ls += master_loop(1, randomize=True, model_file=model_file, explore_thresh=explore_thresh, subset=[map_name])
    pd.DataFrame(track_ls).to_csv(result_file, index=False)
explore_thresh = 0.1
for i in range(15):
    track_ls += master_loop(1, randomize=True, model_file=model_file, explore_thresh=explore_thresh, subset=[map_name])
    pd.DataFrame(track_ls).to_csv(result_file, index=False)

pd.DataFrame(track_ls).to_csv(result_file, index=False)
