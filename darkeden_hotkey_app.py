from hotkey_manager import HotkeyManager
import pyautogui
import time
import threading
import os

class DarkEdenBot:
    def __init__(self):
        self.holding = False
        self.autoClickOn = False
        self.mouseAttackX = 0
        self.mouseAttackY = 0
        self.mouseAntesX = 0
        self.mouseAntesY = 0
        self.bloodwalls = [0, 25, -25, 50, -50]
        
        # Criar o gerenciador de hotkeys
        self.hotkey_manager = HotkeyManager()
        self.setup_hotkeys()
        
    def setup_hotkeys(self):
        """Configura todas as hotkeys do bot"""
        
        # Registrar métodos com hotkeys
        self.hotkey_manager.register_method(
            hotkey='f5',
            method=self.toggle_right_click,
            description="Toggle ataque básico (segurar botão direito)"
        )
        
        self.hotkey_manager.register_method(
            hotkey='\\',
            method=self.autoClickToggle,
            description="Toggle combo completo de mago"
        )
        
        self.hotkey_manager.register_method(
            hotkey='alt+1',
            method=self.set_mouse_attack,
            description="Salvar posição atual do mouse para ataque"
        )
        
        # Hotkeys extras
        self.hotkey_manager.register_method(
            hotkey='f6',
            method=self.print_current_position,
            description="Mostrar posição atual do mouse"
        )
        
        self.hotkey_manager.register_method(
            hotkey='f7',
            method=self.stop_all_actions,
            description="Parar todas as ações do bot"
        )
        
    def saveCurrentMousePosition(self):
        self.mouseAntesX = pyautogui.position().x
        self.mouseAntesY = pyautogui.position().y
        
    def mouseAttackValidation(self):
        return self.mouseAttackX != 0 and self.mouseAttackY != 0
        
    def hold_right_click(self):
        while self.holding:
            pyautogui.click(button='right')
            time.sleep(0.1)
            
    def Mage_hold_right_click(self):
        while self.autoClickOn:
            pyautogui.mouseDown(button='left')
            time.sleep(0.5)
            
    def toggle_right_click(self):
        self.holding = not self.holding
        if self.holding:
            self.saveCurrentMousePosition()
            print("🗡️ Ataque básico INICIADO")
            pyautogui.press('backspace')
            pyautogui.keyDown('alt')
            if self.mouseAttackValidation():
                pyautogui.moveTo(self.mouseAttackX, self.mouseAttackY)
            threading.Thread(target=self.hold_right_click, daemon=True).start()
        else:
            print("⏹️ Ataque básico PARADO")
            pyautogui.keyUp('alt')
            pyautogui.mouseUp(button='right')
            pyautogui.moveTo(self.mouseAntesX, self.mouseAntesY)
            os.system('cls' if os.name == 'nt' else 'clear')
            
    def autoClickToggle(self):
        self.autoClickOn = not self.autoClickOn
        if self.autoClickOn:
            print("🧙 Combo mago INICIADO")
            pyautogui.press('backspace')
            threading.Thread(target=self.autoClickRunning, daemon=True).start()
        else:
            print("⏹️ Combo mago PARADO")
            pyautogui.mouseUp(button='right')
            pyautogui.mouseUp(button='left')
            
    def autoClickRunning(self):
        if self.mouseAttackValidation():
            pyautogui.press('f12')  # Skill do jogo
            self.saveCurrentMousePosition()
            pyautogui.moveTo(self.mouseAttackX, self.mouseAttackY)
            time.sleep(0.5)
            
            # Executar bloody walls
            for i, wall in enumerate(self.bloodwalls):
                if self.autoClickOn:
                    print(f"⚡ Bloody Wall {i+1}/5 (offset: {wall})")
                    pyautogui.keyDown('alt')
                    pyautogui.rightClick(self.mouseAttackX, self.mouseAttackY + wall)
                    pyautogui.keyUp('alt')
                    if wall != -50:
                        time.sleep(2)
                        
            time.sleep(1)
            pyautogui.moveTo(self.mouseAttackX, self.mouseAttackY)
            threading.Thread(target=self.Mage_hold_right_click, daemon=True).start()
            pyautogui.moveTo(self.mouseAntesX, self.mouseAntesY)
        else:
            self.autoClickOn = False
            print("❌ ERRO: Defina uma posição de ataque primeiro (Alt+1)")
            
    def set_mouse_attack(self):
        pyautogui.press('backspace')
        self.mouseAttackX = pyautogui.position().x
        self.mouseAttackY = pyautogui.position().y
        print(f"📍 Posição de ataque salva: ({self.mouseAttackX}, {self.mouseAttackY})")
        
    def print_current_position(self):
        x, y = pyautogui.position()
        print(f"🖱️ Posição atual do mouse: ({x}, {y})")
        pyautogui.press('capslock')
        
    def stop_all_actions(self):
        self.holding = False
        self.autoClickOn = False
        pyautogui.mouseUp(button='right')
        pyautogui.mouseUp(button='left')
        pyautogui.keyUp('alt')
        print("🛑 TODAS AS AÇÕES FORAM PARADAS!")
        
    def start(self):
        """Inicia o bot"""
        print("🎮 Dark Eden Bot iniciado!")
        print("=" * 50)
        
        # Mostrar hotkeys disponíveis
        self.hotkey_manager.list_hotkeys()
        
        print("\n📋 INSTRUÇÕES:")
        print("1. Posicione o mouse onde quer atacar")
        print("2. Pressione Alt+1 para salvar a posição")
        print("3. Use F5 para ataque básico ou \\ para combo mago")
        print("4. Pressione F2 para sair")
        print("\n▶️ Bot ativo! Aguardando hotkeys...")
        
        # Iniciar listener
        self.hotkey_manager.start_listener()
        
        try:
            # Aguardar F2 para sair
            import keyboard
            keyboard.wait('f2')
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all_actions()
            self.hotkey_manager.stop_listener()
            print("👋 Bot finalizado!")

if __name__ == "__main__":
    bot = DarkEdenBot()
    bot.start()