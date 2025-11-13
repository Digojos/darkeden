import pyautogui
import time

print("🎯 FERRAMENTA PARA DESCOBRIR COORDENADAS DA REGIÃO")
print("="*60)

print("\n📍 PASSO 1: Posicione o mouse no CANTO SUPERIOR ESQUERDO da área")
print("Aguardando 5 segundos...")
time.sleep(5)

x1, y1 = pyautogui.position()
print(f"✅ Posição inicial: X={x1}, Y={y1}")

print("\n📍 PASSO 2: Agora posicione o mouse no CANTO INFERIOR DIREITO da área")
print("Aguardando 5 segundos...")
time.sleep(5)

x2, y2 = pyautogui.position()
print(f"✅ Posição final: X={x2}, Y={y2}")

# Calcular largura e altura
width = x2 - x1
height = y2 - y1

print("\n" + "="*60)
print("📋 RESULTADO:")
print("="*60)
print(f"left   (X inicial): {x1}")
print(f"top    (Y inicial): {y1}")
print(f"width  (largura):   {width}")
print(f"height (altura):    {height}")
print("\n📌 Cole esta linha no seu código:")
print(f"region = ({x1}, {y1}, {width}, {height})")
print("="*60)

# Capturar e salvar a região para verificar
try:
    screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
    screenshot.save('regiao_teste.png')
    print("\n✅ Área capturada salva em: regiao_teste.png")
    print("   Abra o arquivo para confirmar se capturou a área correta!")
    screenshot.show()  # Abre automaticamente
except Exception as e:
    print(f"\n⚠️ Erro ao capturar região: {e}")