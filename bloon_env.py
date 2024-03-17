import pytesseract
import numpy as np
import pyautogui
import time
import cv2

import inputs as bloon_input


class BloonEnv():
    def __init__(self):
        # tesseract
        self.tess_config = "--psm 7"
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

        # coordinates in hd, modify to get 2k
        # 2k res is 1440 x 2560
        # hd res is 1080 x 1920
        self.res_mod = (2560 / 1920, 1440 / 1080)

        # dart monkey location
        self.dart_x = 1850 * self.res_mod[0]
        self.dart_y = 250 * self.res_mod[1]

        # round start
        self.is_first_round = True  # double click first time to set fast-forward
        self.grid_spacing = 40

        self.play_button = np.load(r"C:\Users\Daniel\PycharmProjects\BloonsML\play_arr.npy")
        self.play_clean_button = np.load(r"C:\Users\Daniel\PycharmProjects\BloonsML\play_clean_arr.npy")
        self.restart_button = np.load(r"C:\Users\Daniel\PycharmProjects\BloonsML\restart_arr.npy")
        self.victory_button = np.load(r"C:\Users\Daniel\PycharmProjects\BloonsML\victory_arr.npy")
        self.xplace_im = np.load(r"C:\Users\Daniel\PycharmProjects\BloonsML\xplace_arr.npy")

    def restart_game(self):
        pyautogui.moveTo(830 * self.res_mod[0], 830 * self.res_mod[1])
        pyautogui.click()
        time.sleep(0.25)
        pyautogui.moveTo(1150 * self.res_mod[0], 760 * self.res_mod[1])
        pyautogui.click()
        time.sleep(0.25)
        self.is_first_round = True

    def clean_click(self, timer=0.25):
        pyautogui.moveTo(50, 50)
        pyautogui.click()
        time.sleep(timer)

    def take_screenshot(self, force_hd=False):
        screenshot = pyautogui.screenshot()
        if not force_hd:
            return screenshot
        else:
            return screenshot.resize((1920, 1080))

    def place_monkey_by_key(self, key, loc_choice):
        # 250x250 to 1600x1000 is usable space
        if key == -1:
            return 0, (-1, -1)
        #    print(key, len(game_grid))
        # select the monkey on screen

        # start_money = get_money()

        # select the monkey
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
            pyautogui.moveTo(x_n * self.res_mod[0], y_n * self.res_mod[1])
            if i == 0:
                pyautogui.click()
            else:
                pyautogui.mouseUp()
            time.sleep(0.25)  # between 0.3 and 0.5 should be good

            im1 = self.take_screenshot(force_hd=True)
            im1 = np.array(im1)
            print(im1.shape)
            if (im1[95:140, 1575:1625] == self.xplace_im).sum() \
                    < 0.96 * self.xplace_im.shape[0] * self.xplace_im.shape[1] * self.xplace_im.shape[2]:
                # np.save("debug.npy", im1[95:140, 1575:1625])
                # fig,ax=plt.subplots(1,2)
                # ax[0].imshow(im1[95:140, 1575:1625])
                # ax[1].imshow(xplace_im)
                # plt.show()
                return 1, (x_n * self.res_mod[0], y_n * self.res_mod[1])
            pyautogui.mouseDown()

        pyautogui.mouseUp()
        return 0, (-1, -1)

    def get_money(self):
        # 350x50 430x100
        im1 = self.take_screenshot(force_hd=True)
        try_index = 0
        money_str = ''
        while (len(money_str) < 1) and (try_index < 10):
            # start_x = 348 + try_index
            # im2 = im1.crop((352,50,450,95)).convert('L')
            im2 = im1.crop((365, 25, 465, 70)).convert('L')
            im2 = im2.resize((400, 200))
            ret, im3 = cv2.threshold(np.array(im2), 240, 255, cv2.THRESH_BINARY)
            im3 = 255 - im3
            money_str = pytesseract.image_to_string(im3, config=self.tess_config)
            #        print('money str',try_index, money_str)
            money_str = ''.join([s for s in money_str if s in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']])
            try_index += 1
        #    if len(money_str) == 0:
        #        print("WARNING! Could not determine amount of money :(")
        return money_str

    def get_lives(self):
        # 123x53 205x96
        tries = 0
        while tries < 10:
            try:
                im1 = im1 = self.take_screenshot(force_hd=True)
                im2 = im1.crop((118, 25, 200, 68)).convert('L')
                im2 = im2.resize((400, 200))
                ret, im3 = cv2.threshold(np.array(im2), 240, 255, cv2.THRESH_BINARY)
                im3 = 255 - im3
                life_str = pytesseract.image_to_string(im3, config=self.tess_config)
                life_str = ''.join([s for s in life_str if s in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']])
                assert len(life_str) > 0
                return life_str
            except Exception as e:
                print("failed to read lives")
                # plt.imshow(im3)
                # plt.show()
                self.clean_click()
                tries += 1
        return ''

    def hit_play(self, make_trajectory=False):
        # start the round
        done = 0
        # print("start round")
        pyautogui.moveTo(1850 * self.res_mod[0], 1010 * self.res_mod[1])
        time.sleep(1.0)
        pyautogui.click()
        if self.is_first_round:
            time.sleep(0.2)
            pyautogui.click()  # click twice for fast-forward
            self.is_first_round = False

        # wait till round finishes before returning to main loop
        # gameover 777x777 121x126
        # win 716x172 532x85
        pyautogui.moveTo(50, 50)  # move mouse off the play button
        wait_index = 0
        # print("waiting...")
        while wait_index < 1e4:
            wait_index += 1
            done = self.check_game_status()
            if done >= 0:
                break

        pyautogui.click()  # just keep clicking in case other crap shows up on the screen
        if wait_index < 1e4:
            return done
        else:
            raise ValueError("Got tired of waiting :(")

    def check_game_status(self):
        im1 = self.take_screenshot(force_hd=True)
        im2 = im1.crop((1792, 969, 1792 + 90, 969 + 50))
        im2 = np.array(im2)
        end_im = im1.crop((795, 760, 795 + 110, 760 + 100))
        end_im = np.array(end_im)
        win_im = im1.crop((709, 139, 709 + 532, 139 + 85))
        win_im = np.array(win_im)
        # plt.imshow(im2)
        # plt.show()
        # np.save("play_clean_arr.npy", im2)
        if (end_im == self.restart_button).sum() > 0.96 * (end_im.shape[0] * end_im.shape[1] * end_im.shape[2]):
            return 1
        elif (win_im == self.victory_button).sum() > 0.96 * (win_im.shape[0] * win_im.shape[1] * win_im.shape[2]):
            return 2
        elif (im2 == self.play_button).sum() > 0.96 * (im2.shape[0] * im2.shape[1] * im2.shape[2]):
            return 0
        elif (im2 == self.play_clean_button).sum() > 0.96 * (im2.shape[0] * im2.shape[1] * im2.shape[2]):
            return 0
        return -1

    def click_upgrade(self, monkey_spots):
        monkey_key = np.random.randint(0, len(monkey_spots))
        x, y = monkey_spots[monkey_key]

        keys = {0: 0x33, 1: 0x34, 2: 0x35}
        start_money = self.get_money()

        choices = [0, 1, 2]
        attempted = []
        while len(attempted) < len(choices):
            # move onto the upgrade screen
            pyautogui.moveTo(x * self.res_mod[0], y * self.res_mod[1])
            pyautogui.click()
            time.sleep(0.25)

            upgrade_idx = np.random.choice([c for c in choices if c not in attempted])
            attempted.append(upgrade_idx)

            key = keys[upgrade_idx]
            bloon_input.press_key(key)
            time.sleep(0.25)
            bloon_input.release_key(key)

            # move off the upgrade screen, because it shifts the money location
            self.clean_click(0.75)

            new_money = self.get_money()

            if new_money != start_money:
                self.clean_click(0.5)
                return 1

        self.clean_click(0.5)
        return 0
