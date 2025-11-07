import sys
import os
import importlib.util
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import ctypes
import ctypes.wintypes
import psutil
import struct
import threading
import time
import json
import pymem
import pymem.process

# Importar a classe MemoryReader  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar usando importlib para lidar com o hífen no nome do arquivo
import importlib.util
spec = importlib.util.spec_from_file_location("read_memory", "read-memory.py")
read_memory_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(read_memory_module)
MemoryReader = read_memory_module.MemoryReader

class MemoryViewerGUI(QMainWindow):
    # Sinais para comunicação entre threads
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str, str)  # texto, cor
    value_signal = pyqtSignal(str, str, str)  # endereço, valor, tipo
    process_signal = pyqtSignal(str)  # status do processo
    
    def __init__(self):
        super().__init__()
        
        # Instância do leitor de memória
        self.memory_reader = MemoryReader()
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # Novo: armazenar endereço base do processo
        self.process_base_address = 0
        
        # Dicionário para armazenar endereços monitorados
        self.monitored_addresses = {}
        
        # Novo: armazenar valores para regras e conversões
        self.memory_values = {}  # Para acessar valores por descrição
        
        # Arquivo para salvar/carregar endereços
        self.addresses_file = "memory_addresses.json"
        
        self.initUI()
        
        # Conectar sinais
        self.log_signal.connect(self.add_log)
        self.status_signal.connect(self.update_status)
        self.value_signal.connect(self.update_memory_value)
        self.process_signal.connect(self.update_process_status)
        
        # Inicializar lista de processos
        self.refresh_processes()
        
        # Carregar endereços salvos
        self.load_addresses()
        
    def initUI(self):
        self.setWindowTitle('🎮 Dark Eden Memory Viewer')
        self.setGeometry(100, 100, 800, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout()
        
        # === PAINEL ESQUERDO - CONTROLES ===
        left_panel = QWidget()
        left_panel.setFixedWidth(300)
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
        title = QLabel('MEMORY VIEWER')
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
        
        # === SEÇÃO LEITURA DE MEMÓRIA ===
        memory_group = QGroupBox('Leitura de Memória')
        memory_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        memory_layout = QVBoxLayout()
        
        # Endereço
        memory_layout.addWidget(QLabel('Endereço (hex):', styleSheet='color: white;'))
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText('DarkEden.exe+0x1234, base+0x1234 ou 0x12345678')
        memory_layout.addWidget(self.address_input)
        
        # Tipo de dado
        memory_layout.addWidget(QLabel('Tipo de Dado:', styleSheet='color: white;'))
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems([
            'int32', 'uint32', 'float', 'double',
            'int16', 'uint16', 'int8', 'uint8', 
            'string', 'raw_bytes'
        ])
        memory_layout.addWidget(self.data_type_combo)
        
        # Descrição
        memory_layout.addWidget(QLabel('Descrição:', styleSheet='color: white;'))
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText('Ex: HP do jogador, Mana, etc.')
        memory_layout.addWidget(self.description_input)
        
        # String length (só para strings)
        self.string_length_input = QLineEdit()
        self.string_length_input.setPlaceholderText('Comprimento (só para strings)')
        memory_layout.addWidget(self.string_length_input)
        
        # Botões de ação
        memory_buttons = QVBoxLayout()
        
        self.read_once_btn = QPushButton('📖 Ler Uma Vez')
        self.read_once_btn.clicked.connect(self.read_memory_once)
        self.read_once_btn.setStyleSheet('QPushButton { background-color: #aa4444; }')
        memory_buttons.addWidget(self.read_once_btn)
        
        self.start_monitor_btn = QPushButton('🔍 Iniciar Monitoramento')
        self.start_monitor_btn.clicked.connect(self.toggle_monitoring)
        self.start_monitor_btn.setStyleSheet('QPushButton { background-color: #4444aa; }')
        memory_buttons.addWidget(self.start_monitor_btn)
        
        self.add_address_btn = QPushButton('➕ Adicionar à Lista')
        self.add_address_btn.clicked.connect(self.add_to_monitoring_list)
        self.add_address_btn.setStyleSheet('QPushButton { background-color: #44aa44; }')
        memory_buttons.addWidget(self.add_address_btn)
        
        # Novo botão para comparação com Cheat Engine
        self.debug_btn = QPushButton('🔍 Debug & Comparar')
        self.debug_btn.clicked.connect(self.debug_memory_address)
        self.debug_btn.setStyleSheet('QPushButton { background-color: #aa44aa; }')
        memory_buttons.addWidget(self.debug_btn)
        
        # Novo botão para converter endereço
        self.convert_btn = QPushButton('🔄 Converter para Offset')
        self.convert_btn.clicked.connect(self.convert_absolute_to_offset)
        self.convert_btn.setStyleSheet('QPushButton { background-color: #44aa88; }')
        memory_buttons.addWidget(self.convert_btn)
        
        # Novo botão para converter TODOS os endereços absolutos automaticamente
        self.convert_all_btn = QPushButton('🔄 Converter Todos Absolutos')
        self.convert_all_btn.clicked.connect(self.convert_all_absolute_addresses_auto)
        self.convert_all_btn.setEnabled(False)
        self.convert_all_btn.setToolTip('Converte automaticamente todos os endereços absolutos salvos para módulo+offset')
        self.convert_all_btn.setStyleSheet('QPushButton { background-color: #aa44aa; }')
        memory_buttons.addWidget(self.convert_all_btn)
        
        # Novo botão para listar módulos
        self.modules_btn = QPushButton('📋 Listar Módulos')
        self.modules_btn.clicked.connect(self.list_all_modules)
        self.modules_btn.setStyleSheet('QPushButton { background-color: #8844aa; }')
        memory_buttons.addWidget(self.modules_btn)
        
        memory_layout.addLayout(memory_buttons)
        memory_group.setLayout(memory_layout)
        left_layout.addWidget(memory_group)
        
        # === CONFIGURAÇÕES DE MONITORAMENTO ===
        monitor_group = QGroupBox('Configurações do Monitor')
        monitor_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        monitor_layout = QVBoxLayout()
        
        monitor_layout.addWidget(QLabel('Intervalo (segundos):', styleSheet='color: white;'))
        self.interval_input = QLineEdit()
        self.interval_input.setText('1.0')
        self.interval_input.setPlaceholderText('1.0')
        monitor_layout.addWidget(self.interval_input)
        
        monitor_group.setLayout(monitor_layout)
        left_layout.addWidget(monitor_group)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # === PAINEL DIREITO - VISUALIZAÇÃO ===
        right_panel = QWidget()
        right_panel.setStyleSheet('QWidget { background-color: #3a3a3a; }')
        right_layout = QVBoxLayout()
        
        # === VALORES EM TEMPO REAL ===
        values_group = QGroupBox('Valores Monitorados')
        values_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        values_layout = QVBoxLayout()
        
        # Tabela de valores
        self.values_table = QTableWidget()
        self.values_table.setColumnCount(4)
        self.values_table.setHorizontalHeaderLabels(['Endereço', 'Tipo', 'Valor', 'Descrição'])
        self.values_table.setStyleSheet('''
            QTableWidget {
                background-color: #1e1e1e;
                color: white;
                gridline-color: #555;
                border: 1px solid #555;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
            QHeaderView::section {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                padding: 4px;
                font-weight: bold;
            }
        ''')
        self.values_table.horizontalHeader().setStretchLastSection(True)
        self.values_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        values_layout.addWidget(self.values_table)
        
        # Botões para gerenciar lista
        list_buttons = QHBoxLayout()
        
        remove_btn = QPushButton('🗑️ Remover')
        remove_btn.clicked.connect(self.remove_from_monitoring_list)
        remove_btn.setStyleSheet('QPushButton { background-color: #aa4444; }')
        list_buttons.addWidget(remove_btn)
        
        save_btn = QPushButton('💾 Salvar Lista')
        save_btn.clicked.connect(self.save_addresses)
        save_btn.setStyleSheet('QPushButton { background-color: #4444aa; }')
        list_buttons.addWidget(save_btn)
        
        load_btn = QPushButton('📂 Carregar Lista')
        load_btn.clicked.connect(self.load_addresses_dialog)
        load_btn.setStyleSheet('QPushButton { background-color: #44aa44; }')
        list_buttons.addWidget(load_btn)
        
        clear_btn = QPushButton('🧹 Limpar Tudo')
        clear_btn.clicked.connect(self.clear_all_addresses)
        clear_btn.setStyleSheet('QPushButton { background-color: #aa4444; }')
        list_buttons.addWidget(clear_btn)
        
        values_layout.addLayout(list_buttons)
        
        values_group.setLayout(values_layout)
        right_layout.addWidget(values_group)
        
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
            font-size: 9px;
        ''')
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        
        right_panel.setLayout(right_layout)
        
        # Adicionar painéis ao layout principal
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
        
        central_widget.setLayout(main_layout)
        
        # Log inicial
        self.add_log('🎮 Memory Viewer iniciado!')
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
    
    def get_process_base_address(self, pid):
        """Obtém o endereço base do módulo principal do processo"""
        try:
            # Constantes do Windows
            INVALID_HANDLE_VALUE = -1
            TH32CS_SNAPMODULE = 0x00000008
            TH32CS_SNAPMODULE32 = 0x00000010
            
            # Estrutura MODULEENTRY32
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
            
            # Criar snapshot dos módulos
            snapshot = kernel32.CreateToolhelp32Snapshot(
                TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid
            )
            
            if snapshot == INVALID_HANDLE_VALUE:
                self.add_log("❌ Falha ao criar snapshot dos módulos")
                return None
            
            try:
                module_entry = MODULEENTRY32()
                module_entry.dwSize = ctypes.sizeof(MODULEENTRY32)
                
                # Obter primeiro módulo (principal)
                if kernel32.Module32First(snapshot, ctypes.byref(module_entry)):
                    base_addr = ctypes.cast(module_entry.modBaseAddr, ctypes.c_void_p).value
                    module_name = module_entry.szModule.decode('utf-8', errors='ignore')
                    
                    self.add_log(f"📍 Módulo principal: {module_name}")
                    self.add_log(f"🎯 Endereço base: 0x{base_addr:08X}")
                    return base_addr
                else:
                    self.add_log("❌ Falha ao obter primeiro módulo")
                    return None
                    
            finally:
                kernel32.CloseHandle(snapshot)
                
        except Exception as e:
            self.add_log(f"❌ Erro ao obter endereço base: {str(e)}")
            
        return None
    
    def get_module_base_address(self, module_name):
        """Obtém endereço base de um módulo específico"""
        try:
            # Constantes do Windows
            INVALID_HANDLE_VALUE = -1
            TH32CS_SNAPMODULE = 0x00000008
            TH32CS_SNAPMODULE32 = 0x00000010
            
            # Estrutura MODULEENTRY32
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
            pid = self.memory_reader.pid
            
            # Criar snapshot dos módulos
            snapshot = kernel32.CreateToolhelp32Snapshot(
                TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid
            )
            
            if snapshot == INVALID_HANDLE_VALUE:
                return None
            
            try:
                module_entry = MODULEENTRY32()
                module_entry.dwSize = ctypes.sizeof(MODULEENTRY32)
                
                # Iterar por todos os módulos
                if kernel32.Module32First(snapshot, ctypes.byref(module_entry)):
                    while True:
                        current_module = module_entry.szModule.decode('utf-8', errors='ignore')
                        
                        # Comparar nomes (case insensitive)
                        if current_module.lower() == module_name.lower():
                            base_addr = ctypes.cast(module_entry.modBaseAddr, ctypes.c_void_p).value
                            self.add_log(f"📍 Módulo encontrado: {current_module} = 0x{base_addr:08X}")
                            return base_addr
                        
                        # Próximo módulo
                        if not kernel32.Module32Next(snapshot, ctypes.byref(module_entry)):
                            break
                            
            finally:
                kernel32.CloseHandle(snapshot)
                
            return None
            
        except Exception as e:
            self.add_log(f"❌ Erro ao buscar módulo {module_name}: {str(e)}")
            return None
    
    def find_module_for_address(self, absolute_address):
        """Encontra qual módulo contém o endereço e retorna módulo+offset"""
        try:
            # Constantes do Windows
            INVALID_HANDLE_VALUE = -1
            TH32CS_SNAPMODULE = 0x00000008
            TH32CS_SNAPMODULE32 = 0x00000010
            
            # Estrutura MODULEENTRY32
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
            pid = self.memory_reader.pid
            
            # Criar snapshot dos módulos
            snapshot = kernel32.CreateToolhelp32Snapshot(
                TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid
            )
            
            if snapshot == INVALID_HANDLE_VALUE:
                return None
            
            try:
                module_entry = MODULEENTRY32()
                module_entry.dwSize = ctypes.sizeof(MODULEENTRY32)
                
                # Iterar por todos os módulos
                if kernel32.Module32First(snapshot, ctypes.byref(module_entry)):
                    while True:
                        base_addr = ctypes.cast(module_entry.modBaseAddr, ctypes.c_void_p).value
                        module_size = module_entry.modBaseSize
                        module_name = module_entry.szModule.decode('utf-8', errors='ignore')
                        
                        # Verificar se o endereço está dentro deste módulo
                        if base_addr <= absolute_address < (base_addr + module_size):
                            offset = absolute_address - base_addr
                            return {
                                'module': module_name,
                                'base': base_addr,
                                'offset': offset,
                                'format': f"{module_name}+0x{offset:X}"
                            }
                        
                        # Próximo módulo
                        if not kernel32.Module32Next(snapshot, ctypes.byref(module_entry)):
                            break
                            
            finally:
                kernel32.CloseHandle(snapshot)
                
            return None
            
        except Exception as e:
            self.add_log(f"❌ Erro ao buscar módulo para endereço: {str(e)}")
            return None
    
    def convert_absolute_to_offset(self):
        """Converte endereço absoluto em offset automaticamente"""
        if not self.memory_reader.process_handle:
            self.add_log("❌ Conecte-se a um processo primeiro!")
            return
            
        try:
            address_str = self.address_input.text().strip()
            if not address_str:
                self.add_log("❌ Digite um endereço válido!")
                return
            
            # Verificar se já é um offset
            if '+' in address_str or address_str.lower().startswith('base+'):
                self.add_log("❌ Endereço já está em formato de offset!")
                return
            
            # Converter para endereço absoluto
            if address_str.startswith('0x'):
                absolute_address = int(address_str, 16)
            else:
                absolute_address = int(address_str, 16)
            
            self.add_log(f"🔍 === CONVERSÃO DE ENDEREÇO ABSOLUTO ===")
            self.add_log(f"📍 Endereço original: 0x{absolute_address:08X}")
            
            # Tentar converter para offset do processo principal
            if self.process_base_address:
                main_offset = absolute_address - self.process_base_address
                if 0 <= main_offset <= 0x10000000:  # Offset válido (até ~256MB)
                    base_format = f"base+0x{main_offset:X}"
                    self.add_log(f"✅ Processo principal: {base_format}")
                    self.add_log(f"📊 Base: 0x{self.process_base_address:08X} + Offset: 0x{main_offset:X}")
                    
                    # Substituir no campo de endereço
                    self.address_input.setText(base_format)
                    self.add_log(f"🔄 Campo atualizado para: {base_format}")
                    return
            
            # Tentar encontrar em outros módulos
            module_info = self.find_module_for_address(absolute_address)
            if module_info:
                module_format = module_info['format']
                self.add_log(f"✅ Módulo específico: {module_format}")
                self.add_log(f"📊 {module_info['module']}: 0x{module_info['base']:08X} + Offset: 0x{module_info['offset']:X}")
                
                # Substituir no campo de endereço
                self.address_input.setText(module_format)
                self.add_log(f"🔄 Campo atualizado para: {module_format}")
                return
            
            # Se não encontrou, mostrar informações de debug detalhadas
            self.add_log("⚠️ Endereço não pertence a nenhum módulo conhecido")
            self.add_log("")
            self.add_log("📋 Análise detalhada:")
            
            # Listar os 3 primeiros módulos para referência
            self.add_log(f"📦 Primeiros módulos do processo:")
            pm_modules = pymem.Pymem()
            pm_modules.open_process_from_id(self.memory_reader.process_id)
            modules_list = list(pm_modules.list_modules())[:3]
            for i, mod in enumerate(modules_list, 1):
                self.add_log(f"   {i}. {mod.name}: 0x{mod.lpBaseOfDll:08X} - 0x{mod.lpBaseOfDll + mod.SizeOfImage:08X}")
            
            self.add_log("")
            self.add_log("📋 Possíveis causas:")
            self.add_log("   1️⃣ Endereço em HEAP - memória alocada dinamicamente")
            self.add_log("   2️⃣ Endereço em STACK - dados temporários da execução")
            self.add_log("   3️⃣ Ponteiro multi-level - precisa usar Pointer Scan")
            self.add_log("   4️⃣ Endereço de outro processo (verificar se conectou ao correto)")
            self.add_log("")
            self.add_log("💡 SOLUÇÃO:")
            self.add_log("   🔍 Use o Cheat Engine:")
            self.add_log("   1. Encontre o endereço que quer (o valor que muda)")
            self.add_log("   2. Clique direito → 'Pointer scan for this address'")
            self.add_log("   3. Aguarde o scan terminar")
            self.add_log("   4. Reinicie o jogo e faça 'Pointer scan again'")
            self.add_log("   5. Repita até encontrar poucos ponteiros (< 100)")
            self.add_log("   6. O ponteiro terá formato: [[darkeden.exe+X]+Y]+Z")
            self.add_log("")
            self.add_log("💡 Enquanto isso, mantenha o endereço absoluto no JSON")
            self.add_log("   (mas será necessário atualizar manualmente a cada restart)")
            
            # Tentar encontrar ponteiros automaticamente
            self.try_find_pointer_to_address(target_address)
            
        except ValueError as e:
            self.add_log(f"❌ Endereço inválido: {str(e)}")
        except Exception as e:
            self.add_log(f"❌ Erro na conversão: {str(e)}")
    
    def list_all_modules(self):
        """Lista todos os módulos carregados no processo"""
        if not self.memory_reader.process_handle:
            self.add_log("❌ Conecte-se a um processo primeiro!")
            return
            
        try:
            # Constantes do Windows
            INVALID_HANDLE_VALUE = -1
            TH32CS_SNAPMODULE = 0x00000008
            TH32CS_SNAPMODULE32 = 0x00000010
            
            # Estrutura MODULEENTRY32
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
            pid = self.memory_reader.pid
            
            # Criar snapshot dos módulos
            snapshot = kernel32.CreateToolhelp32Snapshot(
                TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid
            )
            
            if snapshot == INVALID_HANDLE_VALUE:
                self.add_log("❌ Falha ao criar snapshot dos módulos")
                return
            
            try:
                self.add_log("📋 === MÓDULOS CARREGADOS ===")
                module_entry = MODULEENTRY32()
                module_entry.dwSize = ctypes.sizeof(MODULEENTRY32)
                
                module_count = 0
                # Iterar por todos os módulos
                if kernel32.Module32First(snapshot, ctypes.byref(module_entry)):
                    while True:
                        base_addr = ctypes.cast(module_entry.modBaseAddr, ctypes.c_void_p).value
                        module_size = module_entry.modBaseSize
                        module_name = module_entry.szModule.decode('utf-8', errors='ignore')
                        
                        # Mostrar informações do módulo
                        size_mb = module_size / 1024 / 1024
                        end_addr = base_addr + module_size
                        
                        if module_count == 0:
                            self.add_log(f"🎯 {module_name}: 0x{base_addr:08X} - 0x{end_addr:08X} ({size_mb:.1f}MB) [PRINCIPAL]")
                        else:
                            self.add_log(f"📦 {module_name}: 0x{base_addr:08X} - 0x{end_addr:08X} ({size_mb:.1f}MB)")
                        
                        module_count += 1
                        
                        # Próximo módulo
                        if not kernel32.Module32Next(snapshot, ctypes.byref(module_entry)):
                            break
                            
                self.add_log(f"📊 Total: {module_count} módulos carregados")
                self.add_log("💡 Use os nomes dos módulos para criar offsets: ModuleName.dll+0x1234")
                            
            finally:
                kernel32.CloseHandle(snapshot)
                
        except Exception as e:
            self.add_log(f"❌ Erro ao listar módulos: {str(e)}")
    
    def parse_address(self, address_str):
        """Converte string de endereço em endereço absoluto - versão com suporte a módulos melhorado"""
        address_str = address_str.strip()
        
        # Formato: DarkEden.exe+0x1234 ou game.dll+1234
        if '+' in address_str and not address_str.lower().startswith('base+'):
            parts = address_str.split('+')
            if len(parts) == 2:
                module_name = parts[0].strip()
                offset_str = parts[1].strip()
                
                # Obter base do módulo específico
                module_base = self.get_module_base_address(module_name)
                if not module_base:
                    # Tentar buscar com diferentes extensões
                    if not module_name.lower().endswith('.exe') and not module_name.lower().endswith('.dll'):
                        # Tentar com .exe primeiro
                        module_base = self.get_module_base_address(f"{module_name}.exe")
                        if not module_base:
                            # Depois com .dll
                            module_base = self.get_module_base_address(f"{module_name}.dll")
                    
                    if not module_base:
                        raise ValueError(f"Módulo '{module_name}' não encontrado no processo!")
                
                # Converter offset
                if offset_str.lower().startswith('0x'):
                    offset = int(offset_str, 16)
                else:
                    offset = int(offset_str, 16)  # Assumir hex
                    
                return module_base + offset
        
        # Formato: base+0x1234 (módulo principal)
        elif address_str.lower().startswith('base+'):
            if not self.process_base_address:
                raise ValueError("Endereço base do processo não disponível! Conecte-se ao processo primeiro.")
                
            offset_str = address_str[5:]  # Remove "base+"
            
            if offset_str.startswith('0x'):
                offset = int(offset_str, 16)
            else:
                offset = int(offset_str, 16)
                
            return self.process_base_address + offset
            
        # Formato tradicional: 0x12345678
        elif address_str.startswith('0x'):
            return int(address_str, 16)
            
        # Assumir que é endereço em hex
        else:
            return int(address_str, 16)
    
    def connect_to_process(self):
        """Conecta ao processo selecionado - versão melhorada"""
        if self.process_combo.currentIndex() == -1:
            self.add_log("❌ Selecione um processo primeiro!")
            return
            
        try:
            pid = self.process_combo.currentData()
            process_name = self.process_combo.currentText().split(' (PID:')[0]
            
            if self.memory_reader.find_process_by_pid(pid):
                if self.memory_reader.open_process():
                    # Obter endereço base
                    self.process_base_address = self.get_process_base_address(pid)
                    
                    self.connection_status.setText(f'✅ Conectado: {process_name}')
                    self.connection_status.setStyleSheet('color: #44ff44; font-weight: bold;')
                    self.add_log(f"🔗 Conectado ao processo: {process_name} (PID: {pid})")
                    
                    if self.process_base_address:
                        self.add_log(f"🎯 Base calculada: 0x{self.process_base_address:08X}")
                        self.add_log("💡 Use formato: DarkEden.exe+0x1234, base+0x1234 ou 0x1234")
                        self.add_log("📋 Exemplo: DarkEden.exe+0x1000 para módulo específico")
                    else:
                        self.add_log("⚠️ Não foi possível obter endereço base (modo absoluto)")
                    
                    # Habilitar controles
                    self.read_once_btn.setEnabled(True)
                    self.start_monitor_btn.setEnabled(True)
                    self.add_address_btn.setEnabled(True)
                    self.convert_all_btn.setEnabled(True)  # Habilitar conversão automática
                    
                    # Recalcular endereços carregados
                    self.recalculate_addresses()
                else:
                    self.connection_status.setText('❌ Falha na conexão')
                    self.connection_status.setStyleSheet('color: #ff4444; font-weight: bold;')
                    self.add_log("❌ Falha ao abrir processo. Execute como administrador!")
            else:
                self.add_log("❌ Processo não encontrado!")
                
        except Exception as e:
            self.add_log(f"❌ Erro ao conectar: {str(e)}")
    
    def debug_memory_address(self):
        """Faz debug detalhado de um endereço de memória - versão melhorada"""
        if not self.memory_reader.process_handle:
            self.add_log("❌ Conecte-se a um processo primeiro!")
            return
            
        try:
            address_str = self.address_input.text().strip()
            if not address_str:
                self.add_log("❌ Digite um endereço válido!")
                return
                
            # Usar novo parser de endereço
            address = self.parse_address(address_str)
                
            self.add_log(f"🔍 === DEBUG DO ENDEREÇO {address_str} ===")
            
            # Mostrar cálculo se for offset
            if address_str.lower().startswith('base+'):
                self.add_log(f"🧮 Endereço calculado: 0x{address:08X}")
                self.add_log(f"📍 Base do processo: 0x{self.process_base_address:08X}")
                offset = address - self.process_base_address
                self.add_log(f"📏 Offset: +0x{offset:X}")
            elif '+' in address_str and not address_str.lower().startswith('base+'):
                self.add_log(f"🧮 Endereço calculado: 0x{address:08X}")
                parts = address_str.split('+')
                if len(parts) == 2:
                    module_name = parts[0].strip()
                    offset_str = parts[1].strip()
                    if offset_str.lower().startswith('0x'):
                        offset = int(offset_str, 16)
                    else:
                        offset = int(offset_str, 16)
                    self.add_log(f"📍 Módulo: {module_name}, Offset: +0x{offset:X}")
            
            # 1. Ler bytes brutos
            raw_bytes = self.memory_reader.read_bytes(address, 16)
            if raw_bytes:
                hex_bytes = ' '.join(f'{b:02X}' for b in raw_bytes)
                self.add_log(f"📊 Bytes brutos (16 bytes): {hex_bytes}")
                
                # 2. Interpretar como diferentes tipos
                import struct
                self.add_log("🔢 Interpretações possíveis:")
                
                # Int32 (Little Endian - padrão Windows)
                if len(raw_bytes) >= 4:
                    int32_le = struct.unpack('<i', raw_bytes[:4])[0]
                    int32_be = struct.unpack('>i', raw_bytes[:4])[0]
                    uint32_le = struct.unpack('<I', raw_bytes[:4])[0]
                    uint32_be = struct.unpack('>I', raw_bytes[:4])[0]
                    
                    self.add_log(f"   • int32 (Little Endian): {int32_le}")
                    self.add_log(f"   • int32 (Big Endian): {int32_be}")
                    self.add_log(f"   • uint32 (Little Endian): {uint32_le}")
                    self.add_log(f"   • uint32 (Big Endian): {uint32_be}")
                
                # Float (Little Endian)
                if len(raw_bytes) >= 4:
                    try:
                        float_le = struct.unpack('<f', raw_bytes[:4])[0]
                        float_be = struct.unpack('>f', raw_bytes[:4])[0]
                        self.add_log(f"   • float (Little Endian): {float_le}")
                        self.add_log(f"   • float (Big Endian): {float_be}")
                    except:
                        self.add_log("   • float: erro na conversão")
                
                # Double (Little Endian)
                if len(raw_bytes) >= 8:
                    try:
                        double_le = struct.unpack('<d', raw_bytes[:8])[0]
                        double_be = struct.unpack('>d', raw_bytes[:8])[0]
                        self.add_log(f"   • double (Little Endian): {double_le}")
                        self.add_log(f"   • double (Big Endian): {double_be}")
                    except:
                        self.add_log("   • double: erro na conversão")
                
                # 3. Comparar com nossos métodos
                self.add_log("🔧 Comparação com métodos internos:")
                
                methods_to_test = ['int32', 'uint32', 'float', 'int16', 'uint16']
                for method in methods_to_test:
                    try:
                        value = self.read_value_by_type(address, method)
                        self.add_log(f"   • {method}: {value}")
                    except Exception as e:
                        self.add_log(f"   • {method}: ERRO - {str(e)}")
                
                # 4. Informações do processo
                self.add_log("💻 Informações do processo:")
                try:
                    proc = psutil.Process(self.memory_reader.pid)
                    self.add_log(f"   • Nome: {proc.name()}")
                    self.add_log(f"   • PID: {proc.pid}")
                    self.add_log(f"   • Arquitetura: {proc.exe()}")
                    
                    # Verificar se é processo 64-bit
                    import platform
                    is_64bit = platform.machine().endswith('64')
                    self.add_log(f"   • Sistema 64-bit: {is_64bit}")
                    
                except Exception as e:
                    self.add_log(f"   • Erro ao obter info: {str(e)}")
                
                self.add_log("🎯 DICA: Compare estes valores com o Cheat Engine!")
                self.add_log("📋 Cheat Engine normalmente usa Little Endian (padrão Windows)")
                self.add_log("=== FIM DO DEBUG ===")
                
            else:
                self.add_log("❌ Não foi possível ler os bytes do endereço")
                
        except ValueError as e:
            self.add_log(f"❌ Endereço inválido: {str(e)}")
            self.add_log("💡 Formatos válidos: base+0x1234, 0x12345678, 1234")
        except Exception as e:
            self.add_log(f"❌ Erro no debug: {str(e)}")
    
    def read_memory_once(self):
        """Lê um valor da memória uma única vez - versão melhorada"""
        if not self.memory_reader.process_handle:
            self.add_log("❌ Conecte-se a um processo primeiro!")
            return
            
        try:
            address_str = self.address_input.text().strip()
            if not address_str:
                self.add_log("❌ Digite um endereço válido!")
                return
                
            # Usar novo parser de endereço
            address = self.parse_address(address_str)
                
            data_type = self.data_type_combo.currentText()
            description = self.description_input.text().strip() or "Leitura única"
            
            # Mostrar endereço calculado se for offset
            if address_str.lower().startswith('base+') and self.process_base_address:
                self.add_log(f"🧮 {address_str} = 0x{address:08X}")
            elif '+' in address_str and not address_str.lower().startswith('base+'):
                self.add_log(f"🧮 {address_str} = 0x{address:08X}")
            
            # Ler valor baseado no tipo
            value = self.read_value_by_type(address, data_type)
            
            if value is not None:
                self.add_log(f"🔍 [0x{address:08X}] {data_type}: {value}")
                
                # Atualizar na tabela (usar endereço original para identificação)
                self.update_or_add_table_row(address_str, data_type, str(value), description)
            else:
                self.add_log(f"❌ Falha ao ler endereço {address_str}")
                
        except ValueError as e:
            self.add_log(f"❌ Endereço inválido: {str(e)}")
            self.add_log("💡 Formatos válidos: base+0x1234, 0x12345678, 1234")
        except Exception as e:
            self.add_log(f"❌ Erro na leitura: {str(e)}")
    
    def read_value_by_type(self, address, data_type):
        """Lê valor baseado no tipo especificado"""
        if data_type == 'int32':
            return self.memory_reader.read_int32(address)
        elif data_type == 'uint32':
            return self.memory_reader.read_uint32(address)
        elif data_type == 'float':
            return self.memory_reader.read_float(address)
        elif data_type == 'double':
            return self.memory_reader.read_double(address)
        elif data_type == 'int16':
            return self.memory_reader.read_int16(address)
        elif data_type == 'uint16':
            return self.memory_reader.read_uint16(address)
        elif data_type == 'int8':
            return self.memory_reader.read_int8(address)
        elif data_type == 'uint8':
            return self.memory_reader.read_uint8(address)
        elif data_type == 'string':
            try:
                length = int(self.string_length_input.text() or "50")
                return self.memory_reader.read_string(address, length)
            except ValueError:
                return self.memory_reader.read_string(address, 50)
        elif data_type == 'raw_bytes':
            # Novo tipo: lê bytes brutos
            try:
                size = int(self.string_length_input.text() or "4")
                return self.memory_reader.read_bytes(address, size)
            except ValueError:
                return self.memory_reader.read_bytes(address, 4)
        return None
    
    def add_to_monitoring_list(self):
        """Adiciona endereço à lista de monitoramento - versão melhorada"""
        address_str = self.address_input.text().strip()
        if not address_str:
            self.add_log("❌ Digite um endereço válido!")
            return
            
        data_type = self.data_type_combo.currentText()
        description = self.description_input.text().strip() or "Sem descrição"
        
        try:
            # Usar novo parser de endereço
            address = self.parse_address(address_str)
                
            # Adicionar ao dicionário (manter string original para identificação)
            key = f"{address_str}_{data_type}"
            self.monitored_addresses[key] = {
                'address': address,
                'address_str': address_str,  # String original (ex: "base+0x1234")
                'address_calculated': f"0x{address:08X}",  # Endereço calculado
                'data_type': data_type,
                'description': description,
                'last_value': None
            }
            
            # Adicionar à tabela
            self.update_or_add_table_row(address_str, data_type, "Aguardando...", description)
            
            # Log com endereço calculado
            if address_str.lower().startswith('base+'):
                self.add_log(f"➕ {address_str} (0x{address:08X}) - {description}")
            elif '+' in address_str and not address_str.lower().startswith('base+'):
                self.add_log(f"➕ {address_str} (0x{address:08X}) - {description}")
            else:
                self.add_log(f"➕ Endereço adicionado: {address_str} - {description}")
            
            # Limpar campo de descrição para próxima entrada
            self.description_input.clear()
            
            # Auto-salvar após adicionar
            self.save_addresses()
            
        except ValueError as e:
            self.add_log(f"❌ Endereço inválido: {str(e)}")
            self.add_log("💡 Exemplos: DarkEden.exe+0x1234, base+4660, 0x401000")
    
    def save_addresses(self):
        """Salva a lista de endereços em arquivo JSON"""
        try:
            # Preparar dados para salvar
            save_data = {
                'addresses': [],
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'version': '1.0'
            }
            
            for key, addr_info in self.monitored_addresses.items():
                save_data['addresses'].append({
                    'address_str': addr_info['address_str'],
                    'data_type': addr_info['data_type'],
                    'description': addr_info['description']
                })
            
            # Salvar em arquivo
            with open(self.addresses_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            self.add_log(f"💾 Lista salva: {len(save_data['addresses'])} endereços em '{self.addresses_file}'")
            
        except Exception as e:
            self.add_log(f"❌ Erro ao salvar: {str(e)}")
    
    def load_addresses(self):
        """Carrega a lista de endereços do arquivo JSON (automático)"""
        try:
            if not os.path.exists(self.addresses_file):
                self.add_log("📂 Nenhuma lista salva encontrada")
                return
            
            with open(self.addresses_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Limpar lista atual
            self.monitored_addresses.clear()
            self.values_table.setRowCount(0)
            
            # Carregar endereços
            addresses = save_data.get('addresses', [])
            loaded_count = 0
            
            for addr_data in addresses:
                try:
                    address_str = addr_data['address_str']
                    data_type = addr_data['data_type']
                    description = addr_data.get('description', 'Sem descrição')
                    
                    # Adicionar ao dicionário (sem calcular endereço ainda)
                    key = f"{address_str}_{data_type}"
                    self.monitored_addresses[key] = {
                        'address': 0,  # Será calculado quando conectar ao processo
                        'address_str': address_str,
                        'address_calculated': 'Aguardando conexão',
                        'data_type': data_type,
                        'description': description,
                        'last_value': None
                    }
                    
                    # Adicionar à tabela
                    self.update_or_add_table_row(address_str, data_type, "Não conectado", description)
                    loaded_count += 1
                    
                except Exception as e:
                    self.add_log(f"⚠️ Erro ao carregar endereço: {str(e)}")
            
            if loaded_count > 0:
                timestamp = save_data.get('timestamp', 'Desconhecido')
                self.add_log(f"📂 Lista carregada: {loaded_count} endereços (salva em {timestamp})")
                self.add_log("💡 Conecte-se ao processo para calcular endereços")
            
        except Exception as e:
            self.add_log(f"❌ Erro ao carregar lista: {str(e)}")
    
    def load_addresses_dialog(self):
        """Carrega lista de endereços com confirmação"""
        if self.monitored_addresses:
            reply = QMessageBox.question(
                self, 
                'Carregar Lista', 
                'Isso substituirá a lista atual. Deseja continuar?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        self.load_addresses()
    
    def clear_all_addresses(self):
        """Limpa todos os endereços da lista"""
        if not self.monitored_addresses:
            self.add_log("❌ Lista já está vazia!")
            return
        
        reply = QMessageBox.question(
            self, 
            'Limpar Lista', 
            f'Remover todos os {len(self.monitored_addresses)} endereços da lista?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            count = len(self.monitored_addresses)
            self.monitored_addresses.clear()
            self.values_table.setRowCount(0)
            self.add_log(f"🧹 Lista limpa: {count} endereços removidos")
    
    def recalculate_addresses(self):
        """Recalcula todos os endereços após conectar ao processo"""
        if not self.process_base_address:
            return
        
        recalculated = 0
        for key, addr_info in self.monitored_addresses.items():
            try:
                address_str = addr_info['address_str']
                # Recalcular endereço usando o parser
                new_address = self.parse_address(address_str)
                addr_info['address'] = new_address
                addr_info['address_calculated'] = f"0x{new_address:08X}"
                
                # Atualizar tabela com status "Aguardando..."
                self.update_or_add_table_row(
                    address_str, 
                    addr_info['data_type'], 
                    "Aguardando...", 
                    addr_info['description']
                )
                recalculated += 1
                
            except Exception as e:
                self.add_log(f"⚠️ Erro ao recalcular {address_str}: {str(e)}")
        
        if recalculated > 0:
            self.add_log(f"🔄 {recalculated} endereços recalculados com nova base")
    
    def update_or_add_table_row(self, address_str, data_type, value, description=""):
        """Atualiza ou adiciona linha na tabela"""
        # Procurar se já existe
        for row in range(self.values_table.rowCount()):
            if (self.values_table.item(row, 0) and 
                self.values_table.item(row, 0).text() == address_str and
                self.values_table.item(row, 1).text() == data_type):
                # Atualizar valor existente
                self.values_table.setItem(row, 2, QTableWidgetItem(str(value)))
                # Manter descrição existente se não foi fornecida uma nova
                if description and self.values_table.item(row, 3):
                    self.values_table.setItem(row, 3, QTableWidgetItem(description))
                return
        
        # Adicionar nova linha
        row_count = self.values_table.rowCount()
        self.values_table.setRowCount(row_count + 1)
        
        self.values_table.setItem(row_count, 0, QTableWidgetItem(address_str))
        self.values_table.setItem(row_count, 1, QTableWidgetItem(data_type))
        self.values_table.setItem(row_count, 2, QTableWidgetItem(str(value)))
        self.values_table.setItem(row_count, 3, QTableWidgetItem(description or "Sem descrição"))
    
    def remove_from_monitoring_list(self):
        """Remove endereço selecionado da lista"""
        current_row = self.values_table.currentRow()
        if current_row >= 0:
            address_str = self.values_table.item(current_row, 0).text()
            data_type = self.values_table.item(current_row, 1).text()
            key = f"{address_str}_{data_type}"
            
            # Remover do dicionário
            if key in self.monitored_addresses:
                del self.monitored_addresses[key]
            
            # Remover da tabela
            self.values_table.removeRow(current_row)
            
            self.add_log(f"🗑️ Endereço removido: {address_str}")
            
            # Auto-salvar após remover
            self.save_addresses()
        else:
            self.add_log("❌ Selecione um endereço para remover!")
    
    def toggle_monitoring(self):
        """Inicia/para o monitoramento"""
        if not self.monitoring_active:
            if not self.monitored_addresses:
                self.add_log("❌ Adicione endereços à lista primeiro!")
                return
                
            try:
                interval = float(self.interval_input.text() or "1.0")
                self.start_monitoring(interval)
            except ValueError:
                self.add_log("❌ Intervalo inválido!")
        else:
            self.stop_monitoring()
    
    def start_monitoring(self, interval):
        """Inicia o monitoramento em thread separada"""
        self.monitoring_active = True
        self.start_monitor_btn.setText('⏹️ Parar Monitoramento')
        self.start_monitor_btn.setStyleSheet('QPushButton { background-color: #aa4444; }')
        
        self.monitoring_thread = threading.Thread(
            target=self.monitoring_loop, 
            args=(interval,), 
            daemon=True
        )
        self.monitoring_thread.start()
        
        self.add_log(f"🔍 Monitoramento iniciado (intervalo: {interval}s)")
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.monitoring_active = False
        self.start_monitor_btn.setText('🔍 Iniciar Monitoramento')
        self.start_monitor_btn.setStyleSheet('QPushButton { background-color: #4444aa; }')
        
        self.add_log("⏹️ Monitoramento parado")
    
    def monitoring_loop(self, interval):
        """Loop de monitoramento executado em thread separada"""
        while self.monitoring_active:
            try:
                for key, addr_info in self.monitored_addresses.items():
                    if not self.monitoring_active:
                        break
                        
                    address = addr_info['address']
                    address_str = addr_info['address_str']
                    data_type = addr_info['data_type']
                    
                    # Ler valor atual
                    current_value = self.read_value_by_type(address, data_type)
                    
                    if current_value is not None:
                        # Verificar se valor mudou
                        if current_value != addr_info['last_value']:
                            addr_info['last_value'] = current_value
                            
                            # Emitir sinal para atualizar UI
                            self.value_signal.emit(address_str, str(current_value), data_type)
                
                time.sleep(interval)
                
            except Exception as e:
                self.log_signal.emit(f"❌ Erro no monitoramento: {str(e)}")
                break
    
    def update_memory_value(self, address_str, value, data_type):
        """Atualiza valor na tabela (chamado pelo signal)"""
        # Buscar descrição existente no dicionário
        key = f"{address_str}_{data_type}"
        description = ""
        if key in self.monitored_addresses:
            description = self.monitored_addresses[key].get('description', '')
        
        self.update_or_add_table_row(address_str, data_type, value, description)
        
        # Log apenas se for mudança significativa
        if isinstance(value, str) and value != "Aguardando...":
            timestamp = time.strftime('%H:%M:%S')
            desc_text = f" ({description})" if description else ""
            self.add_log(f"[{timestamp}] {address_str}{desc_text}: {value}")
    
    def add_log(self, message):
        """Adiciona mensagem ao log"""
        timestamp = time.strftime('%H:%M:%S')
        self.log_text.append(f'[{timestamp}] {message}')
        self.log_text.ensureCursorVisible()
    
    def update_status(self, text, color):
        """Atualiza status geral"""
        # Implementar se necessário
        pass
    
    def update_process_status(self, status):
        """Atualiza status do processo"""
        self.connection_status.setText(status)
    
    def closeEvent(self, event):
        """Cleanup ao fechar aplicação"""
        self.stop_monitoring()
        
        # Salvar endereços antes de fechar
        if self.monitored_addresses:
            self.save_addresses()
            self.add_log("💾 Lista de endereços salva automaticamente")
        
        if self.memory_reader:
            self.memory_reader.close()
        event.accept()
    
    def calculate_offset_from_absolute(self, absolute_address_str):
        """
        Calcula o offset de um endereço absoluto baseado nos módulos carregados
        Usa pymem para listar todos os módulos e encontrar onde o endereço está
        
        Args:
            absolute_address_str: String do endereço absoluto (ex: "191A5061" ou "0x191A5061")
        
        Returns:
            (success, new_address_format, module_name, offset, base_address)
            Exemplo: (True, "darkeden.exe+A5061", "darkeden.exe", 0xA5061, 0x19100000)
        """
        try:
            # Converter endereço string para inteiro
            if absolute_address_str.startswith('0x'):
                target_address = int(absolute_address_str, 16)
            else:
                target_address = int(absolute_address_str, 16)
            
            self.add_log(f"")
            self.add_log(f"🔍 === CALCULANDO OFFSET PARA ENDEREÇO ABSOLUTO ===")
            self.add_log(f"📍 Endereço alvo: 0x{target_address:08X}")
            
            # Verificar se está conectado a um processo
            if not self.memory_reader or not self.memory_reader.process_id:
                self.add_log("❌ Conecte-se a um processo primeiro!")
                return False, None, None, None, None
            
            pid = self.memory_reader.process_id
            self.add_log(f"🎯 Processo conectado: PID {pid}")
            
            # Abrir processo com pymem
            pm = pymem.Pymem()
            pm.open_process_from_id(pid)
            
            # Listar todos os módulos do processo
            modules = list(pm.list_modules())
            self.add_log(f"📚 Verificando {len(modules)} módulos carregados no processo...")
            self.add_log("")
            
            # Procurar em qual módulo o endereço está
            for module in modules:
                base = module.lpBaseOfDll
                size = module.SizeOfImage
                module_name = module.name
                end_address = base + size
                
                # Verificar se o endereço está dentro deste módulo
                if base <= target_address < end_address:
                    offset = target_address - base
                    
                    self.add_log(f"✅ ═══════════════════════════════════════")
                    self.add_log(f"✅ ENDEREÇO ENCONTRADO!")
                    self.add_log(f"✅ ═══════════════════════════════════════")
                    self.add_log(f"")
                    self.add_log(f"📦 Módulo: {module_name}")
                    self.add_log(f"📍 Base do módulo: 0x{base:08X}")
                    self.add_log(f"📏 Tamanho do módulo: 0x{size:08X} ({size / 1024 / 1024:.2f} MB)")
                    self.add_log(f"🎯 Endereço final: 0x{end_address:08X}")
                    self.add_log(f"")
                    self.add_log(f"📐 Offset calculado: +0x{offset:X}")
                    self.add_log(f"")
                    self.add_log(f"🔢 FÓRMULA:")
                    self.add_log(f"   {module_name} + 0x{offset:X} = 0x{target_address:08X}")
                    self.add_log(f"")
                    self.add_log(f"💡 Use no Memory Viewer:")
                    self.add_log(f"   {module_name}+{offset:X}")
                    self.add_log(f"")
                    
                    # Formato final
                    new_format = f"{module_name}+{offset:X}"
                    return True, new_format, module_name, offset, base
            
            # Se não encontrou em nenhum módulo
            self.add_log(f"")
            self.add_log(f"⚠️ ═══════════════════════════════════════")
            self.add_log(f"⚠️ ENDEREÇO NÃO ENCONTRADO EM NENHUM MÓDULO!")
            self.add_log(f"⚠️ ═══════════════════════════════════════")
            self.add_log(f"")
            self.add_log(f"📋 Possíveis causas:")
            self.add_log(f"   1️⃣ Memória alocada dinamicamente (heap)")
            self.add_log(f"   2️⃣ Stack do processo")
            self.add_log(f"   3️⃣ Ponteiro multi-level")
            self.add_log(f"   4️⃣ Endereço inválido")
            self.add_log(f"")
            
            # Mostrar módulos mais próximos para debug
            self.show_nearby_modules(modules, target_address)
            
            return False, None, None, None, None
            
        except Exception as e:
            self.add_log(f"❌ Erro ao calcular offset: {str(e)}")
            import traceback
            self.add_log(f"🔍 Stack trace:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    self.add_log(f"   {line}")
            return False, None, None, None, None
    
    def show_nearby_modules(self, modules, target_address):
        """Mostra os 5 módulos mais próximos ao endereço alvo para debug"""
        self.add_log(f"🔍 Módulos mais próximos ao endereço 0x{target_address:08X}:")
        self.add_log(f"")
        
        nearby = []
        for module in modules:
            base = module.lpBaseOfDll
            size = module.SizeOfImage
            end = base + size
            
            # Calcular distância
            if target_address < base:
                distance = base - target_address
                position = "antes do módulo"
            elif target_address >= end:
                distance = target_address - end
                position = "depois do módulo"
            else:
                distance = 0
                position = "DENTRO do módulo (não deveria chegar aqui!)"
            
            nearby.append({
                'name': module.name,
                'base': base,
                'end': end,
                'size': size,
                'distance': distance,
                'position': position
            })
        
        # Ordenar por distância (mais próximo primeiro)
        nearby.sort(key=lambda x: x['distance'])
        
        # Mostrar os 5 mais próximos
        for i, item in enumerate(nearby[:5], 1):
            size_mb = item['size'] / 1024 / 1024
            self.add_log(f"   {i}. {item['name']}")
            self.add_log(f"      Range: 0x{item['base']:08X} - 0x{item['end']:08X} ({size_mb:.2f} MB)")
            self.add_log(f"      Status: {item['position']}")
            if item['distance'] > 0:
                distance_kb = item['distance'] / 1024
                self.add_log(f"      Distância: 0x{item['distance']:X} bytes ({distance_kb:.2f} KB)")
            self.add_log("")
    
    def convert_all_absolute_addresses_auto(self):
        """
        Converte TODOS os endereços absolutos salvos automaticamente
        Esta função é chamada pelo botão "🔄 Converter Todos Absolutos"
        """
        if not self.memory_reader or not self.memory_reader.process_id:
            self.add_log("⚠️ Conecte ao processo primeiro!")
            return
        
        self.add_log("")
        self.add_log("=" * 60)
        self.add_log("🔄 === CONVERSÃO AUTOMÁTICA DE ENDEREÇOS ABSOLUTOS ===")
        self.add_log("=" * 60)
        self.add_log("")
        
        converted_count = 0
        failed_count = 0
        failed_addresses = []
        
        for key, addr_info in list(self.monitored_addresses.items()):
            address_str = addr_info['address_str']
            
            # Verificar se é endereço absoluto (sem '+' e só números/hex)
            is_absolute = ('+' not in address_str and 
                          not address_str.lower().startswith('base') and
                          all(c in '0123456789ABCDEFabcdefx' for c in address_str))
            
            if is_absolute:
                self.add_log(f"🎯 Processando: {addr_info['description']}")
                self.add_log(f"   Endereço original: {address_str}")
                
                success, new_format, module_name, offset, base = self.calculate_offset_from_absolute(address_str)
                
                if success:
                    # Atualizar no dicionário
                    old_key = key
                    addr_info['address_str'] = new_format
                    
                    # Recalcular endereço usando parse_address
                    try:
                        new_address = self.parse_address(new_format)
                        addr_info['address'] = new_address
                        addr_info['address_calculated'] = f"0x{new_address:08X}"
                    except:
                        pass
                    
                    # Criar nova chave
                    new_key = f"{new_format}_{addr_info['data_type']}"
                    
                    # Atualizar dicionário
                    if new_key != old_key:
                        self.monitored_addresses[new_key] = self.monitored_addresses.pop(old_key)
                    
                    # Atualizar na tabela
                    for row in range(self.values_table.rowCount()):
                        if (self.values_table.item(row, 0) and 
                            self.values_table.item(row, 0).text() == address_str):
                            self.values_table.setItem(row, 0, QTableWidgetItem(new_format))
                            self.add_log(f"   ✅ Tabela atualizada: {new_format}")
                            break
                    
                    converted_count += 1
                    self.add_log(f"   ✅ CONVERSÃO CONCLUÍDA COM SUCESSO!")
                else:
                    failed_count += 1
                    failed_addresses.append({
                        'description': addr_info['description'],
                        'address': address_str
                    })
                    self.add_log(f"   ❌ Não foi possível converter")
                
                self.add_log("")
        
        # Resumo final
        self.add_log("=" * 60)
        self.add_log(f"📊 === RESUMO DA CONVERSÃO ===")
        self.add_log("=" * 60)
        self.add_log(f"✅ Convertidos com sucesso: {converted_count}")
        self.add_log(f"❌ Não convertidos: {failed_count}")
        self.add_log(f"📋 Total de endereços verificados: {converted_count + failed_count}")
        self.add_log("=" * 60)
        
        if failed_addresses:
            self.add_log(f"")
            self.add_log(f"⚠️ Endereços que permaneceram absolutos:")
            for item in failed_addresses:
                self.add_log(f"   • {item['description']}: {item['address']}")
            
            self.add_log(f"")
            self.add_log(f"💡 DICA PARA ENDEREÇOS DINÂMICOS:")
            self.add_log(f"   1. Abra o Cheat Engine")
            self.add_log(f"   2. Encontre o endereço que muda")
            self.add_log(f"   3. Clique com botão direito → Pointer scan")
            self.add_log(f"   4. Encontre o caminho estático do ponteiro")
            self.add_log(f"   5. Exemplo: [[darkeden.exe+2FB000]+10]+8")
            self.add_log(f"")
        
        # Salvar alterações no JSON
        if converted_count > 0:
            self.save_addresses()
            self.add_log(f"")
            self.add_log(f"💾 Alterações salvas automaticamente em '{self.addresses_file}'")
        
        self.add_log("")
        self.add_log("=== FIM DA CONVERSÃO ===")
        self.add_log("")
    
    def try_find_pointer_to_address(self, target_address):
        """
        Tenta encontrar ponteiros que apontam para um endereço dinâmico
        Faz uma busca básica na região .data dos módulos
        """
        try:
            self.add_log("")
            self.add_log("🔍 === BUSCANDO PONTEIROS PARA O ENDEREÇO ===")
            self.add_log(f"🎯 Alvo: 0x{target_address:08X}")
            self.add_log("")
            
            pm = pymem.Pymem()
            pm.open_process_from_id(self.memory_reader.process_id)
            modules = list(pm.list_modules())
            
            found_pointers = []
            
            # Procurar nos primeiros 5 módulos principais
            for module in modules[:5]:
                base = module.lpBaseOfDll
                size = min(module.SizeOfImage, 0x100000)  # Limitar a 1MB para não travar
                module_name = module.name
                
                self.add_log(f"🔍 Escaneando: {module_name}")
                
                try:
                    # Ler região de memória do módulo
                    data = pm.read_bytes(base, size)
                    
                    # Procurar por valores que sejam próximos ao endereço alvo
                    import struct
                    tolerance = 0x1000  # Tolerância de 4KB
                    
                    for i in range(0, len(data) - 4, 4):
                        try:
                            pointer_value = struct.unpack('<I', data[i:i+4])[0]
                            
                            # Verificar se aponta para próximo do endereço alvo
                            if abs(pointer_value - target_address) < tolerance:
                                pointer_address = base + i
                                offset_from_base = i
                                offset_to_target = target_address - pointer_value
                                
                                found_pointers.append({
                                    'module': module_name,
                                    'address': pointer_address,
                                    'offset_from_base': offset_from_base,
                                    'points_to': pointer_value,
                                    'offset_to_target': offset_to_target
                                })
                        except:
                            continue
                    
                except Exception as e:
                    self.add_log(f"   ⚠️ Erro ao escanear {module_name}: {e}")
                    continue
            
            if found_pointers:
                self.add_log("")
                self.add_log(f"✅ Encontrados {len(found_pointers)} ponteiros potenciais!")
                self.add_log("")
                
                for i, ptr in enumerate(found_pointers[:10], 1):  # Mostrar até 10
                    self.add_log(f"{i}. 📍 {ptr['module']}+{ptr['offset_from_base']:X}")
                    self.add_log(f"   Endereço: 0x{ptr['address']:08X}")
                    self.add_log(f"   Aponta para: 0x{ptr['points_to']:08X}")
                    if ptr['offset_to_target'] != 0:
                        self.add_log(f"   Offset adicional: +0x{ptr['offset_to_target']:X}")
                    self.add_log(f"   💡 Teste no Cheat Engine: [{ptr['module']}+{ptr['offset_from_base']:X}]")
                    if ptr['offset_to_target'] != 0:
                        self.add_log(f"      Com offset: [[{ptr['module']}+{ptr['offset_from_base']:X}]+{ptr['offset_to_target']:X}]")
                    self.add_log("")
                
                if len(found_pointers) > 10:
                    self.add_log(f"... e mais {len(found_pointers) - 10} ponteiros")
                
                self.add_log("💡 Use o Cheat Engine para validar estes ponteiros!")
                self.add_log("   1. Adicione endereço manualmente")
                self.add_log("   2. Use o formato mostrado acima")
                self.add_log("   3. Reinicie o jogo para testar se o ponteiro é estático")
            else:
                self.add_log("")
                self.add_log("❌ Nenhum ponteiro direto encontrado")
                self.add_log("💡 Isso significa que é um ponteiro multi-level (2+ níveis)")
                self.add_log("   Use o Pointer Scan do Cheat Engine para encontrar")
            
            self.add_log("")
            return found_pointers
            
        except Exception as e:
            self.add_log(f"❌ Erro na busca de ponteiros: {e}")
            import traceback
            self.add_log(traceback.format_exc())
            return []

def main():
    app = QApplication(sys.argv)
    
    # Aplicar tema escuro
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.WindowText, Qt.white)
    app.setPalette(palette)
    
    # Verificar se arquivo read-memory.py existe
    if not os.path.exists('read-memory.py'):
        QMessageBox.critical(None, "Erro", "Arquivo 'read-memory.py' não encontrado!\nCertifique-se de que está na mesma pasta.")
        sys.exit(1)
    
    window = MemoryViewerGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
