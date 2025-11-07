# Teste rápido da aplicação
import sys
try:
    from dota import TomagoxaApp, main
    from PyQt5.QtWidgets import QApplication
    
    print("Importação bem-sucedida!")
    print("Iniciando aplicação...")
    
    # Teste básico de criação da app
    app = QApplication(sys.argv)
    window = TomagoxaApp()
    print("Aplicação criada com sucesso!")
    
    # Não mostrar a janela, apenas testar criação
    print("Teste concluído - aplicação está funcionando!")
    
except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()
