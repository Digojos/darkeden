
import keyboard
import threading
import time
import pyautogui
import os

npcX = 879
npcY = 362
menuoptionX = 750
menuoptionY = 460
potionX = 288
potionY = 433
btOkX = 562
btOkY = 547

mapaX = 918
mapaY = 572

# Get position after a delay (gives you time to move mouse)
print("1 - Move mouse to desired position...")
time.sleep(3)  # 3 second delay
x, y = pyautogui.position()
print(f"Mouse position:\n\n\n\n\n\n ({x}, {y})")
print("2 - Move mouse to desired position...")
time.sleep(10)  # 3 second delay
x, y = pyautogui.position()
print(f"2 - Mouse position:\n\n\n\n\n\n ({x}, {y})")