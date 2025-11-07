import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyautogui
import threading
import time
import keyboard  # Adicionar para hotkeys personalizadas

class DarkEdenBotGUI(QMainWindow):
    # Sinais para comunicação entre threads
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str, str)  # texto, cor
    
    def __init__(self):
        super().__init__()
        
        # Estados do bot
        self.holding = False
        self.autoClickOn = False
        self.mouseAttackX = 0
        self.mouseAttackY = 0
        self.mouseAntesX = 0
        self.mouseAntesY = 0
        self.bloodwalls = [0, 25, -25, 50, -50]
        
        # Dicionário para hotkeys personalizadas
        self.custom_hotkeys = {}
        
        # === NOVO: Sistema de Múltiplos Jogos ===
        self.games = {
            "Sapphire": {
                "players": ["Digo", "John"],
                "current_index": 0,
                "hotkey": "ALT+3",
                "enabled": True
            },
            "Myterios Box": {
                "players": ["Digo", "John"],
                "current_index": 0,
                "hotkey": "ALT+2",
                "enabled": True
            }
        }
        self.current_game = "Sapphire"  # Jogo ativo no momento
        
        self.initUI()
        
        # Conectar sinais
        self.log_signal.connect(self.add_log)
        self.status_signal.connect(self.update_status)
        
        # Configurar hotkeys padrão
        self.setup_default_hotkeys()
        
    def initUI(self):
        self.setWindowTitle('Dark Eden Bot - PyQt5')
        self.setGeometry(100, 100, 600, 500)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout()
        
        # === PAINEL ESQUERDO - CONTROLES ===
        left_panel = QWidget()
        left_panel.setFixedWidth(200)
        left_panel.setStyleSheet("""
            QWidget { background-color: #2b2b2b; }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #505050; }
            QPushButton:pressed { background-color: #353535; }
        """)
        
        left_layout = QVBoxLayout()
        
        # Título
        title = QLabel('DARK EDEN BOT')
        title.setStyleSheet('color: #00ff00; font-size: 14px; font-weight: bold;')
        title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title)
        
        left_layout.addSpacing(20)
        
        # Botões de ação
        self.attack_btn = QPushButton('🗡️ Ataque Básico')
        self.attack_btn.clicked.connect(self.toggle_attack)
        self.attack_btn.setStyleSheet('QPushButton { background-color: #ff4444; }')
        left_layout.addWidget(self.attack_btn)
        
        self.mage_btn = QPushButton('🧙 Combo Mago')
        self.mage_btn.clicked.connect(self.toggle_mage)
        self.mage_btn.setStyleSheet('QPushButton { background-color: #4444ff; }')
        left_layout.addWidget(self.mage_btn)
        
        self.pos_btn = QPushButton('📍 Salvar Posição')
        self.pos_btn.clicked.connect(self.set_position)
        self.pos_btn.setStyleSheet('QPushButton { background-color: #44ff44; color: black; }')
        left_layout.addWidget(self.pos_btn)
        
        self.stop_btn = QPushButton('🛑 Parar Tudo')
        self.stop_btn.clicked.connect(self.stop_all)
        self.stop_btn.setStyleSheet('QPushButton { background-color: #ff8800; }')
        left_layout.addWidget(self.stop_btn)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # === PAINEL DIREITO - INFORMAÇÕES ===
        right_panel = QWidget()
        right_panel.setStyleSheet('QWidget { background-color: #3a3a3a; }')
        right_layout = QVBoxLayout()
        
        # Status
        status_group = QGroupBox('Status')
        status_group.setStyleSheet('''
            QGroupBox { color: #ffff00; font-weight: bold; }
            QLabel { color: white; }
        ''')
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel('Pronto')
        self.status_label.setStyleSheet('color: #00ff00; font-size: 12px; font-weight: bold;')
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        right_layout.addWidget(status_group)
        
        # Posição
        pos_group = QGroupBox('Posição de Ataque')
        pos_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        pos_layout = QVBoxLayout()
        
        self.pos_label = QLabel('Não definida')
        self.pos_label.setStyleSheet('color: white;')
        pos_layout.addWidget(self.pos_label)
        
        pos_group.setLayout(pos_layout)
        right_layout.addWidget(pos_group)
        
        # === NOVO: Sistema de Múltiplos Jogos ===
        games_group = QGroupBox('Sistema de Jogos Múltiplos')
        games_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        games_layout = QVBoxLayout()
        
        # Seletor de jogo ativo
        game_selector_layout = QHBoxLayout()
        game_selector_label = QLabel('Jogo Ativo:')
        game_selector_label.setStyleSheet('color: white; font-weight: bold;')
        game_selector_layout.addWidget(game_selector_label)
        
        self.game_selector = QComboBox()
        self.game_selector.addItems(list(self.games.keys()))
        self.game_selector.setCurrentText(self.current_game)
        self.game_selector.setStyleSheet('''
            QComboBox {
                background-color: #1e1e1e; 
                color: white; 
                border: 1px solid #555; 
                padding: 4px;
            }
        ''')
        self.game_selector.currentTextChanged.connect(self.switch_game)
        game_selector_layout.addWidget(self.game_selector)
        
        games_layout.addLayout(game_selector_layout)
        
        # Display do turno atual - GRANDE E VISÍVEL
        self.turn_display = QLabel()
        self.turn_display.setAlignment(Qt.AlignCenter)
        self.turn_display.setStyleSheet('''
            background-color: #1e1e1e;
            color: #00ff00;
            font-size: 18px;
            font-weight: bold;
            border: 2px solid #555;
            padding: 10px;
            margin: 5px;
        ''')
        self.update_turn_display()
        games_layout.addWidget(self.turn_display)
        
        # NOVO: Display de todos os jogos ativos
        all_games_label = QLabel('Status de Todos os Jogos:')
        all_games_label.setStyleSheet('color: #ffaa00; font-weight: bold; margin-top: 10px;')
        games_layout.addWidget(all_games_label)
        
        self.all_games_display = QLabel()
        self.all_games_display.setAlignment(Qt.AlignLeft)
        self.all_games_display.setStyleSheet('''
            background-color: #2a2a2a;
            color: white;
            font-size: 12px;
            font-weight: bold;
            border: 1px solid #555;
            padding: 8px;
            margin: 2px;
        ''')
        self.update_all_games_display()
        games_layout.addWidget(self.all_games_display)
        
        # Controles do jogo atual
        game_controls = QHBoxLayout()
        
        self.prev_turn_btn = QPushButton('⬅️ Anterior')
        self.prev_turn_btn.clicked.connect(self.previous_turn)
        self.prev_turn_btn.setStyleSheet('''
            QPushButton { 
                background-color: #666666; 
                color: white; 
                border: none; 
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #777777; }
        ''')
        game_controls.addWidget(self.prev_turn_btn)
        
        self.next_turn_btn = QPushButton('➡️ Próximo')
        self.next_turn_btn.clicked.connect(self.next_turn)
        self.next_turn_btn.setStyleSheet('''
            QPushButton { 
                background-color: #4444aa; 
                color: white; 
                border: none; 
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5555bb; }
        ''')
        game_controls.addWidget(self.next_turn_btn)
        
        self.toggle_game_btn = QPushButton('🎮 Ativar/Desativar')
        self.toggle_game_btn.clicked.connect(self.toggle_current_game)
        self.toggle_game_btn.setStyleSheet('''
            QPushButton { 
                background-color: #aa44aa; 
                color: white; 
                border: none; 
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #bb55bb; }
        ''')
        game_controls.addWidget(self.toggle_game_btn)
        
        self.debug_btn = QPushButton('🐛 Debug')
        self.debug_btn.clicked.connect(self.debug_hotkeys)
        self.debug_btn.setStyleSheet('''
            QPushButton { 
                background-color: #aa6644; 
                color: white; 
                border: none; 
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #bb7755; }
        ''')
        game_controls.addWidget(self.debug_btn)
        
        games_layout.addLayout(game_controls)
        
        # Informações do jogo atual
        game_info_layout = QHBoxLayout()
        
        self.game_hotkey_label = QLabel()
        self.game_hotkey_label.setStyleSheet('color: #ffaa00; font-weight: bold;')
        game_info_layout.addWidget(self.game_hotkey_label)
        
        self.game_status_label = QLabel()
        self.game_status_label.setStyleSheet('color: #44ff44; font-weight: bold;')
        game_info_layout.addWidget(self.game_status_label)
        
        games_layout.addLayout(game_info_layout)
        
        # Gerenciamento de jogadores do jogo atual
        player_mgmt_label = QLabel('Jogadores do Jogo Atual:')
        player_mgmt_label.setStyleSheet('color: #ffff00; font-weight: bold; margin-top: 10px;')
        games_layout.addWidget(player_mgmt_label)
        
        # Lista de jogadores
        self.player_list = QListWidget()
        self.player_list.setFixedHeight(80)
        self.player_list.setStyleSheet('''
            background-color: #1e1e1e; 
            color: white; 
            border: 1px solid #555;
        ''')
        games_layout.addWidget(self.player_list)
        
        # Input para novo jogador
        player_input_layout = QHBoxLayout()
        self.new_player_input = QLineEdit()
        self.new_player_input.setPlaceholderText('Nome do jogador...')
        self.new_player_input.setStyleSheet('''
            background-color: #1e1e1e; 
            color: white; 
            border: 1px solid #555; 
            padding: 4px;
        ''')
        player_input_layout.addWidget(self.new_player_input)
        
        self.add_player_btn = QPushButton('➕')
        self.add_player_btn.clicked.connect(self.add_player)
        self.add_player_btn.setStyleSheet('''
            QPushButton { 
                background-color: #44aa44; 
                color: white; 
                border: none; 
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #55bb55; }
        ''')
        player_input_layout.addWidget(self.add_player_btn)
        
        self.remove_player_btn = QPushButton('➖')
        self.remove_player_btn.clicked.connect(self.remove_player)
        self.remove_player_btn.setStyleSheet('''
            QPushButton { 
                background-color: #aa4444; 
                color: white; 
                border: none; 
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #bb5555; }
        ''')
        player_input_layout.addWidget(self.remove_player_btn)
        
        games_layout.addLayout(player_input_layout)
        
        # === NOVO: Gerenciamento de Jogos ===
        game_mgmt_label = QLabel('Gerenciar Jogos:')
        game_mgmt_label.setStyleSheet('color: #ff44ff; font-weight: bold; margin-top: 15px;')
        games_layout.addWidget(game_mgmt_label)
        
        # Adicionar novo jogo
        new_game_layout = QHBoxLayout()
        
        self.new_game_input = QLineEdit()
        self.new_game_input.setPlaceholderText('Nome do novo jogo...')
        self.new_game_input.setStyleSheet('''
            background-color: #1e1e1e; 
            color: white; 
            border: 1px solid #555; 
            padding: 4px;
        ''')
        new_game_layout.addWidget(self.new_game_input)
        
        self.new_game_hotkey = QLineEdit()
        self.new_game_hotkey.setPlaceholderText('Hotkey (ex: f3)')
        self.new_game_hotkey.setFixedWidth(80)
        self.new_game_hotkey.setStyleSheet('''
            background-color: #1e1e1e; 
            color: white; 
            border: 1px solid #555; 
            padding: 4px;
        ''')
        new_game_layout.addWidget(self.new_game_hotkey)
        
        self.add_game_btn = QPushButton('🎮 Adicionar')
        self.add_game_btn.clicked.connect(self.add_new_game)
        self.add_game_btn.setStyleSheet('''
            QPushButton { 
                background-color: #ff44aa; 
                color: white; 
                border: none; 
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #ff55bb; }
        ''')
        new_game_layout.addWidget(self.add_game_btn)
        
        games_layout.addLayout(new_game_layout)
        
        # Botões para gerenciar jogo atual
        game_mgmt_buttons = QHBoxLayout()
        
        self.change_hotkey_btn = QPushButton('🔧 Mudar Hotkey')
        self.change_hotkey_btn.clicked.connect(self.change_game_hotkey)
        self.change_hotkey_btn.setStyleSheet('''
            QPushButton { 
                background-color: #4444aa; 
                color: white; 
                border: none; 
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5555bb; }
        ''')
        game_mgmt_buttons.addWidget(self.change_hotkey_btn)
        
        self.remove_game_btn = QPushButton('🗑️ Remover Jogo')
        self.remove_game_btn.clicked.connect(self.remove_game)
        self.remove_game_btn.setStyleSheet('''
            QPushButton { 
                background-color: #aa4444; 
                color: white; 
                border: none; 
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #bb5555; }
        ''')
        game_mgmt_buttons.addWidget(self.remove_game_btn)
        
        games_layout.addLayout(game_mgmt_buttons)
        
        games_group.setLayout(games_layout)
        right_layout.addWidget(games_group)
        
        # Hotkeys Personalizadas
        hotkey_group = QGroupBox('Configurar Hotkeys')
        hotkey_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        hotkey_layout = QVBoxLayout()
        
        # Grid para configurar hotkeys
        hotkey_grid = QGridLayout()
        
        # Labels
        QLabel_tecla = QLabel('Tecla:')
        QLabel_tecla.setStyleSheet('color: white; font-weight: bold;')
        hotkey_grid.addWidget(QLabel_tecla, 0, 0)
        
        QLabel_acao = QLabel('Ação:')
        QLabel_acao.setStyleSheet('color: white; font-weight: bold;')
        hotkey_grid.addWidget(QLabel_acao, 0, 1)
        
        # Input para tecla
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText('Ex: f5, ctrl+c, alt+1')
        self.hotkey_input.setStyleSheet('''
            background-color: #1e1e1e; 
            color: white; 
            border: 1px solid #555; 
            padding: 4px;
        ''')
        hotkey_grid.addWidget(self.hotkey_input, 1, 0)
        
        # ComboBox para ações
        self.action_combo = QComboBox()
        self.update_action_combo()  # Método para preencher dinamicamente
        self.action_combo.setStyleSheet('''
            QComboBox {
                background-color: #1e1e1e; 
                color: white; 
                border: 1px solid #555; 
                padding: 4px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                border: none;
            }
        ''')
        hotkey_grid.addWidget(self.action_combo, 1, 1)
        
        # Botões para adicionar/remover
        hotkey_buttons = QHBoxLayout()
        
        self.add_hotkey_btn = QPushButton('➕ Adicionar')
        self.add_hotkey_btn.clicked.connect(self.add_custom_hotkey)
        self.add_hotkey_btn.setStyleSheet('''
            QPushButton { 
                background-color: #44aa44; 
                color: white; 
                border: none; 
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #55bb55; }
        ''')
        hotkey_buttons.addWidget(self.add_hotkey_btn)
        
        self.remove_hotkey_btn = QPushButton('➖ Remover')
        self.remove_hotkey_btn.clicked.connect(self.remove_custom_hotkey)
        self.remove_hotkey_btn.setStyleSheet('''
            QPushButton { 
                background-color: #aa4444; 
                color: white; 
                border: none; 
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #bb5555; }
        ''')
        hotkey_buttons.addWidget(self.remove_hotkey_btn)
        
        self.refresh_actions_btn = QPushButton('🔄 Atualizar Ações')
        self.refresh_actions_btn.clicked.connect(self.update_action_combo)
        self.refresh_actions_btn.setStyleSheet('''
            QPushButton { 
                background-color: #4444aa; 
                color: white; 
                border: none; 
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5555bb; }
        ''')
        hotkey_buttons.addWidget(self.refresh_actions_btn)
        
        hotkey_layout.addLayout(hotkey_grid)
        hotkey_layout.addLayout(hotkey_buttons)
        
        # Lista de hotkeys ativas
        hotkey_list_label = QLabel('Hotkeys Ativas:')
        hotkey_list_label.setStyleSheet('color: #ffff00; font-weight: bold; margin-top: 10px;')
        hotkey_layout.addWidget(hotkey_list_label)
        
        self.hotkey_list = QTextEdit()
        self.hotkey_list.setFixedHeight(100)
        self.hotkey_list.setReadOnly(True)
        self.hotkey_list.setStyleSheet('''
            background-color: #1e1e1e; 
            color: #00ff00; 
            font-family: Consolas, monospace;
            border: 1px solid #555;
            font-size: 9px;
        ''')
        hotkey_layout.addWidget(self.hotkey_list)
        
        hotkey_group.setLayout(hotkey_layout)
        right_layout.addWidget(hotkey_group)
        
        # Log
        log_group = QGroupBox('Log de Atividades')
        log_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        log_layout = QVBoxLayout()
        
        # Botão para limpar log
        self.clear_log_btn = QPushButton('🗑️ Limpar Log')
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.clear_log_btn.setStyleSheet('''
            QPushButton { 
                background-color: #aa4444; 
                color: white; 
                border: none; 
                padding: 4px 8px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            QPushButton:hover { background-color: #bb5555; }
        ''')
        log_layout.addWidget(self.clear_log_btn)
        
        self.log_text = QTextEdit()
        self.log_text.setStyleSheet('''
            background-color: #1e1e1e; 
            color: #00ff00; 
            font-family: Consolas, monospace;
            border: 1px solid #555;
        ''')
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        
        right_panel.setLayout(right_layout)
        
        # Adicionar painéis ao layout principal
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)  # Expansível
        
        central_widget.setLayout(main_layout)
        
        # Log inicial
        self.add_log('Bot iniciado com sucesso!')
        self.add_log('Configure uma posição de ataque primeiro')
        
        # Atualizar informações dos jogos
        self.update_turn_display()
        self.update_player_list()
        self.update_game_info()
        self.update_action_combo()
        self.update_all_games_display()
        
    def add_log(self, message):
        """Adiciona mensagem ao log com timestamp"""
        timestamp = time.strftime('%H:%M:%S')
        self.log_text.append(f'[{timestamp}] {message}')
        
    def clear_log(self):
        """Limpa o log de atividades"""
        self.log_text.clear()
        self.add_log('Log limpo pelo usuário')
        
    def update_status(self, text, color):
        """Atualiza o status com cor"""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f'color: {color}; font-size: 12px; font-weight: bold;')
        
    def set_position(self):
        """Salva posição atual do mouse - igual ao set_mouse_attack do código original"""
        pyautogui.press('backspace')  # Igual ao código original
        self.mouseAttackX = pyautogui.position().x
        self.mouseAttackY = pyautogui.position().y
        self.pos_label.setText(f'X: {self.mouseAttackX}, Y: {self.mouseAttackY}')
        self.log_signal.emit(f'Posição salva com sucesso: ({self.mouseAttackX}, {self.mouseAttackY})')
        
    def toggle_attack(self):
        """Toggle ataque básico - equivale ao F5 do código original"""
        self.holding = not self.holding
        
        if self.holding:
            # Salvar posição atual do mouse (igual saveCurrentMousePosition)
            self.mouseAntesX = pyautogui.position().x
            self.mouseAntesY = pyautogui.position().y
            
            # Atualizar interface
            self.status_signal.emit('Ataque Básico ATIVO', '#ff4444')
            self.attack_btn.setText('⏹️ Parar Básico')
            self.log_signal.emit('Atacando...')
            
            # Executar sequência do código original
            pyautogui.press('backspace')
            pyautogui.keyDown('alt')
            
            # Só move se posição foi definida (igual ao código original)
            if self.mouseAttackX != 0 and self.mouseAttackY != 0:
                pyautogui.moveTo(self.mouseAttackX, self.mouseAttackY)
            
            # Iniciar thread do ataque
            threading.Thread(target=self.hold_right_click, daemon=True).start()
            
        else:
            # Parar ataque
            self.status_signal.emit('Pronto', '#00ff00')
            self.attack_btn.setText('🗡️ Ataque Básico')
            self.log_signal.emit('Parando de atacar...')
            
            # Restaurar estado original (igual ao código original)
            pyautogui.keyUp('alt')
            pyautogui.mouseUp(button='right')
            pyautogui.moveTo(self.mouseAntesX, self.mouseAntesY)
            
    def toggle_mage(self):
        """Toggle combo mago - equivale à tecla \ do código original"""
        self.autoClickOn = not self.autoClickOn
        
        if self.autoClickOn:
            # Atualizar interface
            self.status_signal.emit('Combo Mago ATIVO', '#4444ff')
            self.mage_btn.setText('⏹️ Parar Mago')
            self.log_signal.emit('Atacando (Combo Mago)')
            
            # Executar sequência do código original
            pyautogui.press('backspace')
            
            # Iniciar thread do combo completo
            threading.Thread(target=self.mage_combo, daemon=True).start()
            
        else:
            # Parar combo
            self.status_signal.emit('Pronto', '#00ff00')
            self.mage_btn.setText('🧙 Combo Mago')
            self.log_signal.emit('Combo mago parado')
            
            # Parar mouse
            pyautogui.mouseUp(button='right')
            pyautogui.mouseUp(button='left')
            
    def stop_all(self):
        """Para todas as ações"""
        self.holding = False
        self.autoClickOn = False
        self.status_signal.emit('Pronto', '#00ff00')
        self.attack_btn.setText('🗡️ Ataque Básico')
        self.mage_btn.setText('🧙 Combo Mago')
        pyautogui.mouseUp(button='right')
        pyautogui.mouseUp(button='left')
        self.log_signal.emit('>>> TODAS AS AÇÕES FORAM PARADAS <<<')
        
    def hold_right_click(self):
        """Ataque básico em loop"""
        while self.holding:
            pyautogui.click(button='right')
            time.sleep(0.1)
            
    def mage_combo(self):
        """Executa combo completo do mago - igual ao autoClickRunning do código original"""
        # Verificar se posição foi definida (igual ao código original)
        if self.mouseAttackX == 0 and self.mouseAttackY == 0:
            self.autoClickOn = False
            self.status_signal.emit('Pronto', '#00ff00')
            self.mage_btn.setText('🧙 Combo Mago')
            self.log_signal.emit('Pressione "Salvar Posição" para setar uma posição inicial')
            return
            
        # Sequência igual ao código original
        pyautogui.press('f12')  # Skill do jogo
        
        # Salvar posição atual
        self.mouseAntesX = pyautogui.position().x
        self.mouseAntesY = pyautogui.position().y
        
        # Mover para posição de ataque
        pyautogui.moveTo(self.mouseAttackX, self.mouseAttackY)
        time.sleep(0.5)
        
        # Executar bloody walls nas 5 posições
        for i, wall in enumerate(self.bloodwalls):
            if not self.autoClickOn:  # Verificar se ainda está ativo
                break
                
            self.log_signal.emit(f'Bloody Wall {i+1}/5 (offset: {wall})')
            pyautogui.keyDown('alt')            
            pyautogui.rightClick(self.mouseAttackX, self.mouseAttackY + wall)
            pyautogui.keyUp('alt')
            
            if wall != -50:  # Não esperar no último
                time.sleep(2)
                
        # Pausa e posicionar para ataque contínuo
        time.sleep(1)  
        pyautogui.moveTo(self.mouseAttackX, self.mouseAttackY)
        
        # Iniciar ataque contínuo (Mage_hold_right_click)
        threading.Thread(target=self.mage_hold_left_click, daemon=True).start()
            
        # Voltar mouse para posição original
        pyautogui.moveTo(self.mouseAntesX, self.mouseAntesY)
        
    def mage_hold_left_click(self):
        """Ataque contínuo do mago - igual ao Mage_hold_right_click do código original"""
        while self.autoClickOn:
            pyautogui.mouseDown(button='left')
            time.sleep(0.5)

    def setup_default_hotkeys(self):
        """Configura hotkeys padrão do sistema"""
        try:
            # Adicionar hotkeys padrão do bot
            self.add_hotkey_mapping('f5', self.toggle_attack, 'Ataque Básico')
            self.add_hotkey_mapping('\\', self.toggle_mage, 'Combo Mago')  
            self.add_hotkey_mapping('alt+1', self.set_position, 'Salvar Posição')
            self.add_hotkey_mapping('f7', self.stop_all, 'Parar Tudo')
            
            # NOVO: Configurar hotkeys de todos os jogos
            self.setup_game_hotkeys()
            
            self.update_hotkey_display()
        except Exception as e:
            self.log_signal.emit(f'Erro ao configurar hotkeys padrão: {str(e)}')
    
    def add_hotkey_mapping(self, hotkey, method, description):
        """Adiciona um mapeamento de hotkey"""
        try:
            # Remover hotkey anterior se existir
            if hotkey in self.custom_hotkeys:
                keyboard.remove_hotkey(hotkey)
                
            # Adicionar nova hotkey
            keyboard.add_hotkey(hotkey, method)
            self.custom_hotkeys[hotkey] = {
                'method': method,
                'description': description
            }
            return True
        except Exception as e:
            self.log_signal.emit(f'Erro ao adicionar hotkey {hotkey}: {str(e)}')
            return False
    
    def add_custom_hotkey(self):
        """Adiciona uma hotkey personalizada via interface"""
        hotkey = self.hotkey_input.text().strip().lower()
        action = self.action_combo.currentText()
        
        if not hotkey:
            self.log_signal.emit('ERRO: Digite uma tecla válida!')
            return
            
        # Mapear ações básicas para métodos
        basic_action_methods = {
            'Ataque Básico': self.toggle_attack,
            'Combo Mago': self.toggle_mage,
            'Salvar Posição': self.set_position,
            'Parar Tudo': self.stop_all,
            'Mostrar Posição Mouse': self.show_mouse_position
        }
        
        # Verificar se é ação básica
        if action in basic_action_methods:
            method = basic_action_methods[action]
            
        # Verificar se é ação de turno específica de jogo
        elif action.startswith('Próximo Turno - '):
            game_name = action.replace('Próximo Turno - ', '')
            if game_name in self.games:
                method = lambda gname=game_name: self.next_turn_for_game(gname)
            else:
                self.log_signal.emit(f'ERRO: Jogo "{game_name}" não encontrado!')
                return
                
        elif action.startswith('Turno Anterior - '):
            game_name = action.replace('Turno Anterior - ', '')
            if game_name in self.games:
                method = lambda gname=game_name: self.previous_turn_for_game(gname)
            else:
                self.log_signal.emit(f'ERRO: Jogo "{game_name}" não encontrado!')
                return
        else:
            self.log_signal.emit(f'ERRO: Ação não reconhecida: {action}')
            return
            
        # Adicionar a hotkey
        if self.add_hotkey_mapping(hotkey, method, action):
            self.log_signal.emit(f'✅ Hotkey adicionada: {hotkey} → {action}')
            self.hotkey_input.clear()
            self.update_hotkey_display()
        else:
            self.log_signal.emit(f'❌ Falha ao adicionar hotkey: {hotkey}')
    
    def previous_turn_for_game(self, game_name):
        """Turno anterior para um jogo específico"""
        if game_name not in self.games or not self.games[game_name]['enabled']:
            return
        
        game_data = self.games[game_name]
        players = game_data['players']
        
        if len(players) == 0:
            return
        
        # Voltar turno
        game_data['current_index'] = (game_data['current_index'] - 1) % len(players)
        
        current_player = players[game_data['current_index']]
        self.log_signal.emit(f'🎮 {game_name}: Turno voltou para {current_player}')
        
        # Atualizar display se for o jogo atual
        if game_name == self.current_game:
            self.update_turn_display()
            self.update_player_list()
    
    def remove_custom_hotkey(self):
        """Remove uma hotkey personalizada"""
        hotkey = self.hotkey_input.text().strip().lower()
        
        if not hotkey:
            self.log_signal.emit('ERRO: Digite a tecla que deseja remover!')
            return
            
        if hotkey not in self.custom_hotkeys:
            self.log_signal.emit(f'ERRO: Hotkey {hotkey} não encontrada!')
            return
            
        try:
            keyboard.remove_hotkey(hotkey)
            del self.custom_hotkeys[hotkey]
            self.log_signal.emit(f'🗑️ Hotkey removida: {hotkey}')
            self.hotkey_input.clear()
            self.update_hotkey_display()
        except Exception as e:
            self.log_signal.emit(f'Erro ao remover hotkey {hotkey}: {str(e)}')
    
    def update_hotkey_display(self):
        """Atualiza a lista de hotkeys ativas na interface"""
        hotkey_text = ""
        for hotkey, info in self.custom_hotkeys.items():
            hotkey_text += f"{hotkey.upper():<12} → {info['description']}\n"
        
        self.hotkey_list.setPlainText(hotkey_text)
    
    def update_action_combo(self):
        """Atualiza o ComboBox com todas as ações disponíveis"""
        self.action_combo.clear()
        
        # Ações básicas do bot
        basic_actions = [
            'Ataque Básico',
            'Combo Mago', 
            'Salvar Posição',
            'Parar Tudo',
            'Mostrar Posição Mouse'
        ]
        
        # Adicionar ações básicas
        for action in basic_actions:
            self.action_combo.addItem(action)
        
        # Adicionar ações de turno para cada jogo
        for game_name in self.games.keys():
            self.action_combo.addItem(f'Próximo Turno - {game_name}')
            self.action_combo.addItem(f'Turno Anterior - {game_name}')
        
        # Aplicar estilo
        self.action_combo.setStyleSheet('''
            QComboBox {
                background-color: #1e1e1e; 
                color: white; 
                border: 1px solid #555; 
                padding: 4px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                border: none;
            }
        ''')
    
    # === MÉTODOS DO SISTEMA DE MÚLTIPLOS JOGOS ===
    
    def setup_game_hotkeys(self):
        """Configura as hotkeys de todos os jogos"""
        for game_name, game_data in self.games.items():
            if game_data['enabled']:
                hotkey = game_data['hotkey']
                # Usar função específica para cada jogo para evitar closure issues
                self.add_game_hotkey(game_name, hotkey)
    
    def add_game_hotkey(self, game_name, hotkey):
        """Adiciona hotkey específica para um jogo"""
        def game_method():
            self.next_turn_for_game(game_name)
        
        self.add_hotkey_mapping(hotkey, game_method, f'Turno - {game_name}')
    
    def next_turn_for_game(self, game_name):
        """Próximo turno para um jogo específico"""
        if game_name not in self.games or not self.games[game_name]['enabled']:
            return
        
        game_data = self.games[game_name]
        players = game_data['players']
        
        if len(players) == 0:
            return
        
        # Avançar turno
        game_data['current_index'] = (game_data['current_index'] + 1) % len(players)
        
        current_player = players[game_data['current_index']]
        self.log_signal.emit(f'🎮 {game_name}: Turno de {current_player}')
        
        # Atualizar display se for o jogo atual
        if game_name == self.current_game:
            self.update_turn_display()
            self.update_player_list()
        
        # Sempre atualizar o display de todos os jogos
        self.update_all_games_display()
    
    def debug_hotkeys(self):
        """Debug das hotkeys ativas - método auxiliar"""
        print("=== DEBUG HOTKEYS ===")
        for hotkey, info in self.custom_hotkeys.items():
            print(f"{hotkey} → {info['description']}")
        print("=== JOGOS ATIVOS ===")
        for game_name, game_data in self.games.items():
            print(f"{game_name}: enabled={game_data['enabled']}, hotkey={game_data['hotkey']}")
        print("====================")
        
        # Emitir no log também
        self.log_signal.emit(f"📊 Debug: {len(self.custom_hotkeys)} hotkeys ativas")
    
    def switch_game(self, game_name):
        """Muda para um jogo diferente"""
        if game_name in self.games:
            self.current_game = game_name
            self.update_turn_display()
            self.update_player_list()
            self.update_game_info()
            self.update_all_games_display()
            self.log_signal.emit(f'🎮 Mudou para: {game_name}')
    
    def update_turn_display(self):
        """Atualiza o display visual do turno"""
        game_data = self.games[self.current_game]
        players = game_data['players']
        
        if not game_data['enabled']:
            self.turn_display.setText(f"{self.current_game} (DESATIVADO)")
            self.turn_display.setStyleSheet('''
                background-color: #333333;
                color: #666666;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid #555;
                padding: 10px;
                margin: 5px;
            ''')
            return
        
        if len(players) == 0:
            current_player = "Nenhum jogador"
        else:
            current_player = players[game_data['current_index']]
        
        self.turn_display.setText(f"{self.current_game}: {current_player}")
        
        # Cores diferentes para cada jogador
        colors = ['#00ff00', '#ff4444', '#4444ff', '#ffaa00', '#ff44ff', '#44ffff']
        color = colors[game_data['current_index'] % len(colors)]
        
        self.turn_display.setStyleSheet(f'''
            background-color: #1e1e1e;
            color: {color};
            font-size: 18px;
            font-weight: bold;
            border: 2px solid {color};
            padding: 10px;
            margin: 5px;
        ''')
    
    def update_all_games_display(self):
        """Atualiza o display de todos os jogos"""
        display_text = ""
        
        for game_name, game_data in self.games.items():
            if game_data['enabled']:
                players = game_data['players']
                if len(players) > 0:
                    current_player = players[game_data['current_index']]
                    hotkey = game_data['hotkey'].upper()
                    display_text += f"🎮 {game_name} ({hotkey}): {current_player}\n"
                else:
                    hotkey = game_data['hotkey'].upper()
                    display_text += f"🎮 {game_name} ({hotkey}): Sem jogadores\n"
            else:
                display_text += f"⭕ {game_name}: DESATIVADO\n"
        
        if not display_text:
            display_text = "Nenhum jogo configurado"
        
        self.all_games_display.setText(display_text.strip())
    
    def update_game_info(self):
        """Atualiza informações do jogo atual"""
        game_data = self.games[self.current_game]
        
        # Hotkey
        self.game_hotkey_label.setText(f"Hotkey: {game_data['hotkey'].upper()}")
        
        # Status
        status = "ATIVO" if game_data['enabled'] else "INATIVO"
        color = "#44ff44" if game_data['enabled'] else "#ff4444"
        self.game_status_label.setText(f"Status: {status}")
        self.game_status_label.setStyleSheet(f'color: {color}; font-weight: bold;')
    
    def next_turn(self):
        """Passa para o próximo jogador do jogo atual"""
        self.next_turn_for_game(self.current_game)
    
    def previous_turn(self):
        """Volta para o jogador anterior do jogo atual"""
        game_data = self.games[self.current_game]
        players = game_data['players']
        
        if not game_data['enabled'] or len(players) == 0:
            return
        
        game_data['current_index'] = (game_data['current_index'] - 1) % len(players)
        
        current_player = players[game_data['current_index']]
        self.log_signal.emit(f'🎮 {self.current_game}: Turno voltou para {current_player}')
        
        self.update_turn_display()
        self.update_player_list()
    
    def toggle_current_game(self):
        """Ativa/desativa o jogo atual"""
        game_data = self.games[self.current_game]
        game_data['enabled'] = not game_data['enabled']
        
        if game_data['enabled']:
            # Reconfigurar hotkey usando método específico
            hotkey = game_data['hotkey']
            self.add_game_hotkey(self.current_game, hotkey)
            self.log_signal.emit(f'✅ {self.current_game} ATIVADO (Hotkey: {hotkey})')
        else:
            # Remover hotkey
            hotkey = game_data['hotkey']
            if hotkey in self.custom_hotkeys:
                keyboard.remove_hotkey(hotkey)
                del self.custom_hotkeys[hotkey]
            self.log_signal.emit(f'❌ {self.current_game} DESATIVADO')
        
        self.update_turn_display()
        self.update_game_info()
        self.update_hotkey_display()
        self.update_all_games_display()
    
    def add_player(self):
        """Adiciona novo jogador ao jogo atual"""
        player_name = self.new_player_input.text().strip()
        
        if not player_name:
            self.log_signal.emit('❌ Digite um nome para o jogador!')
            return
        
        game_data = self.games[self.current_game]
        players = game_data['players']
        
        if player_name in players:
            self.log_signal.emit(f'❌ Jogador "{player_name}" já existe em {self.current_game}!')
            return
        
        players.append(player_name)
        self.new_player_input.clear()
        self.update_player_list()
        self.update_turn_display()
        self.update_all_games_display()
        
        self.log_signal.emit(f'✅ "{player_name}" adicionado ao {self.current_game}!')
    
    def remove_player(self):
        """Remove jogador selecionado do jogo atual"""
        current_row = self.player_list.currentRow()
        
        if current_row < 0:
            self.log_signal.emit('❌ Selecione um jogador para remover!')
            return
        
        game_data = self.games[self.current_game]
        players = game_data['players']
        
        if len(players) <= 1:
            self.log_signal.emit('❌ Deve haver pelo menos 1 jogador!')
            return
        
        removed_player = players.pop(current_row)
        
        # Ajustar índice atual se necessário
        if game_data['current_index'] >= len(players):
            game_data['current_index'] = 0
        
        self.update_player_list()
        self.update_turn_display()
        self.update_all_games_display()
        
        self.log_signal.emit(f'🗑️ "{removed_player}" removido do {self.current_game}!')
    
    def update_player_list(self):
        """Atualiza lista visual de jogadores do jogo atual"""
        self.player_list.clear()
        
        game_data = self.games[self.current_game]
        players = game_data['players']
        current_index = game_data['current_index']
        
        for i, player in enumerate(players):
            item = QListWidgetItem(f"{i+1}. {player}")
            
            # Destacar jogador atual
            if i == current_index and game_data['enabled']:
                item.setBackground(QColor(68, 68, 255, 100))  # Azul translúcido
                item.setText(f"👑 {i+1}. {player} (Vez atual)")
            
            self.player_list.addItem(item)
    
    def add_new_game(self):
        """Adiciona um novo jogo ao sistema"""
        game_name = self.new_game_input.text().strip()
        hotkey = self.new_game_hotkey.text().strip().lower()
        
        if not game_name:
            self.log_signal.emit('❌ Digite o nome do jogo!')
            return
        
        if not hotkey:
            self.log_signal.emit('❌ Digite uma hotkey para o jogo!')
            return
        
        if game_name in self.games:
            self.log_signal.emit(f'❌ Jogo "{game_name}" já existe!')
            return
        
        # Verificar se hotkey já está em uso
        for existing_game, data in self.games.items():
            if data['hotkey'] == hotkey:
                self.log_signal.emit(f'❌ Hotkey "{hotkey}" já usada por {existing_game}!')
                return
        
        # Criar novo jogo
        self.games[game_name] = {
            "players": ["Player1"],
            "current_index": 0,
            "hotkey": hotkey,
            "enabled": False
        }
        
        # Atualizar interface
        self.game_selector.addItem(game_name)
        self.new_game_input.clear()
        self.new_game_hotkey.clear()
        
        # Atualizar ComboBox de ações
        self.update_action_combo()
        
        self.log_signal.emit(f'🎮 Novo jogo criado: "{game_name}" (Hotkey: {hotkey})')
    
    def remove_game(self):
        """Remove o jogo atual"""
        if len(self.games) <= 1:
            self.log_signal.emit('❌ Deve haver pelo menos 1 jogo!')
            return
        
        if self.current_game == "Dark Eden":
            self.log_signal.emit('❌ Não é possível remover o jogo padrão!')
            return
        
        # Remover hotkey se ativa
        game_data = self.games[self.current_game]
        if game_data['enabled']:
            hotkey = game_data['hotkey']
            if hotkey in self.custom_hotkeys:
                keyboard.remove_hotkey(hotkey)
                del self.custom_hotkeys[hotkey]
        
        # Remover jogo
        removed_game = self.current_game
        del self.games[self.current_game]
        
        # Atualizar seletor
        self.game_selector.removeItem(self.game_selector.currentIndex())
        
        # Mudar para primeiro jogo disponível
        self.current_game = list(self.games.keys())[0]
        self.game_selector.setCurrentText(self.current_game)
        
        self.update_turn_display()
        self.update_player_list()
        self.update_game_info()
        self.update_hotkey_display()
        
        # Atualizar ComboBox de ações
        self.update_action_combo()
        
        self.log_signal.emit(f'🗑️ Jogo "{removed_game}" removido!')
    
    def change_game_hotkey(self):
        """Muda a hotkey do jogo atual"""
        new_hotkey = self.new_game_hotkey.text().strip().lower()
        
        if not new_hotkey:
            self.log_signal.emit('❌ Digite a nova hotkey!')
            return
        
        # Verificar se hotkey já está em uso
        for game_name, data in self.games.items():
            if data['hotkey'] == new_hotkey and game_name != self.current_game:
                self.log_signal.emit(f'❌ Hotkey "{new_hotkey}" já usada por {game_name}!')
                return
        
        game_data = self.games[self.current_game]
        old_hotkey = game_data['hotkey']
        
        # Remover hotkey antiga se ativa
        if game_data['enabled'] and old_hotkey in self.custom_hotkeys:
            keyboard.remove_hotkey(old_hotkey)
            del self.custom_hotkeys[old_hotkey]
        
        # Atualizar hotkey
        game_data['hotkey'] = new_hotkey
        
        # Adicionar nova hotkey se jogo ativo
        if game_data['enabled']:
            self.add_game_hotkey(self.current_game, new_hotkey)
        
        self.new_game_hotkey.clear()
        self.update_game_info()
        self.update_hotkey_display()
        
        self.log_signal.emit(f'🔧 Hotkey do {self.current_game} alterada: {old_hotkey} → {new_hotkey}')
    
    def get_current_player(self):
        """Retorna o jogador atual do jogo ativo"""
        game_data = self.games[self.current_game]
        players = game_data['players']
        
        if not game_data['enabled'] or len(players) == 0:
            return None
        
        return players[game_data['current_index']]
    
    # === FIM DOS MÉTODOS DE MÚLTIPLOS JOGOS ===
    
    def show_mouse_position(self):
        """Mostra posição atual do mouse - método extra"""
        x, y = pyautogui.position()
        self.log_signal.emit(f'🖱️ Posição atual: ({x}, {y})')
        pyautogui.press('capslock')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Aplicar tema escuro
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.WindowText, Qt.white)
    app.setPalette(palette)
    
    window = DarkEdenBotGUI()
    window.show()
    
    sys.exit(app.exec_())