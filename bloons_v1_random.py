# -*- coding: utf-8 -*-
"""

"""

#can get to level 40 just with random!
#table of selection per round
#reward function by number of lives start of next round
    #not going to use money, as that discourages expensive towers
#state is count of each monkey type and number of options available
    #count can be binned (0,1,2,3,4+)

#epsilon greedy
    #either choose at random, or just pick the one with max reward

import pyautogui
import time
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import pytesseract
import cv2
import prices
import inputs as bloon_input

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


def place_monkey_by_key(key):
    #250x250 to 1600x1000 is usable space
    if key == -1:
        return 1

    #select the monkey on screen
    time.sleep(0.25)
    bloon_input.press_key(key)
    time.sleep(0.25) #between 0.3 and 0.5 should be good
    bloon_input.release_key(key)
    
    #try locations till it works, or we get "tired"
    num_tries = 10
    start_money = get_money()
    for i in range(num_tries):
        x = np.random.uniform(250,1600,1)[0]
        y = np.random.uniform(250,1000,1)[0]
        pyautogui.moveTo(x, y)
        pyautogui.click()

        #check if money changed, indicating successful placement
        new_money = get_money()
        if (new_money != start_money):
            return 1  

        #failed placement, reset
        pyautogui.moveTo(dart_x, dart_y)
        pyautogui.moveTo(x, y)
        bloon_input.press_key(key)
        time.sleep(0.25) #between 0.3 and 0.5 should be good
        bloon_input.release_key(key)

    return 0


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



def hit_play():
    #start the round
    global IS_FIRST_ROUND
    print("start round")
    pyautogui.moveTo(1850, 1050)
    pyautogui.click()
    if IS_FIRST_ROUND:
        time.sleep(0.2)
        pyautogui.click() #click twice for fast forward
        IS_FIRST_ROUND=False
    
    #wait till round finishes before returning to main loop
    pyautogui.moveTo(50, 50) #move mouse off the play button
    wait_index=0
    print("waiting...")
    while wait_index < 1000:
        im1 = pyautogui.screenshot()
        im2 = im1.crop((1800,1000,1890,1050))
        im2 = np.array(im2)
        wait_index += 1
        if (im2 == play_button).all():
            break
    if wait_index < 1000:
        print("round over!")
        return 1
    else:
        raise ValueError("Got tired of waiting :(")


pyautogui.moveTo(50, 50)
pyautogui.click() 
time.sleep(0.5)

#money_str = get_money()
#money = int(get_money())
#options = prices.get_affordable(money)
#monkey_choice = np.random.choice(options)
#
#pyautogui.moveTo(50, 50)
#pyautogui.click() 
#place_monkey_by_key(monkey_choice)
life_str = get_lives()
num_lives = int(life_str)

for i in range(1000):
    print(i)
    money_str = get_money()
    life_str = get_lives()
    
    print("Lives ", life_str, ", Money ", money_str)

    if len(life_str) > 0:
        num_lives = int(life_str)
    
    if len(money_str) > 0: #if we couldn't read it, just go to next round
        money = int(get_money())
        print("placing monkeys...")

        #get all monkeys that are affordable right now
        options = prices.get_affordable(money)
        if len(options) < 1: 
            raise ("No options? How?? We added none as a choice")
        
        #pick one one monkey to place, or none
        monkey_choice = choose_monkey(options)
   
        #choose where to place the monkey
        success = place_monkey_by_key(monkey_choice)
        if success == 0:
            print("Failed placement. Got tired of trying")

        money_str = get_money()
        if len(money_str) > 0:
            #update money if read was successful
            #if not, we'll try again after next round
            money = int(money_str)
            print("money after placing: ", money)

    hit_play()