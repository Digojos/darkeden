import keyboard
import threading
import time
import pyautogui
import os

holding = False
autoClickOn = False
mouseAttackX = 0
mouseAttackY = 0
mouseAntesX = 0
mouseAntesY = 0

hotkeyHoldRight = 'f4'
hotkeyAttack = '\\'
hotkeySalvar = 'alt+1'
hotkeyBloodyWall = 'f12';
hotkeyMeteoroNoose = 'f5';
hotkeyViolentPhatom = '';


bloodwalls = [0 , 25 , -25, 50, -50] 

def saveCurrentMousePosition():
    global mouseAntesX
    global mouseAntesY
    
    mouseAntesX = pyautogui.position().x
    mouseAntesY = pyautogui.position().y

def mouseAttackValidation():
    global mouseAttackX
    global mouseAttackY

    if (mouseAttackX != 0 and mouseAttackY != 0):
        return True
    
    
    return False


def hold_right_click():
    global holding

    while holding:
        pyautogui.mouseDown(button='right')
        time.sleep(0.1)  # Small sleep to reduce CPU usage        

def Mage_hold_right_click():
    global autoClickOn

    while autoClickOn:
        pyautogui.mouseDown(button='right')
        time.sleep(0.1)  # Small sleep to reduce CPU usage        
                

def toggle_right_click():
    global holding
    global mouseAttackX
    global mouseAttackY
    global mouseAntesX
    global mouseAntesY
    
    holding = not holding
    if holding:
        saveCurrentMousePosition()
        print("\n\n\n\n\n\n\n\nAtacando...")        
        pyautogui.press('backspace')
        if mouseAttackValidation() :
            pyautogui.moveTo(mouseAttackX, mouseAttackY)     
              
        threading.Thread(target=hold_right_click).start()
    else:
        print("Parando de atacar...")
        pyautogui.press('backspace')
        pyautogui.mouseUp(button='right')       
        pyautogui.moveTo(mouseAntesX, mouseAntesY)
        os.system('cls')

def autoClickToggle():
    global autoClickOn
    autoClickOn = not autoClickOn
    if autoClickOn:
      print("\n\n\n\n\nAtacando")        
      pyautogui.press('backspace')          
      threading.Thread(target=autoClickRunning).start()
    else:        
        pyautogui.mouseUp(button='right')
         
  
   
        
def autoClickRunning():
    global autoClickOn
    global mouseAttackX
    global mouseAttackY
    global mouseAntesX
    global mouseAntesY
    
    if mouseAttackValidation():
        pyautogui.press('f12')
        saveCurrentMousePosition()       
        pyautogui.moveTo(mouseAttackX, mouseAttackY)
        time.sleep(0.5)
        for wall in bloodwalls: 
           
            if autoClickOn:
                pyautogui.keyDown('alt')            
                pyautogui.rightClick(mouseAttackX,mouseAttackY + wall)
                pyautogui.keyUp('alt')
                if wall != -50:
                    time.sleep(2)     
                    
        
        time.sleep(1)  
        pyautogui.moveTo(mouseAttackX, mouseAttackY)
        threading.Thread(target=Mage_hold_right_click).start()
            
            
        
        pyautogui.moveTo(mouseAntesX, mouseAntesY)   
    else:
        autoClickOn = False
        print("Pressione a tecla: " + hotkeySalvar + " para setar uma posição inicial");    

def set_mouse_attack():
    global mouseAttackX
    global mouseAttackY
    pyautogui.press('backspace')
    mouseAttackX = pyautogui.position().x
    mouseAttackY = pyautogui.position().y
    print("Posição salva com sucesso");
    
def printar_pos():
    print(pyautogui.position())    
    pyautogui.press('capslock')
def sleep_ms(milliseconds):
    time.sleep(milliseconds / 1000.0)

def background_task():
    while True:
        # Your background task code here
        time.sleep(1)

if __name__ == "__main__":
    # Start the background task in a separate thread
    background_thread = threading.Thread(target=background_task)
    background_thread.daemon = True  # This ensures the thread exits when the main program exits
    background_thread.start()

    # Set up the hotkey
    keyboard.add_hotkey(hotkeyHoldRight, toggle_right_click)
    keyboard.add_hotkey(hotkeySalvar, set_mouse_attack)  
      
    keyboard.add_hotkey(hotkeyAttack, autoClickToggle) 
    print("Tecla para atacar mouse direito (Segurar): " + hotkeyHoldRight)
    print("Tecla para combo mago: " + hotkeyAttack + " NECESSÁRIO MARCAR POSIÇÃO EM BAIXO DO CHAR")
    print("Tecla para setar posição: " + hotkeySalvar)
    
    # Keep the main thread alive to listen for the hotkey
    keyboard.wait('f2')  # Change 'esc' to your desired exit key
