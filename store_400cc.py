import keyboard
import threading
import time
import pyautogui
import os

#variables of positions
shopX = 496
shopY = 551
messageX = 64
messageY = 482
openShopX = 163
openShopY = 490
btOkX = 590
btOkY = 555
############
#variables
price = '3000000'
#pos = 1 = 1 e 2 linha do inventario
#pos 2 = 3 e 4 linha do inventario
#pos 3 = 5,6 linha do invetario
pos = 3

if pos == 1:
    slot1x = 405
    slot1y = 145        
elif pos == 2:  
    slot1x = 405
    slot1y = 207    
elif pos == 3:  
    slot1x = 405
    slot1y = 269

variacao = 30

time.sleep(5)

pyautogui.press('esc')
time.sleep(1)
pyautogui.click(shopX, shopY, button='left')
time.sleep(1.5)


# Primeiro terço
# Método 1: For aninhado (linha por linha)
for linha in range(2):  # 2 linhas
    for coluna in range(10):  # 10 colunas
        pyautogui.click(slot1x, slot1y, button='right')
        #pyautogui.moveTo(slot1x, slot1y)
        time.sleep(0.5)
        pyautogui.write(price)
        time.sleep(0.2)
        pyautogui.press('enter')
        slot1x += variacao
    slot1y += variacao    
    slot1x = 405


time.sleep(1)
pyautogui.click(messageX, messageY, button='left')
time.sleep(1)
pyautogui.write('400cc____3kk________THERE_IS_NO_CHEAPER')
time.sleep(0.5)
pyautogui.click(btOkX, btOkY, button='left')
time.sleep(0.5)
pyautogui.click(openShopX, openShopY, button='left')

