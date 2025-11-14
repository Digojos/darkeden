import pyautogui
import numpy as np
from PIL import Image, ImageEnhance
import time

def has_red_in_region(red_threshold=120, min_red_percentage=20.0):
    region = (335, 283, 361, 227)

    
    """
    Detecta se existe cor vermelha em uma região da tela (monstros no Dark Eden)
    
    Args:
        region: tupla (x, y, largura, altura) da região a analisar
        red_threshold: Valor mínimo de vermelho (0-255). Padrão: 120
        min_red_percentage: % mínima de pixels vermelhos (0-100). Padrão: 0.5%
    
    Returns:
        True se encontrou vermelho (monstro presente), False caso contrário
    """
    print("🔍 Procurando monstros (cor vermelha)...")
    
    # Capturar screenshot da região
    screenshot = pyautogui.screenshot(region=region)
    
    # Aumentar saturação para destacar cores vivas (vermelho dos monstros)
    enhancer = ImageEnhance.Color(screenshot)
    screenshot_enhanced = enhancer.enhance(1.8)  # Aumenta saturação 1.8x
    
    # Converter para numpy array
    img_array = np.array(screenshot_enhanced)
    
    # Separar canais RGB
    red = img_array[:, :, 0].astype(int)
    green = img_array[:, :, 1].astype(int)
    blue = img_array[:, :, 2].astype(int)
    
    # Calcular "vermelhidão" = R - max(G, B)
    # Quanto maior, mais vermelho puro (monstros são vermelho intenso)
    max_gb = np.maximum(green, blue)
    redness = red - max_gb
    
    # Máscara: pixels com alta "vermelhidão"
    # Baseado na imagem fornecida: vermelho intenso (R > 120, R >> G, R >> B)
    red_mask = (
        (red > red_threshold) &           # Vermelho intenso (> 120)
        (redness > 50) &                  # Diferença significativa entre R e G/B
        (red > green + 40) &              # Vermelho muito maior que verde
        (red > blue + 40)                 # Vermelho muito maior que azul
    )
    
    # Calcular porcentagem de pixels vermelhos
    total_pixels = red_mask.size
    red_pixels = np.sum(red_mask)
    red_percentage = (red_pixels / total_pixels) * 100
    
    
    has_red = red_percentage >= min_red_percentage
    
    if has_red:
        print(f"   🔴 MONSTRO DETECTADO! ({red_percentage:.2f}% da região)" )
    else:
        print(f"   ⚪ Área limpa (mínimo: {min_red_percentage}%) {red_percentage:.2f}%")

    save_debug_image(region, "debug_monster_region.png")
    return has_red


def has_red_advanced(region, red_min=100, red_dominance=40, min_percentage=0.3):
    """
    Versão avançada: Detecta vermelho com análise de dominância de cor
    Calibrado para a imagem fornecida (monstros vermelhos intensos)
    
    Args:
        region: tupla (x, y, largura, altura)
        red_min: Intensidade mínima de vermelho (0-255). Padrão: 100
        red_dominance: Diferença mínima entre R e outros canais. Padrão: 40
        min_percentage: % mínima de pixels vermelhos (0.0-100.0). Padrão: 0.3%
    
    Returns:
        True se encontrou monstro, False caso contrário
    """
    print("🔍 Procurando monstros (método avançado)...")
    
    # Capturar screenshot
    screenshot = pyautogui.screenshot(region=region)
    
    # Aumentar contraste e saturação para destacar monstros
    enhancer_color = ImageEnhance.Color(screenshot)
    screenshot_saturated = enhancer_color.enhance(2.0)  # Saturação 2x
    
    enhancer_contrast = ImageEnhance.Contrast(screenshot_saturated)
    screenshot_enhanced = enhancer_contrast.enhance(1.5)  # Contraste 1.5x
    
    # Converter para numpy array
    img_array = np.array(screenshot_enhanced)
    
    # Separar canais RGB
    red = img_array[:, :, 0].astype(int)
    green = img_array[:, :, 1].astype(int)
    blue = img_array[:, :, 2].astype(int)
    
    # Critérios para vermelho de monstro (baseado na imagem):
    # 1. Vermelho alto (> red_min)
    # 2. Vermelho domina verde (R - G > red_dominance)
    # 3. Vermelho domina azul (R - B > red_dominance)
    red_mask = (
        (red > red_min) &
        ((red - green) > red_dominance) &
        ((red - blue) > red_dominance)
    )
    
    # Calcular porcentagem
    total_pixels = red_mask.size
    red_pixels = np.sum(red_mask)
    red_percentage = (red_pixels / total_pixels) * 100
    
    print(f"   📊 Análise: {red_pixels} pixels vermelhos ({red_percentage:.2f}%)")
    
    has_red = red_percentage >= min_percentage
    
    if has_red:
        print(f"   🔴 MONSTRO DETECTADO! ({red_percentage:.2f}% da região)")
    else:
        print(f"   ⚪ Área limpa (mínimo: {min_percentage}%)")
    
    return has_red


def save_debug_image(region, filename="debug_monster.png"):
    """
    Salva imagem da região para debug
    Útil para verificar se a região está correta
    """
    screenshot = pyautogui.screenshot(region=region)
    screenshot.save(filename)
    print(f"💾 Imagem salva: {filename}")


# Exemplo de uso para detecção de monstros
def isThereMonster():
    """
    Detecta se existe monstro (vermelho) na região especificada
    Região calibrada: (335, 283, 361, 227)
    """
    region_monster = (335, 283, 361, 227)  # Região dos monstros
    
    # Método 1: Simples (rápido, boa precisão)
    result = has_red_in_region(red_threshold=120, min_red_percentage=30.0)
    
    # Método 2: Avançado (mais sensível, melhor para monstros pequenos)
    # result = has_red_advanced(region_monster, red_min=100, red_dominance=40, min_percentage=0.3)
    
    if result:
        print("🔴 TEM MONSTRO!")
    else:
        print("⚪ NÃO TEM MONSTRO")
    
    return result


def isThereMonsterQuick():
    """
    Versão rápida sem prints (para uso em loops)
    """
    region_monster = (335, 283, 361, 227)
    screenshot = pyautogui.screenshot(region=region_monster)
    
    enhancer = ImageEnhance.Color(screenshot)
    screenshot_enhanced = enhancer.enhance(1.8)
    
    img_array = np.array(screenshot_enhanced)
    red = img_array[:, :, 0].astype(int)
    green = img_array[:, :, 1].astype(int)
    blue = img_array[:, :, 2].astype(int)
    
    max_gb = np.maximum(green, blue)
    redness = red - max_gb
    
    red_mask = (
        (red > 120) &
        (redness > 50) &
        (red > green + 40) &
        (red > blue + 40)
    )
    
    red_percentage = (np.sum(red_mask) / red_mask.size) * 100
    return red_percentage >= 0.5


# === TESTES E DEBUG ===
if __name__ == "__main__":
    print("⏳ Aguardando 4 segundos...")
    time.sleep(4)
    
    # Testar detecção
    region_monster = (335, 283, 361, 227)
    result_strict = has_red_in_region(red_threshold=120, min_red_percentage=30.0)
 

    save_debug_image(region_monster, "debug_monster_region.png")
   
