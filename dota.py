import sys
import os
import pyautogui
import keyboard
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QCheckBox, QFrame, QSizePolicy, QLineEdit, QComboBox)
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QColor, QPen, QBrush

class KeyboardListener(QThread):
    """Thread para escutar eventos do teclado"""
    combo_triggered = pyqtSignal()
    
    def __init__(self, combo_hotkey="space"):
        super().__init__()
        self.combo_hotkey = combo_hotkey.lower()
        self.running = False
    
    def update_hotkey(self, new_hotkey):
        """Atualizar a tecla do combo"""
        try:
            # Processar a tecla
            processed_hotkey = str(new_hotkey).strip()
            
            # Verificar se a tecla não está vazia
            if not processed_hotkey:
                print("⚠️ Tecla vazia recebida - mantendo tecla atual")
                return
            
            # Validar caracteres básicos para evitar teclas inválidas
            if len(processed_hotkey) > 20:  # Limite razoável
                print("⚠️ Tecla muito longa - ignorando")
                return
            
            # Mapear teclas especiais (incluindo variações de case)
            key_mapping = {
                # Variações de espaço
                'space': 'space', 'Space': 'space', 'SPACE': 'space',
                # Variações de enter
                'enter': 'enter', 'Enter': 'enter', 'ENTER': 'enter',
                'return': 'enter', 'Return': 'enter',
                # Variações de tab
                'tab': 'tab', 'Tab': 'tab', 'TAB': 'tab',
                # Variações de escape
                'esc': 'esc', 'Esc': 'esc', 'ESC': 'esc',
                'escape': 'esc', 'Escape': 'esc',
                # Variações de modificadoras
                'shift': 'shift', 'Shift': 'shift', 'SHIFT': 'shift',
                'ctrl': 'ctrl', 'Ctrl': 'ctrl', 'CTRL': 'ctrl',
                'control': 'ctrl', 'Control': 'ctrl',
                'alt': 'alt', 'Alt': 'alt', 'ALT': 'alt',
            }
            
            # Processar combinações ou tecla simples
            if '+' in processed_hotkey:
                parts = [part.strip() for part in processed_hotkey.split('+')]
                mapped_parts = []
                for part in parts:
                    if part in key_mapping:
                        mapped_parts.append(key_mapping[part])
                    else:
                        mapped_parts.append(part.lower())
                processed_hotkey = '+'.join(mapped_parts)
            else:
                if processed_hotkey in key_mapping:
                    processed_hotkey = key_mapping[processed_hotkey]
                else:
                    processed_hotkey = processed_hotkey.lower()
            
            # Atualizar apenas se for diferente
            if self.combo_hotkey != processed_hotkey:
                old_hotkey = self.combo_hotkey
                
                # Remover hotkey antiga com tratamento de erro
                try:
                    if old_hotkey:
                        keyboard.remove_hotkey(old_hotkey)
                        print(f"Hotkey antiga '{old_hotkey}' removida")
                except Exception as remove_error:
                    print(f"Aviso: Erro ao remover hotkey antiga '{old_hotkey}': {remove_error}")
                
                # Atualizar
                self.combo_hotkey = processed_hotkey
                print(f"Hotkey atualizada para: {self.combo_hotkey}")
                
                # Se estiver rodando, registrar nova hotkey
                if self.running:
                    def on_hotkey():
                        if self.running:
                            self.combo_triggered.emit()
                    
                    try:
                        keyboard.add_hotkey(self.combo_hotkey, on_hotkey)
                        print(f"Nova hotkey '{self.combo_hotkey}' registrada com sucesso")
                    except Exception as add_error:
                        print(f"Erro ao registrar nova hotkey '{self.combo_hotkey}': {add_error}")
                        # Reverter para a hotkey antiga em caso de erro
                        self.combo_hotkey = old_hotkey
                        if old_hotkey:
                            try:
                                keyboard.add_hotkey(old_hotkey, on_hotkey)
                                print(f"Revertido para hotkey antiga: {old_hotkey}")
                            except:
                                print(f"Erro crítico: não foi possível reverter para {old_hotkey}")
                
        except Exception as e:
            print(f"Erro geral ao atualizar hotkey: {e}")
    
    def run(self):
        """Executar o listener do teclado (versão não-bloqueante)"""
        self.running = True
        
        # Usar um callback em vez de wait() bloqueante
        def on_hotkey():
            if self.running:
                self.combo_triggered.emit()
        
        try:
            # Registrar hotkey com callback
            keyboard.add_hotkey(self.combo_hotkey, on_hotkey)
            
            # Loop não-bloqueante
            while self.running:
                self.msleep(50)  # Verificar a cada 50ms
                
        except Exception as e:
            print(f"Erro no keyboard listener: {e}")
        finally:
            # Limpar hotkey ao sair
            try:
                keyboard.remove_hotkey(self.combo_hotkey)
            except:
                pass
    
    def stop(self):
        """Parar o listener"""
        print("Parando KeyboardListener...")
        self.running = False
        
        # Limpar hotkey registrada
        try:
            keyboard.remove_hotkey(self.combo_hotkey)
        except:
            pass
            
        self.quit()
        self.wait(1000)  # Timeout de 1 segundo

class SkillButton(QPushButton):
    def __init__(self, skill_name, hotkey, icon_path=None):
        super().__init__()
        self.skill_name = skill_name
        self.hotkey = hotkey
        self.setFixedSize(80, 80)
        
        # Criar um layout vertical para o botão
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Se tiver ícone, adicionar (por enquanto usar cor de fundo)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #444;
                border: 2px solid #666;
                border-radius: 5px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: #888;
                background-color: #555;
            }}
            QPushButton:pressed {{
                background-color: #333;
            }}
        """)
        
        self.setText(f"{skill_name}\n{hotkey}")

class HotkeyCheckbox(QWidget):
    def __init__(self, hotkey, skill_name):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.checkbox = QCheckBox()
        self.checkbox.setFixedSize(20, 20)
        
        self.label = QLabel(hotkey)
        self.label.setStyleSheet("color: white; font-weight: bold;")
        
        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        # Removido addStretch() para evitar problemas de layout
        # layout.addStretch()
        
        self.setLayout(layout)

class TomagoxaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dota 1.0")
        self.setFixedSize(700, 900)  # Voltando para 1000 pixels com o novo layout otimizado
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
        """)
        
        # Listas para armazenar os widgets
        self.skill_inputs = []  # QLineEdit dos skills
        self.skill_checkboxes = []  # QCheckBox dos skills
        self.item_inputs = []  # QLineEdit dos items
        self.item_checkboxes = []  # QCheckBox dos items
        
        # Variáveis para armazenar as configurações salvas
        self.saved_config = {
            'skills': [],
            'items': [],
            'combo_hotkey': 'space',  # Padrão em minúsculas
            'combo_enabled': True  # Alterado para True por padrão
        }
        
        # Rastreamento da ordem de cliques nos checkboxes
        self.click_order = []  # Lista para armazenar a ordem dos cliques
        self.click_counter = 0  # Contador para numerar a ordem
        
        # Estado do sistema (ligado/desligado) - SIMPLIFICADO
        self.system_enabled = False
        # Removido: self.power_button_debounce e self.combo_active
        
        # Timer para debounce da atualização de hotkey
        self.hotkey_update_timer = QTimer()
        self.hotkey_update_timer.setSingleShot(True)
        self.hotkey_update_timer.timeout.connect(self.delayed_hotkey_update)
        self.pending_hotkey = None
        
        # Inicializar o listener do teclado (sempre ativo, apenas verifica system_enabled)
        self.keyboard_listener = KeyboardListener("space")
        self.keyboard_listener.combo_triggered.connect(self.execute_combo)
        self.keyboard_listener.start()  # Iniciar uma vez e deixar rodando
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Título colorido "Tomagoxa"
        self.create_title_label(main_layout)
        
        # Layout horizontal para skills e items com botões
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Layout da esquerda (skills e items)
        left_content = QVBoxLayout()
        left_content.setSpacing(20)
        
        # Layout para os botões de habilidades
        skills_layout = QVBoxLayout()
        self.create_skill_buttons(skills_layout)
        left_content.addLayout(skills_layout)
        
        # Layout da direita (botões de controle ao lado dos items)
        right_content = QVBoxLayout()
        right_content.setSpacing(15)
        
        # Seção de informações do usuário (botão power)
        self.create_user_info(right_content)
        
        # Botões de ação
        self.create_action_buttons_vertical(right_content)
        
        right_content.addStretch()
        
        # Adicionar conteúdos ao layout horizontal
        content_layout.addLayout(left_content, 3)  # 75% do espaço
        content_layout.addLayout(right_content, 1)  # 25% do espaço
        
        main_layout.addLayout(content_layout)
        
        # Seção Combo (embaixo de tudo)
        self.create_combo_section(main_layout)
        
        main_layout.addStretch()
    
    def create_inventory_slot(self, slot_name, default_hotkey="", is_skill=False):
        """Criar um slot de inventário com quadrado, campo de texto e checkbox"""
        container = QWidget()
        container.setFixedHeight(120)  # Altura fixa para evitar sobreposição
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(3)  # Espaçamento mínimo mas controlado
        
        # Quadrado do inventário (similar ao da imagem)
        inventory_square = QPushButton()
        inventory_square.setFixedSize(60, 60)
        inventory_square.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 3px;
            }
            QPushButton:hover {
                border-color: #777;
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        
        # Campo de texto
        text_field = QLineEdit()
        text_field.setFixedHeight(25)
        text_field.setFixedWidth(60)  # Aumentado para melhor proporção
        text_field.setText(default_hotkey)  # Definir valor padrão
        text_field.setPlaceholderText("Tecla")
        text_field.setStyleSheet("""
            QLineEdit {
                background-color: #444;
                border: 1px solid #666;
                border-radius: 3px;
                color: white;
                padding: 2px 5px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #888;
                background-color: #555;
            }
        """)
        
        # Checkbox
        checkbox = QCheckBox()
        checkbox.setFixedSize(20, 20)
        checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #666;
                border-radius: 3px;
                background-color: #444;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }
            QCheckBox::indicator:hover {
                border-color: #888;
            }
        """)
        
        # Conectar checkbox ao método de rastreamento de ordem
        checkbox_id = f"{'skill' if is_skill else 'item'}_{len(self.skill_inputs if is_skill else self.item_inputs)}"
        checkbox.stateChanged.connect(lambda state, cb_id=checkbox_id, hotkey_field=text_field: self.on_checkbox_clicked(state, cb_id, hotkey_field))
        
        # Adicionar widgets às listas para referência posterior
        if is_skill:
            self.skill_inputs.append(text_field)
            self.skill_checkboxes.append(checkbox)
        else:
            self.item_inputs.append(text_field)
            self.item_checkboxes.append(checkbox)
        
        # Adicionar tudo ao container principal (layout vertical)
        container_layout.addWidget(inventory_square)
        container_layout.addWidget(text_field, 0, Qt.AlignCenter)
        container_layout.addWidget(checkbox, 0, Qt.AlignCenter)
        
        return container
    
    def create_title_label(self, parent_layout):
        title_label = QLabel("Malva Sena")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Criar fonte grande
        font = QFont()
        font.setPointSize(28)
        font.setBold(True)
        title_label.setFont(font)
        
        # Estilo com gradiente colorido
        title_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff4444, stop:0.2 #ff44ff, stop:0.4 #4444ff,
                    stop:0.6 #44ffff, stop:0.8 #44ff44, stop:1 #ffff44);
                color: white;
                padding: 10px;
                border-radius: 10px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
        """)
        
        parent_layout.addWidget(title_label)
    
    def create_skill_buttons(self, skills_layout):
        # Label "Skills" acima da seção superior
        skills_label = QLabel("Skills")
        skills_label.setAlignment(Qt.AlignLeft)
        skills_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 2px 0px;
                margin-bottom: 2px;
            }
        """)
        skills_layout.addWidget(skills_label)
        
        # Criar seção superior com 4 slots
        top_section = QWidget()
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        
        # Valores padrão para Skills: Q, W, E, R
        skill_hotkeys = ["Q", "W", "E", "R"]
        for i in range(4):
            slot_container = self.create_inventory_slot(f"Slot {i+1}", skill_hotkeys[i], is_skill=True)
            top_layout.addWidget(slot_container)
        
        # Adicionar stretch para igualar com a seção inferior
        top_layout.addStretch()
        
        skills_layout.addWidget(top_section)
        
        # Adicionar espaçamento entre as seções (reduzido)
        skills_layout.addSpacing(10)
        
        # Label "Items" acima da seção inferior
        items_label = QLabel("Items")
        items_label.setAlignment(Qt.AlignLeft)
        items_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 2px 0px;
                margin-bottom: 2px;
            }
        """)
        skills_layout.addWidget(items_label)
        
        # Criar seção inferior com 6 slots (3 em cima e 3 embaixo)
        bottom_section = QWidget()
        bottom_main_layout = QVBoxLayout(bottom_section)
        bottom_main_layout.setContentsMargins(0, 0, 0, 0)
        bottom_main_layout.setSpacing(15)  # Reduzido de 20 para 15
        
        # Primeira linha (3 slots)
        first_row = QWidget()
        first_row_layout = QHBoxLayout(first_row)
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        first_row_layout.setSpacing(2)
        
        # Valores padrão para Items primeira linha: 1, 2, 3
        item_hotkeys_row1 = ["1", "2", "3"]
        for i in range(3):
            slot_container = self.create_inventory_slot(f"Slot {5+i}", item_hotkeys_row1[i], is_skill=False)
            first_row_layout.addWidget(slot_container)
        
        first_row_layout.addStretch()
        
        # Segunda linha (3 slots)
        second_row = QWidget()
        second_row_layout = QHBoxLayout(second_row)
        second_row_layout.setContentsMargins(0, 0, 0, 0)
        second_row_layout.setSpacing(2)
        
        # Valores padrão para Items segunda linha: 4, 5, 6
        item_hotkeys_row2 = ["4", "5", "6"]
        for i in range(3):
            slot_container = self.create_inventory_slot(f"Slot {8+i}", item_hotkeys_row2[i], is_skill=False)
            second_row_layout.addWidget(slot_container)
        
        second_row_layout.addStretch()
        
        # Adicionar as duas linhas ao layout principal da seção inferior
        bottom_main_layout.addWidget(first_row)
        bottom_main_layout.addWidget(second_row)
        
        # Adicionar seção inferior ao layout principal
        skills_layout.addWidget(bottom_section)
    
    def create_user_info(self, parent_layout):
        # Botão de ligar/desligar compacto para lateral
        self.power_button = QPushButton("DESLIGADO")
        self.power_button.setFixedSize(120, 45)
        self.power_button.clicked.connect(self.toggle_system_power)
        self.update_power_button_style()
        
        parent_layout.addWidget(self.power_button)
    
    def create_action_buttons_vertical(self, parent_layout):
        """Criar botões de ação em layout vertical para a lateral direita"""
        
        # Botão Aceitar
        self.accept_btn = QPushButton("Aceitar")
        self.accept_btn.setFixedSize(120, 35)
        self.accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.accept_btn.clicked.connect(self.save_configuration)
        
        # Botão Reset
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedSize(120, 35)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        reset_btn.clicked.connect(self.reset_all_configurations)
        
        # Botão Doação
        donate_btn = QPushButton("Doação")
        donate_btn.setFixedSize(120, 35)
        donate_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        parent_layout.addWidget(self.accept_btn)
        parent_layout.addWidget(reset_btn)
        parent_layout.addWidget(donate_btn)
    
    def create_combo_section(self, parent_layout):
        # Container do Combo
        combo_frame = QFrame()
        combo_frame.setStyleSheet("""
            QFrame {
                background-color: #444;
                border: 2px solid #666;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        combo_layout = QVBoxLayout(combo_frame)
        
        # Título Combo
        combo_title = QLabel("Combo")
        combo_title.setAlignment(Qt.AlignCenter)
        combo_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 5px;
                background-color: #555;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        combo_layout.addWidget(combo_title)
        
        # Controles do combo
        combo_controls = QVBoxLayout()
        
        # Seção para definir a tecla do combo
        hotkey_section = QWidget()
        hotkey_layout = QHBoxLayout(hotkey_section)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_layout.setSpacing(10)
        
        # Label para tecla
        hotkey_label = QLabel("Tecla do Combo:")
        hotkey_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        hotkey_layout.addWidget(hotkey_label)
        
        # Campo para definir a tecla (agora usando dropdown)
        self.combo_hotkey_input = QComboBox()
        self.combo_hotkey_input.setFixedHeight(25)
        self.combo_hotkey_input.setFixedWidth(120)  # Aumentado para acomodar texto das opções
        self.combo_hotkey_input.setEditable(True)  # Permitir digitação personalizada
        
        # Opções pré-definidas de teclas
        hotkey_options = [
            "space",           # Teclas comuns
            "enter", "tab", "esc", "caps lock",
            "f1", "f2", "f3", "f4", "f5", "f6", 
            "f7", "f8", "f9", "f10", "f11", "f12",
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
            "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
            "ctrl+a", "ctrl+c", "ctrl+v", "ctrl+x", "ctrl+z",  # Combinações comuns
            "alt+1", "alt+2", "alt+3", "alt+4", "alt+5",
            "shift+1", "shift+2", "shift+3", "shift+4", "shift+5"
        ]
        
        self.combo_hotkey_input.addItems(hotkey_options)
        self.combo_hotkey_input.setCurrentText("space")  # Valor padrão
        
        self.combo_hotkey_input.setStyleSheet("""
            QComboBox {
                background-color: #444;
                border: 1px solid #666;
                border-radius: 3px;
                color: white;
                padding: 3px 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QComboBox:focus {
                border-color: #888;
                background-color: #555;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #555;
            }
            QComboBox::down-arrow {
                image: none;
                border: 1px solid #888;
                border-radius: 2px;
                background-color: #666;
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #444;
                border: 1px solid #666;
                color: white;
                selection-background-color: #555;
            }
        """)
        
        # Conectar mudanças no dropdown (método seguro)
        self.combo_hotkey_input.currentTextChanged.connect(self.update_combo_hotkey)
        self.combo_hotkey_input.editTextChanged.connect(self.update_combo_hotkey)
        hotkey_layout.addWidget(self.combo_hotkey_input)
        
        hotkey_layout.addStretch()
        
        combo_controls.addWidget(hotkey_section)
        
        # Seção para definir o ping (delay)
        ping_section = QWidget()
        ping_layout = QHBoxLayout(ping_section)
        ping_layout.setContentsMargins(0, 0, 0, 0)
        ping_layout.setSpacing(10)
        
        # Label para ping
        ping_label = QLabel("Ping:")
        ping_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        ping_layout.addWidget(ping_label)
        
        # Campo para definir o ping (delay em ms)
        self.ping_input = QLineEdit()
        self.ping_input.setFixedHeight(25)
        self.ping_input.setFixedWidth(80)
        self.ping_input.setText("100")  # Valor padrão 100ms
        self.ping_input.setPlaceholderText("ms")
        self.ping_input.setStyleSheet("""
            QLineEdit {
                background-color: #444;
                border: 1px solid #666;
                border-radius: 3px;
                color: white;
                padding: 3px 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border-color: #888;
                background-color: #555;
            }
        """)
        
        # Validar apenas números
        self.ping_input.textChanged.connect(self.validate_ping_input)
        ping_layout.addWidget(self.ping_input)
        
        # Label de unidade
        ms_label = QLabel("ms")
        ms_label.setStyleSheet("""
            QLabel {
                color: #ccc;
                font-size: 12px;
            }
        """)
        ping_layout.addWidget(ms_label)
        
        ping_layout.addStretch()
        
        combo_controls.addWidget(ping_section)
        
        # Checkbox Nenj com tecla dinâmica
        self.nenj_checkbox = HotkeyCheckbox("space", "Nenj")  # Valor padrão em minúsculas
        # Marcar checkbox como padrão
        self.nenj_checkbox.checkbox.setChecked(True)
        combo_controls.addWidget(self.nenj_checkbox)
        
        combo_layout.addLayout(combo_controls)
        parent_layout.addWidget(combo_frame)
    
    def update_combo_hotkey(self):
        """Atualiza a tecla do combo quando a seleção for alterada (com debounce)"""
        try:
            new_hotkey = self.combo_hotkey_input.currentText().strip()
            
            # Armazenar a nova tecla e parar o timer anterior
            self.pending_hotkey = new_hotkey
            self.hotkey_update_timer.stop()
            
            # Atualizar o label imediatamente para feedback visual
            if hasattr(self, 'nenj_checkbox') and self.nenj_checkbox:
                if new_hotkey:
                    self.nenj_checkbox.label.setText(new_hotkey)
                else:
                    self.nenj_checkbox.label.setText("(vazio)")
            
            # Aguardar 300ms antes de atualizar o listener (debounce reduzido para dropdown)
            self.hotkey_update_timer.start(300)
                
        except Exception as e:
            print(f"Erro ao processar mudança de tecla: {e}")
    
    def delayed_hotkey_update(self):
        """Atualizar o listener após o debounce"""
        try:
            if self.pending_hotkey is None:
                return
                
            new_hotkey = self.pending_hotkey
            
            if new_hotkey:
                # Atualizar a tecla no listener com tratamento de erro
                if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
                    try:
                        self.keyboard_listener.update_hotkey(new_hotkey)
                        print(f"✅ Tecla do combo atualizada para: {new_hotkey}")
                    except Exception as listener_error:
                        print(f"❌ Erro ao atualizar listener: {listener_error}")
            else:
                print("ℹ️ Campo da tecla do combo está vazio")
                
        except Exception as e:
            print(f"Erro na atualização com delay: {e}")
        finally:
            self.pending_hotkey = None
    
    def validate_ping_input(self):
        """Validar input do ping para aceitar apenas números"""
        try:
            text = self.ping_input.text()
            # Remover caracteres não numéricos
            filtered_text = ''.join(filter(str.isdigit, text))
            
            # Limitar a 4 dígitos (máximo 9999ms)
            if len(filtered_text) > 4:
                filtered_text = filtered_text[:4]
            
            # Atualizar o campo se foi modificado
            if filtered_text != text:
                cursor_pos = self.ping_input.cursorPosition()
                self.ping_input.setText(filtered_text)
                self.ping_input.setCursorPosition(min(cursor_pos, len(filtered_text)))
                
        except Exception as e:
            print(f"Erro ao validar ping: {e}")
    
    def get_ping_delay(self):
        """Obter o delay em segundos baseado no ping configurado"""
        try:
            ping_text = self.ping_input.text().strip()
            if not ping_text:
                return 0.1  # Padrão 100ms se vazio
            
            ping_ms = int(ping_text)
            # Limitar entre 10ms e 5000ms
            ping_ms = max(10, min(5000, ping_ms))
            
            return ping_ms / 1000.0  # Converter para segundos
        except (ValueError, AttributeError):
            return 0.1  # Padrão 100ms em caso de erro
    
    def on_checkbox_clicked(self, state, checkbox_id, hotkey_field):
        """Rastrear a ordem dos cliques nos checkboxes"""
        try:
            if state == 2:  # Checkbox marcado
                self.click_counter += 1
                # Obter hotkey atual do campo de texto
                current_hotkey = hotkey_field.text().strip()
                if not current_hotkey:
                    current_hotkey = self.get_default_hotkey(checkbox_id)
                
                order_data = {
                    'id': checkbox_id,
                    'order': self.click_counter,
                    'hotkey': current_hotkey,
                    'timestamp': self.click_counter
                }
                # Remover entrada anterior se existir
                self.click_order = [item for item in self.click_order if item['id'] != checkbox_id]
                # Adicionar nova entrada
                self.click_order.append(order_data)
                print(f"Adicionado à ordem: {checkbox_id} - Posição {self.click_counter}")
            else:  # Checkbox desmarcado
                # Remover da ordem
                self.click_order = [item for item in self.click_order if item['id'] != checkbox_id]
                print(f"Removido da ordem: {checkbox_id}")
            
            # Mostrar ordem atual
            self.show_current_order()
        except Exception as e:
            print(f"Erro no rastreamento de checkbox: {e}")
            # Continuar funcionando mesmo com erro
    
    def get_default_hotkey(self, checkbox_id):
        """Obter hotkey padrão baseado no ID do checkbox"""
        try:
            if checkbox_id.startswith('skill_'):
                index = int(checkbox_id.split('_')[1])
                defaults = ['Q', 'W', 'E', 'R']
                if 0 <= index < len(defaults):
                    return defaults[index]
            elif checkbox_id.startswith('item_'):
                index = int(checkbox_id.split('_')[1])
                if 0 <= index < 6:
                    return str(index + 1)
        except (ValueError, IndexError) as e:
            print(f"Erro ao obter hotkey padrão para {checkbox_id}: {e}")
        return ''
    
    def show_current_order(self):
        """Mostrar a ordem atual no console"""
        if self.click_order:
            sorted_order = sorted(self.click_order, key=lambda x: x['order'])
            order_text = " → ".join([f"{item['hotkey']}" for item in sorted_order])
            print(f"Ordem atual do combo: {order_text}")
        else:
            print("Nenhuma tecla selecionada para o combo")
    
    def save_configuration(self):
        """Salvar todas as configurações quando o botão Aceitar for clicado"""
        try:
            # Salvar configurações dos skills
            skills_config = []
            skill_defaults = ['Q', 'W', 'E', 'R']
            for i, (input_field, checkbox) in enumerate(zip(self.skill_inputs, self.skill_checkboxes)):
                default_hotkey = skill_defaults[i] if i < len(skill_defaults) else f'skill_{i}'
                skill_data = {
                    'index': i,
                    'hotkey': input_field.text().strip() or default_hotkey,
                    'enabled': checkbox.isChecked()
                }
                skills_config.append(skill_data)
            
            # Salvar configurações dos items
            items_config = []
            for i, (input_field, checkbox) in enumerate(zip(self.item_inputs, self.item_checkboxes)):
                item_data = {
                    'index': i,
                    'hotkey': input_field.text().strip() or str(i+1),
                    'enabled': checkbox.isChecked()
                }
                items_config.append(item_data)
            
            # Salvar configuração do combo
            combo_hotkey = self.combo_hotkey_input.currentText().strip()
            
            # Validar se a tecla não está vazia
            if not combo_hotkey:
                print("⚠️ AVISO: Tecla do combo está vazia! Usando 'space' como padrão.")
                combo_hotkey = "space"
                self.combo_hotkey_input.setCurrentText("space")  # Atualizar o dropdown
                self.nenj_checkbox.label.setText("space")  # Atualizar o label
            
            combo_enabled = self.nenj_checkbox.checkbox.isChecked()
            
            # Atualizar o dicionário de configurações salvas
            self.saved_config = {
                'skills': skills_config,
                'items': items_config,
                'combo_hotkey': combo_hotkey,
                'combo_enabled': combo_enabled,
                'click_order': self.click_order.copy()  # Salvar a ordem dos cliques
            }
            
            # Atualizar a tecla do listener (simplificado)
            if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
                self.keyboard_listener.update_hotkey(combo_hotkey)
            
            # Feedback visual para o usuário
            print("Configurações salvas!")
            if self.click_order:
                sorted_order = sorted(self.click_order, key=lambda x: x['order'])
                order_text = " → ".join([f"{item['hotkey']}" for item in sorted_order])
                print(f"Ordem de execução: {order_text}")
            
            # Mostrar feedback de salvamento
            self.show_save_feedback()
            
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
            print("Falha ao salvar. Tente novamente.")
    
    # Métodos apply_combo_settings, start_combo_listener e stop_combo_listener removidos
    # pois não são mais necessários na versão simplificada
    
    def execute_combo(self):
        """Executar o combo quando a tecla for pressionada"""
        try:
            # Verificar APENAS se o sistema está ligado (simplificado)
            if not self.system_enabled:
                print("Sistema desligado - Combo não executado")
                return
                
            print("Combo executado!")
            
            # Executar baseado na ordem de cliques dos checkboxes
            if self.click_order:
                sorted_order = sorted(self.click_order, key=lambda x: x['order'])
                
                # Executar tecla + clique em sequência
                total_executed = 0
                ping_delay = self.get_ping_delay()  # Obter delay dinâmico
                print(f"Usando delay de {int(ping_delay * 1000)}ms baseado no ping")
                
                for item in sorted_order:
                    hotkey = item.get('hotkey', '').lower()
                    if hotkey:
                        print(f"Pressionando tecla: {hotkey} (Posição {item['order']})")
                        self.press_hotkey(hotkey)  # Pressionar a tecla
                        pyautogui.sleep(ping_delay)  # Usar delay dinâmico
                        
                        # Clique esquerdo do mouse após cada tecla
                        print(f"🖱️ Clicando com botão esquerdo após tecla: {hotkey}")
                        pyautogui.click()
                        print(f"✅ Clique executado após tecla: {hotkey}")
                        
                        total_executed += 1
                        pyautogui.sleep(ping_delay)  # Usar delay dinâmico
                
                # Garantir que o último clique seja processado
                if total_executed > 0:
                    pyautogui.sleep(ping_delay)  # Usar delay dinâmico
                    print(f"🎯 Combo finalizado - {total_executed} teclas executadas")
            else:
                # Fallback para ordem sequencial se não houver ordem de cliques
                print("Usando ordem sequencial (nenhum checkbox marcado com ordem)")
                ping_delay = self.get_ping_delay()  # Obter delay dinâmico
                print(f"Usando delay de {int(ping_delay * 1000)}ms baseado no ping")
                
                # Executar skills primeiro (tecla + clique)
                skills_executed = 0
                for skill in self.saved_config.get('skills', []):
                    if skill.get('enabled', False):
                        hotkey = skill.get('hotkey', '').lower()
                        if hotkey:
                            print(f"Pressionando skill: {hotkey}")
                            self.press_hotkey(hotkey)
                            pyautogui.sleep(ping_delay)  # Usar delay dinâmico
                            
                            # Clique esquerdo do mouse após cada skill
                            print(f"🖱️ Clicando com botão esquerdo após skill: {hotkey}")
                            pyautogui.click()
                            print(f"✅ Clique executado após skill: {hotkey}")
                            
                            skills_executed += 1
                            pyautogui.sleep(ping_delay)  # Usar delay dinâmico
                
                # Executar items depois (tecla + clique)
                items_executed = 0
                for item in self.saved_config.get('items', []):
                    if item.get('enabled', False):
                        hotkey = item.get('hotkey', '').lower()
                        if hotkey:
                            print(f"Pressionando item: {hotkey}")
                            self.press_hotkey(hotkey)
                            pyautogui.sleep(ping_delay)  # Usar delay dinâmico
                            
                            # Clique esquerdo do mouse após cada item
                            print(f"🖱️ Clicando com botão esquerdo após item: {hotkey}")
                            pyautogui.click()
                            print(f"✅ Clique executado após item: {hotkey}")
                            
                            items_executed += 1
                            pyautogui.sleep(ping_delay)  # Usar delay dinâmico
                
                # Garantir que o último clique seja processado
                if items_executed > 0:
                    pyautogui.sleep(ping_delay)  # Usar delay dinâmico
                    print(f"🎯 Combo finalizado - {items_executed} items executados")
                
                # Log final consolidado
                total_all = skills_executed + items_executed
                if total_all > 0:
                    print(f"🏁 COMBO COMPLETO - Total: {skills_executed} skills + {items_executed} items = {total_all} ações")
        except Exception as e:
            print(f"Erro ao executar combo: {e}")
            print("Falha na execução do combo")
    
    def press_hotkey(self, hotkey):
        """Pressionar uma tecla ou combinação de teclas corretamente"""
        try:
            hotkey = hotkey.strip().lower()
            
            if '+' in hotkey:
                # É uma combinação (ex: alt+1, ctrl+c, shift+space)
                parts = [part.strip() for part in hotkey.split('+')]
                
                # Mapear modificadores para pyautogui
                modifier_map = {
                    'ctrl': 'ctrl',
                    'alt': 'alt', 
                    'shift': 'shift',
                    'cmd': 'cmd',
                    'win': 'win'
                }
                
                modifiers = []
                key = None
                
                # Separar modificadores da tecla principal
                for part in parts:
                    if part in modifier_map:
                        modifiers.append(modifier_map[part])
                    else:
                        key = part
                
                if key and modifiers:
                    # Usar pyautogui.hotkey para combinações
                    print(f"  🔥 Executando combinação: {'+'.join(modifiers)}+{key}")
                    pyautogui.hotkey(*modifiers, key)
                else:
                    print(f"  ⚠️ Combinação inválida: {hotkey}")
                    # Fallback para pyautogui.press
                    pyautogui.press(hotkey)
                    
            else:
                # É uma tecla simples (ex: a, 1, space, enter)
                print(f"  🎯 Executando tecla simples: {hotkey}")
                pyautogui.press(hotkey)
                
        except Exception as e:
            print(f"  ❌ Erro ao pressionar tecla '{hotkey}': {e}")
            # Tentar fallback com pyautogui.press
            try:
                pyautogui.press(hotkey)
                print(f"  ✅ Fallback bem-sucedido para: {hotkey}")
            except:
                print(f"  💥 Fallback também falhou para: {hotkey}")
    
    def show_save_feedback(self):
        """Mostrar feedback visual de que as configurações foram salvas"""
        try:
            if not hasattr(self, 'accept_btn') or not self.accept_btn:
                return
                
            # Mudar para cor de sucesso
            self.accept_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2E7D32;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
            self.accept_btn.setText("Salvo!")
            
            # Restaurar após 2 segundos
            QTimer.singleShot(2000, self.restore_accept_button)
        except Exception as e:
            print(f"Erro ao mostrar feedback de salvamento: {e}")
    
    def restore_accept_button(self):
        """Restaurar o botão Aceitar ao estado original"""
        try:
            if not hasattr(self, 'accept_btn') or not self.accept_btn:
                return
                
            self.accept_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.accept_btn.setText("Aceitar")
        except Exception as e:
            print(f"Erro ao restaurar botão aceitar: {e}")
    
    def reset_all_configurations(self):
        """Resetar todas as configurações para o estado inicial"""
        try:
            # Desligar o sistema (simplificado)
            self.system_enabled = False
            self.update_power_button_style()
            
            # Desmarcar todos os checkboxes dos skills
            for checkbox in self.skill_checkboxes:
                checkbox.blockSignals(True)
                checkbox.setChecked(False)
                checkbox.blockSignals(False)
            
            # Desmarcar todos os checkboxes dos items
            for checkbox in self.item_checkboxes:
                checkbox.blockSignals(True)
                checkbox.setChecked(False)
                checkbox.blockSignals(False)
            
            # Marcar checkbox do combo como padrão
            self.nenj_checkbox.checkbox.setChecked(True)
            
            # Resetar campos de texto para valores padrão
            skill_defaults = ["Q", "W", "E", "R"]
            for i, input_field in enumerate(self.skill_inputs):
                if i < len(skill_defaults):
                    input_field.setText(skill_defaults[i])
            
            item_defaults = ["1", "2", "3", "4", "5", "6"]
            for i, input_field in enumerate(self.item_inputs):
                if i < len(item_defaults):
                    input_field.setText(item_defaults[i])
            
            # Resetar tecla do combo
            self.combo_hotkey_input.setCurrentText("space")
            self.nenj_checkbox.label.setText("space")
            
            # Limpar ordem de cliques
            self.click_order = []
            self.click_counter = 0
            
            # Resetar configurações salvas
            self.saved_config = {
                'skills': [],
                'items': [],
                'combo_hotkey': 'space',
                'combo_enabled': True,
                'click_order': []
            }
            
            print("Configurações resetadas! Sistema DESLIGADO")
            self.show_reset_feedback()
            
        except Exception as e:
            print(f"Erro ao resetar configurações: {e}")
    
    def show_reset_feedback(self):
        """Mostrar feedback visual de que foi resetado"""
        try:
            # Encontrar o botão reset e mudar sua cor temporariamente
            reset_button = None
            for child in self.findChildren(QPushButton):
                if child.text() == "Reset":
                    reset_button = child
                    break
            
            if reset_button:
                # Mudar para cor de confirmação
                reset_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                """)
                reset_button.setText("Resetado!")
                
                # Restaurar após 2 segundos
                QTimer.singleShot(2000, self.restore_reset_button)
        except Exception as e:
            print(f"Erro ao mostrar feedback de reset: {e}")
    
    def restore_reset_button(self):
        """Restaurar o botão Reset ao estado original"""
        try:
            reset_button = None
            for child in self.findChildren(QPushButton):
                if child.text() == "Resetado!":
                    reset_button = child
                    break
            
            if reset_button:
                reset_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #d32f2f;
                    }
                """)
                reset_button.setText("Reset")
        except Exception as e:
            print(f"Erro ao restaurar botão reset: {e}")
    
    def closeEvent(self, event):
        """Limpar recursos quando a aplicação for fechada (versão otimizada)"""
        try:
            print("Fechando aplicação...")
            
            # Desativar sistema imediatamente
            self.system_enabled = False
            
            # Parar o listener de forma mais agressiva
            if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
                print("Parando KeyboardListener...")
                self.keyboard_listener.stop()
                
                # Se não parar em 500ms, forçar
                if not self.keyboard_listener.wait(500):
                    print("Forçando parada do KeyboardListener...")
                    self.keyboard_listener.terminate()
                    self.keyboard_listener.wait(200)
            
            print("Aplicação fechada!")
            event.accept()
            
        except Exception as e:
            print(f"Erro ao fechar: {e}")
            # Forçar fechamento mesmo com erro
            event.accept()
    
    def lighten_color(self, color):
        """Clarear uma cor hexadecimal"""
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, r + 30)
        g = min(255, g + 30)
        b = min(255, b + 30)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def darken_color(self, color):
        """Escurecer uma cor hexadecimal"""
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, r - 30)
        g = max(0, g - 30)
        b = max(0, b - 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def toggle_system_power(self):
        """Alternar entre ligado e desligado (versão simplificada)"""
        try:
            # Simples: apenas alternar a variável booleana
            self.system_enabled = not self.system_enabled
            
            # Atualizar o visual do botão
            self.update_power_button_style()
            
            if self.system_enabled:
                print("Sistema LIGADO - Combo habilitado")
            else:
                print("Sistema DESLIGADO - Combo desabilitado")
                
        except Exception as e:
            print(f"Erro ao alternar estado do sistema: {e}")
    
    def complete_power_toggle(self):
        """Método não mais necessário - removido da versão simplificada"""
        pass
    
    def release_power_debounce(self):
        """Método não mais necessário - removido da versão simplificada"""
        pass
    
    def update_power_button_style(self):
        """Atualizar o estilo do botão baseado no estado"""
        try:
            # Verificar se o botão existe
            if not hasattr(self, 'power_button') or not self.power_button:
                print("Botão de power não encontrado")
                return
            
            # Verificar se o botão ainda é válido
            try:
                self.power_button.isVisible()  # Teste se o objeto ainda existe
            except RuntimeError:
                print("Botão de power foi deletado")
                return
                
            if self.system_enabled:
                # Estado ligado - verde
                self.power_button.setText("LIGADO")
                self.power_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: 2px solid #45a049;
                        border-radius: 8px;
                        font-size: 12px;
                        font-weight: bold;
                        text-align: center;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                        border-color: #4CAF50;
                    }
                    QPushButton:pressed {
                        background-color: #388e3c;
                    }
                """)
            else:
                # Estado desligado - vermelho
                self.power_button.setText("DESLIGADO")
                self.power_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: 2px solid #d32f2f;
                        border-radius: 8px;
                        font-size: 12px;
                        font-weight: bold;
                        text-align: center;
                    }
                    QPushButton:hover {
                        background-color: #d32f2f;
                        border-color: #f44336;
                    }
                    QPushButton:pressed {
                        background-color: #c62828;
                    }
                """)
                
            print(f"Botão atualizado para: {'LIGADO' if self.system_enabled else 'DESLIGADO'}")
            
        except Exception as e:
            print(f"Erro ao atualizar estilo do botão: {e}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Usar estilo Fusion para melhor aparência
    
    # Aplicar tema escuro global
    app.setStyleSheet("""
        QApplication {
            background-color: #2b2b2b;
            color: white;
        }
    """)
    
    window = TomagoxaApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()