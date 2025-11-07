"""
Dark Eden Bot - Sistema Automatizado
Combina leitura de memória com ações automáticas
Baseado em memory_viewer_gui.py e dk.py
"""

import sys
import os
import time
import threading
import pyautogui
import json
import importlib.util
import ctypes
import ctypes.wintypes
from datetime import datetime

# Importar a classe MemoryReader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("read_memory", "read-memory.py")
read_memory_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(read_memory_module)
MemoryReader = read_memory_module.MemoryReader


class DarkEdenBot:
    """Bot automatizado para Dark Eden"""
    
    def __init__(self):
        # Leitor de memória
        self.memory_reader = MemoryReader()
        self.process_base_address = 0
        
        # Valores de memória
        self.memory_values = {
            'hp': 0,
            'hp_max': 0,
            'x': 0,
            'y': 0,
            'mana': 0,
            'mana_max': 0,
            'map': '',
            'monster_count': 0
        }
        
        # Endereços para monitorar (carregados do JSON)
        self.addresses = {}
        
        # Configurações do bot
        self.config = {
            'hp_min_percent': 30,  # % mínimo de HP para continuar atacando
            'mana_min_percent': 20,  # % mínimo de Mana
            'attack_interval': 1.0,  # Segundos entre ataques
            'memory_read_interval': 1.0,  # Segundos entre leituras de memória
            'auto_heal': False,  # Usar poção automaticamente (DESABILITADO)
            'auto_attack': False,  # Atacar automaticamente (DESABILITADO)
            'auto_move': False,  # Mover automaticamente quando não tem monstros
        }
        
        # Estado do bot
        self.running = False
        self.paused = False
        
        # Posições do mouse (como no dk.py)
        self.mouseAttackX = 0
        self.mouseAttackY = 0
        
        # Arrays para skills (como bloodwalls no dk.py)
        self.bloodwalls = [0, 25, -25]
        
    def log(self, message):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def load_addresses(self, filename="memory_addresses.json"):
        """Carrega endereços salvos do JSON"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if 'addresses' in data:
                    for addr_info in data['addresses']:
                        desc = addr_info.get('description', '').lower()
                        self.addresses[desc] = {
                            'address': addr_info['address'],
                            'type': addr_info['type'],
                            'length': addr_info.get('length', 4)
                        }
                    
                    self.log(f"✅ {len(self.addresses)} endereços carregados de {filename}")
                    return True
            else:
                self.log(f"⚠️ Arquivo {filename} não encontrado")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao carregar endereços: {e}")
            return False
            
    def connect_to_game(self, process_name="DarkEden.exe"):
        """Conecta ao processo do jogo"""
        try:
            if self.memory_reader.find_process_by_name(process_name):
                self.log(f"✅ Conectado ao processo: {process_name}")
                
                # Obter endereço base
                self.process_base_address = self.get_process_base_address(
                    self.memory_reader.pid
                )
                
                if self.process_base_address:
                    self.log(f"📍 Endereço base: 0x{self.process_base_address:08X}")
                    return True
                else:
                    self.log("⚠️ Não foi possível obter endereço base")
                    return True  # Continua mesmo assim
            else:
                self.log(f"❌ Processo {process_name} não encontrado!")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao conectar: {e}")
            return False
            
    def get_process_base_address(self, pid):
        """Obtém endereço base do processo (copiado de memory_viewer_gui.py)"""
        try:
            import ctypes
            import ctypes.wintypes
            
            INVALID_HANDLE_VALUE = -1
            TH32CS_SNAPMODULE = 0x00000008
            TH32CS_SNAPMODULE32 = 0x00000010
            
            class MODULEENTRY32(ctypes.Structure):
                _fields_ = [
                    ("dwSize", ctypes.wintypes.DWORD),
                    ("th32ModuleID", ctypes.wintypes.DWORD),
                    ("th32ProcessID", ctypes.wintypes.DWORD),
                    ("GlblcntUsage", ctypes.wintypes.DWORD),
                    ("ProccntUsage", ctypes.wintypes.DWORD),
                    ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
                    ("modBaseSize", ctypes.wintypes.DWORD),
                    ("hModule", ctypes.wintypes.HMODULE),
                    ("szModule", ctypes.c_char * 256),
                    ("szExePath", ctypes.c_char * 260),
                ]
            
            kernel32 = ctypes.windll.kernel32
            snapshot = kernel32.CreateToolhelp32Snapshot(
                TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid
            )
            
            if snapshot == INVALID_HANDLE_VALUE:
                return None
            
            try:
                module_entry = MODULEENTRY32()
                module_entry.dwSize = ctypes.sizeof(MODULEENTRY32)
                
                if kernel32.Module32First(snapshot, ctypes.byref(module_entry)):
                    base_addr = ctypes.cast(module_entry.modBaseAddr, ctypes.c_void_p).value
                    return base_addr
                    
            finally:
                kernel32.CloseHandle(snapshot)
                
        except Exception as e:
            self.log(f"❌ Erro ao obter endereço base: {e}")
            
        return None
        
    def parse_address(self, address_str):
        """Converte string de endereço para absoluto (baseado em memory_viewer_gui.py)"""
        address_str = address_str.strip()
        
        # Formato: base+0x1234
        if address_str.lower().startswith('base+'):
            if not self.process_base_address:
                raise ValueError("Endereço base não disponível!")
                
            offset_str = address_str[5:]
            if offset_str.lower().startswith('0x'):
                offset = int(offset_str, 16)
            else:
                offset = int(offset_str, 16)
                
            return self.process_base_address + offset
            
        # Formato: DarkEden.exe+0x1234 ou darkeden.exe+0x1234
        elif '+' in address_str:
            parts = address_str.split('+')
            if len(parts) == 2:
                module_name = parts[0].strip()
                offset_str = parts[1].strip()
                
                # Usar base do processo principal
                if not self.process_base_address:
                    raise ValueError("Endereço base não disponível!")
                
                if offset_str.lower().startswith('0x'):
                    offset = int(offset_str, 16)
                else:
                    offset = int(offset_str, 16)
                    
                return self.process_base_address + offset
                
        # Formato: 0x12345678
        elif address_str.lower().startswith('0x'):
            return int(address_str, 16)
        else:
            # Tentar como hex sem prefixo
            try:
                return int(address_str, 16)
            except:
                raise ValueError(f"Formato de endereço inválido: {address_str}")
            
    def read_memory_values(self):
        """Lê todos os valores de memória mapeados"""
        try:
            for key, addr_info in self.addresses.items():
                try:
                    # Parse do endereço
                    address = self.parse_address(addr_info['address'])
                    data_type = addr_info['type']
                    
                    # Ler valor
                    if data_type == 'string':
                        length = addr_info.get('length', 20)
                        value = self.memory_reader.read_string(address, length)
                    else:
                        value = self.memory_reader.read_memory(address, data_type)
                    
                    # Mapear para valores conhecidos (case insensitive)
                    key_lower = key.lower()
                    
                    if 'hp' in key_lower and 'max' in key_lower:
                        self.memory_values['hp_max'] = value
                    elif 'hp' in key_lower:
                        self.memory_values['hp'] = value
                    elif 'x' == key_lower or 'pos x' in key_lower or 'posição x' in key_lower:
                        self.memory_values['x'] = value
                    elif 'y' == key_lower or 'pos y' in key_lower or 'posição y' in key_lower:
                        self.memory_values['y'] = value
                    elif 'mana' in key_lower and 'max' in key_lower:
                        self.memory_values['mana_max'] = value
                    elif 'mana' in key_lower or 'mp' in key_lower:
                        self.memory_values['mana'] = value
                    elif 'map' in key_lower or 'mapa' in key_lower:
                        self.memory_values['map'] = value if isinstance(value, str) else str(value)
                    elif 'monster' in key_lower or 'mob' in key_lower:
                        self.memory_values['monster_count'] = value
                        
                except Exception as e:
                    # Log erro mas continua tentando ler outros endereços
                    if hasattr(self, 'debug_mode') and self.debug_mode:
                        self.log(f"⚠️ Erro ao ler '{key}': {e}")
                    pass
                    
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao ler memória: {e}")
            return False
            
    def get_hp_percent(self):
        """Calcula % de HP atual"""
        if self.memory_values['hp_max'] > 0:
            return (self.memory_values['hp'] / self.memory_values['hp_max']) * 100
        return 100
        
    def get_mana_percent(self):
        """Calcula % de Mana atual"""
        if self.memory_values['mana_max'] > 0:
            return (self.memory_values['mana'] / self.memory_values['mana_max']) * 100
        return 100
        
    # ========== AÇÕES (baseadas em dk.py) ==========
    
    def set_attack_position(self, x=None, y=None):
        """Define posição de ataque"""
        if x is None or y is None:
            self.mouseAttackX = pyautogui.position().x
            self.mouseAttackY = pyautogui.position().y
        else:
            self.mouseAttackX = x
            self.mouseAttackY = y
            
        self.log(f"📍 Posição de ataque: ({self.mouseAttackX}, {self.mouseAttackY})")
        
    def attack_combo_mage(self):
        """Combo de ataque do mago (bloodwall + meteor)"""
        if self.mouseAttackX == 0 or self.mouseAttackY == 0:
            self.log("⚠️ Posição de ataque não definida!")
            return
            
        try:
            # Pressionar F12 (bloodwall hotkey)
            pyautogui.press('f12')
            time.sleep(0.5)
            
            # Executar bloodwalls em diferentes posições
            for wall in self.bloodwalls:
                pyautogui.keyDown('alt')
                pyautogui.rightClick(self.mouseAttackX, self.mouseAttackY + wall)
                pyautogui.keyUp('alt')
                
                if wall != self.bloodwalls[-1]:
                    time.sleep(2)
                    
            # Atacar continuamente com F9
            pyautogui.moveTo(self.mouseAttackX, self.mouseAttackY)
            pyautogui.press('f9')
            pyautogui.keyDown('alt')
            pyautogui.click(button='right')
            pyautogui.keyUp('alt')
            
            self.log("⚔️ Combo de ataque executado")
            
        except Exception as e:
            self.log(f"❌ Erro no ataque: {e}")
            
    def attack_simple(self):
        """Ataque simples (right click + alt)"""
        if self.mouseAttackX == 0 or self.mouseAttackY == 0:
            return
            
        try:
            pyautogui.moveTo(self.mouseAttackX, self.mouseAttackY)
            pyautogui.keyDown('alt')
            pyautogui.click(button='right')
            pyautogui.keyUp('alt')
            
        except Exception as e:
            self.log(f"❌ Erro no ataque: {e}")
            
    def move_direction(self, direction):
        """Move em uma direção usando rapid gliding (F7)"""
        if self.mouseAttackX == 0 or self.mouseAttackY == 0:
            return
            
        offsets = {
            'right': (250, 0),
            'left': (-250, 0),
            'up': (0, -130),
            'down': (0, 130)
        }
        
        if direction not in offsets:
            return
            
        try:
            offset_x, offset_y = offsets[direction]
            
            pyautogui.press('f7')  # Rapid gliding
            time.sleep(0.5)
            pyautogui.keyDown('alt')
            pyautogui.rightClick(
                self.mouseAttackX + offset_x,
                self.mouseAttackY + offset_y
            )
            pyautogui.keyUp('alt')
            
            self.log(f"🏃 Movimento: {direction}")
            
        except Exception as e:
            self.log(f"❌ Erro no movimento: {e}")
            
    def use_healing_potion(self):
        """Usa poção de cura (pressiona a tecla configurada)"""
        try:
            pyautogui.press('f6')  # Ajuste para sua tecla de poção
            self.log("💊 Usando poção de cura")
        except Exception as e:
            self.log(f"❌ Erro ao usar poção: {e}")
            
    # ========== VALIDAÇÕES E LÓGICA DO BOT ==========
    
    def should_heal(self):
        """Verifica se precisa curar"""
        return self.get_hp_percent() < self.config['hp_min_percent']
        
    def should_attack(self):
        """Verifica se deve atacar"""
        hp_ok = self.get_hp_percent() > self.config['hp_min_percent']
        mana_ok = self.get_mana_percent() > self.config['mana_min_percent']
        # Pode adicionar verificação de monstros: has_monsters = self.memory_values['monster_count'] > 0
        
        return hp_ok and mana_ok
        
    def should_move(self):
        """Verifica se deve mover"""
        # Implementar lógica: ex. não tem monstros próximos
        return False  # Por enquanto desabilitado
        
    # ========== LOOP PRINCIPAL ==========
    
    def main_loop(self):
        """Loop principal do bot"""
        self.log("🤖 Iniciando monitoramento de memória...")
        self.log(f"⚙️ Configurações:")
        self.log(f"   Intervalo de leitura: {self.config['memory_read_interval']}s")
        self.log(f"   Auto-heal: {self.config['auto_heal']}")
        self.log(f"   Auto-attack: {self.config['auto_attack']}")
        self.log("")
        self.log("=" * 80)
        
        last_attack_time = 0
        last_memory_read = 0
        
        while self.running:
            try:
                if self.paused:
                    time.sleep(0.5)
                    continue
                
                current_time = time.time()
                
                # Ler memória periodicamente
                if current_time - last_memory_read >= self.config['memory_read_interval']:
                    self.read_memory_values()
                    last_memory_read = current_time
                    
                    # Log de status formatado
                    hp = self.memory_values['hp']
                    hp_max = self.memory_values['hp_max']
                    hp_pct = self.get_hp_percent()
                    
                    mana = self.memory_values.get('mana', 0)
                    mana_max = self.memory_values.get('mana_max', 0)
                    mana_pct = self.get_mana_percent()
                    
                    x = self.memory_values['x']
                    y = self.memory_values['y']
                    mapa = self.memory_values['map']
                    
                    # Exibir informações formatadas
                    self.log(f"HP: {hp_pct:6.1f}% ({hp}/{hp_max}) | Mana: {mana_pct:6.1f}% | Pos: ({x}, {y}) | Mapa: {mapa}")
                
                # APENAS MONITORAR - Não executar ações automáticas
                # As validações abaixo só executam se as flags estiverem True
                
                # Validação 1: Precisa curar? (DESABILITADO por padrão)
                if self.config['auto_heal'] and self.should_heal():
                    self.log("⚠️ HP baixo! Curando...")
                    self.use_healing_potion()
                    time.sleep(2)  # Aguardar poção
                    continue
                
                # Validação 2: Pode atacar? (DESABILITADO por padrão)
                if self.config['auto_attack'] and self.should_attack():
                    if current_time - last_attack_time >= self.config['attack_interval']:
                        self.attack_simple()
                        last_attack_time = current_time
                
                # Validação 3: Precisa mover? (DESABILITADO por padrão)
                if self.config['auto_move'] and self.should_move():
                    self.move_direction('right')
                    time.sleep(1)
                
                # Sleep pequeno para não sobrecarregar CPU
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                self.log("⚠️ Interrompido pelo usuário")
                break
            except Exception as e:
                self.log(f"❌ Erro no loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)
                
        self.log("🛑 Bot parado")
        
    def start(self):
        """Inicia o bot"""
        if self.running:
            self.log("⚠️ Bot já está rodando!")
            return
            
        self.running = True
        
        # Iniciar loop em thread separada
        bot_thread = threading.Thread(target=self.main_loop)
        bot_thread.daemon = True
        bot_thread.start()
        
    def stop(self):
        """Para o bot"""
        self.log("🛑 Parando bot...")
        self.running = False
        
    def pause(self):
        """Pausa o bot"""
        self.paused = not self.paused
        status = "pausado" if self.paused else "resumido"
        self.log(f"⏸️ Bot {status}")


# ========== EXECUÇÃO PRINCIPAL ==========

if __name__ == "__main__":
    print("=" * 60)
    print("🎮 DARK EDEN BOT - Monitor de Memória")
    print("=" * 60)
    print()
    
    # Criar instância do bot
    bot = DarkEdenBot()
    
    # Carregar endereços do JSON
    if not bot.load_addresses("memory_addresses.json"):
        print("⚠️ Continuando sem endereços carregados...")
    
    # Conectar ao jogo
    if not bot.connect_to_game("DarkEden.exe"):
        print("❌ Não foi possível conectar ao jogo!")
        print("💡 Certifique-se que o jogo está rodando")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("🔍 MODO: MONITORAMENTO APENAS (sem ações automáticas)")
    print("=" * 60)
    print()
    print("⌨️ CONTROLES:")
    print("   P - Pausar/Retomar monitoramento")
    print("   Q - Parar e sair")
    print()
    print("💡 Para habilitar ações automáticas, edite bot.config")
    print()
    
    # Iniciar bot
    bot.start()
    
    # Loop de controle por teclado
    try:
        import keyboard
        
        while bot.running:
            if keyboard.is_pressed('p'):
                bot.pause()
                time.sleep(0.5)  # Debounce
                
            if keyboard.is_pressed('q'):
                bot.stop()
                break
                
            time.sleep(0.1)
            
    except ImportError:
        # Se não tiver biblioteca keyboard, só manter rodando
        print("💡 Biblioteca 'keyboard' não encontrada")
        print("   Pressione Ctrl+C para parar")
        
        try:
            while bot.running:
                time.sleep(1)
        except KeyboardInterrupt:
            bot.stop()
    
    print()
    print("=" * 60)
    print("👋 Bot finalizado. Até logo!")
    print("=" * 60)
