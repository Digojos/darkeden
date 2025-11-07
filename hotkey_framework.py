import keyboard
import threading
import time
import json
import os
from typing import Dict, Callable, Any

class HotkeyManager:
    def __init__(self):
        self.hotkeys: Dict[str, Dict[str, Any]] = {}
        self.active_hotkeys = []
        self.config_file = "hotkey_config.json"
        
    def register_method(self, hotkey: str, method: Callable, description: str = "", args: tuple = (), kwargs: dict = {}):
        """
        Cadastra um método para ser executado por uma hotkey
        
        Args:
            hotkey: Combinação de teclas (ex: 'f5', 'ctrl+c', 'alt+1')
            method: Função/método a ser executado
            description: Descrição do que a hotkey faz
            args: Argumentos posicionais para o método
            kwargs: Argumentos nomeados para o método
        """
        self.hotkeys[hotkey] = {
            'method': method,
            'description': description,
            'args': args,
            'kwargs': kwargs,
            'enabled': True
        }
        print(f"Hotkey registrada: {hotkey} -> {method.__name__}")
        
    def unregister_method(self, hotkey: str):
        """Remove uma hotkey cadastrada"""
        if hotkey in self.hotkeys:
            del self.hotkeys[hotkey]
            print(f"Hotkey removida: {hotkey}")
            
    def execute_method(self, hotkey: str):
        """Executa o método associado à hotkey"""
        if hotkey in self.hotkeys and self.hotkeys[hotkey]['enabled']:
            try:
                method_info = self.hotkeys[hotkey]
                method = method_info['method']
                args = method_info['args']
                kwargs = method_info['kwargs']
                
                # Executar em thread separada para não bloquear
                thread = threading.Thread(
                    target=method, 
                    args=args, 
                    kwargs=kwargs,
                    daemon=True
                )
                thread.start()
                print(f"Executando: {hotkey} -> {method.__name__}")
                
            except Exception as e:
                print(f"Erro ao executar {hotkey}: {str(e)}")
                
    def enable_hotkey(self, hotkey: str):
        """Habilita uma hotkey"""
        if hotkey in self.hotkeys:
            self.hotkeys[hotkey]['enabled'] = True
            
    def disable_hotkey(self, hotkey: str):
        """Desabilita uma hotkey"""
        if hotkey in self.hotkeys:
            self.hotkeys[hotkey]['enabled'] = False
            
    def list_hotkeys(self):
        """Lista todas as hotkeys cadastradas"""
        print("\n=== HOTKEYS CADASTRADAS ===")
        for hotkey, info in self.hotkeys.items():
            status = "ATIVA" if info['enabled'] else "DESATIVADA"
            print(f"{hotkey:<15} -> {info['method'].__name__:<20} | {info['description']:<30} | {status}")
        print("=" * 80)
        
    def start_listener(self):
        """Inicia o listener das hotkeys"""
        print("Iniciando listener de hotkeys...")
        
        # Registrar todas as hotkeys no keyboard
        for hotkey in self.hotkeys.keys():
            try:
                keyboard.add_hotkey(hotkey, lambda h=hotkey: self.execute_method(h))
                self.active_hotkeys.append(hotkey)
            except Exception as e:
                print(f"Erro ao registrar hotkey {hotkey}: {str(e)}")
                
        print(f"Listener ativo com {len(self.active_hotkeys)} hotkeys")
        
    def stop_listener(self):
        """Para o listener das hotkeys"""
        keyboard.unhook_all_hotkeys()
        self.active_hotkeys.clear()
        print("Listener parado")
        
    def save_config(self):
        """Salva configuração das hotkeys em arquivo JSON"""
        config = {}
        for hotkey, info in self.hotkeys.items():
            config[hotkey] = {
                'method_name': info['method'].__name__,
                'description': info['description'],
                'enabled': info['enabled']
            }
            
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Configuração salva em {self.config_file}")
        
    def load_config(self):
        """Carrega configuração das hotkeys do arquivo JSON"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            print(f"Configuração carregada de {self.config_file}")
            return config
        return {}

# Classe base para criar suas próprias ações
class BaseActions:
    """Classe base com métodos exemplo que podem ser executados por hotkeys"""
    
    def __init__(self):
        self.state = {"active": False, "count": 0}
        
    def example_action(self):
        """Método exemplo"""
        print("Executando ação exemplo!")
        self.state["count"] += 1
        
    def toggle_state(self):
        """Toggle de estado exemplo"""
        self.state["active"] = not self.state["active"]
        status = "ATIVA" if self.state["active"] else "INATIVA"
        print(f"Estado alterado para: {status}")
        
    def print_info(self, message="Info padrão"):
        """Método com parâmetros"""
        print(f"Informação: {message} | Count: {self.state['count']}")
        
    def long_running_task(self):
        """Simula uma tarefa demorada"""
        print("Iniciando tarefa longa...")
        for i in range(5):
            time.sleep(1)
            print(f"Processando... {i+1}/5")
        print("Tarefa concluída!")

# Função para demonstrar uso
def demo():
    """Demonstração de como usar o HotkeyManager"""
    
    # Criar instâncias
    manager = HotkeyManager()
    actions = BaseActions()
    
    # Registrar métodos com hotkeys
    manager.register_method(
        hotkey='f1', 
        method=actions.example_action,
        description="Ação exemplo simples"
    )
    
    manager.register_method(
        hotkey='f2',
        method=actions.toggle_state,
        description="Alternar estado ativo/inativo"
    )
    
    manager.register_method(
        hotkey='f3',
        method=actions.print_info,
        description="Mostrar informações",
        args=("Mensagem customizada!",)
    )
    
    manager.register_method(
        hotkey='f4',
        method=actions.long_running_task,
        description="Tarefa que demora 5 segundos"
    )
    
    # Método lambda inline
    manager.register_method(
        hotkey='f5',
        method=lambda: print("Lambda executada!"),
        description="Função lambda simples"
    )
    
    # Listar hotkeys
    manager.list_hotkeys()
    
    # Salvar configuração
    manager.save_config()
    
    # Iniciar listener
    manager.start_listener()
    
    print("\n=== HOTKEYS ATIVAS ===")
    print("F1: Ação exemplo")
    print("F2: Toggle estado")
    print("F3: Mostrar info")
    print("F4: Tarefa longa")
    print("F5: Lambda")
    print("ESC: Sair")
    print("Pressione as teclas para testar...")
    
    try:
        # Aguardar ESC para sair
        keyboard.wait('esc')
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_listener()
        print("Programa finalizado")

if __name__ == "__main__":
    demo()