import pyautogui
import pytesseract
from PIL import Image
import time
import os

# Configurar caminho do Tesseract
# IMPORTANTE: Ajuste o caminho conforme onde você instalou
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Verificar se o Tesseract está instalado
if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
    print("❌ ERRO: Tesseract OCR não encontrado!")
    print(f"   Procurado em: {pytesseract.pytesseract.tesseract_cmd}")
    print("\n📦 SOLUÇÃO:")
    print("   1. Baixe o Tesseract em: https://github.com/UB-Mannheim/tesseract/wiki")
    print("   2. Instale o programa")
    print("   3. Ajuste o caminho na linha 9 do código")
    print("\n   Caminhos comuns:")
    print("   - C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
    print("   - C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe")
    input("\nPressione ENTER para sair...")
    exit()

def has_text_in_region(region, min_confidence=50):
    from PIL import ImageEnhance, ImageFilter, ImageOps

    print("Procurando itens...")
    
    pyautogui.keyDown('alt')
    screenshot = pyautogui.screenshot(region=region)
    pyautogui.keyUp('alt')
    
    screenshot_gray = screenshot.convert('L')
    enhancer = ImageEnhance.Contrast(screenshot_gray)
    screenshot_v1 = enhancer.enhance(2.5)
    screenshot_v1 = screenshot_v1.filter(ImageFilter.SHARPEN)
    
    screenshot_v2 = ImageOps.invert(screenshot_gray)
    enhancer2 = ImageEnhance.Contrast(screenshot_v2)
    screenshot_v2 = enhancer2.enhance(3.0)
    
    width, height = screenshot.size
    screenshot_v3 = screenshot.resize((width * 2, height * 2), Image.LANCZOS)
    screenshot_v3_gray = screenshot_v3.convert('L')
    enhancer3 = ImageEnhance.Contrast(screenshot_v3_gray)
    screenshot_v3 = enhancer3.enhance(2.5)
    screenshot_v3 = screenshot_v3.filter(ImageFilter.SHARPEN)
    
    estrategias = [
        (screenshot_v1, 7),
        (screenshot_v1, 6),
        (screenshot_v2, 7),
        (screenshot_v3, 7),
        (screenshot_v1, 11),
    ]
    
    all_words = []
    
    for img, psm in estrategias:
        custom_config = f'--oem 3 --psm {psm}'
        try:
            data = pytesseract.image_to_data(
                img, 
                output_type=pytesseract.Output.DICT,
                config=custom_config
            )
            
            for i, word in enumerate(data['text']):
                if word and word.strip():
                    conf = data['conf'][i]
                    if conf >= min_confidence:
                        all_words.append({'word': word, 'conf': conf})
        except:
            pass
    
    return len(all_words) > 0

# Exemplo de uso
def isThereAreItem():
    region_test = (939, 184, 86, 78)
    result = has_text_in_region(region_test, min_confidence=50)
    if(result):
        print("Tem item!")
    else:
        print("Não tem item!")    
    return result


time.sleep(4)
isThereAreItem()