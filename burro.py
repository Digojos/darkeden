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

def has_text_in_region(region, text_to_find=None, min_confidence=50):
    """
    Verifica se existe texto em uma região
    
    Args:
        region: Tupla (left, top, width, height)
        text_to_find: Se fornecido, procura texto específico. Se None, verifica qualquer texto
        min_confidence: Confiança mínima do OCR (0-100)
    
    Returns:
        True se encontrou texto, False caso contrário
    """
    print(f"\n🔍 Verificando texto na região...")
    if region:
        print(f"   Região: left={region[0]}, top={region[1]}, width={region[2]}, height={region[3]}")
    
    pyautogui.keyDown('alt')  # ← AQUI: Simular tecla pressionada durante captura)  
    # Capturar screenshot
    screenshot = pyautogui.screenshot(region=region)
    
    pyautogui.keyUp('alt')  # ← AQUI: Soltar a tecla após captura
    # Salvar screenshot original para debug
    screenshot.save('debug_has_text_original.png')
    
    # Preprocessamento - vamos testar múltiplas estratégias
    from PIL import ImageEnhance, ImageFilter, ImageOps
    
    # === ESTRATÉGIA 1: Contraste simples (original) ===
    screenshot_gray = screenshot.convert('L')
    enhancer = ImageEnhance.Contrast(screenshot_gray)
    screenshot_v1 = enhancer.enhance(2.5)
    screenshot_v1 = screenshot_v1.filter(ImageFilter.SHARPEN)
    screenshot_v1.save('debug_v1_contraste.png')
    
    # === ESTRATÉGIA 2: Inversão de cores (texto escuro em fundo claro) ===
    screenshot_v2 = ImageOps.invert(screenshot_gray)
    enhancer2 = ImageEnhance.Contrast(screenshot_v2)
    screenshot_v2 = enhancer2.enhance(3.0)
    screenshot_v2.save('debug_v2_invertido.png')
    
    # === ESTRATÉGIA 3: Escala maior (2x) para melhorar detecção ===
    width, height = screenshot.size
    screenshot_v3 = screenshot.resize((width * 2, height * 2), Image.LANCZOS)
    screenshot_v3_gray = screenshot_v3.convert('L')
    enhancer3 = ImageEnhance.Contrast(screenshot_v3_gray)
    screenshot_v3 = enhancer3.enhance(2.5)
    screenshot_v3 = screenshot_v3.filter(ImageFilter.SHARPEN)
    screenshot_v3.save('debug_v3_escalado.png')
    
    print("💾 Screenshots de teste salvos:")
    print("   - debug_has_text_original.png (original)")
    print("   - debug_v1_contraste.png (estratégia 1)")
    print("   - debug_v2_invertido.png (estratégia 2)")
    print("   - debug_v3_escalado.png (estratégia 3)")
    
    # Testar OCR com cada estratégia e diferentes PSM modes
    estrategias = [
        (screenshot_v1, 'v1_contraste', 7),
        (screenshot_v1, 'v1_contraste', 6),
        (screenshot_v2, 'v2_invertido', 7),
        (screenshot_v3, 'v3_escalado', 7),
        (screenshot_v1, 'v1_contraste', 11),
    ]
    
    all_words = []
    print("\n🔍 Testando diferentes estratégias de OCR...")
    
    for img, nome, psm in estrategias:
        custom_config = f'--oem 3 --psm {psm}'
        try:
            data = pytesseract.image_to_data(
                img, 
                output_type=pytesseract.Output.DICT,
                config=custom_config
            )
            
            # Coletar palavras encontradas
            for i, word in enumerate(data['text']):
                if word and word.strip():
                    conf = data['conf'][i]
                    if conf >= 0:  # Aceitar qualquer confiança para debug
                        all_words.append({
                            'word': word,
                            'conf': conf,
                            'estrategia': nome,
                            'psm': psm,
                            'data_index': i,
                            'data': data
                        })
            
            print(f"   [{nome} PSM{psm}] Palavras: {len([w for w in data['text'] if w.strip()])}")
        except Exception as e:
            print(f"   [{nome} PSM{psm}] ERRO: {e}")
    
    # Mostrar TODAS as palavras encontradas
    if all_words:
        print(f"\n📝 TODAS AS PALAVRAS DETECTADAS ({len(all_words)} total):")
        print("-" * 80)
        for w in sorted(all_words, key=lambda x: x['conf'], reverse=True)[:20]:  # Top 20
            print(f"   '{w['word']}' - {w['conf']}% confiança - [{w['estrategia']} PSM{w['psm']}]")
        print("-" * 80)
    else:
        print("\n❌ NENHUMA palavra foi detectada em NENHUMA estratégia!")
        print("   Isso é muito incomum. Possíveis causas:")
        print("   1. A região está capturando área vazia")
        print("   2. Tesseract não está funcionando corretamente")
        print("   3. O texto é muito pequeno/distorcido")
        return False
    
    # BUSCAR nas palavras coletadas (all_words)
    if text_to_find:
        # Procurando texto específico
        text_lower = text_to_find.lower()
        matches = []
        
        for word_info in all_words:
            word = word_info['word']
            word_lower = word.lower()
            conf = word_info['conf']
            
            if conf >= min_confidence:
                # Busca flexível (exata ou parcial)
                if text_lower in word_lower or word_lower in text_lower:
                    matches.append(word_info)
        
        if matches:
            best_match = max(matches, key=lambda x: x['conf'])
            print(f"\n✅ Texto '{text_to_find}' encontrado!")
            print(f"   Palavra: '{best_match['word']}'")
            print(f"   Confiança: {best_match['conf']}%")
            print(f"   Estratégia: {best_match['estrategia']} PSM{best_match['psm']}")
            return True
        else:
            print(f"\n❌ Texto '{text_to_find}' não encontrado na região")
            print(f"   (min_confidence={min_confidence})")
            return False
    else:
        # Verificando qualquer texto
        palavras_validas = [w for w in all_words if w['conf'] >= min_confidence]
        
        if palavras_validas:
            melhor = max(palavras_validas, key=lambda x: x['conf'])
            print(f"\n✅ Texto encontrado na região!")
            print(f"   Palavra: '{melhor['word']}'")
            print(f"   Confiança: {melhor['conf']}%")
            print(f"   Estratégia: {melhor['estrategia']} PSM{melhor['psm']}")
            return True
        else:
            print(f"\n❌ Nenhum texto com confiança >= {min_confidence}% encontrado")
            if all_words:
                melhor_geral = max(all_words, key=lambda x: x['conf'])
                print(f"   Melhor palavra detectada: '{melhor_geral['word']}' ({melhor_geral['conf']}%)")
            return False

# Exemplo de uso
time.sleep(3)

# ========================================
# TESTE: has_text_in_region()
# ========================================
region_test = (939, 184, 86, 78)
print("🧪 TESTANDO: has_text_in_region()")
print("="*60)

# Teste 1: Verificar se existe QUALQUER texto
print("\n📌 TESTE 1: Verificar se existe qualquer texto na região")
tem_texto = has_text_in_region(region_test)
print(f"💡 Resultado: {tem_texto}")

# Teste 2: Verificar se existe texto específico (exemplo com "Mystery")
print("\n📌 TESTE 2: Procurar 'Mystery' especificamente")
tem_mystery = has_text_in_region(region_test, text_to_find="Mystery")
print(f"💡 Resultado: {tem_mystery}")

print("\n" + "="*60)
