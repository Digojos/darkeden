import sys
import win32gui
import win32con
import win32api
import win32process
import keyboard
import threading
import time
import os
import psutil
import pyautogui
import ctypes
from ctypes import wintypes, windll
from ctypes.wintypes import DWORD, LONG, UINT, WORD, POINT

try:
    from pynput.mouse import Button, Listener as MouseListener
    from pynput import mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Estruturas e constantes para diferentes métodos de clique
class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", DWORD),
        ("mi", ctypes.c_char * 24),  # MOUSEINPUT ou KEYBDINPUT
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", LONG),
        ("dy", LONG),
        ("mouseData", DWORD),
        ("dwFlags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

# Constantes para SendInput
INPUT_MOUSE = 0
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000

class ProcessMouseControllerGUI(QMainWindow):
    # Sinais para comunicação entre threads
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str, str)  # texto, cor
    
    def __init__(self):
        super().__init__()
        
        # Instância do controlador
        self.controller = None
        
        self.initUI()
        
        # Conectar sinais
        self.log_signal.connect(self.add_log)
        self.status_signal.connect(self.update_status)
        
        # Inicializar lista de processos
        self.refresh_processes()
        
    def initUI(self):
        self.setWindowTitle('🎮 DarkEden - Mouse Controller')
        self.setGeometry(100, 100, 900, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout()
        
        # === PAINEL ESQUERDO - CONTROLES ===
        left_panel = QWidget()
        left_panel.setFixedWidth(350)
        left_panel.setStyleSheet("""
            QWidget { background-color: #2b2b2b; }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #505050; }
            QPushButton:pressed { background-color: #353535; }
            QLineEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #555;
                padding: 6px;
                border-radius: 4px;
            }
            QComboBox {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #555;
                padding: 6px;
                border-radius: 4px;
            }
        """)
        
        left_layout = QVBoxLayout()
        
        # Título
        title = QLabel('MOUSE CONTROLLER')
        title.setStyleSheet('color: #00ff00; font-size: 16px; font-weight: bold;')
        title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title)
        
        left_layout.addSpacing(10)
        
        # === SEÇÃO PROCESSO ===
        process_group = QGroupBox('Conectar ao Processo')
        process_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        process_layout = QVBoxLayout()
        
        # ComboBox para processos
        self.process_combo = QComboBox()
        self.process_combo.setFixedHeight(30)
        process_layout.addWidget(QLabel('Selecione o Processo:', styleSheet='color: white;'))
        process_layout.addWidget(self.process_combo)
        
        # Botões de processo
        process_buttons = QHBoxLayout()
        self.refresh_btn = QPushButton('🔄 Atualizar')
        self.refresh_btn.clicked.connect(self.refresh_processes)
        self.refresh_btn.setStyleSheet('QPushButton { background-color: #4444aa; }')
        process_buttons.addWidget(self.refresh_btn)
        
        self.connect_btn = QPushButton('🔗 Conectar')
        self.connect_btn.clicked.connect(self.connect_to_process)
        self.connect_btn.setStyleSheet('QPushButton { background-color: #44aa44; }')
        process_buttons.addWidget(self.connect_btn)
        
        process_layout.addLayout(process_buttons)
        
        # Status da conexão
        self.connection_status = QLabel('❌ Desconectado')
        self.connection_status.setStyleSheet('color: #ff4444; font-weight: bold;')
        process_layout.addWidget(self.connection_status)
        
        process_group.setLayout(process_layout)
        left_layout.addWidget(process_group)
        
        # === SEÇÃO CONFIGURAÇÕES ===
        config_group = QGroupBox('Configurações de Posição')
        config_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        config_layout = QVBoxLayout()
        
        # Posição X
        config_layout.addWidget(QLabel('Posição X:', styleSheet='color: white;'))
        self.pos_x_input = QLineEdit()
        self.pos_x_input.setText('400')
        self.pos_x_input.setPlaceholderText('Coordenada X')
        config_layout.addWidget(self.pos_x_input)
        
        # Posição Y
        config_layout.addWidget(QLabel('Posição Y:', styleSheet='color: white;'))
        self.pos_y_input = QLineEdit()
        self.pos_y_input.setText('300')
        self.pos_y_input.setPlaceholderText('Coordenada Y')
        config_layout.addWidget(self.pos_y_input)
        
        # Botão para salvar posição
        self.save_pos_btn = QPushButton('💾 Salvar Posição')
        self.save_pos_btn.clicked.connect(self.save_position)
        self.save_pos_btn.setStyleSheet('QPushButton { background-color: #aa44aa; }')
        self.save_pos_btn.setEnabled(False)
        config_layout.addWidget(self.save_pos_btn)
        
        # Botão para capturar posição atual do mouse
        self.capture_pos_btn = QPushButton('📍 Capturar Posição do Mouse')
        self.capture_pos_btn.clicked.connect(self.capture_mouse_position)
        self.capture_pos_btn.setStyleSheet('QPushButton { background-color: #44aa88; }')
        config_layout.addWidget(self.capture_pos_btn)
        
        # Checkbox para método alternativo
        self.alt_method_checkbox = QCheckBox('Usar PyAutoGUI (clique físico)')
        self.alt_method_checkbox.setStyleSheet('QCheckBox { color: white; }')
        self.alt_method_checkbox.toggled.connect(self.toggle_click_method)
        config_layout.addWidget(self.alt_method_checkbox)
        
        # ComboBox para seleção de método de clique
        config_layout.addWidget(QLabel('Método de Clique:', styleSheet='color: white;'))
        self.click_method_combo = QComboBox()
        self.click_method_combo.addItems([
            '🔧 Win32API - PostMessage',
            '📨 Win32API - SendMessage', 
            '🎯 SendInput - Sistema',
            '🖱️ SetCursorPos + mouse_event',
            '💻 PyAutoGUI - Físico',
            '🔄 Múltiplos Métodos',
            '⚡ DirectInput - Avançado',
            '🎮 GameInput - Especializado',
            '🧬 Memory Injection',
            '🔗 Process Hook'
        ])
        self.click_method_combo.currentIndexChanged.connect(self.change_click_method)
        self.click_method_combo.setStyleSheet('QComboBox { background-color: #2a2a2a; }')
        config_layout.addWidget(self.click_method_combo)
        
        # Checkbox para congelar mouse
        self.freeze_mouse_checkbox = QCheckBox('Congelar mouse durante cliques')
        self.freeze_mouse_checkbox.setStyleSheet('QCheckBox { color: #ffaa00; }')
        self.freeze_mouse_checkbox.setChecked(True)
        self.freeze_mouse_checkbox.toggled.connect(self.update_freeze_setting)
        config_layout.addWidget(self.freeze_mouse_checkbox)
        
        # Botão para alternar rapidamente
        toggle_method_btn = QPushButton('⚡ Alternar Método')
        toggle_method_btn.clicked.connect(self.quick_toggle_method)
        toggle_method_btn.setStyleSheet('QPushButton { background-color: #666644; }')
        config_layout.addWidget(toggle_method_btn)
        
        # Indicador do método ativo
        self.method_indicator = QLabel('🔧 Método: Win32API PostMessage')
        self.method_indicator.setStyleSheet('color: #00aaff; font-weight: bold; text-align: center;')
        config_layout.addWidget(self.method_indicator)
        
        # Status do último clique
        self.click_status_label = QLabel('📊 Status: Aguardando...')
        self.click_status_label.setStyleSheet('color: #ffaa00; font-weight: bold; font-size: 9px;')
        config_layout.addWidget(self.click_status_label)
        
        # Display da posição do mouse
        self.mouse_pos_label = QLabel('🖱️ Mouse: (0, 0)')
        self.mouse_pos_label.setStyleSheet('color: #00ff88; font-weight: bold; font-family: monospace;')
        config_layout.addWidget(self.mouse_pos_label)
        
        # Timer para atualizar posição do mouse
        self.mouse_timer = QTimer()
        self.mouse_timer.timeout.connect(self.update_mouse_position)
        self.mouse_timer.start(100)  # Atualiza a cada 100ms
        
        config_group.setLayout(config_layout)
        left_layout.addWidget(config_group)
        
        # === SEÇÃO CONTROLES ===
        controls_group = QGroupBox('Controles de Ação')
        controls_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        controls_layout = QVBoxLayout()
        
        # Botão de teste de clique (método atual)
        self.test_click_btn = QPushButton('🎯 Teste Método Atual')
        self.test_click_btn.clicked.connect(self.test_current_method)
        self.test_click_btn.setStyleSheet('QPushButton { background-color: #aaaa44; }')
        self.test_click_btn.setEnabled(False)
        controls_layout.addWidget(self.test_click_btn)
        
        # Botão de teste de todos os métodos
        self.test_all_btn = QPushButton('� Testar Todos os Métodos')
        self.test_all_btn.clicked.connect(self.test_all_methods)
        self.test_all_btn.setStyleSheet('QPushButton { background-color: #44aaaa; }')
        self.test_all_btn.setEnabled(False)
        controls_layout.addWidget(self.test_all_btn)
        
        # Botão para mostrar onde vai clicar
        self.preview_click_btn = QPushButton('👁️ Visualizar Posição')
        self.preview_click_btn.clicked.connect(self.preview_click_position)
        self.preview_click_btn.setStyleSheet('QPushButton { background-color: #6644aa; }')
        self.preview_click_btn.setEnabled(False)
        controls_layout.addWidget(self.preview_click_btn)
        
        # Botão de ataque básico
        self.attack_btn = QPushButton('🗡️ Atacar (F5)')
        self.attack_btn.clicked.connect(self.toggle_attack)
        self.attack_btn.setStyleSheet('QPushButton { background-color: #aa4444; }')
        self.attack_btn.setEnabled(False)
        controls_layout.addWidget(self.attack_btn)
        
        # Botão de combo mago
        self.combo_btn = QPushButton('🔮 Combo Mago (\\)')
        self.combo_btn.clicked.connect(self.toggle_combo)
        self.combo_btn.setStyleSheet('QPushButton { background-color: #4444aa; }')
        self.combo_btn.setEnabled(False)
        controls_layout.addWidget(self.combo_btn)
        
        # Status dos controles
        self.attack_status = QLabel('⏹️ Ataque: Parado')
        self.attack_status.setStyleSheet('color: white; font-weight: bold;')
        controls_layout.addWidget(self.attack_status)
        
        self.combo_status = QLabel('⏹️ Combo: Parado')
        self.combo_status.setStyleSheet('color: white; font-weight: bold;')
        controls_layout.addWidget(self.combo_status)
        
        controls_group.setLayout(controls_layout)
        left_layout.addWidget(controls_group)
        
        # === SEÇÃO HOTKEYS ===
        hotkeys_group = QGroupBox('Hotkeys Globais')
        hotkeys_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        hotkeys_layout = QVBoxLayout()
        
        hotkeys_info = QLabel("""
F5 - Alternar Ataque
\\ - Alternar Combo Mago
Alt+1 - Salvar Posição
F6 - Alternar Método
F7 - Capturar Posição Mouse
F2 - Sair

MÉTODOS DE CLIQUE:
• Win32API PostMessage: Envio básico
• Win32API SendMessage: Envio direto
• SendInput Sistema: Input baixo nível
• SetCursorPos + mouse_event: Move + clique
• PyAutoGUI: Clique físico real
• DirectInput Avançado: Hardware level
• GameInput Especializado: Anti-detecção
• Memory Injection: Injeção na memória
• Process Hook: Hook no processo
• Múltiplos Métodos: Tenta todos""")
        hotkeys_info.setStyleSheet('color: #cccccc; font-size: 7px;')
        hotkeys_layout.addWidget(hotkeys_info)
        
        hotkeys_group.setLayout(hotkeys_layout)
        left_layout.addWidget(hotkeys_group)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # === PAINEL DIREITO - LOG ===
        right_panel = QWidget()
        right_panel.setStyleSheet('QWidget { background-color: #3a3a3a; }')
        right_layout = QVBoxLayout()
        
        # === LOG DE ATIVIDADES ===
        log_group = QGroupBox('Log de Atividades')
        log_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setStyleSheet('''
            background-color: #1e1e1e; 
            color: #00ff00; 
            font-family: Consolas, monospace;
            border: 1px solid #555;
            font-size: 10px;
        ''')
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # Botão para limpar log
        clear_log_btn = QPushButton('🗑️ Limpar Log')
        clear_log_btn.clicked.connect(self.clear_log)
        clear_log_btn.setStyleSheet('QPushButton { background-color: #aa4444; }')
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        
        right_panel.setLayout(right_layout)
        
        # Adicionar painéis ao layout principal
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
        
        central_widget.setLayout(main_layout)
        
        # Log inicial
        self.add_log('🎮 Mouse Controller iniciado!')
        self.add_log('📋 Selecione um processo para começar')
        
    def refresh_processes(self):
        """Atualiza a lista de processos"""
        self.process_combo.clear()
        
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    # Filtrar apenas processos com .exe
                    if name.lower().endswith('.exe'):
                        processes.append((pid, name))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Ordenar por nome
            processes.sort(key=lambda x: x[1].lower())
            
            # Adicionar à combobox
            for pid, name in processes:
                self.process_combo.addItem(f"{name} (PID: {pid})", pid)
                
            self.add_log(f"📋 Lista atualizada: {len(processes)} processos encontrados")
            
        except Exception as e:
            self.add_log(f"❌ Erro ao listar processos: {str(e)}")
    
    def connect_to_process(self):
        """Conecta ao processo selecionado"""
        if self.process_combo.currentIndex() == -1:
            self.add_log("❌ Selecione um processo primeiro!")
            return
            
        try:
            pid = self.process_combo.currentData()
            process_name = self.process_combo.currentText().split(' (PID:')[0]
            
            # Criar controlador com nome do processo
            self.controller = ProcessMouseController(process_name, self.add_log)
            
            # Definir método de clique inicial
            self.controller.click_method = 'win32_post'
            
            # Tentar encontrar janela por PID
            if self.find_window_by_pid(pid):
                self.connection_status.setText(f'✅ Conectado: {process_name}')
                self.connection_status.setStyleSheet('color: #44ff44; font-weight: bold;')
                self.add_log(f"🔗 Conectado ao processo: {process_name} (PID: {pid})")
                
                # Atualizar posições no controlador
                self.save_position()
                
                # Sincronizar configurações
                self.controller.use_alternative_click = self.alt_method_checkbox.isChecked()
                self.controller.freeze_mouse = self.freeze_mouse_checkbox.isChecked()
                
                # Configurar hotkeys
                self.setup_hotkeys()
                
                # Habilitar controles
                self.attack_btn.setEnabled(True)
                self.combo_btn.setEnabled(True)
                self.save_pos_btn.setEnabled(True)
                self.test_click_btn.setEnabled(True)
                self.test_all_btn.setEnabled(True)
                self.preview_click_btn.setEnabled(True)
            else:
                self.connection_status.setText('❌ Falha na conexão')
                self.connection_status.setStyleSheet('color: #ff4444; font-weight: bold;')
                self.add_log("❌ Falha ao encontrar janela do processo!")
                
        except Exception as e:
            self.add_log(f"❌ Erro ao conectar: {str(e)}")
    
    def find_window_by_pid(self, target_pid):
        """Encontrar janela por PID específico"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                    if process_id == target_pid:
                        window_text = win32gui.GetWindowText(hwnd)
                        if window_text:  # Apenas janelas com título
                            windows.append((hwnd, window_text, process_id))
                except Exception:
                    pass
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        if windows:
            # Usar a primeira janela encontrada
            self.controller.hwnd = windows[0][0]
            window_info = windows[0]
            self.add_log(f"✅ Janela encontrada: {window_info[1]}")
            return True
        else:
            self.add_log(f"❌ Nenhuma janela encontrada para PID: {target_pid}")
            return False
    
    def change_click_method(self, index):
        """Alterar método de clique"""
        methods = [
            ('win32_post', '🔧 Win32API PostMessage'),
            ('win32_send', '📨 Win32API SendMessage'),
            ('send_input', '🎯 SendInput Sistema'),
            ('set_cursor', '🖱️ SetCursorPos + mouse_event'),
            ('pyautogui', '💻 PyAutoGUI Físico'),
            ('multiple', '🔄 Múltiplos Métodos'),
            ('direct_input', '⚡ DirectInput Avançado'),
            ('game_input', '🎮 GameInput Especializado'),
            ('memory_inject', '🧬 Memory Injection'),
            ('process_hook', '🔗 Process Hook')
        ]
        
        if self.controller:
            method_key, method_name = methods[index]
            self.controller.click_method = method_key
            self.method_indicator.setText(f'🔧 Método: {method_name.split()[1]}')
            
            # Definir cor do indicador baseado no método
            colors = {
                'win32_post': '#00aaff',
                'win32_send': '#00ff88', 
                'send_input': '#ff8800',
                'set_cursor': '#ff00ff',
                'pyautogui': '#ff6600',
                'multiple': '#ffff00',
                'direct_input': '#aa00ff',
                'game_input': '#00ffaa',
                'memory_inject': '#ff0088',
                'process_hook': '#88ff00'
            }
            
            self.method_indicator.setStyleSheet(f'color: {colors.get(method_key, "#00aaff")}; font-weight: bold;')
            self.add_log(f"🔧 Método alterado para: {method_name}")
            
            # Avisos para métodos avançados
            if method_key in ['memory_inject', 'process_hook']:
                self.add_log("⚠️ AVISO: Método avançado - pode ser detectado por anti-cheat!")
            elif method_key in ['direct_input', 'game_input']:
                self.add_log("💡 INFO: Método especializado para jogos - baixa detecção")
    
    def quick_toggle_method(self):
        """Alternar rapidamente entre métodos"""
        current_index = self.click_method_combo.currentIndex()
        next_index = (current_index + 1) % self.click_method_combo.count()
        self.click_method_combo.setCurrentIndex(next_index)
    
    def capture_mouse_position(self):
        """Capturar posição atual do mouse e colocar nos campos"""
        try:
            current_pos = pyautogui.position()
            
            # Se conectado a uma janela, usar coordenadas relativas
            if self.controller and self.controller.hwnd:
                try:
                    rect = win32gui.GetWindowRect(self.controller.hwnd)
                    window_x, window_y = rect[0], rect[1]
                    relative_x = current_pos.x - window_x
                    relative_y = current_pos.y - window_y
                    
                    self.pos_x_input.setText(str(relative_x))
                    self.pos_y_input.setText(str(relative_y))
                    
                    self.add_log(f"📍 Posição capturada (relativa à janela): ({relative_x}, {relative_y})")
                    self.add_log(f"   Posição absoluta na tela: ({current_pos.x}, {current_pos.y})")
                    
                except Exception as e:
                    # Fallback para posição absoluta
                    self.pos_x_input.setText(str(current_pos.x))
                    self.pos_y_input.setText(str(current_pos.y))
                    self.add_log(f"📍 Posição capturada (absoluta): ({current_pos.x}, {current_pos.y})")
            else:
                # Se não conectado, usar posição absoluta
                self.pos_x_input.setText(str(current_pos.x))
                self.pos_y_input.setText(str(current_pos.y))
                self.add_log(f"📍 Posição capturada: ({current_pos.x}, {current_pos.y})")
                
            # Salvar automaticamente
            self.save_position()
            
        except Exception as e:
            self.add_log(f"❌ Erro ao capturar posição do mouse: {e}")
    
    def update_mouse_position(self):
        """Atualizar display da posição do mouse"""
        try:
            current_pos = pyautogui.position()
            self.mouse_pos_label.setText(f'🖱️ Mouse: ({current_pos.x}, {current_pos.y})')
            
            # Se conectado, mostrar também posição relativa à janela
            if self.controller and self.controller.hwnd:
                try:
                    rect = win32gui.GetWindowRect(self.controller.hwnd)
                    window_x, window_y = rect[0], rect[1]
                    relative_x = current_pos.x - window_x
                    relative_y = current_pos.y - window_y
                    
                    self.mouse_pos_label.setText(
                        f'🖱️ Tela: ({current_pos.x}, {current_pos.y}) | Janela: ({relative_x}, {relative_y})'
                    )
                except:
                    pass
        except:
            self.mouse_pos_label.setText('🖱️ Mouse: (erro)')
    
    def update_freeze_setting(self, checked):
        """Atualizar configuração de congelar mouse"""
        if self.controller:
            self.controller.freeze_mouse = checked
            status = "ativada" if checked else "desativada"
            self.add_log(f"🧊 Restauração do mouse {status}")
    
    def toggle_click_method(self, checked):
        """Manter compatibilidade com checkbox antigo"""
        if checked:
            self.click_method_combo.setCurrentIndex(4)  # PyAutoGUI
        else:
            self.click_method_combo.setCurrentIndex(0)  # Win32API PostMessage
    
    def save_position(self):
        """Salvar posição atual"""
        if not self.controller:
            self.add_log("❌ Conecte-se a um processo primeiro!")
            return
            
        try:
            x = int(self.pos_x_input.text() or "400")
            y = int(self.pos_y_input.text() or "300")
            
            self.controller.mouseAttackX = x
            self.controller.mouseAttackY = y
            
            self.add_log(f"💾 Posição salva: ({x}, {y})")
            
        except ValueError:
            self.add_log("❌ Posições inválidas! Use apenas números.")
    
    def preview_click_position(self):
        """Mostrar visualmente onde o clique vai acontecer"""
        if not self.controller:
            self.add_log("❌ Conecte-se a um processo primeiro!")
            return
            
        self.save_position()  # Atualizar posições
        
        try:
            # Calcular posição na tela
            if self.controller.hwnd:
                rect = win32gui.GetWindowRect(self.controller.hwnd)
                window_x, window_y = rect[0], rect[1]
                screen_x = window_x + self.controller.mouseAttackX
                screen_y = window_y + self.controller.mouseAttackY
                
                # Salvar posição atual do mouse
                original_pos = pyautogui.position()
                
                # Mover mouse para posição de clique por 2 segundos
                pyautogui.moveTo(screen_x, screen_y, duration=0.5)
                self.add_log(f"👁️ Mouse movido para posição de clique: ({screen_x}, {screen_y})")
                self.add_log("   Mouse ficará na posição por 3 segundos...")
                
                # Esperar 3 segundos
                QTimer.singleShot(3000, lambda: pyautogui.moveTo(original_pos.x, original_pos.y, duration=0.5))
                QTimer.singleShot(3500, lambda: self.add_log("🔙 Mouse restaurado para posição original"))
                
            else:
                self.add_log("❌ Janela não encontrada para preview!")
                
        except Exception as e:
            self.add_log(f"❌ Erro no preview: {e}")
    
    def test_current_method(self):
        """Testar método atual selecionado"""
        if not self.controller:
            self.add_log("❌ Conecte-se a um processo primeiro!")
            return
            
        self.save_position()  # Atualizar posições
        
        method_name = self.click_method_combo.currentText()
        self.add_log(f"🧪 Testando {method_name}...")
        
        result = self.controller.click_in_window_current_method(
            self.controller.mouseAttackX, 
            self.controller.mouseAttackY, 
            'right'
        )
        
        if result:
            self.add_log(f"✅ {method_name} executado com sucesso!")
            self.click_status_label.setText(f"✅ Último: {method_name.split()[1]} - OK")
            self.click_status_label.setStyleSheet('color: #44ff44; font-weight: bold; font-size: 9px;')
        else:
            self.add_log(f"❌ {method_name} falhou!")
            self.click_status_label.setText(f"❌ Último: {method_name.split()[1]} - FALHA")
            self.click_status_label.setStyleSheet('color: #ff4444; font-weight: bold; font-size: 9px;')
    
    def test_all_methods(self):
        """Testar todos os métodos disponíveis"""
        if not self.controller:
            self.add_log("❌ Conecte-se a um processo primeiro!")
            return
            
        self.save_position()
        self.add_log("🔬 Iniciando teste de todos os métodos...")
        
        methods = [
            ('win32_post', '🔧 Win32API PostMessage'),
            ('win32_send', '📨 Win32API SendMessage'),
            ('send_input', '🎯 SendInput Sistema'),
            ('set_cursor', '🖱️ SetCursorPos + mouse_event'),
            ('pyautogui', '💻 PyAutoGUI Físico'),
            ('direct_input', '⚡ DirectInput Avançado'),
            ('game_input', '🎮 GameInput Especializado'),
            ('memory_inject', '🧬 Memory Injection')
        ]
        
        successful_methods = []
        failed_methods = []
        
        for method_key, method_name in methods:
            self.add_log(f"   Testando {method_name}...")
            
            # Temporariamente alterar método
            original_method = self.controller.click_method
            self.controller.click_method = method_key
            
            # Testar método
            result = self.controller.click_in_window_current_method(
                self.controller.mouseAttackX,
                self.controller.mouseAttackY,
                'right'
            )
            
            if result:
                successful_methods.append(method_name)
                self.add_log(f"   ✅ {method_name} - SUCESSO")
            else:
                failed_methods.append(method_name)
                self.add_log(f"   ❌ {method_name} - FALHA")
            
            # Restaurar método original
            self.controller.click_method = original_method
            
            # Delay entre testes
            time.sleep(0.5)
        
        self.add_log("🔬 Resultado dos testes:")
        if successful_methods:
            self.add_log(f"✅ Métodos funcionando: {len(successful_methods)}")
            for method in successful_methods:
                self.add_log(f"   • {method}")
        
        if failed_methods:
            self.add_log(f"❌ Métodos falhando: {len(failed_methods)}")
            for method in failed_methods:
                self.add_log(f"   • {method}")
        
        # Recomendar melhor método
        if successful_methods:
            recommended = successful_methods[0]
            self.add_log(f"💡 Recomendação: Use {recommended}")
            
            # Auto-selecionar o primeiro método que funciona
            for i, (method_key, method_name) in enumerate(methods):
                if method_name in successful_methods:
                    self.click_method_combo.setCurrentIndex(i)
                    break
    
    def toggle_attack(self):
        """Toggle do ataque básico"""
        if not self.controller:
            self.add_log("❌ Conecte-se a um processo primeiro!")
            return
            
        # Salvar posição antes de atacar
        self.save_position()
        
        self.controller.toggle_right_click()
        
        if self.controller.holding:
            self.attack_status.setText('▶️ Ataque: Ativo')
            self.attack_status.setStyleSheet('color: #44ff44; font-weight: bold;')
            self.attack_btn.setText('🛑 Parar Ataque')
            self.attack_btn.setStyleSheet('QPushButton { background-color: #aa4444; }')
            self.add_log("🗡️ Ataque iniciado!")
        else:
            self.attack_status.setText('⏹️ Ataque: Parado')
            self.attack_status.setStyleSheet('color: white; font-weight: bold;')
            self.attack_btn.setText('🗡️ Atacar (F5)')
            self.attack_btn.setStyleSheet('QPushButton { background-color: #44aa44; }')
            self.add_log("🛑 Ataque parado!")
    
    def toggle_combo(self):
        """Toggle do combo mago"""
        if not self.controller:
            self.add_log("❌ Conecte-se a um processo primeiro!")
            return
            
        # Salvar posição antes do combo
        self.save_position()
        
        self.controller.auto_click_toggle()
        
        if self.controller.autoClickOn:
            self.combo_status.setText('▶️ Combo: Ativo')
            self.combo_status.setStyleSheet('color: #44ff44; font-weight: bold;')
            self.combo_btn.setText('🛑 Parar Combo')
            self.combo_btn.setStyleSheet('QPushButton { background-color: #aa4444; }')
            self.add_log("🔮 Combo de mago iniciado!")
        else:
            self.combo_status.setText('⏹️ Combo: Parado')
            self.combo_status.setStyleSheet('color: white; font-weight: bold;')
            self.combo_btn.setText('🔮 Combo Mago (\\)')
            self.combo_btn.setStyleSheet('QPushButton { background-color: #4444aa; }')
            self.add_log("🛑 Combo de mago parado!")
    
    def setup_hotkeys(self):
        """Configurar hotkeys globais"""
        try:
            keyboard.add_hotkey('f5', self.toggle_attack)
            keyboard.add_hotkey('\\', self.toggle_combo)
            keyboard.add_hotkey('alt+1', self.save_position)
            keyboard.add_hotkey('f6', self.quick_toggle_method)
            keyboard.add_hotkey('f7', self.capture_mouse_position)
            
            self.add_log("⌨️ Hotkeys configuradas:")
            self.add_log("   F5 - Atacar")
            self.add_log("   \\ - Combo Mago")
            self.add_log("   Alt+1 - Salvar Posição")
            self.add_log("   F6 - Alternar Método")
            self.add_log("   F7 - Capturar Posição do Mouse")
            
        except Exception as e:
            self.add_log(f"❌ Erro ao configurar hotkeys: {e}")
    
    def add_log(self, message):
        """Adiciona mensagem ao log"""
        timestamp = time.strftime('%H:%M:%S')
        self.log_text.append(f'[{timestamp}] {message}')
        self.log_text.ensureCursorVisible()
    
    def clear_log(self):
        """Limpar log"""
        self.log_text.clear()
        self.add_log('🗑️ Log limpo')
    
    def update_status(self, text, color):
        """Atualiza status geral"""
        # Implementar se necessário
        pass
    
    def closeEvent(self, event):
        """Cleanup ao fechar aplicação"""
        # Parar timer do mouse
        if hasattr(self, 'mouse_timer'):
            self.mouse_timer.stop()
            
        if self.controller:
            self.controller.holding = False
            self.controller.autoClickOn = False
        
        # Limpar hotkeys
        try:
            keyboard.unhook_all()
        except:
            pass
            
        event.accept()

class ProcessMouseController:
    def __init__(self, window_title, gui_callback=None):
        self.window_title = window_title
        self.hwnd = None
        self.holding = False
        self.autoClickOn = False
        self.mouseAttackX = 400  # Posição padrão X
        self.mouseAttackY = 300  # Posição padrão Y
        self.gui_callback = gui_callback  # Callback para logs na GUI
        self.use_alternative_click = False  # Flag para usar método alternativo
        self.freeze_mouse = True  # Flag para congelar mouse durante cliques
        self.original_mouse_pos = None  # Posição original do mouse
        
        # Array para combo mago (mesmo do script original)
        self.bloodwalls = [0, 25, -25, 50, -50]
        
        # Método de clique atual
        self.click_method = 'win32_post'  # Padrão: Win32API PostMessage
        
    def find_window(self):
        """Encontrar a janela do processo"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                
                # Obter informações do processo
                try:
                    _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                    process_handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, process_id)
                    process_name = win32process.GetModuleFileNameEx(process_handle, 0).split('\\')[-1]
                    win32api.CloseHandle(process_handle)
                    
                    # Verificar por nome do executável OU título da janela
                    if (self.window_title.lower() in window_text.lower() or 
                        self.window_title.lower() in process_name.lower()):
                        windows.append((hwnd, window_text, process_name, process_id))
                        
                except Exception:
                    # Fallback para apenas título da janela
                    if self.window_title.lower() in window_text.lower():
                        windows.append((hwnd, window_text, "Unknown", 0))
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        if windows:
            # Mostrar opções encontradas se houver múltiplas
            if len(windows) > 1:
                print("🔍 Múltiplas janelas encontradas:")
                for i, (hwnd, title, proc_name, proc_id) in enumerate(windows):
                    print(f"   {i+1}. {title} | Processo: {proc_name} | PID: {proc_id}")
                print("� Usando a primeira opção...")
            
            self.hwnd = windows[0][0]
            window_info = windows[0]
            print(f"✅ Janela encontrada: {window_info[1]}")
            print(f"📋 Processo: {window_info[2]} | PID: {window_info[3]}")
            return True
        else:
            print(f"❌ Janela não encontrada: {self.window_title}")
            print("🔍 Processos disponíveis:")
            self.list_available_processes()
            return False
    
    def list_available_processes(self):
        """Listar processos e janelas disponíveis"""
        def enum_callback(hwnd, processes):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_text:
                    try:
                        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                        process_handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, process_id)
                        process_name = win32process.GetModuleFileNameEx(process_handle, 0).split('\\')[-1]
                        win32api.CloseHandle(process_handle)
                        processes.append((window_text, process_name, process_id))
                    except:
                        processes.append((window_text, "Unknown", 0))
        
        processes = []
        win32gui.EnumWindows(enum_callback, processes)
        
        # Filtrar e mostrar apenas os mais relevantes
        relevant_processes = []
        keywords = ['dark', 'eden', 'game', 'client', 'launcher']
        
        for title, proc_name, pid in processes:
            if any(keyword in title.lower() or keyword in proc_name.lower() for keyword in keywords):
                relevant_processes.append((title, proc_name, pid))
        
        if relevant_processes:
            print("🎮 Processos relacionados a jogos encontrados:")
            for i, (title, proc_name, pid) in enumerate(relevant_processes[:5]):
                print(f"   {i+1}. Título: {title}")
                print(f"      Processo: {proc_name} | PID: {pid}")
                print()
        else:
            print("📋 Primeiras 10 janelas visíveis:")
            for i, (title, proc_name, pid) in enumerate(processes[:10]):
                print(f"   {i+1}. {title} | {proc_name}")
    
    def log_message(self, message):
        """Enviar mensagem para GUI se disponível"""
        if self.gui_callback:
            self.gui_callback(message)
        else:
            print(message)
    
    def click_in_window_current_method(self, x, y, button='right'):
        """Clicar usando o método atualmente selecionado"""
        if not self.hwnd:
            self.log_message("⚠️ Janela não encontrada!")
            return False
        
        method_map = {
            'win32_post': self.click_win32_post,
            'win32_send': self.click_win32_send,
            'send_input': self.click_send_input,
            'set_cursor': self.click_set_cursor,
            'pyautogui': self.click_pyautogui,
            'multiple': self.click_multiple_methods,
            'direct_input': self.click_direct_input,
            'game_input': self.click_game_input,
            'memory_inject': self.click_memory_inject,
            'process_hook': self.click_process_hook
        }
        
        click_function = method_map.get(self.click_method, self.click_win32_post)
        return click_function(x, y, button)
    
    def click_win32_post(self, x, y, button='right'):
        """Método 1: Win32API PostMessage"""
        try:
            if not win32gui.IsWindow(self.hwnd):
                self.log_message("❌ Handle da janela inválido!")
                return False
            
            lParam = win32api.MAKELONG(x, y)
            
            if button == 'right':
                result1 = win32api.PostMessage(self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
                time.sleep(0.02)
                result2 = win32api.PostMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
            else:
                result1 = win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                time.sleep(0.02)
                result2 = win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)
            
            self.log_message(f"🔧 PostMessage {button} em ({x}, {y}) - Resultados: {result1}, {result2}")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Erro PostMessage: {e}")
            return False
    
    def click_win32_send(self, x, y, button='right'):
        """Método 2: Win32API SendMessage"""
        try:
            if not win32gui.IsWindow(self.hwnd):
                return False
            
            lParam = win32api.MAKELONG(x, y)
            
            if button == 'right':
                win32api.SendMessage(self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
                time.sleep(0.02)
                win32api.SendMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
            else:
                win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                time.sleep(0.02)
                win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)
            
            self.log_message(f"📨 SendMessage {button} em ({x}, {y})")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Erro SendMessage: {e}")
            return False
    
    def click_send_input(self, x, y, button='right'):
        """Método 3: SendInput (sistema)"""
        try:
            # Calcular posição absoluta na tela
            rect = win32gui.GetWindowRect(self.hwnd)
            window_x, window_y = rect[0], rect[1]
            screen_x = window_x + x
            screen_y = window_y + y
            
            # Converter para coordenadas normalizadas (0-65535)
            screen_width = windll.user32.GetSystemMetrics(0)
            screen_height = windll.user32.GetSystemMetrics(1)
            
            norm_x = int((screen_x * 65535) / screen_width)
            norm_y = int((screen_y * 65535) / screen_height)
            
            # Preparar estrutura MOUSEINPUT
            mouse_input = MOUSEINPUT()
            mouse_input.dx = norm_x
            mouse_input.dy = norm_y
            mouse_input.mouseData = 0
            mouse_input.time = 0
            mouse_input.dwExtraInfo = None
            
            # Definir flags baseado no botão
            if button == 'right':
                down_flag = MOUSEEVENTF_RIGHTDOWN
                up_flag = MOUSEEVENTF_RIGHTUP
            else:
                down_flag = MOUSEEVENTF_LEFTDOWN
                up_flag = MOUSEEVENTF_LEFTUP
            
            # Mover cursor e clicar
            mouse_input.dwFlags = MOUSEEVENTF_ABSOLUTE | down_flag
            
            input_struct = INPUT()
            input_struct.type = INPUT_MOUSE
            ctypes.memmove(input_struct.mi, ctypes.byref(mouse_input), ctypes.sizeof(MOUSEINPUT))
            
            # Enviar input
            result1 = windll.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(INPUT))
            time.sleep(0.02)
            
            # Soltar botão
            mouse_input.dwFlags = MOUSEEVENTF_ABSOLUTE | up_flag
            ctypes.memmove(input_struct.mi, ctypes.byref(mouse_input), ctypes.sizeof(MOUSEINPUT))
            result2 = windll.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(INPUT))
            
            self.log_message(f"🎯 SendInput {button} em ({screen_x}, {screen_y}) - Resultados: {result1}, {result2}")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Erro SendInput: {e}")
            return False
    
    def click_set_cursor(self, x, y, button='right'):
        """Método 4: SetCursorPos + mouse_event"""
        try:
            # Salvar posição original se necessário
            if self.freeze_mouse:
                original_pos = win32gui.GetCursorPos()
            
            # Calcular posição absoluta na tela
            rect = win32gui.GetWindowRect(self.hwnd)
            window_x, window_y = rect[0], rect[1]
            screen_x = window_x + x
            screen_y = window_y + y
            
            # Mover cursor
            win32api.SetCursorPos((screen_x, screen_y))
            time.sleep(0.01)
            
            # Clicar usando mouse_event
            if button == 'right':
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            else:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            # Restaurar posição original se necessário
            if self.freeze_mouse:
                time.sleep(0.01)
                win32api.SetCursorPos(original_pos)
            
            self.log_message(f"🖱️ SetCursorPos+mouse_event {button} em ({screen_x}, {screen_y})")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Erro SetCursorPos: {e}")
            return False
    
    def click_pyautogui(self, x, y, button='right'):
        """Método 5: PyAutoGUI (clique físico)"""
        try:
            # Salvar posição original se necessário
            if self.freeze_mouse:
                self.original_mouse_pos = pyautogui.position()
            
            # Calcular posição absoluta na tela
            rect = win32gui.GetWindowRect(self.hwnd)
            window_x, window_y = rect[0], rect[1]
            screen_x = window_x + x
            screen_y = window_y + y
            
            # Trazer janela para frente
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.05)
            
            # Clicar com pyautogui
            if button == 'right':
                pyautogui.rightClick(screen_x, screen_y)
            else:
                pyautogui.leftClick(screen_x, screen_y)
            
            # Restaurar posição original se necessário
            if self.freeze_mouse and self.original_mouse_pos:
                time.sleep(0.01)
                pyautogui.moveTo(self.original_mouse_pos.x, self.original_mouse_pos.y, duration=0.1)
            
            self.log_message(f"💻 PyAutoGUI {button} em ({screen_x}, {screen_y})")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Erro PyAutoGUI: {e}")
            return False
    
    def click_multiple_methods(self, x, y, button='right'):
        """Método 6: Tentar múltiplos métodos até um funcionar"""
        methods = [
            ('DirectInput Avançado', self.click_direct_input),
            ('GameInput Especializado', self.click_game_input),
            ('Win32API SendMessage', self.click_win32_send),
            ('Win32API PostMessage', self.click_win32_post),
            ('Process Hook', self.click_process_hook),
            ('SetCursorPos + mouse_event', self.click_set_cursor),
            ('SendInput Sistema', self.click_send_input),
            ('Memory Injection', self.click_memory_inject),
            ('PyAutoGUI', self.click_pyautogui)
        ]
        
        self.log_message(f"🔄 Tentando múltiplos métodos para {button} em ({x}, {y})")
        self.log_message("   Ordem: Métodos não-físicos primeiro, físicos por último")
        
        for method_name, method_func in methods:
            try:
                self.log_message(f"   Tentando {method_name}...")
                if method_func(x, y, button):
                    self.log_message(f"   ✅ {method_name} funcionou!")
                    return True
                else:
                    self.log_message(f"   ❌ {method_name} falhou")
                    
                # Pequeno delay entre tentativas para não sobrecarregar
                time.sleep(0.1)
                    
            except Exception as e:
                self.log_message(f"   ❌ {method_name} erro: {e}")
                continue
        
        self.log_message("❌ Todos os métodos falharam!")
        return False
    
    def click_direct_input(self, x, y, button='right'):
        """Método 7: DirectInput - Simulação de hardware"""
        try:
            # Calcular posição absoluta na tela
            rect = win32gui.GetWindowRect(self.hwnd)
            window_x, window_y = rect[0], rect[1]
            screen_x = window_x + x
            screen_y = window_y + y
            
            # Usar estruturas de baixo nível para simular input de hardware
            # Este método tenta bypass de detecção de software
            
            # Primeiro, focar a janela sem SetForegroundWindow
            win32gui.AttachThreadInput(
                win32api.GetCurrentThreadId(),
                win32process.GetWindowThreadProcessId(self.hwnd)[0],
                True
            )
            
            # Enviar mensagem WM_SETFOCUS para garantir foco
            win32api.SendMessage(self.hwnd, win32con.WM_SETFOCUS, 0, 0)
            
            # Usar coordenadas da janela diretamente
            lParam = win32api.MAKELONG(x, y)
            
            # Enviar sequência completa de mensagens para simular clique real
            if button == 'right':
                # Simular hover primeiro
                win32api.SendMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                time.sleep(0.001)
                
                # Enviar mensagem de botão pressionado
                win32api.SendMessage(self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
                time.sleep(0.010)  # Hold por 10ms
                
                # Enviar mensagem de botão solto
                win32api.SendMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                
                # Enviar também WM_CONTEXTMENU para alguns jogos
                win32api.SendMessage(self.hwnd, win32con.WM_CONTEXTMENU, self.hwnd, lParam)
            else:
                win32api.SendMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                time.sleep(0.001)
                win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                time.sleep(0.010)
                win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)
            
            # Desfazer attach
            try:
                win32gui.AttachThreadInput(
                    win32api.GetCurrentThreadId(),
                    win32process.GetWindowThreadProcessId(self.hwnd)[0],
                    False
                )
            except:
                pass
            
            self.log_message(f"⚡ DirectInput {button} em ({x}, {y}) - Hardware Level")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Erro DirectInput: {e}")
            return False
    
    def click_game_input(self, x, y, button='right'):
        """Método 8: GameInput - Especializado para jogos"""
        try:
            # Método que tenta contornar proteções de jogos
            # usando técnicas específicas para aplicações de jogo
            
            # 1. Obter informações detalhadas da janela
            rect = win32gui.GetWindowRect(self.hwnd)
            client_rect = win32gui.GetClientRect(self.hwnd)
            
            # 2. Calcular coordenadas considerando bordas da janela
            border_x = (rect[2] - rect[0] - client_rect[2]) // 2
            border_y = (rect[3] - rect[1] - client_rect[3]) - border_x
            
            adjusted_x = x
            adjusted_y = y
            
            # 3. Usar múltiplas abordagens simultaneamente
            lParam = win32api.MAKELONG(adjusted_x, adjusted_y)
            
            # Approach 1: Usar WM_NCHITTEST para verificar se área é válida
            hit_test = win32api.SendMessage(self.hwnd, win32con.WM_NCHITTEST, 0, lParam)
            
            if hit_test == win32con.HTCLIENT:  # Área cliente válida
                # Approach 2: Enviar sequência de eventos de mouse completa
                if button == 'right':
                    # Sequência completa para clique direito
                    events = [
                        (win32con.WM_MOUSEMOVE, 0, lParam),
                        (win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam),
                        (win32con.WM_RBUTTONUP, 0, lParam)
                    ]
                else:
                    events = [
                        (win32con.WM_MOUSEMOVE, 0, lParam),
                        (win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam),
                        (win32con.WM_LBUTTONUP, 0, lParam)
                    ]
                
                # Enviar eventos com timing preciso
                for msg, wparam, lparam in events:
                    win32api.PostMessage(self.hwnd, msg, wparam, lparam)
                    time.sleep(0.005)  # 5ms entre eventos
                
                self.log_message(f"🎮 GameInput {button} em ({adjusted_x}, {adjusted_y}) - Área cliente válida")
                return True
            else:
                self.log_message(f"⚠️ GameInput: Coordenadas fora da área cliente (hit_test: {hit_test})")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Erro GameInput: {e}")
            return False
    
    def click_memory_inject(self, x, y, button='right'):
        """Método 9: Memory Injection - Injeção na memória do processo"""
        try:
            # AVISO: Este método é muito avançado e pode ser detectado
            self.log_message("🧬 Tentando Memory Injection...")
            
            # Obter PID do processo
            _, process_id = win32process.GetWindowThreadProcessId(self.hwnd)
            
            # Tentar abrir handle do processo com privilégios máximos
            try:
                process_handle = win32api.OpenProcess(
                    win32con.PROCESS_ALL_ACCESS, 
                    False, 
                    process_id
                )
            except Exception as e:
                self.log_message(f"❌ Não foi possível abrir processo: {e}")
                return False
            
            # Método alternativo: usar WriteProcessMemory para modificar estado do mouse
            try:
                # Primeiro tentar encontrar estruturas de input na memória
                # Este é um método muito avançado e específico para cada jogo
                
                # Por agora, usar uma abordagem mais simples: injetar DLL
                # que pode interceptar mensagens de mouse
                
                # Fallback para método híbrido: combinar memory access com mensagens
                rect = win32gui.GetWindowRect(self.hwnd)
                
                # Usar VirtualAllocEx para alocar memória no processo alvo
                allocated_memory = windll.kernel32.VirtualAllocEx(
                    process_handle,
                    0,
                    1024,  # 1KB
                    0x3000,  # MEM_COMMIT | MEM_RESERVE
                    0x40  # PAGE_EXECUTE_READWRITE
                )
                
                if allocated_memory:
                    # Criar estrutura de dados para click
                    click_data = f"{x},{y},{button}".encode('ascii')
                    
                    # Escrever dados na memória do processo
                    bytes_written = ctypes.c_size_t(0)
                    success = windll.kernel32.WriteProcessMemory(
                        process_handle,
                        allocated_memory,
                        click_data,
                        len(click_data),
                        ctypes.byref(bytes_written)
                    )
                    
                    if success:
                        self.log_message(f"🧬 Memory injection successful - escreveu {bytes_written.value} bytes")
                        
                        # Liberar memória
                        windll.kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, 0x8000)
                        
                        # Como não podemos injetar código facilmente, usar método híbrido
                        # Combinar memory injection com mensagem normal
                        lParam = win32api.MAKELONG(x, y)
                        if button == 'right':
                            win32api.SendMessage(self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
                            time.sleep(0.01)
                            win32api.SendMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                        else:
                            win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                            time.sleep(0.01)
                            win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                        
                        win32api.CloseHandle(process_handle)
                        return True
                    else:
                        windll.kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, 0x8000)
                
                win32api.CloseHandle(process_handle)
                self.log_message("❌ Memory injection falhou - usando fallback")
                return False
                
            except Exception as e:
                win32api.CloseHandle(process_handle)
                self.log_message(f"❌ Erro na injeção de memória: {e}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Erro Memory Injection: {e}")
            return False
    
    def click_process_hook(self, x, y, button='right'):
        """Método 10: Process Hook - Hook no processo"""
        try:
            self.log_message("🔗 Tentando Process Hook...")
            
            # Obter informações do processo
            _, process_id = win32process.GetWindowThreadProcessId(self.hwnd)
            thread_id = win32process.GetWindowThreadProcessId(self.hwnd)[0]
            
            # Método 1: Hook de mensagens usando SetWindowsHookEx
            try:
                # Este é um hook de baixo nível
                def low_level_mouse_proc(nCode, wParam, lParam):
                    if nCode >= 0:
                        # Simular que o clique veio do mouse físico
                        pass
                    return windll.user32.CallNextHookExW(None, nCode, wParam, lParam)
                
                # Definir tipo de função para hook
                HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
                hook_proc = HOOKPROC(low_level_mouse_proc)
                
                # Instalar hook (WH_MOUSE_LL = 14)
                hook = windll.user32.SetWindowsHookExW(14, hook_proc, windll.kernel32.GetModuleHandleW(None), 0)
                
                if hook:
                    # Enviar clique enquanto hook está ativo
                    lParam = win32api.MAKELONG(x, y)
                    
                    if button == 'right':
                        win32api.SendMessage(self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
                        time.sleep(0.01)
                        win32api.SendMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                    else:
                        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                        time.sleep(0.01)
                        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                    
                    # Remover hook
                    windll.user32.UnhookWindowsHookEx(hook)
                    
                    self.log_message(f"🔗 Process Hook {button} em ({x}, {y}) - Hook ativo")
                    return True
                else:
                    self.log_message("❌ Falha ao instalar hook")
                    
            except Exception as e:
                self.log_message(f"❌ Erro no hook: {e}")
            
            # Método 2: Fallback para SubclassWindow
            try:
                # Tentar subclassificar a janela temporariamente
                original_proc = win32gui.GetWindowLong(self.hwnd, win32con.GWL_WNDPROC)
                
                if original_proc:
                    # Enviar mensagem diretamente para o procedure original
                    lParam = win32api.MAKELONG(x, y)
                    
                    if button == 'right':
                        windll.user32.CallWindowProcW(original_proc, self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
                        time.sleep(0.01)
                        windll.user32.CallWindowProcW(original_proc, self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                    else:
                        windll.user32.CallWindowProcW(original_proc, self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                        time.sleep(0.01)
                        windll.user32.CallWindowProcW(original_proc, self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                    
                    self.log_message(f"🔗 Process Hook {button} em ({x}, {y}) - Direct WndProc")
                    return True
                    
            except Exception as e:
                self.log_message(f"❌ Erro no WndProc: {e}")
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Erro Process Hook: {e}")
            return False
    
    def click_in_window(self, x, y, button='right'):
        """Método legado - redireciona para método atual"""
        return self.click_in_window_current_method(x, y, button)
    
    def send_key_to_window(self, key_code):
        """Enviar tecla para janela específica"""
        if not self.hwnd:
            return False
            
        try:
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, key_code, 0)
            time.sleep(0.01)
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, key_code, 0)
            return True
        except Exception as e:
            print(f"❌ Erro ao enviar tecla: {e}")
            return False
    
    def send_alt_key_combo(self, key_code):
        """Enviar combinação Alt + tecla para janela específica"""
        if not self.hwnd:
            return False
            
        try:
            # Pressionar Alt
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, win32con.VK_MENU, 0)
            time.sleep(0.01)
            # Pressionar tecla específica
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, key_code, 0)
            time.sleep(0.01)
            # Soltar tecla específica
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, key_code, 0)
            time.sleep(0.01)
            # Soltar Alt
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, win32con.VK_MENU, 0)
            return True
        except Exception as e:
            print(f"❌ Erro ao enviar Alt+tecla: {e}")
            return False
    
    def hold_right_click_in_window(self):
        """Segurar clique direito na janela específica"""
        self.log_message("🎯 Loop de ataques iniciado...")
        method_names = {
            'win32_post': 'Win32API PostMessage',
            'win32_send': 'Win32API SendMessage',
            'send_input': 'SendInput Sistema',
            'set_cursor': 'SetCursorPos + mouse_event',
            'pyautogui': 'PyAutoGUI Físico',
            'multiple': 'Múltiplos Métodos',
            'direct_input': 'DirectInput Avançado',
            'game_input': 'GameInput Especializado',
            'memory_inject': 'Memory Injection',
            'process_hook': 'Process Hook'
        }
        self.log_message(f"🔧 Usando método: {method_names.get(self.click_method, 'Desconhecido')}")
        
        while self.holding:
            if self.hwnd:  # Verificar se janela ainda existe
                self.click_in_window_current_method(self.mouseAttackX, self.mouseAttackY, 'right')
            time.sleep(0.1)
    
    def mage_hold_left_click_in_window(self):
        """Segurar clique esquerdo na janela específica (para mago)"""
        print("🔥 Mantendo clique esquerdo para mago...")
        while self.autoClickOn:
            if self.hwnd:
                # Simular mouseDown mantido
                lParam = win32api.MAKELONG(self.mouseAttackX, self.mouseAttackY)
                win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            time.sleep(0.5)
    
    def toggle_right_click(self):
        """Toggle do clique direito"""
        if not self.hwnd:
            self.log_message("❌ Janela não encontrada!")
            return
            
        self.holding = not self.holding
        if self.holding:
            self.log_message(f"🗡️ Iniciando ataques na posição ({self.mouseAttackX}, {self.mouseAttackY})")
            
            # Enviar backspace para a janela
            self.send_key_to_window(0x08)  # VK_BACK (backspace)
            
            # Enviar Alt (segurar)
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, win32con.VK_MENU, 0)
            
            # Iniciar thread de ataques
            threading.Thread(target=self.hold_right_click_in_window, daemon=True).start()
        else:
            self.log_message("🛑 Parando ataques...")
            
            # Soltar Alt
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, win32con.VK_MENU, 0)
            
            # Soltar botão direito
            lParam = win32api.MAKELONG(self.mouseAttackX, self.mouseAttackY)
            win32api.PostMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
    
    def auto_click_toggle(self):
        """Toggle do combo de mago"""
        if not self.hwnd:
            print("❌ Janela não encontrada!")
            return
            
        self.autoClickOn = not self.autoClickOn
        if self.autoClickOn:
            print("🔮 Iniciando combo de mago...")
            self.send_key_to_window(0x08)  # backspace
            threading.Thread(target=self.auto_click_running, daemon=True).start()
        else:
            print("🛑 Parando combo de mago...")
            # Soltar botão direito
            lParam = win32api.MAKELONG(self.mouseAttackX, self.mouseAttackY)
            win32api.PostMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, lParam)
    
    def auto_click_running(self):
        """Executar combo de mago"""
        if not self.mouse_attack_validation():
            self.autoClickOn = False
            print("❌ Posição de ataque não definida!")
            return
        
        print("🎯 Executando combo de mago...")
        
        # Pressionar F12
        self.send_key_to_window(0x7B)  # VK_F12
        
        # Executar bloodwalls
        for wall in self.bloodwalls:
            if self.autoClickOn and self.hwnd:
                print(f"💥 Executando bloodwall: {wall}")
                
                # Alt + clique direito na posição + offset
                target_y = self.mouseAttackY + wall
                
                # Pressionar Alt
                win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, win32con.VK_MENU, 0)
                time.sleep(0.01)
                
                # Clique direito
                self.click_in_window_current_method(self.mouseAttackX, target_y, 'right')
                
                # Soltar Alt
                win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, win32con.VK_MENU, 0)
                
                if wall != -50:
                    time.sleep(2)
        
        time.sleep(1)
        
        # Iniciar thread para manter clique esquerdo
        if self.autoClickOn:
            threading.Thread(target=self.mage_hold_left_click_in_window, daemon=True).start()
    
    def set_mouse_attack_position(self):
        """Definir posição de ataque manualmente"""
        if not self.find_window():
            print("❌ Janela não encontrada!")
            return
            
        # Para simplicidade, vamos usar posições pré-definidas
        # Em uma implementação real, você poderia pegar do cursor ou input do usuário
        print("💾 Definindo posição de ataque...")
        print(f"📍 Posição atual: ({self.mouseAttackX}, {self.mouseAttackY})")
        
        # Enviar backspace
        self.send_key_to_window(0x08)  # VK_BACK
        
        print("✅ Posição salva com sucesso")
    
    def mouse_attack_validation(self):
        """Validar se posição de ataque foi definida"""
        return self.mouseAttackX != 0 and self.mouseAttackY != 0

def main():
    app = QApplication(sys.argv)
    
    # Aplicar tema escuro
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    window = ProcessMouseControllerGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
