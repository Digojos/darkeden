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
#char auxiliar pra sc deve ficar em perona NE x = 37, y = 124
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

# === HOTKEYS DE MONITORAMENTO DE MEMÓRIA ===
hotkeyShowMemory = 'ctrl+alt+m'          # Mostrar valores de memória
hotkeyToggleMonitoring = 'ctrl+alt+t'    # Ativar/Desativar monitoramento
hotkeyDebugXY = 'ctrl+alt+d'             # Debug detalhado X/Y
hotkeyReconnectProcess = 'ctrl+alt+r'    # Reconectar a outro processo

opcoes = [1, 2, 3, 4]
bloodwalls = [0 , 25 , -25]
franz = dict([("25,138","844,246"),("24,138","891,246")])
# === VARIÁVEIS PARA MONITORAMENTO DE MEMÓRIA ===
memory_reader = None
process_base_address = 0
monitored_addresses = {}
memory_values = {}  # Valores atuais da memória (acessível por descrição)
monitoring_active = False
monitoring_thread = None
addresses_file = "memory_addresses.json"

# === VARIÁVEL PARA CONTROLE DE MOVIMENTO ===
ultimo_movimento = None  # Guarda o último movimento bem-sucedido para evitar vai-e-volta 

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
    x, y = pyautogui.position()
    print(f"Mouse position:\n\n\n\n\n\n ({x}, {y})")
    # currentPlayerX = get_memory_value("X")
    # currentPlayerY = get_memory_value("Y")
    # key = f"{currentPlayerX},{currentPlayerY}"
    # valor = franz.get(key)
    # print("chave: ", key)

def move(): 
    global autoClickOn
    global ultimo_movimento

    # Obter posição atual da memória ANTES de tentar mover
    pos_x_ante = get_memory_value("X")
    pos_y_ante = get_memory_value("Y")
    
    print("Movendo...")
    
    # === VERIFICAR LIMITES DO MAPA ===
    opcoes_disponiveis = []
    
    # Verificar se pode ir para DIREITA (1)
    if pos_x_ante is None or pos_x_ante <= 110:
        opcoes_disponiveis.append(1)
    else:
        print("⚠️ Limite direito atingido! X = " + str(pos_x_ante))
    
    # Verificar se pode ir para ESQUERDA (2)
    if pos_x_ante is None or pos_x_ante >= 20:
        opcoes_disponiveis.append(2)
    else:
        print("⚠️ Limite esquerdo atingido! X = " + str(pos_x_ante))
    
    # Verificar se pode ir para CIMA (3)
    if pos_y_ante is None or pos_y_ante >= 20:
        opcoes_disponiveis.append(3)
    else:
        print("⚠️ Limite superior atingido! Y = " + str(pos_y_ante))
    
    # Verificar se pode ir para BAIXO (4)
    if pos_y_ante is None or pos_y_ante <= 230:
        opcoes_disponiveis.append(4)
    else:
        print("⚠️ Limite inferior atingido! Y = " + str(pos_y_ante))
        # Diagonais
    # Noroeste (esquerda + cima)
    if (pos_x_ante is None or pos_x_ante >= 20) and (pos_y_ante is None or pos_y_ante >= 20):
        opcoes_disponiveis.append(5)
    # Sudoeste (esquerda + baixo)
    if (pos_x_ante is None or pos_x_ante >= 20) and (pos_y_ante is None or pos_y_ante <= 230):
        opcoes_disponiveis.append(6)
    # Sudeste (direita + baixo)
    if (pos_x_ante is None or pos_x_ante <= 110) and (pos_y_ante is None or pos_y_ante <= 230):
        opcoes_disponiveis.append(7)
    # Nordeste (direita + cima)
    if (pos_x_ante is None or pos_x_ante <= 110) and (pos_y_ante is None or pos_y_ante >= 20):
        opcoes_disponiveis.append(8)
        
    # Se não houver opções disponíveis, não mover
    if not opcoes_disponiveis:
        print("❌ Sem opções de movimento disponíveis! Personagem pode estar preso.")
        return
    
    # Definir quantas vezes mover para cada direção
    repeticoes = {
        1: 3,  # Direita: 3 vezes
        2: 3,  # Esquerda: 3 vezes
        3: 4,  # Cima: 4 vezes
        4: 4,  # Baixo: 4 vezes
        5:3,   # Noroeste: 3 vezes
        6:3,    #Suoeste: 3 vezes
        7:3,   #Sudeste: 3 vezes
        8:3    #Nordeste: 3 vezes
    }
    
    # Definir qual função chamar para cada escolha
    movimentos = {
        1: moveRight,
        2: moveLeft,
        3: moveUp,
        4: moveDown,
        5: moveNorthWest,
        6: moveSouthWest,
        7: moveSouthEast,
        8: moveNorthEast
    }
    
    # Nomes das direções
    nomes_direcoes = {
        1: "➡️ Direita",
        2: "⬅️ Esquerda",
        3: "⬆️ Cima",
        4: "⬇️ Baixo",
        5: "↖️ Noroeste",
        6: "↙️ Sudoeste",
        7: "↘️ Sudeste",
        8: "↗️ Nordeste"
    }
    
    # === MAPEAMENTO DE DIREÇÕES OPOSTAS ===
    direcoes_opostas = {
        1: 2,  # Direita ↔ Esquerda
        2: 1,  # Esquerda ↔ Direita
        3: 4,  # Cima ↔ Baixo
        4: 3,   # Baixo ↔ Cima
        8:6, # Nordeste ↔ Sudoeste
        6:8, # Sudoeste ↔ Nordeste
        5:7, # Noroeste ↔ Sudeste
        7:5  # Sudeste ↔ Noroeste
    }
    
    # === SISTEMA DE TENTATIVAS ===
    tentativas = 0
    max_tentativas = 10
    movimento_sucesso = False
    
    while tentativas < max_tentativas and autoClickOn and not movimento_sucesso:
        # Criar cópia das opções disponíveis para este ciclo
        opcoes_atuais = opcoes_disponiveis.copy()
        
        # === EVITAR MOVIMENTO OPOSTO AO ANTERIOR ===
        if ultimo_movimento is not None and ultimo_movimento in direcoes_opostas:
            direcao_oposta = direcoes_opostas[ultimo_movimento]
            
            # Remover direção oposta APENAS se houver outras opções
            if direcao_oposta in opcoes_atuais and len(opcoes_atuais) > 1:
                opcoes_atuais.remove(direcao_oposta)
                print(f"🚫 Evitando direção oposta: {nomes_direcoes[direcao_oposta]}")
        
        # === CALCULAR PROBABILIDADES BASEADAS NA POSIÇÃO ===
        pesos = {}
        
        if pos_x_ante is not None and pos_y_ante is not None:
            # Normalizar posição (0 a 1)
            posicao_x_normalizada = (pos_x_ante - 20) / (110 - 20)  # 0 = esquerda, 1 = direita
            posicao_y_normalizada = (pos_y_ante - 20) / (230 - 20)  # 0 = cima, 1 = baixo
            
            for direcao in opcoes_atuais:
                peso_base = 1.0
                
                if direcao == 1:  # DIREITA
                    # Se está muito à esquerda, aumentar MUITO a probabilidade de ir pra direita
                    if posicao_x_normalizada < 0.2:
                        peso_base = 4.0
                    elif posicao_x_normalizada < 0.4:
                        peso_base = 2.5
                    # Se está muito à direita, REDUZIR probabilidade
                    elif posicao_x_normalizada > 0.8:
                        peso_base = 0.2
                        
                elif direcao == 2:  # ESQUERDA
                    # Se está muito à direita, aumentar MUITO a probabilidade de ir pra esquerda
                    if posicao_x_normalizada > 0.8:
                        peso_base = 4.0
                    elif posicao_x_normalizada > 0.6:
                        peso_base = 2.5
                    # Se está muito à esquerda, REDUZIR probabilidade
                    elif posicao_x_normalizada < 0.2:
                        peso_base = 0.2
                        
                elif direcao == 3:  # CIMA
                    # Se está muito embaixo, aumentar probabilidade de subir
                    if posicao_y_normalizada > 0.8:
                        peso_base = 3.0
                    elif posicao_y_normalizada > 0.6:
                        peso_base = 2.0
                    # Se está em cima, REDUZIR BASTANTE (para focar em horizontal)
                    elif posicao_y_normalizada < 0.3:
                        peso_base = 0.1
                        
                elif direcao == 4:  # BAIXO
                    # Se está muito em cima, aumentar probabilidade de descer
                    if posicao_y_normalizada < 0.2:
                        peso_base = 3.0
                    elif posicao_y_normalizada < 0.4:
                        peso_base = 2.0
                    # Se está embaixo, REDUZIR BASTANTE (para focar em horizontal)
                    elif posicao_y_normalizada > 0.7:
                        peso_base = 0.1
                
                pesos[direcao] = peso_base
        else:
            # Se não tiver posição, usar pesos iguais
            for direcao in opcoes_atuais:
                pesos[direcao] = 1.0
        
        # Escolher direção usando pesos (random.choices com weights)
        escolha = random.choices(opcoes_atuais, weights=[pesos[d] for d in opcoes_atuais], k=1)[0]
        
        # Debug: mostrar pesos calculados na primeira tentativa
        if tentativas == 0 and pos_x_ante is not None and pos_y_ante is not None:
            print(f"📊 Probabilidades: ", end="")
            for d in opcoes_atuais:
                print(f"{nomes_direcoes[d]}={pesos[d]:.1f}x ", end="")
            print()
        funcao_movimento = movimentos[escolha]
        quantidade = repeticoes[escolha]
        direcao = nomes_direcoes[escolha]
        
        if tentativas == 0:
            print(f"📍 Posição antes: X={pos_x_ante}, Y={pos_y_ante}")
            print(f"Movendo para {direcao} por {quantidade} vezes.")
        else:
            print(f"🔄 Tentativa {tentativas + 1}/{max_tentativas}: Movendo para {direcao}")

        # CAPTURAR posição ANTES do movimento (para comparação posterior)
        pos_x_antes_movimento = get_memory_value("X")
        pos_y_antes_movimento = get_memory_value("Y")
        
        # === EXECUTAR MOVIMENTO ===
        for i in range(quantidade):
            if autoClickOn:
                funcao_movimento()
                time.sleep(0.2)
        
        # === AGUARDAR ESTABILIZAÇÃO (aumentado para garantir atualização) ===
        time.sleep(2.0)  # Aumentado de 1.2s para 2.0s
        
        # Forçar atualização imediata dos valores de memória
        force_memory_update()
        
        # === VERIFICAR SE MOVEU ===
        pos_x_depois = get_memory_value("X")
        pos_y_depois = get_memory_value("Y")
        
        print(f"📍 Posição depois: X={pos_x_depois}, Y={pos_y_depois}")
        
        # Verificar se a posição mudou (comparar com a posição ANTES do movimento)
        if pos_x_antes_movimento is not None and pos_y_antes_movimento is not None and \
           pos_x_depois is not None and pos_y_depois is not None:
            
            # Calcular diferença
            diferenca_x = abs(pos_x_depois - pos_x_antes_movimento)
            diferenca_y = abs(pos_y_depois - pos_y_antes_movimento)
            
            # Se moveu (diferença >= 1 pixel - mais tolerante)
            if diferenca_x >= 1 or diferenca_y >= 1:
                print(f"✅ Movimento confirmado! Δx={diferenca_x}, Δy={diferenca_y}")
                movimento_sucesso = True
                ultimo_movimento = escolha  # ← GUARDAR movimento bem-sucedido
            else:
                print(f"⚠️ PERSONAGEM NÃO SE MOVEU! (Δx={diferenca_x}, Δy={diferenca_y})")
                print(f"   Posição antes: ({pos_x_antes_movimento}, {pos_y_antes_movimento})")
                print(f"   Posição depois: ({pos_x_depois}, {pos_y_depois})")
                
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
        print("❌ Personagem PRESO após 10 tentativas! Voltando para Beginners...")
        backToBeginners()
        

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
        checks()
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
        # pyautogui.press('esc')
        # time.sleep(1)
        # pyautogui.press('l')
        backToBeginners()


def Dead():
    time.sleep(6)
    pyautogui.keyUp('alt')
    time.sleep(1)
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
    global mouseAttackX
    global mouseAttackY

    pyautogui.press('f9')
    time.sleep(0.3)
    pyautogui.rightClick(mouseAttackX, mouseAttackY)
    time.sleep(0.2)
    pyautogui.write('daron'.lower())
    time.sleep(0.2)
    pyautogui.press('enter')
    time.sleep(14)
    pyautogui.keyDown('ctrlright') 
    pyautogui.leftClick(216, 556)
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


def moveSouthEast():
    offset = -110
    global mouseAttackX
    global mouseAttackY
    print("Movendo para o Sudeste...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX + offset, mouseAttackY + offset)
    time.sleep(0.5)  # Solta Alt quando para  
    pyautogui.leftClick(mouseAttackX + (offset * 2), mouseAttackY + (offset * 2))
    time.sleep(2)
    pyautogui.keyUp('alt')

def moveNorthEast():
    offset = 110
    global mouseAttackX
    global mouseAttackY
    print("Movendo para o Nordeste...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX + offset, mouseAttackY - offset)
    time.sleep(0.5)  # Solta Alt quando para  
    pyautogui.leftClick(mouseAttackX + (offset * 2), mouseAttackY - (offset * 2))
    time.sleep(2)
    pyautogui.keyUp('alt')

def moveSouthWest():
    offset = -110
    global mouseAttackX
    global mouseAttackY
    print("Movendo para o Sudoeste...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX - offset, mouseAttackY + offset)
    time.sleep(0.5)  # Solta Alt quando para  
    pyautogui.leftClick(mouseAttackX - (offset * 2), mouseAttackY + (offset * 2))
    time.sleep(2)
    pyautogui.keyUp('alt')

def moveNorthWest():
    offset = 110
    global mouseAttackX
    global mouseAttackY
    print("Movendo para o Noroeste...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX - offset, mouseAttackY - offset)
    time.sleep(0.5)  # Solta Alt quando para  
    pyautogui.leftClick(mouseAttackX - (offset * 2), mouseAttackY - (offset * 2))
    time.sleep(2)
    pyautogui.keyUp('alt')

def moveRight():
    offset = 250
    global mouseAttackX
    global mouseAttackY
    print("Movendo para a direita...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX + offset, mouseAttackY)
    time.sleep(0.5)  
    pyautogui.leftClick(mouseAttackX + (offset * 2), mouseAttackY)
    time.sleep(2)
    pyautogui.keyUp('alt')

def moveLeft():
    offset = -250
    global mouseAttackX
    global mouseAttackY
    print("Movendo para a esquerda...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX + offset, mouseAttackY)
    time.sleep(0.5)  # Solta Alt quando para  
    pyautogui.leftClick(mouseAttackX + (offset * 2), mouseAttackY)
    time.sleep(2)
    pyautogui.keyUp('alt')
    

def moveUp():
    offset = -130
    global mouseAttackX
    global mouseAttackY
    print("Movendo para cima...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX , mouseAttackY + offset)
    time.sleep(0.5)  # Solta Alt quando para  
    pyautogui.leftClick(mouseAttackX , mouseAttackY + (offset * 2))
    time.sleep(2)
    pyautogui.keyUp('alt')
def moveDown():
    offset = 130
    global mouseAttackX
    global mouseAttackY
    print("Movendo para baixo...")
    pyautogui.press('f7') #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    pyautogui.keyDown('alt')
    pyautogui.rightClick(mouseAttackX , mouseAttackY + offset)
    time.sleep(0.5)
    pyautogui.leftClick(mouseAttackX , mouseAttackY + (offset * 2))
    time.sleep(2)
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
    
    # Procurar TODOS os processos darkeden.exe
    darkeden_processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        if 'darkeden' in proc.info['name'].lower():
            darkeden_processes.append(proc)
    
    if not darkeden_processes:
        print("❌ Nenhum processo Dark Eden encontrado!")
        return False
    
    # Se houver múltiplos processos, permitir seleção
    target_process = None
    if len(darkeden_processes) == 1:
        target_process = darkeden_processes[0]
        print(f"✅ Único processo encontrado: PID {target_process.info['pid']}")
    else:
        print("\n" + "="*60)
        print(f"⚠️ MÚLTIPLOS PROCESSOS DETECTADOS ({len(darkeden_processes)} processos)")
        print("="*60)
        print("Escolha qual processo usar:")
        print("-"*60)
        
        for idx, proc in enumerate(darkeden_processes, 1):
            try:
                # Tentar obter informações extras do processo
                cpu_percent = proc.cpu_percent(interval=0.1)
                memory_mb = proc.memory_info().rss / (1024 * 1024)
                print(f"  [{idx}] PID: {proc.info['pid']:<6} | CPU: {cpu_percent:5.1f}% | RAM: {memory_mb:6.1f} MB")
            except:
                print(f"  [{idx}] PID: {proc.info['pid']}")
        
        print("="*60)
        
        while True:
            try:
                escolha = input(f"Digite o número do processo [1-{len(darkeden_processes)}]: ").strip()
                escolha_num = int(escolha)
                
                if 1 <= escolha_num <= len(darkeden_processes):
                    target_process = darkeden_processes[escolha_num - 1]
                    print(f"✅ Processo selecionado: PID {target_process.info['pid']}")
                    break
                else:
                    print(f"❌ Número inválido! Digite entre 1 e {len(darkeden_processes)}")
            except ValueError:
                print("❌ Digite um número válido!")
            except KeyboardInterrupt:
                print("\n❌ Operação cancelada pelo usuário")
                return False
    
    # Conectar ao processo selecionado
    try:
        # Inicializar MemoryReader corretamente
        memory_reader = MemoryReader()
        if not memory_reader.find_process_by_pid(target_process.info['pid']):
            return False
        if not memory_reader.open_process():
            return False
        
        process_base_address = get_process_base_address(target_process.info['pid'], target_process.info['name'])
        print(f"✅ Conectado ao processo: {target_process.info['name']} (PID: {target_process.info['pid']})")
        print(f"📍 Base address: 0x{process_base_address:X}")
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
        
        time.sleep(0.1)  # Atualiza a cada 100ms (reduzido de 200ms)

def show_memory_values():
    """Exibe os valores atuais da memória com debug detalhado (acionado por F6)"""
    if not memory_values:
        print("Nenhum valor de memória disponível. Ative o monitoramento com " + hotkeyToggleMonitoring.upper())
        return
    
    # Forçar atualização IMEDIATA antes de exibir
    force_memory_update()
    time.sleep(0.05)  # Pequeno delay para garantir leitura
    
    print("\n" + "="*80)
    print("🔍 VALORES DE MEMÓRIA (Debug Detalhado)")
    print("="*80)
    print(f"{'DESCRIÇÃO':<15} | {'VALOR':<15} | {'ENDEREÇO':<20} | {'TIPO':<10}")
    print("-"*80)
    
    for description, value in memory_values.items():
        info = monitored_addresses.get(description, {})
        address_str = info.get('address_str', 'N/A')
        address_hex = info.get('address', 0)
        data_type = info.get('type', 'N/A')
        
        # Formatar valor baseado no tipo
        if value is None:
            value_display = "❌ NULL"
        else:
            value_display = str(value)
        
        # Exibir linha principal
        print(f"{description:<15} | {value_display:<15} | 0x{address_hex:08X} ({address_str[:10]}) | {data_type:<10}")
        
        # DEBUG ESPECIAL para X e Y - ler diretamente e comparar
        # if description in ["X", "Y"] and address_hex != 0:
        #     # Tentar ler com TODOS os tipos possíveis
        #     tipos_teste = ['int32', 'uint32', 'int16', 'uint16', 'int8', 'uint8', 'float']
        #     print(f"   🔬 Teste de tipos para {description}:")
            
        #     for tipo in tipos_teste:
        #         try:
        #             valor_teste = read_value_by_type(address_hex, tipo)
        #             if valor_teste is not None and valor_teste != value:
        #                 print(f"      • {tipo}: {valor_teste} {'← DIFERENTE!' if abs(valor_teste - (value or 0)) > 1 else ''}")
        #         except:
        #             pass
    
    print("="*80 + "\n")

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

def force_memory_update():
    """Força atualização imediata dos valores de memória com retry"""
    global memory_values
    if not monitored_addresses or not memory_reader:
        return
    
    # Ler DUAS vezes para garantir consistência
    for tentativa in range(2):
        for description, info in monitored_addresses.items():
            address = info['address']
            data_type = info['type']
            value = read_value_by_type(address, data_type)
            
            # Validação extra para X e Y
            if description in ["X", "Y"] and value is not None:
                # X deve estar entre 0-200, Y entre 0-300 (valores razoáveis)
                if description == "X" and (value < 0 or value > 200):
                    print(f"⚠️ Valor suspeito para X: {value} (tipo: {data_type}, endereço: 0x{address:08X})")
                    print(f"   Tentando ler como outros tipos...")
                    # Tentar int16 se for int32
                    if data_type == 'int32':
                        value_alt = read_value_by_type(address, 'int16')
                        if value_alt and 0 < value_alt < 200:
                            print(f"   ✅ Valor correto com int16: {value_alt}")
                            value = value_alt
                            
                elif description == "Y" and (value < 0 or value > 300):
                    print(f"⚠️ Valor suspeito para Y: {value} (tipo: {data_type}, endereço: 0x{address:08X})")
                    print(f"   Tentando ler como outros tipos...")
                    if data_type == 'int32':
                        value_alt = read_value_by_type(address, 'int16')
                        if value_alt and 0 < value_alt < 300:
                            print(f"   ✅ Valor correto com int16: {value_alt}")
                            value = value_alt
            
            memory_values[description] = value
        
        if tentativa == 0:
            time.sleep(0.02)  # Pequeno delay entre tentativas

def reconnect_to_process():
    """Reconecta a um processo diferente (acionado por F9)"""
    global monitoring_active, memory_reader, process_base_address, memory_values
    
    print("\n" + "="*60)
    print("🔄 RECONECTANDO A OUTRO PROCESSO...")
    print("="*60)
    
    # Parar monitoramento se estiver ativo
    was_monitoring = monitoring_active
    if monitoring_active:
        monitoring_active = False
        time.sleep(0.3)  # Aguardar thread parar
        print("⏸️ Monitoramento pausado")
    
    # Fechar conexão atual
    if memory_reader and hasattr(memory_reader, 'process_handle'):
        try:
            if memory_reader.process_handle:
                ctypes.windll.kernel32.CloseHandle(memory_reader.process_handle)
                print("🔌 Conexão anterior fechada")
        except:
            pass
    
    memory_reader = None
    process_base_address = 0
    memory_values = {}
    
    # Reinicializar com novo processo
    if init_memory_reader():
        load_addresses()
        
        # Reativar monitoramento se estava ativo
        if was_monitoring:
            monitoring_active = True
            monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
            monitoring_thread.start()
            print("▶️ Monitoramento reativado")
        
        print("✅ Reconexão bem-sucedida!")
    else:
        print("❌ Falha na reconexão")
    
    print("="*60 + "\n")

def debug_xy_memory():
    """Debug específico para X e Y - análise completa com bytes brutos e offsets"""
    print("\n" + "="*80)
    print("🔬 DEBUG DETALHADO - POSIÇÃO X e Y (Análise de Bytes)")
    print("="*80)
    
    for desc in ["X", "Y"]:
        if desc not in monitored_addresses:
            print(f"❌ {desc} não está nos endereços monitorados")
            continue
        
        info = monitored_addresses[desc]
        address = info['address']
        address_str = info['address_str']
        data_type_config = info['type']
        
        print(f"\n📍 {desc}:")
        print(f"   Endereço base: 0x{address:08X} ({address_str})")
        print(f"   Tipo configurado: {data_type_config}")
        print(f"   Valor atual (cache): {memory_values.get(desc, 'N/A')}")
        
        # === LER BYTES BRUTOS (8 bytes para análise) ===
        try:
            import ctypes
            if memory_reader and memory_reader.process_handle:
                bytes_read = ctypes.c_ulonglong()
                buffer = ctypes.create_string_buffer(8)
                success = ctypes.windll.kernel32.ReadProcessMemory(
                    memory_reader.process_handle,
                    ctypes.c_void_p(address),
                    buffer,
                    8,
                    ctypes.byref(bytes_read)
                )
                
                if success:
                    raw_bytes = buffer.raw[:8]
                    print(f"\n   📦 Bytes brutos (8 bytes a partir de 0x{address:08X}):")
                    print(f"      Hex: {' '.join(f'{b:02X}' for b in raw_bytes)}")
                    print(f"      Dec: {' '.join(f'{b:3d}' for b in raw_bytes)}")
                    
                    # Interpretar como int32 (little-endian)
                    int32_value = int.from_bytes(raw_bytes[:4], byteorder='little', signed=True)
                    uint32_value = int.from_bytes(raw_bytes[:4], byteorder='little', signed=False)
                    print(f"\n   🔢 Interpretação dos primeiros 4 bytes:")
                    print(f"      int32 (com sinal):  {int32_value} {('✅ VÁLIDO' if (desc=='X' and 0<=int32_value<=200) or (desc=='Y' and 0<=int32_value<=300) else '')}")
                    print(f"      uint32 (sem sinal): {uint32_value} {('✅ VÁLIDO' if (desc=='X' and 0<=uint32_value<=200) or (desc=='Y' and 0<=uint32_value<=300) else '')}")
                    
                    # Tentar diferentes offsets (caso esteja desalinhado)
                    print(f"\n   🔄 Testando offsets (+1, +2, +3 bytes):")
                    for offset in [1, 2, 3]:
                        offset_addr = address + offset
                        buffer_offset = ctypes.create_string_buffer(4)
                        success_offset = ctypes.windll.kernel32.ReadProcessMemory(
                            memory_reader.process_handle,
                            ctypes.c_void_p(offset_addr),
                            buffer_offset,
                            4,
                            ctypes.byref(bytes_read)
                        )
                        
                        if success_offset:
                            bytes_offset = buffer_offset.raw[:4]
                            int32_offset = int.from_bytes(bytes_offset, byteorder='little', signed=True)
                            uint32_offset = int.from_bytes(bytes_offset, byteorder='little', signed=False)
                            
                            valido_int32 = (desc=='X' and 0<=int32_offset<=200) or (desc=='Y' and 0<=int32_offset<=300)
                            valido_uint32 = (desc=='X' and 0<=uint32_offset<=200) or (desc=='Y' and 0<=uint32_offset<=300)
                            
                            if valido_int32 or valido_uint32:
                                print(f"      ➕ Offset +{offset} (0x{offset_addr:08X}):")
                                print(f"         Bytes: {' '.join(f'{b:02X}' for b in bytes_offset)}")
                                if valido_int32:
                                    print(f"         int32:  {int32_offset} ✅ VÁLIDO")
                                if valido_uint32:
                                    print(f"         uint32: {uint32_offset} ✅ VÁLIDO")
                    
                    # Testar int16 e uint16 também
                    print(f"\n   🔢 Interpretação como 16-bit (2 bytes):")
                    int16_value = int.from_bytes(raw_bytes[:2], byteorder='little', signed=True)
                    uint16_value = int.from_bytes(raw_bytes[:2], byteorder='little', signed=False)
                    print(f"      int16 (com sinal):  {int16_value} {('✅ VÁLIDO' if (desc=='X' and 0<=int16_value<=200) or (desc=='Y' and 0<=int16_value<=300) else '')}")
                    print(f"      uint16 (sem sinal): {uint16_value} {('✅ VÁLIDO' if (desc=='X' and 0<=uint16_value<=200) or (desc=='Y' and 0<=uint16_value<=300) else '')}")
                    
        except Exception as e:
            print(f"   ❌ Erro ao ler bytes brutos: {e}")
            traceback.print_exc()
    
    print("="*80)
    print("💡 DICA: Se um offset diferente mostrar ✅ VÁLIDO, atualize o endereço no JSON")
    print("   Exemplo: Se offset +2 é válido, mude 'darkeden.exe+357778' para 'darkeden.exe+35777A'")
    print("="*80 + "\n")

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
    keyboard.add_hotkey(hotkeyShowMemory, show_memory_values)
    keyboard.add_hotkey(hotkeyToggleMonitoring, toggle_memory_monitoring)
    keyboard.add_hotkey(hotkeyDebugXY, debug_xy_memory)
    keyboard.add_hotkey(hotkeyReconnectProcess, reconnect_to_process)
    
    print("Tecla para atacar mouse direito (Segurar): " + hotkeyHoldRight)
    print("Tecla para combo mago: " + hotkeyAttack + " NECESSÁRIO MARCAR POSIÇÃO EM BAIXO DO CHAR")
    print("Tecla para setar posição: " + hotkeySalvar)
    print("\n=== MONITORAMENTO DE MEMÓRIA ===")
    print(hotkeyShowMemory.upper() + ": Mostrar valores de memória")
    print(hotkeyToggleMonitoring.upper() + ": Ativar/Desativar monitoramento")
    print(hotkeyDebugXY.upper() + ": Debug detalhado X/Y (todos os tipos)")
    print(hotkeyReconnectProcess.upper() + ": Reconectar a outro processo (útil quando há múltiplas instâncias)")
    print("================================\n")
    
    # Keep the main thread alive to listen for the hotkey
    keyboard.wait('f2')  # Change 'esc' to your desired exit key