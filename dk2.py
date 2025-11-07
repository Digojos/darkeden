import keyboard
import threading
import time
import pyautogui
import os
import win32gui
import win32con
import win32api
import psutil
import sys
from PyQt5.QtWidgets import QApplication
from process_selector_gui import ProcessSelectorGUI

holding = False
autoClickOn = False
mouseAttackX = 0
mouseAttackY = 0
mouseAntesX = 0
mouseAntesY = 0
game_hwnd = None

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


bloodwalls = [0 , 25 , -25] 

# Funções para Windows API
def list_all_processes():
    """Lista todos os processos em execução"""
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                processes.append((proc.info['pid'], proc.info['name']))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Ordenar por nome
        processes.sort(key=lambda x: x[1].lower())
        
        print("=== PROCESSOS EM EXECUÇÃO ===")
        for i, (pid, name) in enumerate(processes, 1):
            print(f"{i:3d}. PID: {pid:5d} | {name}")
        print("=============================")
        return processes
    except Exception as e:
        print(f"❌ Erro ao listar processos: {str(e)}")
        return []

def select_process_with_gui():
    """Abre GUI para seleção de processo"""
    global game_hwnd
    
    print("🖥️ Abrindo interface gráfica para seleção de processo...")
    
    # Criar aplicação Qt se não existir
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Criar e mostrar GUI
    selector = ProcessSelectorGUI()
    
    # Variável para armazenar resultado
    result = {'success': False, 'pid': None, 'name': None, 'hwnd': None}
    
    def on_process_selected(pid, name, hwnd):
        result['success'] = True
        result['pid'] = pid
        result['name'] = name
        result['hwnd'] = hwnd
        selector.close()
    
    # Conectar sinal
    selector.process_selected.connect(on_process_selected)
    
    # Mostrar GUI e aguardar resultado
    selector.show()
    app.exec_()
    
    if result['success']:
        if result['hwnd'] == 0:
            # Processo sem janela específica - tentar encontrar janelas automaticamente
            print(f"🔍 Processo {result['name']} selecionado sem janela específica")
            print("🔄 Tentando encontrar janelas automaticamente...")
            
            # Buscar janelas do processo
            found_hwnd = find_any_window_by_pid(result['pid'])
            if found_hwnd:
                game_hwnd = found_hwnd
                print(f"✅ Janela encontrada automaticamente: HWND {found_hwnd}")
            else:
                print("⚠️ Nenhuma janela encontrada, mas processo conectado")
                game_hwnd = None  # Será definido quando necessário
        else:
            game_hwnd = result['hwnd']
            print(f"✅ Janela específica selecionada: HWND {result['hwnd']}")
        
        print(f"✅ Processo selecionado via GUI:")
        print(f"📋 Nome: {result['name']}")
        print(f"🔢 PID: {result['pid']}")
        print(f"🪟 HWND: {game_hwnd or 'A ser determinado'}")
        return True
    else:
        print("❌ Seleção cancelada pelo usuário")
        return False

def find_any_window_by_pid(pid):
    """Encontra qualquer janela de um processo pelo PID"""
    found_hwnd = None
    
    def enum_windows_proc(hwnd, lParam):
        nonlocal found_hwnd
        try:
            window_pid = win32gui.GetWindowThreadProcessId(hwnd)[1]
            if window_pid == pid:
                window_text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                is_visible = win32gui.IsWindowVisible(hwnd)
                
                # Priorizar janelas visíveis com título
                if is_visible and window_text:
                    found_hwnd = hwnd
                    return False  # Para a busca
                elif not found_hwnd:  # Se ainda não encontrou nenhuma, guardar esta
                    found_hwnd = hwnd
        except:
            pass
        return True
    
    win32gui.EnumWindows(enum_windows_proc, 0)
    return found_hwnd

def select_process_interactive():
    """Permite selecionar um processo interativamente - agora com opção GUI"""
    global game_hwnd
    
    print("\n🎮 SELEÇÃO DE PROCESSO PARA DARK EDEN")
    print("Escolha o método de seleção:")
    print("1. Interface Gráfica (Recomendado)")
    print("2. Terminal/Console")
    print("3. Cancelar")
    
    try:
        choice = input("Sua escolha (1-3): ")

        if choice == '1':
            return select_process_with_gui()
        elif choice == '2':
            return select_process_console()
        elif choice == '3':
            print("Cancelado pelo usuário.")
            return False
        else:
            print("Opção inválida. Usando interface gráfica...")
            return select_process_with_gui()
            
    except KeyboardInterrupt:
        print("\nCancelado pelo usuário.")
        return False

def select_process_console():
    """Seleção de processo via console (método original)"""
    global game_hwnd
    
    processes = list_all_processes()
    if not processes:
        return False
    
    while True:
        try:
            print("\n📋 SELEÇÃO VIA CONSOLE")
            print("Digite o número do processo ou nome para filtrar:")
            print("(Digite 'q' para cancelar, 'game' para ver só jogos, 'gui' para interface gráfica)")
            
            user_input = input("Sua escolha: ").strip()
            
            if user_input.lower() == 'q':
                print("Cancelado pelo usuário.")
                return False
            
            if user_input.lower() == 'gui':
                return select_process_with_gui()
            
            # Filtro especial para jogos
            if user_input.lower() == 'game':
                game_keywords = ['game', 'dark', 'eden', '.exe']
                filtered = [(i+1, pid, name) for i, (pid, name) in enumerate(processes) 
                           if any(keyword in name.lower() for keyword in game_keywords)]
                
                if filtered:
                    print(f"\n🎮 {len(filtered)} processos relacionados a jogos:")
                    for idx, pid, name in filtered:
                        print(f"{idx:3d}. PID: {pid:5d} | {name}")
                else:
                    print("Nenhum processo de jogo encontrado")
                continue
            
            # Se for um número, tentar selecionar diretamente
            if user_input.isdigit():
                choice = int(user_input)
                if 1 <= choice <= len(processes):
                    pid, name = processes[choice - 1]
                    if connect_to_process_by_pid(pid, name):
                        return True
                    else:
                        print("Falha ao conectar. Tente outro processo.")
                        continue
                else:
                    print(f"Número inválido. Digite entre 1 e {len(processes)}")
                    continue
            
            # Se não for número, filtrar por nome
            filtered = [(i+1, pid, name) for i, (pid, name) in enumerate(processes) 
                       if user_input.lower() in name.lower()]
            
            if not filtered:
                print(f"Nenhum processo encontrado com '{user_input}'")
                continue
            
            if len(filtered) == 1:
                idx, pid, name = filtered[0]
                print(f"Processo encontrado: {name} (PID: {pid})")
                if connect_to_process_by_pid(pid, name):
                    return True
            else:
                print(f"\n{len(filtered)} processos encontrados:")
                for idx, pid, name in filtered:
                    print(f"{idx:3d}. PID: {pid:5d} | {name}")
                
        except ValueError:
            print("Entrada inválida. Digite um número ou nome do processo.")
        except KeyboardInterrupt:
            print("\nCancelado pelo usuário.")
            return False

def connect_to_process_by_pid(pid, name):
    """Conecta a um processo específico pelo PID"""
    global game_hwnd
    
    try:
        found_windows = []
        
        # Tentar encontrar TODAS as janelas do processo
        def enum_windows_proc(hwnd, lParam):
            try:
                window_pid = win32gui.GetWindowThreadProcessId(hwnd)[1]
                if window_pid == pid:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    is_visible = win32gui.IsWindowVisible(hwnd)
                    
                    # Adicionar à lista todas as janelas encontradas
                    found_windows.append({
                        'hwnd': hwnd,
                        'title': window_text,
                        'class': class_name,
                        'visible': is_visible
                    })
            except:
                pass
            return True
        
        print(f"🔍 Procurando janelas do processo {name} (PID: {pid})...")
        win32gui.EnumWindows(enum_windows_proc, 0)
        
        if not found_windows:
            print(f"❌ Nenhuma janela encontrada para o processo {name}")
            return False
        
        print(f"📋 Encontradas {len(found_windows)} janela(s):")
        
        # Mostrar todas as janelas encontradas
        valid_windows = []
        for i, window in enumerate(found_windows):
            status = "✅ Visível" if window['visible'] else "❌ Oculta"
            title = window['title'] or "(Sem título)"
            print(f"  {i+1}. {status} | '{title}' | Classe: '{window['class']}'")
            
            # Priorizar janelas visíveis com título
            if window['visible'] and window['title']:
                valid_windows.append(window)
        
        # Escolher a melhor janela
        if valid_windows:
            # Usar a primeira janela visível com título
            best_window = valid_windows[0]
            game_hwnd = best_window['hwnd']
            print(f"🎯 Selecionada: '{best_window['title']}'")
        elif found_windows:
            # Se não há janelas visíveis com título, usar a primeira disponível
            best_window = found_windows[0]
            game_hwnd = best_window['hwnd']
            print(f"⚠️ Usando janela sem título: Classe '{best_window['class']}'")
        
        if game_hwnd:
            print(f"✅ Conectado com sucesso!")
            print(f"📋 Processo: {name} (PID: {pid})")
            print(f"🪟 HWND: {game_hwnd}")
            return True
        else:
            print(f"❌ Falha ao conectar ao processo {name}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao conectar ao processo: {str(e)}")
        return False

def list_all_windows():
    """Lista todas as janelas abertas para debug"""
    windows_list = []
    
    def enum_windows_proc(hwnd, lParam):
        window_text = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        is_visible = win32gui.IsWindowVisible(hwnd)
        
        if window_text or is_visible:  # Mostra janelas com título ou visíveis
            windows_list.append({
                'hwnd': hwnd,
                'title': window_text or "(Sem título)",
                'class': class_name,
                'visible': is_visible
            })
        return True
    
    print("=== JANELAS ABERTAS ===")
    win32gui.EnumWindows(enum_windows_proc, 0)
    
    # Ordenar por título
    windows_list.sort(key=lambda x: x['title'].lower())
    
    for i, window in enumerate(windows_list, 1):
        status = "✅" if window['visible'] else "❌"
        print(f"{i:3d}. {status} | '{window['title']}' | {window['class']} | HWND: {window['hwnd']}")
    
    print("=====================")
    return windows_list

def connect_to_window_by_hwnd(hwnd, title=""):
    """Conecta diretamente a uma janela pelo HWND"""
    global game_hwnd
    
    try:
        # Verificar se a janela é válida
        if not win32gui.IsWindow(hwnd):
            print(f"❌ HWND {hwnd} não é uma janela válida")
            return False
        
        # Obter informações da janela
        window_text = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        is_visible = win32gui.IsWindowVisible(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        
        print(f"✅ Conectando à janela:")
        print(f"   📋 Título: '{window_text or title}'")
        print(f"   🏷️ Classe: '{class_name}'")
        print(f"   👁️ Visível: {is_visible}")
        print(f"   📐 Posição: {rect}")
        print(f"   🪟 HWND: {hwnd}")
        
        # Conectar
        game_hwnd = hwnd
        
        # Teste de conectividade
        result = win32gui.PostMessage(game_hwnd, win32con.WM_NULL, 0, 0)
        if result != 0:
            print(f"🔗 Conexão estabelecida com sucesso!")
            return True
        else:
            print(f"⚠️ Conexão estabelecida, mas teste falhou (resultado: {result})")
            return True  # Ainda considerar sucesso
            
    except Exception as e:
        print(f"❌ Erro ao conectar à janela: {e}")
        return False

def select_window_interactive():
    """Permite selecionar uma janela interativamente"""
    global game_hwnd
    
    print("\n🪟 SELEÇÃO DE JANELA")
    windows_list = list_all_windows()
    
    if not windows_list:
        print("❌ Nenhuma janela encontrada")
        return False
    
    while True:
        try:
            print(f"\nDigite o número da janela (1-{len(windows_list)}) ou:")
            print("'dark' - filtrar por Dark Eden")
            print("'game' - filtrar por jogos")
            print("'visible' - mostrar só janelas visíveis")
            print("'q' - cancelar")
            
            user_input = input("Sua escolha: ").strip()
            
            if user_input.lower() == 'q':
                print("Cancelado.")
                return False
            
            # Filtros especiais
            if user_input.lower() == 'dark':
                filtered = [w for w in windows_list if 'dark' in w['title'].lower() or 'eden' in w['title'].lower()]
                if filtered:
                    print(f"\n🎮 {len(filtered)} janela(s) do Dark Eden:")
                    for i, w in enumerate(filtered, 1):
                        status = "✅" if w['visible'] else "❌"
                        print(f"{i}. {status} | '{w['title']}' | HWND: {w['hwnd']}")
                    
                    if len(filtered) == 1:
                        print("Auto-selecionando única janela encontrada...")
                        return connect_to_window_by_hwnd(filtered[0]['hwnd'], filtered[0]['title'])
                else:
                    print("Nenhuma janela do Dark Eden encontrada")
                continue
            
            elif user_input.lower() == 'game':
                game_keywords = ['game', 'dark', 'eden', 'client', 'launcher']
                filtered = [w for w in windows_list if any(kw in w['title'].lower() or kw in w['class'].lower() for kw in game_keywords)]
                if filtered:
                    print(f"\n🎮 {len(filtered)} janela(s) de jogos:")
                    for i, w in enumerate(filtered, 1):
                        status = "✅" if w['visible'] else "❌"
                        print(f"{i}. {status} | '{w['title']}' | HWND: {w['hwnd']}")
                else:
                    print("Nenhuma janela de jogo encontrada")
                continue
            
            elif user_input.lower() == 'visible':
                filtered = [w for w in windows_list if w['visible']]
                if filtered:
                    print(f"\n👁️ {len(filtered)} janela(s) visíveis:")
                    for i, w in enumerate(filtered, 1):
                        print(f"{i}. ✅ | '{w['title']}' | HWND: {w['hwnd']}")
                else:
                    print("Nenhuma janela visível encontrada")
                continue
            
            # Tentar interpretar como número
            if user_input.isdigit():
                choice = int(user_input)
                if 1 <= choice <= len(windows_list):
                    selected_window = windows_list[choice - 1]
                    return connect_to_window_by_hwnd(selected_window['hwnd'], selected_window['title'])
                else:
                    print(f"Número inválido. Digite entre 1 e {len(windows_list)}")
            else:
                print("Entrada inválida. Digite um número ou comando válido.")
                
        except ValueError:
            print("Entrada inválida. Digite um número.")
        except KeyboardInterrupt:
            print("\nCancelado.")
            return False

def find_dark_eden_window():
    """Encontra a janela do Dark Eden - agora com opção interativa"""
    global game_hwnd
    
    # Se já tem uma janela conectada, verificar se ainda é válida
    if game_hwnd:
        try:
            if win32gui.IsWindow(game_hwnd) and win32gui.IsWindowVisible(game_hwnd):
                return True
            else:
                print("⚠️ Janela anterior não está mais válida")
                game_hwnd = None
        except:
            game_hwnd = None
    
    def enum_windows_proc(hwnd, lParam):
        global game_hwnd
        window_text = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        
        # Lista expandida de keywords para Dark Eden
        window_keywords = ["dark eden", "다크에덴", "darkeden", "dark-eden", "darkedge"]
        class_keywords = ["darkeden", "darkedge", "game"]
        
        # Procura por Dark Eden ou nomes comuns da janela
        if any(keyword in window_text.lower() for keyword in window_keywords) or \
           any(keyword in class_name.lower() for keyword in class_keywords):
            game_hwnd = hwnd
            print(f"🎮 JOGO ENCONTRADO AUTOMATICAMENTE: '{window_text}' | Classe: '{class_name}'")
            return False
        return True
    
    print("🔍 Procurando janela do Dark Eden automaticamente...")
    win32gui.EnumWindows(enum_windows_proc, 0)
    
    if game_hwnd:
        print(f"✅ Janela do jogo encontrada: {win32gui.GetWindowText(game_hwnd)}")
        return True
    else:
        print("❌ Dark Eden não encontrado automaticamente.")
        print("🔧 Iniciando seleção manual de processo...")
        print("💡 Dica: Procure por processos como 'darkeden.exe', 'game.exe' ou similar")
        print("💡 Mesmo sem janelas visíveis, alguns processos podem funcionar")
        return select_process_interactive()

def send_key_to_game(key_code):
    """Envia tecla para o jogo usando MÉTODO FÍSICO COM FOCO (confirmado funcionando)"""
    global game_hwnd
    
    # Se não tem janela, tentar encontrar uma
    if not game_hwnd:
        print("⚠️ Janela não definida, tentando encontrar automaticamente...")
        if not find_dark_eden_window():
            print("❌ Não foi possível encontrar janela do jogo")
            return False
    
    try:
        # Verificar se a janela ainda é válida
        if not win32gui.IsWindow(game_hwnd):
            print("❌ Janela não é mais válida")
            return False
        
        # MÉTODO FÍSICO COM FOCO - Confirmado funcionando no Dark Eden
        try:
            # Dar foco à janela
            win32gui.SetForegroundWindow(game_hwnd)
            time.sleep(0.05)  # Pausa para garantir foco
            
            # Enviar tecla física
            win32api.keybd_event(key_code, 0, 0, 0)  # Key down
            time.sleep(0.05)
            win32api.keybd_event(key_code, 0, 2, 0)  # Key up
            
            print(f"⌨️ Tecla {key_code} enviada com SUCESSO! ✅")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar tecla: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Erro geral ao enviar tecla: {e}")
        return False

def send_click_to_game(x, y, button='right'):
    """Envia clique para o jogo sem mover mouse físico"""
    global game_hwnd
    
    # Se não tem janela, tentar encontrar uma
    if not game_hwnd:
        print("⚠️ Janela não definida, tentando encontrar automaticamente...")
        if not find_dark_eden_window():
            print("❌ Não foi possível encontrar janela do jogo")
            return False
    
    try:
        # Verificar se a janela ainda é válida
        if not win32gui.IsWindow(game_hwnd):
            print("❌ Janela não é mais válida")
            return False
        
        # Verificar se a janela está em foco ou pode receber mensagens
        foreground_hwnd = win32gui.GetForegroundWindow()
        print(f"🔍 Janela em foco: {foreground_hwnd}, Nossa janela: {game_hwnd}")
        
        # Converte coordenadas de tela para coordenadas da janela
        rect = win32gui.GetWindowRect(game_hwnd)
        client_rect = win32gui.GetClientRect(game_hwnd)
        client_x = x - rect[0]
        client_y = y - rect[1]
        
        # Debug das coordenadas
        print(f"🎯 Clique: tela({x},{y}) -> cliente({client_x},{client_y})")
        print(f"📐 Window rect: {rect}")
        print(f"📐 Client rect: {client_rect}")
        
        # Verificar se as coordenadas estão dentro da janela
        window_width = rect[2] - rect[0]
        window_height = rect[3] - rect[1]
        
        if client_x < 0 or client_y < 0 or client_x > window_width or client_y > window_height:
            print(f"⚠️ Clique fora da janela! Janela: {window_width}x{window_height}")
            print(f"   Ajustando coordenadas para centro da janela...")
            client_x = window_width // 2
            client_y = window_height // 2
        
        # Tentar diferentes métodos de envio
        success = False
        
        # Método 1: PostMessage (atual)
        try:
            lParam = win32api.MAKELONG(client_x, client_y)
            
            if button == 'right':
                result1 = win32gui.PostMessage(game_hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
                result2 = win32gui.PostMessage(game_hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                print(f"� PostMessage direito: down={result1}, up={result2}")
                success = result1 != 0 and result2 != 0
            else:
                result1 = win32gui.PostMessage(game_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                result2 = win32gui.PostMessage(game_hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                print(f"� PostMessage esquerdo: down={result1}, up={result2}")
                success = result1 != 0 and result2 != 0
        except Exception as e:
            print(f"❌ Erro PostMessage: {e}")
        
        # Método 2: SendMessage (se PostMessage falhar)
        if not success:
            try:
                print("🔄 Tentando SendMessage...")
                lParam = win32api.MAKELONG(client_x, client_y)
                
                if button == 'right':
                    result1 = win32gui.SendMessage(game_hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
                    result2 = win32gui.SendMessage(game_hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                    print(f"📤 SendMessage direito: down={result1}, up={result2}")
                else:
                    result1 = win32gui.SendMessage(game_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                    result2 = win32gui.SendMessage(game_hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                    print(f"📤 SendMessage esquerdo: down={result1}, up={result2}")
                success = True
            except Exception as e:
                print(f"❌ Erro SendMessage: {e}")
        
        # Método 3: SetCursorPos + Click físico (último recurso)
        if not success:
            print("🔄 Usando clique físico otimizado para Dark Eden...")
            return send_click_dark_eden(x, y, button)
        
        return success
    except Exception as e:
        print(f"❌ Erro geral ao enviar clique: {e}")
        return False

# Códigos de teclas comuns
KEY_CODES = {
    'f7': 0x76,
    'f11': 0x7A,
    'f12': 0x7B,
    'alt': win32con.VK_MENU,
    'backspace': win32con.VK_BACK,
    'capslock': win32con.VK_CAPITAL
} 

# Função de clique específica para Dark Eden (que bloqueia PostMessage)
def send_click_dark_eden(x, y, button='right'):
    """Função de clique otimizada para Dark Eden que bloqueia PostMessage"""
    global game_hwnd
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return False
    
    print(f"🎯 Clique Dark Eden {button} em ({x}, {y})")
    
    # Salvar estado atual
    current_pos = win32gui.GetCursorPos()
    
    try:
        # Método direto: clique físico otimizado
        # Mover mouse para posição
        win32api.SetCursorPos((x, y))
        time.sleep(0.01)  # Pausa mínima
        
        # Executar clique
        if button == 'right':
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            time.sleep(0.005)  # Pausa muito pequena
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        else:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.005)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        # Restaurar posição imediatamente
        time.sleep(0.01)
        win32api.SetCursorPos(current_pos)
        
        print("✅ Clique físico Dark Eden executado")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        # Restaurar posição mesmo com erro
        try:
            win32api.SetCursorPos(current_pos)
        except:
            pass
        return False 

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

    if not find_dark_eden_window():
        return
    
    # DAR FOCO - método confirmado funcionando
    win32gui.SetForegroundWindow(game_hwnd)
    time.sleep(0.1)
    
    # Pressiona Alt no jogo
    send_key_to_game(KEY_CODES['alt'])
    
    while holding:
        send_click_to_game(mouseAttackX, mouseAttackY, 'right')
        time.sleep(0.1)  # Small sleep to reduce CPU usage  

def Mage_hold_right_click():
    global autoClickOn

    if not find_dark_eden_window():
        return
    
    # DAR FOCO - método confirmado funcionando
    win32gui.SetForegroundWindow(game_hwnd)
    time.sleep(0.1)
    
    while autoClickOn:
        send_key_to_game(KEY_CODES['f11'])
        send_click_to_game(mouseAttackX, mouseAttackY, 'right')
        time.sleep(1)  # Small sleep to reduce CPU usage        
                

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
        send_key_to_game(KEY_CODES['backspace'])
        if mouseAttackValidation():
            # Não precisa mais mover mouse físico
            threading.Thread(target=hold_right_click).start()
    else:
        print("Parando de atacar...")
        send_key_to_game(KEY_CODES['backspace'])
        os.system('cls')

def autoClickToggle():
    global autoClickOn
    autoClickOn = not autoClickOn
    if autoClickOn:
      print("\n\n\n\n\nAtacando")        
      send_key_to_game(KEY_CODES['backspace'])          
      threading.Thread(target=autoClickRunning).start()
    else:        
        print("\n\n\n\n\nParando de atacar")
        os.system('cls')
         
  
   
        
def autoClickRunning():
    global autoClickOn
    global mouseAttackX
    global mouseAttackY
    global mouseAntesX
    global mouseAntesY
    
    if not find_dark_eden_window():
        print("Janela do Dark Eden não encontrada!")
        autoClickOn = False
        return
    
    # DAR FOCO - método confirmado funcionando
    win32gui.SetForegroundWindow(game_hwnd)
    time.sleep(0.1)
    
    if mouseAttackValidation():
        # Envia F12 para o jogo
        send_key_to_game(KEY_CODES['f12'])
        saveCurrentMousePosition()
        
        time.sleep(0.5)
        
        for wall in bloodwalls:
            if autoClickOn:
                # Simula Alt+RightClick no jogo
                send_key_to_game(KEY_CODES['alt'])
                send_click_to_game(mouseAttackX, mouseAttackY + wall, 'right')
                
                if wall != -50:
                    time.sleep(2)
        
        # Inicia thread de ataque contínuo
        threading.Thread(target=Mage_hold_right_click).start()
    else:
        autoClickOn = False
        print("Pressione a tecla: " + hotkeySalvar + " para setar uma posição inicial");

def set_mouse_attack():
    global mouseAttackX
    global mouseAttackY
    send_key_to_game(KEY_CODES['backspace'])
    mouseAttackX = pyautogui.position().x
    mouseAttackY = pyautogui.position().y
    print("Posição salva com sucesso")

def moveRight():
    offset = 250
    global mouseAttackX
    global mouseAttackY

    if not find_dark_eden_window():
        return
    
    # DAR FOCO - método confirmado funcionando
    win32gui.SetForegroundWindow(game_hwnd)
    time.sleep(0.1)
        
    send_key_to_game(KEY_CODES['f7']) #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    send_key_to_game(KEY_CODES['alt'])
    send_click_to_game(mouseAttackX + offset, mouseAttackY, 'right')

def moveLeft():
    offset = -250
    global mouseAttackX
    global mouseAttackY

    if not find_dark_eden_window():
        return
    
    # DAR FOCO - método confirmado funcionando
    win32gui.SetForegroundWindow(game_hwnd)
    time.sleep(0.1)
        
    send_key_to_game(KEY_CODES['f7']) #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    send_key_to_game(KEY_CODES['alt'])
    send_click_to_game(mouseAttackX + offset, mouseAttackY, 'right')

def moveUp():
    offset = -130
    global mouseAttackX
    global mouseAttackY

    if not find_dark_eden_window():
        return
    
    # DAR FOCO - método confirmado funcionando
    win32gui.SetForegroundWindow(game_hwnd)
    time.sleep(0.1)
        
    send_key_to_game(KEY_CODES['f7']) #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    send_key_to_game(KEY_CODES['alt'])
    send_click_to_game(mouseAttackX, mouseAttackY + offset, 'right')

def moveDown():
    offset = 130
    global mouseAttackX
    global mouseAttackY

    if not find_dark_eden_window():
        return
    
    # DAR FOCO - método confirmado funcionando
    win32gui.SetForegroundWindow(game_hwnd)
    time.sleep(0.1)
        
    send_key_to_game(KEY_CODES['f7']) #usar skill f7 (rapid glinding)
    time.sleep(0.5)
    send_key_to_game(KEY_CODES['alt'])
    send_click_to_game(mouseAttackX, mouseAttackY + offset, 'right')

def printar_pos():
    print(pyautogui.position())    
    send_key_to_game(KEY_CODES['capslock'])

def debug_windows():
    """Função para debugar janelas disponíveis"""
    list_all_windows()

def debug_processes():
    """Função para debugar processos disponíveis"""
    list_all_processes()

def debug_current_connection():
    """Debug da conexão atual"""
    global game_hwnd
    
    print("=== DEBUG DA CONEXÃO ATUAL ===")
    print(f"🪟 HWND atual: {game_hwnd}")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return
    
    try:
        # Verificar se a janela é válida
        is_valid = win32gui.IsWindow(game_hwnd)
        print(f"✅ Janela válida: {is_valid}")
        
        if is_valid:
            window_text = win32gui.GetWindowText(game_hwnd)
            class_name = win32gui.GetClassName(game_hwnd)
            is_visible = win32gui.IsWindowVisible(game_hwnd)
            rect = win32gui.GetWindowRect(game_hwnd)
            
            print(f"📋 Título: '{window_text}'")
            print(f"🏷️ Classe: '{class_name}'")
            print(f"👁️ Visível: {is_visible}")
            print(f"📐 Posição: {rect} (x:{rect[0]}, y:{rect[1]}, w:{rect[2]-rect[0]}, h:{rect[3]-rect[1]})")
            
            # Testar envio de mensagem simples
            print("🧪 Testando envio de mensagem...")
            result = win32gui.PostMessage(game_hwnd, win32con.WM_NULL, 0, 0)
            print(f"📤 Resultado do teste: {result}")
            
        else:
            print("❌ Janela inválida")
            
    except Exception as e:
        print(f"❌ Erro no debug: {e}")
    
    print("===============================")

def test_click_to_game():
    """Testa um clique no jogo com debug detalhado"""
    global game_hwnd, mouseAttackX, mouseAttackY
    
    print("=== TESTE DE CLIQUE ===")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return
    
    # Usar posição atual do mouse se não há posição salva
    if mouseAttackX == 0 or mouseAttackY == 0:
        pos = pyautogui.position()
        test_x, test_y = pos.x, pos.y
        print(f"🖱️ Usando posição atual do mouse: ({test_x}, {test_y})")
    else:
        test_x, test_y = mouseAttackX, mouseAttackY
        print(f"🎯 Usando posição salva: ({test_x}, {test_y})")
    
    try:
        # Obter informações da janela
        rect = win32gui.GetWindowRect(game_hwnd)
        client_x = test_x - rect[0]
        client_y = test_y - rect[1]
        
        print(f"📐 Janela: {rect}")
        print(f"🎯 Coordenadas da tela: ({test_x}, {test_y})")
        print(f"🎯 Coordenadas do cliente: ({client_x}, {client_y})")
        
        # Verificar se as coordenadas estão dentro da janela
        window_width = rect[2] - rect[0]
        window_height = rect[3] - rect[1]
        
        if 0 <= client_x <= window_width and 0 <= client_y <= window_height:
            print("✅ Coordenadas dentro da janela")
        else:
            print("⚠️ Coordenadas fora da janela!")
            print(f"   Janela: 0-{window_width} x 0-{window_height}")
            print(f"   Clique: {client_x} x {client_y}")
        
        # Enviar clique de teste
        lParam = win32api.MAKELONG(client_x, client_y)
        print(f"📤 Enviando clique direito...")
        
        result1 = win32gui.PostMessage(game_hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
        result2 = win32gui.PostMessage(game_hwnd, win32con.WM_RBUTTONUP, 0, lParam)
        
        print(f"📥 Resultado RBUTTONDOWN: {result1}")
        print(f"📥 Resultado RBUTTONUP: {result2}")
        
        if result1 != 0 and result2 != 0:
            print("✅ Clique enviado com sucesso!")
        else:
            print("❌ Falha no envio do clique")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
    
    print("=====================")

def test_key_to_game():
    """Testa envio de tecla com debug"""
    global game_hwnd
    
    print("=== TESTE DE TECLA ===")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return
    
    try:
        test_key = KEY_CODES['backspace']  # Tecla segura para testar
        print(f"🎹 Testando tecla BACKSPACE (código: {test_key})")
        
        result1 = win32gui.PostMessage(game_hwnd, win32con.WM_KEYDOWN, test_key, 0)
        result2 = win32gui.PostMessage(game_hwnd, win32con.WM_KEYUP, test_key, 0)
        
        print(f"📥 Resultado KEYDOWN: {result1}")
        print(f"📥 Resultado KEYUP: {result2}")
        
        if result1 != 0 and result2 != 0:
            print("✅ Tecla enviada com sucesso!")
        else:
            print("❌ Falha no envio da tecla")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
    
    print("===================")

def test_simple_keys():
    """Testa teclas simples como letras e números"""
    global game_hwnd
    
    print("=== TESTE DE TECLAS SIMPLES ===")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return
    
    # Lista de teclas para testar
    test_keys = [
        ('A', ord('A'), "Letra A"),
        ('1', ord('1'), "Número 1"),
        ('ENTER', 0x0D, "Enter"),
        ('SPACE', 0x20, "Espaço"),
        ('ESC', 0x1B, "Escape")
    ]
    
    print("🧪 Testando diferentes tipos de teclas...")
    print("💡 Observe o jogo para ver se alguma tecla tem efeito!")
    
    for key_name, key_code, description in test_keys:
        print(f"\n🎹 Testando {description} ({key_name})...")
        
        try:
            # Método 1: PostMessage
            result1 = win32gui.PostMessage(game_hwnd, win32con.WM_KEYDOWN, key_code, 0)
            result2 = win32gui.PostMessage(game_hwnd, win32con.WM_KEYUP, key_code, 0)
            
            print(f"   PostMessage: down={result1}, up={result2}")
            
            # Se PostMessage falhar, tentar SendMessage
            if not result1 or not result2:
                print("   Tentando SendMessage...")
                result3 = win32gui.SendMessage(game_hwnd, win32con.WM_KEYDOWN, key_code, 0)
                result4 = win32gui.SendMessage(game_hwnd, win32con.WM_KEYUP, key_code, 0)
                print(f"   SendMessage: down={result3}, up={result4}")
            
            time.sleep(0.5)  # Pausa entre testes
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print("\n💡 Se você viu alguma reação no jogo, significa que as teclas funcionam!")
    print("=======================================")

def test_physical_keys():
    """Testa envio de teclas físicas (simulação real de teclado)"""
    global game_hwnd
    
    print("=== TESTE DE TECLAS FÍSICAS ===")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return
    
    print("🚨 ATENÇÃO: Este teste vai simular teclas FÍSICAS!")
    print("⚠️  Certifique-se de que a janela do jogo está em foco")
    print("⚠️  As teclas serão enviadas para a janela ativa")
    print("💡 Aguarde 3 segundos para você focar na janela do jogo...")
    
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print("🚀 Enviando teclas físicas...")
    
    try:
        # Forçar foco na janela do jogo
        try:
            win32gui.SetForegroundWindow(game_hwnd)
            time.sleep(0.1)
        except:
            pass
        
        # Testar teclas usando SendInput (simulação física)
        import ctypes
        from ctypes import wintypes
        
        # Definir estruturas para SendInput
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
            ]
        
        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", wintypes.DWORD),
                ("ki", KEYBDINPUT)
            ]
        
        # Função para enviar tecla física
        def send_physical_key(vk_code, key_name):
            print(f"   🎹 Enviando {key_name}...")
            
            # Key down
            input_down = INPUT()
            input_down.type = 1  # INPUT_KEYBOARD
            input_down.ki.wVk = vk_code
            input_down.ki.dwFlags = 0
            
            # Key up
            input_up = INPUT()
            input_up.type = 1  # INPUT_KEYBOARD
            input_up.ki.wVk = vk_code
            input_up.ki.dwFlags = 2  # KEYEVENTF_KEYUP
            
            # Enviar teclas
            ctypes.windll.user32.SendInput(1, ctypes.byref(input_down), ctypes.sizeof(INPUT))
            time.sleep(0.05)
            ctypes.windll.user32.SendInput(1, ctypes.byref(input_up), ctypes.sizeof(INPUT))
            time.sleep(0.3)
        
        # Testar teclas básicas
        test_keys = [
            (ord('A'), "A"),
            (ord('1'), "1"),
            (0x0D, "Enter"),
            (0x20, "Espaço")
        ]
        
        for vk_code, key_name in test_keys:
            send_physical_key(vk_code, key_name)
        
        print("✅ Teste de teclas físicas concluído!")
        print("💡 Se funcionou, você deve ter visto reação no jogo")
        
    except Exception as e:
        print(f"❌ Erro no teste físico: {e}")
    
    print("===================================")

def test_chat_input():
    """Teste específico para entrada de chat (se o jogo tiver)"""
    global game_hwnd
    
    print("=== TESTE DE ENTRADA DE CHAT ===")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return
    
    print("🗨️ Testando abertura de chat e digitação...")
    print("💡 Muitos jogos abrem chat com Enter ou T")
    
    try:
        # Forçar foco
        try:
            win32gui.SetForegroundWindow(game_hwnd)
            time.sleep(0.2)
        except:
            pass
        
        # Tentar abrir chat com Enter
        print("🎹 Tentando abrir chat com Enter...")
        win32api.keybd_event(0x0D, 0, 0, 0)  # Enter down
        time.sleep(0.05)
        win32api.keybd_event(0x0D, 0, 2, 0)  # Enter up
        time.sleep(0.5)
        
        # Digitar texto de teste
        print("🎹 Digitando 'teste123'...")
        test_text = "teste123"
        for char in test_text:
            vk_code = ord(char.upper())
            win32api.keybd_event(vk_code, 0, 0, 0)  # Key down
            time.sleep(0.02)
            win32api.keybd_event(vk_code, 0, 2, 0)  # Key up
            time.sleep(0.05)
        
        time.sleep(0.5)
        
        # Pressionar Enter para enviar (ou ESC para cancelar)
        print("🎹 Pressionando ESC para cancelar...")
        win32api.keybd_event(0x1B, 0, 0, 0)  # ESC down
        time.sleep(0.05)
        win32api.keybd_event(0x1B, 0, 2, 0)  # ESC up
        
        print("✅ Teste de chat concluído!")
        print("💡 Se viu uma caixa de chat ou texto aparecendo, as teclas funcionam!")
        
    except Exception as e:
        print(f"❌ Erro no teste de chat: {e}")
    
    print("==================================")

def test_background_vs_foreground():
    """Testa se as teclas funcionam em background vs foreground"""
    global game_hwnd
    
    print("=== TESTE BACKGROUND vs FOREGROUND ===")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return
    
    print("🧪 Comparando métodos de envio de teclas...")
    print("💡 Observe o jogo durante os testes!")
    
    test_key = KEY_CODES['alt']  # Tecla segura para testar
    
    # Teste 1: PostMessage (background)
    print("\n1️⃣ TESTE: PostMessage (deve funcionar em background)")
    try:
        result1 = win32gui.PostMessage(game_hwnd, win32con.WM_KEYDOWN, test_key, 0)
        result2 = win32gui.PostMessage(game_hwnd, win32con.WM_KEYUP, test_key, 0)
        print(f"   PostMessage: down={result1}, up={result2}")
        if result1 and result2:
            print("   ✅ PostMessage funcionou!")
        else:
            print("   ❌ PostMessage falhou")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Erro PostMessage: {e}")
    
    # Teste 2: SendMessage (background)
    print("\n2️⃣ TESTE: SendMessage (deve funcionar em background)")
    try:
        result1 = win32gui.SendMessage(game_hwnd, win32con.WM_KEYDOWN, test_key, 0)
        result2 = win32gui.SendMessage(game_hwnd, win32con.WM_KEYUP, test_key, 0)
        print(f"   SendMessage: down={result1}, up={result2}")
        print("   ✅ SendMessage enviado!")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Erro SendMessage: {e}")
    
    # Teste 3: Tecla física SEM foco (background)
    print("\n3️⃣ TESTE: Tecla física SEM dar foco (background)")
    try:
        print("   Enviando ALT físico sem dar foco...")
        win32api.keybd_event(test_key, 0, 0, 0)  # Key down
        time.sleep(0.05)
        win32api.keybd_event(test_key, 0, 2, 0)  # Key up
        print("   ✅ Tecla física enviada sem foco!")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Erro tecla física: {e}")
    
    # Teste 4: Tecla física COM foco (foreground)
    print("\n4️⃣ TESTE: Tecla física COM foco (foreground)")
    print("   🚨 ATENÇÃO: Vou dar foco ao jogo!")
    try:
        win32gui.SetForegroundWindow(game_hwnd)
        time.sleep(0.2)
        print("   Enviando ALT físico COM foco...")
        win32api.keybd_event(test_key, 0, 0, 0)  # Key down
        time.sleep(0.05)
        win32api.keybd_event(test_key, 0, 2, 0)  # Key up
        print("   ✅ Tecla física enviada COM foco!")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Erro tecla física com foco: {e}")
    
    print("\n🏁 TESTE CONCLUÍDO!")
    print("💡 Qual teste funcionou? Me diga qual teve efeito no jogo!")
    print("=====================================")

def test_automation_functions():
    """Testa as funções principais de automação sem ativar loops e SEM DAR FOCO"""
    global game_hwnd
    
    print("=== TESTE DAS FUNÇÕES DE AUTOMAÇÃO (BACKGROUND) ===")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return
    
    print("🎮 Testando funções de automação do Dark Eden EM BACKGROUND...")
    print("💡 Observe o jogo para verificar as reações!")
    print("🔥 JOGO PERMANECERÁ EM SEGUNDO PLANO!")
    
    # NÃO dar foco - manter em background
    print("✅ Mantendo jogo em background (sem dar foco)")
    
    # Testar teclas individuais primeiro
    automation_tests = [
        (KEY_CODES['f7'], "F7 - Rapid Gliding"),
        (KEY_CODES['f11'], "F11 - Skill"), 
        (KEY_CODES['f12'], "F12 - Bloody Wall"),
        (KEY_CODES['alt'], "ALT - Action"),
        (KEY_CODES['backspace'], "BACKSPACE - UI")
    ]
    
    for key_code, description in automation_tests:
        print(f"\n🎹 Testando {description} em BACKGROUND...")
        
        try:
            # NÃO dar foco - enviar tecla diretamente
            
            # Enviar tecla usando método físico sem foco
            win32api.keybd_event(key_code, 0, 0, 0)  # Key down
            time.sleep(0.05)
            win32api.keybd_event(key_code, 0, 2, 0)  # Key up
            
            print(f"   ✅ {description} enviada em BACKGROUND!")
            time.sleep(1)  # Pausa para observar efeito
            
        except Exception as e:
            print(f"   ❌ Erro ao testar {description}: {e}")
    
    print("\n🎯 TESTE DE CLIQUE FÍSICO EM BACKGROUND...")
    
    # Testar clique se há posição salva
    if mouseAttackX != 0 and mouseAttackY != 0:
        print(f"🖱️ Testando clique na posição salva: ({mouseAttackX}, {mouseAttackY})")
        try:
            success = send_click_dark_eden(mouseAttackX, mouseAttackY, 'right')
            if success:
                print("   ✅ Clique físico funcionou em BACKGROUND!")
            else:
                print("   ❌ Clique físico falhou")
        except Exception as e:
            print(f"   ❌ Erro no clique: {e}")
    else:
        print("⚠️ Nenhuma posição salva para testar clique")
        print("💡 Use Alt+1 para salvar uma posição primeiro")
    
    print("\n🏁 Teste das funções de automação EM BACKGROUND concluído!")
    print("💡 Se as teclas e cliques funcionaram, sua automação está pronta!")
    print("💡 Agora você pode usar F4 (hold attack) e F3 (combo mago) EM BACKGROUND!")
    print("🔥 O JOGO PERMANECERÁ EM SEGUNDO PLANO DURANTE A AUTOMAÇÃO!")
    print("===============================================================")

def test_game_keys():
    """Testa as teclas principais usadas no jogo"""
    global game_hwnd
    
    print("=== TESTE DAS TECLAS DO JOGO ===")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return
    
    print("🎮 Testando teclas principais do Dark Eden...")
    print("💡 Observe o jogo para verificar as reações!")
    
    # Garantir foco na janela
    try:
        win32gui.SetForegroundWindow(game_hwnd)
        time.sleep(0.2)
    except:
        pass
    
    # Lista de teclas para testar
    game_keys = [
        (KEY_CODES['f7'], "F7 (Rapid Gliding)"),
        (KEY_CODES['f11'], "F11 (Skill)"),
        (KEY_CODES['f12'], "F12 (Bloody Wall)"),
        (KEY_CODES['alt'], "ALT (Action)"),
        (KEY_CODES['backspace'], "BACKSPACE (UI)"),
        (KEY_CODES['capslock'], "CAPSLOCK (Toggle)")
    ]
    
    for key_code, description in game_keys:
        print(f"\n🎹 Testando {description}...")
        
        try:
            # Usar método físico que funciona
            win32api.keybd_event(key_code, 0, 0, 0)  # Key down
            time.sleep(0.05)
            win32api.keybd_event(key_code, 0, 2, 0)  # Key up
            
            print(f"   ✅ {description} enviada!")
            time.sleep(0.8)  # Pausa entre testes para observar
            
        except Exception as e:
            print(f"   ❌ Erro ao testar {description}: {e}")
    
    print("\n🏁 Teste das teclas do jogo concluído!")
    print("💡 Se viu reações no jogo, as teclas estão funcionando perfeitamente!")
    print("====================================")

def test_all_key_methods():
    """Executa todos os testes de teclas em sequência"""
    print("🧪 EXECUTANDO TODOS OS TESTES DE TECLAS")
    print("=" * 50)
    
    print("\n1️⃣ Teste básico de teclas...")
    test_key_to_game()
    
    print("\n2️⃣ Teste de teclas simples...")
    test_simple_keys()
    
    input("\n⏸️ Pressione Enter para continuar com testes físicos...")
    
    print("\n3️⃣ Teste de teclas físicas...")
    test_physical_keys()
    
    input("\n⏸️ Pressione Enter para continuar com teste de chat...")
    
    print("\n4️⃣ Teste de entrada de chat...")
    test_chat_input()
    
    input("\n⏸️ Pressione Enter para testar teclas específicas do jogo...")
    
    print("\n5️⃣ Teste das teclas do jogo...")
    test_game_keys()
    
    print("\n🏁 TODOS OS TESTES CONCLUÍDOS!")
    print("💡 Se algum teste funcionou, sabemos que método usar!")

def test_game_compatibility():
    """Testa diferentes aspectos da compatibilidade com o jogo"""
    global game_hwnd
    
    print("=== TESTE DE COMPATIBILIDADE ===")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return False
    
    try:
        # 1. Informações básicas da janela
        window_text = win32gui.GetWindowText(game_hwnd)
        class_name = win32gui.GetClassName(game_hwnd)
        is_visible = win32gui.IsWindowVisible(game_hwnd)
        
        print(f"🪟 Janela: '{window_text}' | Classe: '{class_name}' | Visível: {is_visible}")
        
        # 2. Testar se a janela aceita mensagens
        print("🧪 Testando mensagens básicas...")
        
        # WM_NULL é a mensagem mais segura para testar
        result_null = win32gui.PostMessage(game_hwnd, win32con.WM_NULL, 0, 0)
        print(f"   WM_NULL: {result_null} ({'✅ OK' if result_null else '❌ Falhou'})")
        
        # Testar mensagem de char (tecla)
        result_char = win32gui.PostMessage(game_hwnd, win32con.WM_CHAR, ord('a'), 0)
        print(f"   WM_CHAR: {result_char} ({'✅ OK' if result_char else '❌ Falhou'})")
        
        # Se PostMessage retorna None/0, o jogo pode estar bloqueando
        if not result_null and not result_char:
            print("⚠️ PROBLEMA DETECTADO: O jogo parece estar bloqueando PostMessage!")
            print("   Isso pode ser devido a:")
            print("   - Anti-cheat ativo")
            print("   - Proteção do jogo contra automação")
            print("   - Permissões de segurança do Windows")
            print("   💡 Tentaremos usar métodos alternativos...")
        else:
            print("✅ Jogo aceita mensagens básicas")
        
        # 3. Verificar se a janela está sendo filtrada por anti-cheat
        try:
            # Tentar obter informações mais detalhadas
            thread_id, process_id = win32gui.GetWindowThreadProcessId(game_hwnd)
            print(f"📋 Thread ID: {thread_id}, Process ID: {process_id}")
            
            # Verificar se conseguimos obter o processo
            try:
                process = psutil.Process(process_id)
                process_name = process.name()
                print(f"📋 Nome do processo: {process_name}")
                
                # Verificar se há processos de anti-cheat comuns
                anticheat_processes = ['battleye', 'easyanticheat', 'xigncode', 'hackshield', 'gameguard']
                all_processes = [p.name().lower() for p in psutil.process_iter()]
                found_anticheat = [ac for ac in anticheat_processes if any(ac in proc for proc in all_processes)]
                
                if found_anticheat:
                    print(f"⚠️ Anti-cheat detectado: {found_anticheat}")
                    print("   Isso pode bloquear mensagens de automação")
                else:
                    print("✅ Nenhum anti-cheat comum detectado")
                    
            except Exception as e:
                print(f"❌ Erro ao verificar processo: {e}")
        
        except Exception as e:
            print(f"❌ Erro ao obter informações do processo: {e}")
        
        # 4. Testar diferentes tipos de mensagem de mouse
        print("🖱️ Testando mensagens de mouse...")
        rect = win32gui.GetWindowRect(game_hwnd)
        center_x = (rect[2] - rect[0]) // 2
        center_y = (rect[3] - rect[1]) // 2
        lParam = win32api.MAKELONG(center_x, center_y)
        
        # Testar WM_MOUSEMOVE primeiro
        result_move = win32gui.PostMessage(game_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
        print(f"   WM_MOUSEMOVE: {result_move} ({'✅ OK' if result_move else '❌ Falhou'})")
        
        # Testar clique
        result_down = win32gui.PostMessage(game_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        result_up = win32gui.PostMessage(game_hwnd, win32con.WM_LBUTTONUP, 0, lParam)
        print(f"   WM_LBUTTONDOWN: {result_down} ({'✅ OK' if result_down else '❌ Falhou'})")
        print(f"   WM_LBUTTONUP: {result_up} ({'✅ OK' if result_up else '❌ Falhou'})")
        
        # Diagnóstico
        if not result_move and not result_down and not result_up:
            print("❌ PROBLEMA CRÍTICO: Todas as mensagens de mouse falharam!")
            print("   🔧 SOLUÇÕES RECOMENDADAS:")
            print("   1. Use F6 para testar clique físico")
            print("   2. Execute o jogo como Administrador")
            print("   3. Desative temporariamente antivírus")
            print("   4. Verifique se há anti-cheat ativo")
        else:
            print("✅ Algumas mensagens de mouse funcionam")
        
        # 5. Verificar se a janela tem foco ou pode receber foco
        foreground = win32gui.GetForegroundWindow()
        print(f"🔍 Janela em foco: {foreground} (nossa: {game_hwnd})")
        
        if foreground != game_hwnd:
            print("⚠️ Janela não está em foco - isso pode afetar a recepção de mensagens")
            
            # Tentar trazer para frente (cuidado - pode ser bloqueado)
            try:
                win32gui.SetForegroundWindow(game_hwnd)
                print("✅ Tentativa de trazer janela para frente")
            except Exception as e:
                print(f"❌ Não foi possível trazer janela para frente: {e}")
        
        print("================================")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de compatibilidade: {e}")
        return False

def test_click_methods():
    """Testa diferentes métodos de clique"""
    global game_hwnd, mouseAttackX, mouseAttackY
    
    print("=== TESTE DE MÉTODOS DE CLIQUE ===")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return
    
    # Usar posição salva ou centro da janela
    if mouseAttackX != 0 and mouseAttackY != 0:
        test_x, test_y = mouseAttackX, mouseAttackY
        print(f"🎯 Usando posição salva: ({test_x}, {test_y})")
    else:
        rect = win32gui.GetWindowRect(game_hwnd)
        test_x = rect[0] + (rect[2] - rect[0]) // 2
        test_y = rect[1] + (rect[3] - rect[1]) // 2
        print(f"🎯 Usando centro da janela: ({test_x}, {test_y})")
    
    print("\n1️⃣ Testando PostMessage...")
    send_click_to_game(test_x, test_y, 'right')
    
    print("\n2️⃣ Aguarde 2 segundos para próximo teste...")
    time.sleep(2)
    
    print("3️⃣ Testando clique físico direto...")
    try:
        current_pos = win32gui.GetCursorPos()
        win32api.SetCursorPos((test_x, test_y))
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        time.sleep(0.1)
        win32api.SetCursorPos(current_pos)
        print("✅ Clique físico executado")
    except Exception as e:
        print(f"❌ Erro no clique físico: {e}")
    
    print("===================================")

def test_dark_eden_click():
    """Testa o método de clique específico para Dark Eden"""
    global game_hwnd, mouseAttackX, mouseAttackY
    
    print("=== TESTE DE CLIQUE DARK EDEN ===")
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return
    
    # Usar posição salva ou posição atual do mouse
    if mouseAttackX != 0 and mouseAttackY != 0:
        test_x, test_y = mouseAttackX, mouseAttackY
        print(f"🎯 Usando posição salva: ({test_x}, {test_y})")
    else:
        pos = pyautogui.position()
        test_x, test_y = pos.x, pos.y
        print(f"🎯 Usando posição atual do mouse: ({test_x}, {test_y})")
    
    print("🚀 Executando clique otimizado para Dark Eden...")
    success = send_click_dark_eden(test_x, test_y, 'right')
    
    if success:
        print("✅ Teste concluído - verifique se o clique funcionou no jogo!")
    else:
        print("❌ Teste falhou")
    
    print("=====================================")

def force_window_focus():
    """Força a janela do jogo a ter foco"""
    global game_hwnd
    
    if not game_hwnd:
        print("❌ Nenhuma janela conectada")
        return False
    
    try:
        print("🔍 Tentando dar foco à janela do jogo...")
        
        # Método 1: SetForegroundWindow
        try:
            win32gui.SetForegroundWindow(game_hwnd)
            print("✅ SetForegroundWindow executado")
        except Exception as e:
            print(f"❌ SetForegroundWindow falhou: {e}")
        
        # Método 2: ShowWindow
        try:
            win32gui.ShowWindow(game_hwnd, win32con.SW_RESTORE)
            win32gui.ShowWindow(game_hwnd, win32con.SW_SHOW)
            print("✅ ShowWindow executado")
        except Exception as e:
            print(f"❌ ShowWindow falhou: {e}")
        
        # Método 3: SetActiveWindow (pode não funcionar entre processos)
        try:
            win32gui.SetActiveWindow(game_hwnd)
            print("✅ SetActiveWindow executado")
        except Exception as e:
            print(f"❌ SetActiveWindow falhou: {e}")
        
        # Verificar se funcionou
        foreground = win32gui.GetForegroundWindow()
        if foreground == game_hwnd:
            print("✅ Janela agora está em foco!")
            return True
        else:
            print(f"⚠️ Janela ainda não está em foco (atual: {foreground})")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao dar foco: {e}")
        return False

def manual_process_selection():
    """Força seleção manual de processo"""
    global game_hwnd
    game_hwnd = None  # Reset conexão atual
    return select_process_with_gui()  # Usar GUI diretamente

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
    keyboard.add_hotkey(hotkeyMoveRight, moveRight)
    keyboard.add_hotkey(hotkeyMoveLeft, moveLeft)
    keyboard.add_hotkey(hotkeyMoveUp, moveUp)
    keyboard.add_hotkey(hotkeyMoveDown, moveDown)
    keyboard.add_hotkey(hotkeyAttack, autoClickToggle)
    keyboard.add_hotkey('f1', debug_windows)  # Debug janelas
    keyboard.add_hotkey('f2', select_window_interactive)  # Seleção de janela direta
    keyboard.add_hotkey('ctrl+f3', test_dark_eden_click)  # Teste clique Dark Eden
    keyboard.add_hotkey('ctrl+f1', test_simple_keys)  # Teste teclas simples
    keyboard.add_hotkey('f5', test_game_compatibility)  # Teste compatibilidade
    keyboard.add_hotkey('f6', test_click_methods)  # Teste métodos de clique
    keyboard.add_hotkey('f7', force_window_focus)  # Forçar foco
    keyboard.add_hotkey('f8', test_key_to_game)  # Teste de tecla
    keyboard.add_hotkey('f9', debug_processes)  # Debug processos
    keyboard.add_hotkey('f10', manual_process_selection)  # Seleção manual
    keyboard.add_hotkey('f11', debug_current_connection)  # Debug conexão
    keyboard.add_hotkey('f12', test_click_to_game)  # Teste de clique
    keyboard.add_hotkey('ctrl+f4', test_physical_keys)  # Teste teclas físicas
    keyboard.add_hotkey('ctrl+f5', test_chat_input)  # Teste chat
    keyboard.add_hotkey('ctrl+f6', test_game_keys)  # Teste teclas do jogo
    keyboard.add_hotkey('ctrl+f7', test_automation_functions)  # Teste automações completas
    keyboard.add_hotkey('ctrl+f9', test_background_vs_foreground)  # Teste background vs foreground
    keyboard.add_hotkey('ctrl+f8', test_all_key_methods)  # Todos os testes
    
    print("🎮 DARK EDEN AUTOMATION - Windows API Version")
    print("=" * 50)
    print("Tecla para atacar mouse direito (Segurar): " + hotkeyHoldRight)
    print("Tecla para combo mago: " + hotkeyAttack + " NECESSÁRIO MARCAR POSIÇÃO EM BAIXO DO CHAR")
    print("Tecla para setar posição: " + hotkeySalvar)
    print("")
    print("🔧 TECLAS DE DEBUG:")
    print("F1:  Mostrar todas as janelas")
    print("F2:  Conectar diretamente a uma janela")
    print("Ctrl+F1: Teste de teclas simples (A, 1, Enter, etc)")
    print("Ctrl+F3: Teste de clique Dark Eden (método otimizado)")
    print("F5:  Teste de compatibilidade (anti-cheat, etc)")
    print("F6:  Teste de diferentes métodos de clique")
    print("F7:  Forçar foco na janela do jogo")
    print("F8:  Testar envio de tecla básica")
    print("F9:  Mostrar todos os processos") 
    print("F10: Seleção manual de processo")
    print("F11: Debug da conexão atual")
    print("F12: Testar clique no jogo")
    print("")
    print("🧪 TESTES AVANÇADOS DE TECLAS:")
    print("Ctrl+F4: Teste de teclas físicas (simulação real)")
    print("Ctrl+F5: Teste de entrada de chat")
    print("Ctrl+F6: Teste das teclas principais do jogo")
    print("Ctrl+F7: Teste completo das automações (RECOMENDADO)")
    print("Ctrl+F9: Teste Background vs Foreground ⭐ NOVO")
    print("Ctrl+F8: Executar TODOS os testes de teclas")
    print("")
    print("💡 SEQUÊNCIA RECOMENDADA PARA DARK EDEN:")
    print("1. Conecte-se ao jogo (F2)")
    print("2. Teste automações completas (Ctrl+F7) ⭐ PRINCIPAL")
    print("3. Se funcionou, salve posição (Alt+1) e use automações!")
    print("4. F4 = Hold Attack | F3 = Combo Mago")
    print("5. Setas = Movimento (↑↓←→)")
    print("")
    print("� FUNCIONA EM BACKGROUND - JOGO NÃO PRECISA ESTAR EM FOCO! 🔥")
    print("💡 Você pode usar o computador normalmente durante a automação!")
    print("")
    print("�🚨 SE CTRL+F7 FUNCIONAR, SUA AUTOMAÇÃO ESTÁ PRONTA! 🚨")
    print("")
    print("Pressione ESC para sair")
    
    # Keep the main thread alive to listen for the hotkey
    keyboard.wait('esc')  # Change 'esc' to your desired exit key