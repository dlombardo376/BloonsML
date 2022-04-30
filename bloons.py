# -*- coding: utf-8 -*-
"""

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

#tesseract
tess_config = "--psm 7"
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

#dart moneky lcoation
dart_x = 1850
dart_y = 250

#round start
IS_FIRST_ROUND = True #double click first time to set fast forward
play_button = Image.open(r"C:\Users\Danny\Documents\ML_projects\bloons_ai\bloon_play.png")
play_button = np.array(play_button)

restart_button = Image.open(r"C:\Users\Danny\Documents\ML_projects\bloons_ai\bloon_restart.png")
restart_button = np.array(restart_button)

victory_button = Image.open(r"C:\Users\Danny\Documents\ML_projects\bloons_ai\bloon_victory.png")
victory_button = np.array(victory_button)

def place_dart_monkey():
    #250x250 to 1600x1000 is usable space
    pyautogui.moveTo(dart_x, dart_y)
    time.sleep(0.2)
    pyautogui.click()
    x = np.random.uniform(250,1600,1)[0]
    y = np.random.uniform(250,1000,1)[0]
    pyautogui.moveTo(x, y)
    pyautogui.click()
    pyautogui.moveTo(dart_x, dart_y)


def choose_monkey(options):
    return np.random.choice(options)


def place_monkey_by_key(key,game_grid):
    #250x250 to 1600x1000 is usable space
    if key == -1:
        return 1, game_grid

    #select the monkey on screen
    time.sleep(0.25)
    bloon_input.press_key(key)
    time.sleep(0.25) #between 0.3 and 0.5 should be good
    bloon_input.release_key(key)
    
    #try locations till it works, or we get "tired"
    num_tries = 10
    start_money = get_money()
    for i in range(num_tries):
        #before placing monkeys again, check one more time for end game screen
        done = check_game_status()
        if done > 0:
            break
            
#        x = np.random.uniform(250,1600,1)[0]
#        y = np.random.uniform(250,1000,1)[0]
        choice = np.random.randint(0, len(game_grid)-1)
        x = game_grid[choice][0]
        y = game_grid[choice][1]
        pyautogui.moveTo(x, y)
        pyautogui.click()

        game_grid.pop(choice)
        #check if money changed, indicating successful placement
        new_money = get_money()
        if (new_money != start_money):
            return 1, game_grid  

        #failed placement, reset
        pyautogui.moveTo(dart_x, dart_y)
        pyautogui.moveTo(x, y)
        bloon_input.press_key(key)
        time.sleep(0.25) #between 0.3 and 0.5 should be good
        bloon_input.release_key(key)

    return 0, game_grid


def restart_game():
    pyautogui.moveTo(830, 830)
    pyautogui.click()
    time.sleep(0.25)
    pyautogui.moveTo(1150, 760)
    pyautogui.click()
    time.sleep(0.25)

    
def get_lives():
    #123x53 205x96
    im1 = pyautogui.screenshot()
    im2 = im1.crop((123,53,205,96)).convert('L')
    im2 = im2.resize((400,200))
    ret,im3 = cv2.threshold(np.array(im2), 240, 255, cv2.THRESH_BINARY)
    im3 = 255-im3
    life_str = pytesseract.image_to_string(im3, config=tess_config)
    life_str = ''.join([s for s in life_str if s in ['0','1','2','3','4','5','6','7','8','9']])
    if len(life_str) < 1:
        print('WARNING: Could not determine number of lives :(')
    return life_str


def get_money():
    #350x50 430x100
    im1 = pyautogui.screenshot()
    
    try_index = 0
    money_str = ''
    while (len(money_str) < 1) and (try_index < 10):
        #start_x = 348 + try_index
        im2 = im1.crop((352,50,450,95)).convert('L')
        im2 = im2.resize((400,200))
        ret,im3 = cv2.threshold(np.array(im2), 240, 255, cv2.THRESH_BINARY)
        im3 = 255-im3
        money_str = pytesseract.image_to_string(im3, config=tess_config)
        #print('money str',try_index, money_str)
        money_str = ''.join([s for s in money_str if s in ['0','1','2','3','4','5','6','7','8','9']])
        try_index += 1
    if len(money_str) == 0:
        print("WARNING! Could not determine amount of money :(")
    return money_str


def check_game_status():
    im1 = pyautogui.screenshot()
    im2 = im1.crop((1800,1000,1890,1050))
    im2 = np.array(im2)
    end_im = im1.crop((777,777,777+121, 777+126))
    end_im = np.array(end_im)
    win_im = im1.crop((716,172,716+532,172+85))
    win_im = np.array(win_im)

    if (end_im == restart_button).sum() > 0.96 * (end_im.shape[0] * end_im.shape[1] * end_im.shape[2]):
        return 1
    elif (win_im == victory_button).sum() > 0.96 * (win_im.shape[0] * win_im.shape[1] * win_im.shape[2]):
        return 2
    elif (im2 == play_button).all():
        return 0
    return -1


def hit_play():
    #start the round
    global IS_FIRST_ROUND
    done = 0
    #print("start round")
    pyautogui.moveTo(1850, 1050)
    pyautogui.click()
    if IS_FIRST_ROUND:
        time.sleep(0.2)
        pyautogui.click() #click twice for fast forward
        IS_FIRST_ROUND=False
    
    #wait till round finishes before returning to main loop
    #gameover 777x777 121x126
    #win 716x172 532x85
    pyautogui.moveTo(50, 50) #move mouse off the play button
    wait_index=0
    #print("waiting...")
    while wait_index < 1000:
        im1 = pyautogui.screenshot()
        im2 = im1.crop((1800,1000,1890,1050))
        im2 = np.array(im2)
        end_im = im1.crop((777,777,777+121, 777+126))
        end_im = np.array(end_im)
        win_im = im1.crop((716,172,716+532,172+85))
        win_im = np.array(win_im)

        wait_index += 1
        done = check_game_status()
        if done >= 0:
            break

    pyautogui.click() #just keep clicking in case other crap shows up on the screen
    if wait_index < 1000:
        #print("round over!")
        return done
    else:
        raise ValueError("Got tired of waiting :(")


def make_grid():
    x_space = list(range(250,1600,30))
    y_space = list(range(250,1000,30))
    grid = []
    for x in x_space:
        for y in y_space:
            grid.append((x,y))
    return grid


def game_loop(model_file = None):
    global IS_FIRST_ROUND
    #make game the active window
    pyautogui.moveTo(50, 50)
    pyautogui.click() 
    time.sleep(0.25)
    money = int(get_money())
    options = prices.get_affordable(money)
    buffer = bloon_buffer.Buffer(len(options), num_rounds=41)
    
    epsilon = 0.99
    explore_thresh = 1.0
    
    if model_file is not None:
        model= pd.read_pickle(model_file)
    else:
        model = bloon_model.QTable(buffer,num_rounds=41)
    
    for epoch in range(10): #number of times to try winning
        print(f"start game, attempt {epoch+1}")
        IS_FIRST_ROUND = True
        start_lives = int(get_lives())
        num_lives = start_lives
        buffer.reset()
        game_grid= make_grid()
        
        
#        print("Lives ", start_lives, ", Money ", money)
        for j in range(41):
        
#            print("Lives ", num_lives, ", Money ", money)
        
            money_str = get_money()
            if len(money_str) > 0: #if we couldn't read it, just go to next round
                money = int(money_str)
#            print("placing a new monkey...")
        
            #get all monkeys that are affordable right now
            e = np.random.uniform(0,1)
            options = prices.get_affordable(money)
            if e > explore_thresh:
                model_options = model.predict(j)
                #print("model prediction used")
                model_options = [o for o in model_options if o in options]
                if len(model_options) > 0:
                    options = model_options[:]
            explore_thresh = explore_thresh * epsilon

            #pick one one monkey to place, or none
            monkey_choice = choose_monkey(options)
        
            hotkey_choice = prices.get_key_for_monkey(monkey_choice)

            #choose where to place the monkey
            success,game_grid = place_monkey_by_key(hotkey_choice, game_grid)
#            if success == 0:
#                print("Failed placement. Got tired of trying")

            money_str = get_money()
            if len(money_str) > 0:
                money = int(money_str)
#                print("money after placing: ", money)
        #    else:
        #        action = 'none'

            done = hit_play()

            #update the reward
            life_str = get_lives()
            if len(life_str) > 0:
                num_lives = int(life_str)
            reward = num_lives - start_lives
            start_lives = num_lives

            #update the number of options
            money_str = get_money()
            if len(money_str) > 0:
                money = int(money_str)

            if done == 1:
                print("Game Over!")
                #lost all remaining lives this round
                buffer.add(action=monkey_choice,reward=-start_lives, is_done=done)
                break
            elif done == 2:
                print("Victory!")
                #regardless of any lives lost, give a good reward
                buffer.add(action=monkey_choice,reward=num_lives, is_done=done)
                return 1
            else:
                buffer.add(action=monkey_choice,reward=reward, is_done=done)

        model.update(buffer)
        buffer.save()
        model.save()
        restart_game()
    return 0

#game_loop()
game_loop("./bloon_model.pkl")