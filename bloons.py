# -*- coding: utf-8 -*-
"""
Works with full screen
"""
import pyautogui
import time
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import pytesseract
import cv2
import pandas as pd
import prices
import inputs as bloon_input
import buffer as bloon_buffer
import model as bloon_model
import location_model as bloon_loc_model
import pathfinder as bloon_paths

# tesseract
tess_config = "--psm 7"
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# dart monkey location
dart_x = 1850
dart_y = 250

# round start
IS_FIRST_ROUND = True  # double click first time to set fast-forward
GRID_SPACING = 40
# play_button = Image.open(r"C:\Users\Daniel\PycharmProjects\BloonsML\bloon_play.png")
# play_button = np.array(play_button)
# np.save(r"C:\Users\Daniel\PycharmProjects\BloonsML\play_arr.npy", play_button)
play_button = np.load(r"C:\Users\Daniel\PycharmProjects\BloonsML\play_arr.npy")
play_clean_button = np.load(r"C:\Users\Daniel\PycharmProjects\BloonsML\play_clean_arr.npy")

# restart_button = Image.open(r"C:\Users\Daniel\PycharmProjects\BloonsML\bloon_restart.png")
# restart_button = np.array(restart_button)
# np.save(r"C:\Users\Daniel\PycharmProjects\BloonsML\restart_arr.npy", restart_button)
restart_button = np.load(r"C:\Users\Daniel\PycharmProjects\BloonsML\restart_arr.npy")

# victory_button = Image.open(r"C:\Users\Daniel\PycharmProjects\BloonsML\bloon_victory.png")
# victory_button = np.array(victory_button)
# np.save(r"C:\Users\Daniel\PycharmProjects\BloonsML\victory_arr.npy",victory_button)
victory_button = np.load(r"C:\Users\Daniel\PycharmProjects\BloonsML\victory_arr.npy")

heart_im = np.load(r"C:\Users\Daniel\PycharmProjects\BloonsML\heart_arr.npy")

def click_upgrade(monkey_spots):
    monkey_key = np.random.randint(0, len(monkey_spots))
    x, y = monkey_spots[monkey_key]

    keys = {0: 0x33, 1: 0x34, 2: 0x35}
    start_money = get_money()

    choices = [0, 1, 2]
    attempted = []
    while len(attempted) < len(choices):
        # move onto the upgrade screen
        pyautogui.moveTo(x, y)
        pyautogui.click()
        time.sleep(0.25)

        upgrade_idx = np.random.choice([c for c in choices if c not in attempted])
        attempted.append(upgrade_idx)

        key = keys[upgrade_idx]
        bloon_input.press_key(key)
        time.sleep(0.25)
        bloon_input.release_key(key)

        # move off the upgrade screen, because it shifts the money location
        pyautogui.moveTo(50, 50)
        pyautogui.click()
        time.sleep(0.75)

        new_money = get_money()

        if new_money != start_money:
            pyautogui.moveTo(50, 50)
            pyautogui.click()
            time.sleep(0.5)
            return 1

    pyautogui.moveTo(50, 50)
    pyautogui.click()
    time.sleep(0.5)
    return 0


def choose_monkey(options):
    return np.random.choice(options)


def place_monkey_by_key(key, loc_choice):
    # 250x250 to 1600x1000 is usable space
    if key == -1:
        return 0, (-1, -1)
    #    print(key, len(game_grid))
    # select the monkey on screen

    # start_money = get_money()

    time.sleep(0.25)
    bloon_input.press_key(key)
    time.sleep(0.25)  # between 0.3 and 0.5 should be good
    bloon_input.release_key(key)

    xm = loc_choice[0]
    ym = loc_choice[1]
    xM = loc_choice[2]
    yM = loc_choice[3]
    for i in range(25):  # try moving randomly around the block
        x_n = np.random.randint(xm, xM)
        y_n = np.random.randint(ym, yM)
        pyautogui.moveTo(x_n, y_n)
        pyautogui.click()
        time.sleep(0.5)  # between 0.3 and 0.5 should be good

        # check if money changed, indicating successful placement
        # new_money = get_money()
        im1 = np.array(pyautogui.screenshot())
        # fig,ax = plt.subplots(2)
        # ax[0].imshow(heart_im)
        # ax[1].imshow(im1[20: 55, 78: 123])
        # plt.show()
        if (im1[20: 55, 78: 123] == heart_im).sum() > 0.96 * heart_im.shape[0] * heart_im.shape[1] * heart_im.shape[2]:
        # if new_money != start_money and len(new_money) > 0:
            return 1, (x_n, y_n)

            # failed placement, reset
        pyautogui.moveTo(dart_x, dart_y)
        pyautogui.moveTo(x_n, y_n)
        bloon_input.press_key(key)
        time.sleep(0.25)  # between 0.3 and 0.5 should be good
        bloon_input.release_key(key)

    return 0, (-1, -1)


def restart_game():
    pyautogui.moveTo(830, 830)
    pyautogui.click()
    time.sleep(0.25)
    pyautogui.moveTo(1150, 760)
    pyautogui.click()
    time.sleep(0.25)


def get_lives():
    # 123x53 205x96
    im1 = pyautogui.screenshot()
    #    im2 = im1.crop((123,53,205,96)).convert('L')
    im2 = im1.crop((113, 28, 195, 71)).convert('L')
    im2 = im2.resize((400, 200))
    ret, im3 = cv2.threshold(np.array(im2), 240, 255, cv2.THRESH_BINARY)
    im3 = 255 - im3
    life_str = pytesseract.image_to_string(im3, config=tess_config)
    life_str = ''.join([s for s in life_str if s in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']])
    #    if len(life_str) < 1:
    #        print('WARNING: Could not determine number of lives :(')
    return life_str


def get_money():
    # 350x50 430x100
    im1 = pyautogui.screenshot()
    try_index = 0
    money_str = ''
    while (len(money_str) < 1) and (try_index < 10):
        # start_x = 348 + try_index
        # im2 = im1.crop((352,50,450,95)).convert('L')
        im2 = im1.crop((365, 25, 465, 70)).convert('L')
        im2 = im2.resize((400, 200))
        ret, im3 = cv2.threshold(np.array(im2), 240, 255, cv2.THRESH_BINARY)
        im3 = 255 - im3
        money_str = pytesseract.image_to_string(im3, config=tess_config)
        #        print('money str',try_index, money_str)
        money_str = ''.join([s for s in money_str if s in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']])
        try_index += 1
    #    if len(money_str) == 0:
    #        print("WARNING! Could not determine amount of money :(")
    return money_str


def check_game_status():
    im1 = pyautogui.screenshot()
    im2 = im1.crop((1792, 969, 1792 + 90, 969 + 50))
    im2 = np.array(im2)
    end_im = im1.crop((787, 733, 787 + 121, 733 + 126))
    end_im = np.array(end_im)
    win_im = im1.crop((709, 139, 709 + 532, 139 + 85))
    win_im = np.array(win_im)
    # fig,ax = plt.subplots(2)
    # ax[0].imshow(end_im)
    # ax[1].imshow(restart_button)
    # plt.show()
    if (end_im == restart_button).sum() > 0.96 * (end_im.shape[0] * end_im.shape[1] * end_im.shape[2]):
        return 1
    elif (win_im == victory_button).sum() > 0.96 * (win_im.shape[0] * win_im.shape[1] * win_im.shape[2]):
        return 2
    elif (im2 == play_button).sum() > 0.96 * (im2.shape[0] * im2.shape[1] * im2.shape[2]):
        return 0
    elif (im2 == play_clean_button).sum() > 0.96 * (im2.shape[0] * im2.shape[1] * im2.shape[2]):
        return 0
    return -1


def hit_play():
    # start the round
    global IS_FIRST_ROUND
    done = 0
    # print("start round")
    pyautogui.moveTo(1850, 1050)
    pyautogui.click()
    if IS_FIRST_ROUND:
        time.sleep(0.2)
        pyautogui.click()  # click twice for fast-forward
        IS_FIRST_ROUND = False

    # wait till round finishes before returning to main loop
    # gameover 777x777 121x126
    # win 716x172 532x85
    pyautogui.moveTo(50, 50)  # move mouse off the play button
    wait_index = 0
    # print("waiting...")
    while wait_index < 1e4:
        wait_index += 1
        done = check_game_status()
        if done >= 0:
            break

    pyautogui.click()  # just keep clicking in case other crap shows up on the screen
    if wait_index < 1e4:
        return done
    else:
        raise ValueError("Got tired of waiting :(")


def make_grid(spacing=30):
    x_space = list(range(150, 1600, spacing))
    y_space = list(range(150, 1000, spacing))
    grid = []
    for x in x_space:
        for y in y_space:
            grid.append((x, y))

    # get the whole map, then locate where the path is
    orig_map = pyautogui.screenshot()
    bloon_map = bloon_paths.preprocess_image(orig_map)

    contours = bloon_paths.find_contours(bloon_map)
    filtered_grid = bloon_paths.find_viable_squares(contours, grid)

    fig, ax = plt.subplots()
    ax.imshow(orig_map)
    ax.scatter([x for x, y in filtered_grid], [y for x, y in filtered_grid])

    return filtered_grid


def game_loop(model_file=None, should_save=True):
    global IS_FIRST_ROUND
    # make game the active window
    pyautogui.moveTo(50, 50)
    pyautogui.click()
    time.sleep(0.25)
    money = int(get_money())
    options = prices.get_affordable(money)
    buffer = bloon_buffer.Buffer(len(options), num_rounds=41)
    did_win = False
    # epsilon = 0.1
    # call_upgrade_model_thresh = 0.5
    explore_thresh = 0.1
    loc_explore_thresh = 1.0

    loc_model = bloon_loc_model.LocQTable(buffer)

    if model_file is not None:
        print("reading in model")
        model = pd.read_pickle(model_file)
    else:
        model = bloon_model.QTable(buffer, num_rounds=41)

    for epoch in range(50):  # number of times to try winning
        if did_win == True:
            break
        print(f"start game, attempt {epoch + 1}")
        IS_FIRST_ROUND = True
        start_lives = int(get_lives())
        num_lives = start_lives
        buffer.reset()
        # game_grid= make_grid(spacing=GRID_SPACING)
        monkey_spots = {}  # key by monkey name, list of all locations

        for j in range(41):

            money_str = get_money()
            if len(money_str) > 0:
                money = int(money_str)
            # print("money", money)
            # get all monkeys that are affordable right now
            e = np.random.uniform(0, 1)
            options = prices.get_affordable(money)
            # options += ['upgrade_' + m for m in monkey_spots.keys()]  # add possible upgrade monkeys
            if e > explore_thresh:
                model_options = model.predict(j)
                # print("model prediction used")
                model_options = [o for o in model_options if o in options]
                if len(model_options) > 0:
                    options = model_options[:]
            # explore_thresh = explore_thresh * epsilon

            # pick one monkey to place, or none
            #            if len(game_grid) > 0:
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
                click_upgrade(monkey_spots[upgrade_choice])
            else:
                print("adding monkey ", monkey_choice, loc_choice)
                hotkey_choice = prices.get_key_for_monkey(monkey_choice)

                # choose where to place the monkey
                success, monkey_spot = place_monkey_by_key(hotkey_choice, loc_choice)

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
            money_str = get_money()
            if len(money_str) > 0:
                money = int(money_str)

            done = hit_play()

            # update the reward
            life_str = get_lives()
            if len(life_str) > 0:
                num_lives = int(life_str)
            reward = num_lives - start_lives
            start_lives = num_lives

            # update the number of options
            money_str = get_money()
            if len(money_str) > 0:
                money = int(money_str)

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
                buffer.add(action=monkey_choice, reward=reward, is_done=done, loc_action=loc_idx_choice)

        #        fig,ax=plt.subplots()
        #        ax.scatter([x for x,y in game_grid], [y for x,y in game_grid])
        #        plt.show()

        model.update(buffer)
        loc_model.update(buffer)
        if should_save:
            buffer.save("./bloon_buffer_temp.pkl")
            model.save("./bloon_model_tmp.pkl")
        restart_game()
    return did_win, model, buffer, loc_model


should_save = True
success, model, buffer, loc_model = game_loop(should_save=should_save)
# success, model, buffer, loc_model = game_loop("./bloon_model.pkl", should_save=should_save)

if success == True and should_save == True:
    buffer.save("./bloon_buffer.pkl")
    model.save("./bloon_model.pkl")
    loc_model.save("./bloon_loc_model.pkl")
