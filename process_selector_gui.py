import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import psutil
import win32gui
import win32con
import win32api

class ProcessSelectorGUI(QMainWindow):
    # Sinal para comunicar processo selecionado
    process_selected = pyqtSignal(int, str, int)  # pid, name, hwnd
    
    def __init__(self):
        super().__init__()
        self.selected_hwnd = None
        self.initUI()
        self.refresh_processes()
        
    def initUI(self):
        self.setWindowTitle('🎮 Dark Eden - Seletor de Processo')
        self.setGeometry(100, 100, 700, 500)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        
        # Estilo escuro
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QWidget { background-color: #2b2b2b; color: white; }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
                min-height: 25px;
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
                padding: 8px;
                font-weight: bold;
            }
            QLabel { color: white; font-weight: bold; }
        """)
        
        # Título
        title = QLabel('🎮 SELETOR DE PROCESSO - DARK EDEN')
        title.setStyleSheet('color: #00ff00; font-size: 16px; font-weight: bold;')
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Filtro
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel('Filtrar processos:'))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText('Digite para filtrar por nome...')
        self.filter_input.textChanged.connect(self.filter_processes)
        filter_layout.addWidget(self.filter_input)
        
        filter_btn = QPushButton('🎮 Só Jogos')
        filter_btn.clicked.connect(self.filter_games_only)
        filter_btn.setStyleSheet('QPushButton { background-color: #4444aa; }')
        filter_layout.addWidget(filter_btn)
        
        refresh_btn = QPushButton('🔄 Atualizar')
        refresh_btn.clicked.connect(self.refresh_processes)
        refresh_btn.setStyleSheet('QPushButton { background-color: #44aa44; }')
        filter_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(filter_layout)
        
        # Tabela de processos
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(3)
        self.process_table.setHorizontalHeaderLabels(['PID', 'Nome do Processo', 'Janelas'])
        self.process_table.horizontalHeader().setStretchLastSection(True)
        self.process_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.process_table.itemDoubleClicked.connect(self.on_process_double_click)
        main_layout.addWidget(self.process_table)
        
        # Detalhes do processo selecionado
        details_group = QGroupBox('Detalhes do Processo Selecionado')
        details_group.setStyleSheet('QGroupBox { color: #ffff00; font-weight: bold; }')
        details_layout = QVBoxLayout()
        
        self.details_label = QLabel('Selecione um processo da lista acima')
        self.details_label.setStyleSheet('color: #cccccc;')
        details_layout.addWidget(self.details_label)
        
        # Tabela de janelas
        self.windows_table = QTableWidget()
        self.windows_table.setColumnCount(4)
        self.windows_table.setHorizontalHeaderLabels(['HWND', 'Título', 'Classe', 'Status'])
        self.windows_table.horizontalHeader().setStretchLastSection(True)
        self.windows_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.windows_table.setMaximumHeight(150)
        details_layout.addWidget(self.windows_table)
        
        details_group.setLayout(details_layout)
        main_layout.addWidget(details_group)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        self.select_btn = QPushButton('✅ Conectar ao Processo')
        self.select_btn.clicked.connect(self.connect_to_selected)
        self.select_btn.setStyleSheet('QPushButton { background-color: #44aa44; font-size: 14px; }')
        self.select_btn.setEnabled(False)
        button_layout.addWidget(self.select_btn)
        
        cancel_btn = QPushButton('❌ Cancelar')
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setStyleSheet('QPushButton { background-color: #aa4444; font-size: 14px; }')
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel('Carregando processos...')
        self.status_label.setStyleSheet('color: #888888; font-style: italic;')
        main_layout.addWidget(self.status_label)
        
        central_widget.setLayout(main_layout)
        
        # Conectar seleção da tabela
        self.process_table.itemSelectionChanged.connect(self.on_process_selected)
        
    def refresh_processes(self):
        """Atualiza a lista de processos"""
        self.process_table.setRowCount(0)
        self.status_label.setText('Carregando processos...')
        
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    
                    # Contar janelas do processo
                    window_count = self.count_process_windows(pid)
                    
                    processes.append((pid, name, window_count))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Ordenar por nome
            processes.sort(key=lambda x: x[1].lower())
            
            # Adicionar à tabela
            self.process_table.setRowCount(len(processes))
            for row, (pid, name, window_count) in enumerate(processes):
                self.process_table.setItem(row, 0, QTableWidgetItem(str(pid)))
                self.process_table.setItem(row, 1, QTableWidgetItem(name))
                
                window_text = f"{window_count} janela(s)" if window_count > 0 else "Sem janelas"
                self.process_table.setItem(row, 2, QTableWidgetItem(window_text))
                
                # Destacar processos com janelas
                if window_count > 0:
                    for col in range(3):
                        item = self.process_table.item(row, col)
                        item.setBackground(QColor(40, 60, 40))
            
            self.status_label.setText(f'✅ {len(processes)} processos carregados')
            
        except Exception as e:
            self.status_label.setText(f'❌ Erro: {str(e)}')
    
    def count_process_windows(self, pid):
        """Conta quantas janelas um processo possui"""
        window_count = 0
        
        def enum_windows_proc(hwnd, lParam):
            nonlocal window_count
            try:
                window_pid = win32gui.GetWindowThreadProcessId(hwnd)[1]
                if window_pid == pid:
                    window_text = win32gui.GetWindowText(hwnd)
                    if window_text:  # Só contar janelas com título
                        window_count += 1
            except:
                pass
            return True
        
        try:
            win32gui.EnumWindows(enum_windows_proc, 0)
        except:
            pass
        
        return window_count
    
    def filter_processes(self):
        """Filtra processos baseado no texto digitado"""
        filter_text = self.filter_input.text().lower()
        
        for row in range(self.process_table.rowCount()):
            process_name = self.process_table.item(row, 1).text().lower()
            should_show = filter_text in process_name
            self.process_table.setRowHidden(row, not should_show)
    
    def filter_games_only(self):
        """Filtra apenas processos relacionados a jogos"""
        game_keywords = ['game', 'dark', 'eden', '.exe', 'client', 'launcher']
        
        for row in range(self.process_table.rowCount()):
            process_name = self.process_table.item(row, 1).text().lower()
            window_count = int(self.process_table.item(row, 2).text().split()[0])
            
            # Mostrar se tem keywords de jogo OU se tem janelas
            should_show = any(keyword in process_name for keyword in game_keywords) or window_count > 0
            self.process_table.setRowHidden(row, not should_show)
    
    def on_process_selected(self):
        """Quando um processo é selecionado na tabela"""
        selected_rows = self.process_table.selectionModel().selectedRows()
        
        if not selected_rows:
            self.details_label.setText('Selecione um processo da lista acima')
            self.windows_table.setRowCount(0)
            self.select_btn.setEnabled(False)
            return
        
        row = selected_rows[0].row()
        pid = int(self.process_table.item(row, 0).text())
        name = self.process_table.item(row, 1).text()
        
        self.details_label.setText(f'🔍 Processo: {name} (PID: {pid})')
        self.load_process_windows(pid, name)
    
    def load_process_windows(self, pid, name):
        """Carrega as janelas de um processo específico"""
        self.windows_table.setRowCount(0)
        
        found_windows = []
        
        def enum_windows_proc(hwnd, lParam):
            try:
                window_pid = win32gui.GetWindowThreadProcessId(hwnd)[1]
                if window_pid == pid:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    is_visible = win32gui.IsWindowVisible(hwnd)
                    
                    found_windows.append({
                        'hwnd': hwnd,
                        'title': window_text,
                        'class': class_name,
                        'visible': is_visible
                    })
            except:
                pass
            return True
        
        win32gui.EnumWindows(enum_windows_proc, 0)
        
        if not found_windows:
            self.details_label.setText(f'⚠️ Processo {name} não possui janelas')
            # Mesmo sem janelas, permitir conexão para processos específicos
            if any(keyword in name.lower() for keyword in ['darkeden', 'dark', 'eden', 'game']):
                self.details_label.setText(f'⚠️ Processo {name} não possui janelas, mas pode ser conectado')
                self.select_btn.setEnabled(True)
            else:
                self.select_btn.setEnabled(False)
            return
        
        # Adicionar janelas à tabela
        self.windows_table.setRowCount(len(found_windows))
        valid_windows = 0
        
        for row, window in enumerate(found_windows):
            self.windows_table.setItem(row, 0, QTableWidgetItem(str(window['hwnd'])))
            
            title = window['title'] or "(Sem título)"
            self.windows_table.setItem(row, 1, QTableWidgetItem(title))
            self.windows_table.setItem(row, 2, QTableWidgetItem(window['class']))
            
            status = "✅ Visível" if window['visible'] else "❌ Oculta"
            self.windows_table.setItem(row, 3, QTableWidgetItem(status))
            
            # Destacar janelas visíveis com título
            if window['visible'] and window['title']:
                valid_windows += 1
                for col in range(4):
                    item = self.windows_table.item(row, col)
                    item.setBackground(QColor(40, 60, 40))
        
        # Sempre permitir conexão se há janelas ou se é processo de jogo
        self.select_btn.setEnabled(True)
        
        if valid_windows > 0:
            self.details_label.setText(f'✅ {len(found_windows)} janela(s) encontrada(s) ({valid_windows} utilizável(is))')
        else:
            self.details_label.setText(f'⚠️ {len(found_windows)} janela(s) encontrada(s), mas pode tentar conectar mesmo assim')
    
    def on_process_double_click(self, item):
        """Conecta diretamente quando processo é clicado duas vezes"""
        self.connect_to_selected()
    
    def connect_to_selected(self):
        """Conecta ao processo selecionado"""
        selected_rows = self.process_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        pid = int(self.process_table.item(row, 0).text())
        name = self.process_table.item(row, 1).text()
        
        # Encontrar a janela (pode ser None para processos sem janelas)
        hwnd = self.find_best_window(pid)
        
        if hwnd:
            self.process_selected.emit(pid, name, hwnd)
            QMessageBox.information(self, "Sucesso", f"Conectado ao processo:\n{name} (PID: {pid})\nJanela encontrada!")
            self.close()
        else:
            # Para processos específicos, permitir conexão mesmo sem janela
            if any(keyword in name.lower() for keyword in ['darkeden', 'dark', 'eden', 'game']):
                # Usar HWND 0 para indicar que não há janela específica
                self.process_selected.emit(pid, name, 0)
                QMessageBox.information(self, "Conectado", f"Conectado ao processo:\n{name} (PID: {pid})\n\n⚠️ Processo sem janela principal.\nO script tentará encontrar janelas automaticamente.")
                self.close()
            else:
                QMessageBox.warning(self, "Erro", f"Não foi possível encontrar uma janela válida para:\n{name} (PID: {pid})\n\nTente outro processo ou procure por processos relacionados ao jogo.")
    
    def find_best_window(self, pid):
        """Encontra a melhor janela de um processo"""
        found_windows = []
        
        def enum_windows_proc(hwnd, lParam):
            try:
                window_pid = win32gui.GetWindowThreadProcessId(hwnd)[1]
                if window_pid == pid:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    is_visible = win32gui.IsWindowVisible(hwnd)
                    
                    found_windows.append({
                        'hwnd': hwnd,
                        'title': window_text,
                        'class': class_name,
                        'visible': is_visible
                    })
            except:
                pass
            return True
        
        win32gui.EnumWindows(enum_windows_proc, 0)
        
        # Priorizar janelas visíveis com título
        valid_windows = [w for w in found_windows if w['visible'] and w['title']]
        
        if valid_windows:
            return valid_windows[0]['hwnd']
        elif found_windows:
            return found_windows[0]['hwnd']
        
        return None

def main():
    app = QApplication(sys.argv)
    
    # Aplicar tema escuro
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.WindowText, Qt.white)
    app.setPalette(palette)
    
    window = ProcessSelectorGUI()
    window.show()
    
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
