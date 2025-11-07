import keyboard
import threading
import time
import pyautogui
import os
import random
import sys
import ctypes
import ctypes.wintypes
import psutil
import struct
import json

# Importar MemoryReader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("read_memory", "read-memory.py")
read_memory_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(read_memory_module)
MemoryReader = read_memory_module.MemoryReader

holding = False
autoClickOn = False
mouseAttackX = 0
mouseAttackY = 0
mouseAntesX = 0
mouseAntesY = 0
posAntesX = 0
posAntesY = 0
lootMouseX = 1262
lootMouseY = 194
hotkeyHoldRight = 'f4'
hotkeyAttack = 'f3'
hotkeySalvar = 'alt+1'
hotkeyBloodyWall = 'f12'
hotkeyMeteoroNoose = 'f5'
hotkeyMoveRight = 'right'
hotkeyMoveLeft = 'left'
hotkeyMoveUp = 'up'
hotkeyMoveDown = 'down'
hotkeyViolentPhatom = '';
hotkeyLoot = '\\'

opcoes = [1, 2, 3, 4]
bloodwalls = [0 , 25 , -25]

# === VARIÁVEIS PARA MONITORAMENTO DE MEMÓRIA ===
memory_reader = None
process_base_address = 0
monitored_addresses = {}
memory_values = {}  # Valores atuais da memória (acessível por descrição)
monitoring_active = False
monitoring_thread = None
addresses_file = "memory_addresses.json" 

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

def lootGround():
    saveCurrentMousePosition()
    pyautogui.keyDown('alt')
    time.sleep(0.1)
    pyautogui.leftClick(lootMouseX, lootMouseY)
    pyautogui.keyUp('alt')
    pyautogui.press('backspace')
    pyautogui.moveTo(mouseAntesX, mouseAntesY)
def debug():
    print("isDead" , isDead())
    print("amIinPerona" , amIinPerona())

def move():
    global autoClickOn


    # Obter posição atual da memória ANTES de tentar mover
    pos_x_antes = get_memory_value("X")
    pos_y_antes = get_memory_value("Y")
    
    print("Movendo...")
    
    # === VERIFICAR LIMITES DO MAPA ===
    opcoes_disponiveis = []
    
    # Verificar se pode ir para DIREITA (1)
    if pos_x_antes is None or pos_x_antes <= 110:
        opcoes_disponiveis.append(1)
    else:
        print("⚠️ Limite direito atingido! X = " + str(pos_x_antes))
    
    # Verificar se pode ir para ESQUERDA (2)
    if pos_x_antes is None or pos_x_antes >= 20:
        opcoes_disponiveis.append(2)
    else:
        print("⚠️ Limite esquerdo atingido! X = " + str(pos_x_antes))
    
    # Verificar se pode ir para CIMA (3)
    if pos_y_antes is None or pos_y_antes >= 20:
        opcoes_disponiveis.append(3)
    else:
        print("⚠️ Limite superior atingido! Y = " + str(pos_y_antes))
    
    # Verificar se pode ir para BAIXO (4)
    if pos_y_antes is None or pos_y_antes <= 230:
        opcoes_disponiveis.append(4)
    else:
        print("⚠️ Limite inferior atingido! Y = " + str(pos_y_antes))
    
    # Se não houver opções disponíveis, não mover
    if not opcoes_disponiveis:
        print("❌ Sem opções de movimento disponíveis! Personagem pode estar preso.")
        return
    
    # Definir quantas vezes mover para cada direção
    repeticoes = {
        1: 3,  # Direita: 3 vezes
        2: 3,  # Esquerda: 3 vezes
        3: 4,  # Cima: 4 vezes
        4: 4   # Baixo: 4 vezes
    }
    
    # Definir qual função chamar para cada escolha
    movimentos = {
        1: moveRight,
        2: moveLeft,
        3: moveUp,
        4: moveDown
    }
    
    # Nomes das direções
    nomes_direcoes = {
        1: "➡️ Direita",
        2: "⬅️ Esquerda",
        3: "⬆️ Cima",
        4: "⬇️ Baixo"
    }
    
    # === SISTEMA DE TENTATIVAS ===
    tentativas = 0
    max_tentativas = 10
    movimento_sucesso = False
    
    while tentativas < max_tentativas and autoClickOn and not movimento_sucesso:
        # Escolher direção
        escolha = random.choice(opcoes_disponiveis)
        funcao_movimento = movimentos[escolha]
        quantidade = repeticoes[escolha]
        direcao = nomes_direcoes[escolha]
        
        if tentativas == 0:
            print(f"📍 Posição antes: X={pos_x_antes}, Y={pos_y_antes}")
            print(f"Movendo para {direcao} por {quantidade} vezes.")
        else:
            print(f"🔄 Tentativa {tentativas + 1}/{max_tentativas}: Movendo para {direcao}")

            
        pos_x_antes = get_memory_value("X")
        pos_y_antes = get_memory_value("Y")
        # === EXECUTAR MOVIMENTO ===
        for i in range(quantidade):
            if autoClickOn:
                funcao_movimento()
                time.sleep(0.2)
        
        # === AGUARDAR ESTABILIZAÇÃO ===
        time.sleep(1)
        
        # === VERIFICAR SE MOVEU ===
        pos_x_depois = get_memory_value("X")
        pos_y_depois = get_memory_value("Y")
        
        print(f"📍 Posição depois: X={pos_x_depois}, Y={pos_y_depois}")
        
        # Verificar se a posição mudou
        if pos_x_antes is not None and pos_y_antes is not None and \
           pos_x_depois is not None and pos_y_depois is not None:
            
            # Calcular diferença
            diferenca_x = abs(pos_x_depois - pos_x_antes)
            diferenca_y = abs(pos_y_depois - pos_y_antes)
            
            # Se moveu (diferença >= 2 pixels)
            if diferenca_x >= 2 or diferenca_y >= 2:
                print(f"✅ Movimento confirmado! Δx={diferenca_x}, Δy={diferenca_y}")
                movimento_sucesso = True
            else:
                print("⚠️ PERSONAGEM NÃO SE MOVEU!")
                
                # Remover direção que falhou
                if escolha in opcoes_disponiveis:
                    opcoes_disponiveis.remove(escolha)
                
                # Se não tem mais opções
                if not opcoes_disponiveis:
                    print("❌ Sem mais opções! Voltando para Beginners...")
                    break
                
                # Incrementar tentativas
                tentativas += 1
        else:
            print("⚠️ Não foi possível verificar movimento (valores None)")
            tentativas += 1
    
    # Se esgotou tentativas sem sucesso
    if not movimento_sucesso and tentativas >= max_tentativas:
        print("❌ Personagem PRESO após 3 tentativas! Voltando para Beginners...")
        

def attack():
    global autoClickOn
    tempo_maximo = 40  # segundos
    tempo_inicio = time.time()
    print("Iniciando ataque por até " + str(tempo_maximo) + " segundos...")
    pyautogui.moveTo(mouseAttackX, mouseAttackY)
    pyautogui.keyDown('alt')  # Pressiona e mantém Alt no início
    
    while autoClickOn:
        # Calcular tempo decorrido
        tempo_decorrido = time.time() - tempo_inicio
        
        # Verificar se já passou o tempo máximo
        if tempo_decorrido >= tempo_maximo:
            print(f"⏱️ Tempo limite de {tempo_maximo}s atingido!")
            break
        
        pyautogui.press('f11')
        #pyautogui.mouseDown(button='right')
        pyautogui.click(button='right')  # Clica e solta automaticamente
        time.sleep(1)  # Small sleep to reduce CPU usage
    
    pyautogui.keyUp('alt')  # Solta Alt quando para

def init_bot():
    global autoClickOn

    while autoClickOn:
        if autoClickOn:
            checks()
            attack()
        if autoClickOn:    
            checks()
            move()

def checks():
    if isDead():
        print("O personagem está morto.")
        Dead()
    if amIinPerona():
        print("O personagem está em Perona.")
        backToBeginners()


def Dead():
    time.sleep(7)
    pyautogui.leftClick(272, 850)
    time.sleep(3)

def hold_right_click():
    global holding

    pyautogui.keyDown('alt')  # Pressiona e mantém Ctrl
    
    while holding:
        pyautogui.mouseDown(button='right')
        time.sleep(0.1)  # Small sleep to reduce CPU usage
    
    pyautogui.keyUp('alt')  # Solta Alt quando para  
def backToBeginners():
    pyautogui.keyDown('ctrlright') 
    pyautogui.leftClick(793, 233)
    time.sleep(0.5)
    pyautogui.keyUp('ctrlright')
    pyautogui.leftClick(540, 559)
    time.sleep(0.5)
    pyautogui.leftClick(597, 635)
    time.sleep(1.5)
    for i in range(6):
        moveInicioBegginers()
        time.sleep(0.2)

def isDead():
    if get_memory_value("HP") is not None:
        return get_memory_value("HP") <= 0

def amIinPerona():
    if get_memory_value("Mapa") is not None:
        mapa = get_memory_value("Mapa")
        if "Perona" in str(mapa):
            return True
    return False

def Mage_hold_right_click():
    global autoClickOn

    pyautogui.moveTo(mouseAttackX, mouseAttackY)
    pyautogui.keyDown('alt')  # Pressiona e mantém Alt no início
    
    while autoClickOn:
        pyautogui.press('f11')
        #pyautogui.mouseDown(button='right')
        pyautogui.click(button='right')  # Clica e solta automaticamente
        time.sleep(1)  # Small sleep to reduce CPU usage
    
    pyautogui.keyUp('alt')  # Solta Alt quando para        
                

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
        print("\n\n\n\n\nParando de atacar")
        os.system('cls')
        #pyautogui.mouseUp(button='right')
         
  
   
        
def autoClickRunning():
    global autoClickOn
    global mouseAttackX
    global mouseAttackY
    global mouseAntesX
    global mouseAntesY
    
    if mouseAttackValidation():
        saveCurrentMousePosition()       
        pyautogui.moveTo(mouseAttackX, mouseAttackY)
        threading.Thread(target=init_bot).start()
            
        
    else:
        autoClickOn = False
        print("Pressione a tecla: " + hotkeySalvar + " para setar uma posição inicial");    

def set_mouse_attack():
    global mouseAttackX
    global mouseAttackY
    pyautogui.press('backspace')
    mouseAttackX = pyautogui.position().x
    mouseAttackY = pyautogui.position().y
    print("Posição salva com sucesso")

def moveInicioBegginers():
    offset = 120
    global mouseAttackX
    global mouseAttackY
    print("Movendo inicio beginners...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX + offset, mouseAttackY + offset)
    pyautogui.keyUp('alt')  # Solta Alt quando para  

def moveRight():
    offset = 250
    global mouseAttackX
    global mouseAttackY
    print("Movendo para a direita...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX + offset, mouseAttackY)
    pyautogui.keyUp('alt')  # Solta Alt quando para  

def moveLeft():
    offset = -250
    global mouseAttackX
    global mouseAttackY
    print("Movendo para a esquerda...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX + offset, mouseAttackY)
    pyautogui.keyUp('alt')  # Solta Alt quando para  

def moveUp():
    offset = -130
    global mouseAttackX
    global mouseAttackY
    print("Movendo para cima...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX , mouseAttackY + offset)
    pyautogui.keyUp('alt')  # Solta Alt quando para  

def moveDown():
    offset = 130
    global mouseAttackX
    global mouseAttackY
    print("Movendo para baixo...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX , mouseAttackY + offset)
    pyautogui.keyUp('alt')  # Solta Alt quando para

def printar_pos():
    print(pyautogui.position())    
    pyautogui.press('capslock')
def sleep_ms(milliseconds):
    time.sleep(milliseconds / 1000.0)

def background_task():
    while True:
        # Your background task code here
        time.sleep(1)

# === FUNÇÕES DE MONITORAMENTO DE MEMÓRIA ===

def init_memory_reader():
    """Inicializa o leitor de memória conectando ao processo Dark Eden"""
    global memory_reader, process_base_address
    
    # Procurar processo darkeden.exe
    target_process = None
    for proc in psutil.process_iter(['pid', 'name']):
        if 'darkeden' in proc.info['name'].lower():
            target_process = proc
            break
    
    if not target_process:
        print("Processo Dark Eden não encontrado!")
        return False
    
    try:
        # Inicializar MemoryReader corretamente
        memory_reader = MemoryReader()
        if not memory_reader.find_process_by_pid(target_process.info['pid']):
            return False
        if not memory_reader.open_process():
            return False
        
        process_base_address = get_process_base_address(target_process.info['pid'], target_process.info['name'])
        print(f"✅ Conectado ao processo: {target_process.info['name']} (PID: {target_process.info['pid']})")
        print(f"Base address: 0x{process_base_address:X}")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar ao processo: {e}")
        return False

def get_process_base_address(pid, process_name):
    """Obtém o endereço base do módulo principal do processo"""
    try:
        import pymem
        pm = pymem.Pymem()
        pm.open_process_from_id(pid)
        
        for module in pm.list_modules():
            if process_name.lower() in module.name.lower():
                return module.lpBaseOfDll
        
        return 0
    except Exception as e:
        print(f"Erro ao obter base address: {e}")
        return 0

def parse_address(address_str):
    """
    Converte string de endereço para endereço absoluto
    Formatos suportados:
    - 0x18F304D1 (hexadecimal absoluto)
    - base+0x1234 (base + offset)
    - darkeden.exe+357778 (módulo + offset decimal)
    - darkeden.exe+2FB1CC (módulo + offset hex sem 0x)
    """
    address_str = address_str.strip()
    
    # Formato hexadecimal direto
    if address_str.startswith('0x'):
        return int(address_str, 16)
    
    # Formato base+offset
    if address_str.lower().startswith('base+'):
        offset_str = address_str[5:]
        offset = int(offset_str, 16) if offset_str.startswith('0x') else int(offset_str)
        return process_base_address + offset
    
    # Formato módulo+offset
    if '+' in address_str:
        module_name, offset_str = address_str.split('+')
        
        # Tentar converter o offset
        if offset_str.startswith('0x'):
            offset = int(offset_str, 16)
        else:
            # Tentar hex primeiro (sem 0x), depois decimal
            try:
                offset = int(offset_str, 16)
            except ValueError:
                offset = int(offset_str, 10)
        
        return process_base_address + offset
    
    # Número decimal direto
    return int(address_str)

def load_addresses():
    """Carrega endereços do arquivo JSON"""
    global monitored_addresses
    
    if not os.path.exists(addresses_file):
        print(f"❌ Arquivo {addresses_file} não encontrado!")
        return False
    
    try:
        with open(addresses_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # O JSON tem estrutura: {"addresses": [...], "timestamp": "...", "version": "..."}
        addresses_list = data.get('addresses', [])
        
        if not addresses_list:
            print(f"⚠️ Nenhum endereço encontrado no arquivo {addresses_file}")
            return False
            
        monitored_addresses = {}
        for item in addresses_list:
            address_str = item.get('address_str', '')
            data_type = item.get('data_type', 'int32')  # Atenção: é 'data_type' não 'type'
            description = item.get('description', 'Sem descrição')
            
            if address_str:  # Só adiciona se tiver endereço válido
                monitored_addresses[description] = {
                    'address_str': address_str,
                    'address': parse_address(address_str),
                    'type': data_type
                }
        
        print(f"✅ Carregados {len(monitored_addresses)} endereços de memória")
        for desc, info in monitored_addresses.items():
            print(f"   - {desc}: {info['address_str']} ({info['type']})")
        return True
    except Exception as e:
        print(f"❌ Erro ao carregar endereços: {e}")
        import traceback
        traceback.print_exc()
        return False

def read_value_by_type(address, data_type):
    """Lê valor da memória com base no tipo de dado - usando nomes corretos do MemoryReader"""
    if not memory_reader:
        return None
    
    try:
        if data_type == 'int32':
            return memory_reader.read_int32(address)
        elif data_type == 'uint32':
            return memory_reader.read_uint32(address)
        elif data_type == 'float':
            return memory_reader.read_float(address)
        elif data_type == 'double':
            return memory_reader.read_double(address)
        elif data_type == 'int16':
            return memory_reader.read_int16(address)
        elif data_type == 'uint16':
            return memory_reader.read_uint16(address)
        elif data_type == 'int8' or data_type == 'byte':
            return memory_reader.read_int8(address)
        elif data_type == 'uint8':
            return memory_reader.read_uint8(address)
        elif data_type == 'string':
            # Ler string com tamanho padrão de 50 bytes
            return memory_reader.read_string(address, 50)
        else:
            # Default: int32
            return memory_reader.read_int32(address)
    except Exception as e:
        print(f"⚠️ Erro ao ler endereço 0x{address:08X} ({data_type}): {e}")
        return None

def monitoring_loop():
    """Loop de monitoramento contínuo dos valores na memória"""
    global memory_values
    
    while monitoring_active:
        for description, info in monitored_addresses.items():
            address = info['address']
            data_type = info['type']
            value = read_value_by_type(address, data_type)
            memory_values[description] = value
        
        time.sleep(0.5)  # Atualiza a cada 100ms

def show_memory_values():
    """Exibe os valores atuais da memória (acionado por F6)"""
    if not memory_values:
        print("Nenhum valor de memória disponível. Ative o monitoramento com F7.")
        return
    
    print("\n=== VALORES DE MEMÓRIA ===")
    for description, value in memory_values.items():
        info = monitored_addresses.get(description, {})
        address_str = info.get('address_str', 'N/A')
        print(f"{description}: {value} (Endereço: {address_str})")
    print("========================\n")

def toggle_memory_monitoring():
    """Ativa/desativa o monitoramento de memória (acionado por F7)"""
    global monitoring_active, monitoring_thread
    
    if not memory_reader:
        print("Inicializando leitor de memória...")
        if not init_memory_reader():
            return
        load_addresses()
    
    monitoring_active = not monitoring_active
    
    if monitoring_active:
        print("Monitoramento de memória ATIVADO")
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
    else:
        print("Monitoramento de memória DESATIVADO")

def get_memory_value(description):
    """
    Retorna o valor atual de um endereço de memória pela descrição
    Exemplo: hp_atual = get_memory_value("HP")
    """
    return memory_values.get(description, None)

# === FUNÇÕES EXISTENTES ===
if __name__ == "__main__":
    # Start the background task in a separate thread
    background_thread = threading.Thread(target=background_task)
    background_thread.daemon = True  # This ensures the thread exits when the main program exits
    background_thread.start()

    # Set up the hotkey
    keyboard.add_hotkey(hotkeyHoldRight, toggle_right_click)
    keyboard.add_hotkey(hotkeySalvar, set_mouse_attack)  
    keyboard.add_hotkey(hotkeyAttack, autoClickToggle)
    keyboard.add_hotkey(hotkeyLoot, debug)
    
    # === HOTKEYS DE MONITORAMENTO DE MEMÓRIA ===
    keyboard.add_hotkey('f6', show_memory_values)
    keyboard.add_hotkey('f7', toggle_memory_monitoring)
    
    print("Tecla para atacar mouse direito (Segurar): " + hotkeyHoldRight)
    print("Tecla para combo mago: " + hotkeyAttack + " NECESSÁRIO MARCAR POSIÇÃO EM BAIXO DO CHAR")
    print("Tecla para setar posição: " + hotkeySalvar)
    print("\n=== MONITORAMENTO DE MEMÓRIA ===")
    print("F6: Mostrar valores de memória")
    print("F7: Ativar/Desativar monitoramento")
    print("================================\n")
    
    # Keep the main thread alive to listen for the hotkey
    keyboard.wait('f2')  # Change 'esc' to your desired exit key