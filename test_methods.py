#!/usr/bin/env python3
"""
Script de teste rápido para os novos métodos de clique
"""

import sys
import time
import win32gui
import win32process
import psutil

# Importar nossa classe
from dk_window_specific import ProcessMouseController

def find_game_process():
    """Encontrar processo de jogo"""
    print("🔍 Procurando processos de jogo...")
    
    keywords = ['dark', 'eden', 'game', 'client']
    found_processes = []
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower()
            if any(keyword in name for keyword in keywords):
                found_processes.append((proc.info['pid'], proc.info['name']))
        except:
            continue
    
    if found_processes:
        print("🎮 Processos encontrados:")
        for i, (pid, name) in enumerate(found_processes):
            print(f"   {i+1}. {name} (PID: {pid})")
        
        # Usar o primeiro
        return found_processes[0][1]
    else:
        print("❌ Nenhum processo de jogo encontrado")
        print("💡 Você pode testar com qualquer aplicação aberta (ex: notepad.exe)")
        return None

def test_methods():
    """Testar todos os métodos"""
    process_name = find_game_process()
    
    if not process_name:
        process_name = "notepad.exe"
        print(f"🧪 Usando processo de teste: {process_name}")
        print("   Abra o Notepad para testar!")
        time.sleep(3)
    
    # Criar controlador
    controller = ProcessMouseController(process_name)
    
    if not controller.find_window():
        print("❌ Não foi possível conectar à janela!")
        return
    
    # Configurar posição de teste
    controller.mouseAttackX = 100
    controller.mouseAttackY = 100
    
    # Testar cada método
    methods = [
        ('direct_input', '⚡ DirectInput Avançado'),
        ('game_input', '🎮 GameInput Especializado'),
        ('memory_inject', '🧬 Memory Injection'),
        ('process_hook', '🔗 Process Hook'),
        ('win32_send', '📨 Win32API SendMessage'),
        ('win32_post', '🔧 Win32API PostMessage')
    ]
    
    print("\n🧪 Iniciando testes dos métodos avançados...")
    print("=" * 50)
    
    for method_key, method_name in methods:
        print(f"\n🔬 Testando: {method_name}")
        controller.click_method = method_key
        
        try:
            result = controller.click_in_window_current_method(100, 100, 'left')
            if result:
                print(f"✅ {method_name} - FUNCIONOU!")
            else:
                print(f"❌ {method_name} - Falhou")
        except Exception as e:
            print(f"❌ {method_name} - Erro: {e}")
        
        time.sleep(1)  # Delay entre testes
    
    print("\n" + "=" * 50)
    print("🏁 Testes concluídos!")

if __name__ == "__main__":
    print("🚀 Testador de Métodos Avançados de Clique")
    print("=" * 50)
    test_methods()
