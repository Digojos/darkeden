# 📦 Guia de Instalação - Dark Eden Bot (dk4.py)

Este guia contém as instruções completas para instalar todas as dependências necessárias para executar o bot Dark Eden.

---

## 📋 Pré-requisitos

- **Python 3.10 ou superior** instalado
- **Windows 10/11** (o bot usa bibliotecas específicas do Windows)
- **Dark Eden** instalado e funcionando

---

## 🚀 Instalação Rápida

### 1. Instalar Dependências Python

Abra o **PowerShell** ou **CMD** na pasta do projeto e execute:

```powershell
pip install -r dk4-requirements.txt
```

**Ou com Python específico:**

```powershell
python -m pip install -r dk4-requirements.txt
```

---

### 2. Instalar Tesseract OCR (Obrigatório)

O Tesseract é necessário para o módulo `findItemDK.py` detectar itens no chão.

#### Download:
- **Link oficial:** https://github.com/UB-Mannheim/tesseract/wiki
- **Download direto:** [tesseract-ocr-w64-setup-5.3.3.20231005.exe](https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe)

#### Instalação:
1. Execute o instalador baixado
2. Durante a instalação, certifique-se de instalar em:
   ```
   C:\Program Files\Tesseract-OCR\
   ```
3. Marque a opção para adicionar ao PATH (opcional)

#### Verificar Instalação:
```powershell
tesseract --version
```

**Se instalou em outro local**, edite o arquivo `findItemDK.py` linha 13:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\SEU\CAMINHO\tesseract.exe'
```

---

## 📦 Dependências Instaladas

| Pacote | Versão | Descrição |
|--------|--------|-----------|
| **keyboard** | 0.13.5 | Gerenciamento de hotkeys e controle de teclado |
| **pyautogui** | 0.9.54 | Controle de mouse, teclado e screenshots |
| **Pillow** | 10.1.0 | Processamento e manipulação de imagens |
| **numpy** | 1.24.3 | Análise de arrays (detecção de cor vermelha) |
| **pytesseract** | 0.3.10 | Interface Python para Tesseract OCR |
| **psutil** | 5.9.6 | Listagem e gerenciamento de processos |
| **pymem** | 1.13.1 | Leitura de memória de processos |

---

## ✅ Verificar Instalação

Execute este comando para verificar se tudo está instalado corretamente:

```powershell
python -c "import keyboard, pyautogui, PIL, numpy, pytesseract, psutil, pymem; print('✅ Todas as dependências estão instaladas!')"
```

**Resultado esperado:**
```
✅ Todas as dependências estão instaladas!
```

---

## 🔧 Solução de Problemas

### ❌ Erro: "No module named 'keyboard'"

**Solução:**
```powershell
pip install keyboard==0.13.5
```

---

### ❌ Erro: "pytesseract.pytesseract.TesseractNotFoundError"

**Causa:** Tesseract OCR não está instalado ou não foi encontrado.

**Solução:**
1. Instale o Tesseract OCR (veja seção 2 acima)
2. Ou edite `findItemDK.py` linha 13 com o caminho correto:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

---

### ❌ Erro: "Permission denied" ao instalar pacotes

**Causa:** Falta de permissões de administrador.

**Solução 1:** Abra PowerShell/CMD como **Administrador**

**Solução 2:** Instale apenas para o usuário atual:
```powershell
pip install --user -r dk4-requirements.txt
```

---

### ❌ Erro: "pip não é reconhecido como comando"

**Causa:** Python não foi adicionado ao PATH durante instalação.

**Solução:**
```powershell
python -m pip install -r dk4-requirements.txt
```

---

### ⚠️ Múltiplas versões do Python instaladas

Se você tem Python 3.10, 3.11, 3.12, etc., especifique a versão:

```powershell
# Python 3.11
py -3.11 -m pip install -r dk4-requirements.txt

# Python 3.10
py -3.10 -m pip install -r dk4-requirements.txt
```

---

## 🎮 Executar o Bot

Após instalar todas as dependências:

```powershell
python dk4.py
```

### Hotkeys Disponíveis:

| Tecla | Função |
|-------|--------|
| **Alt+1** | Salvar posição do mouse (ponto de ataque) |
| **\\** (Backslash) | Iniciar/Parar bot |
| **F4** | Segurar botão direito do mouse |
| **F3** | Debug (mostrar posição do mouse) |
| **Ctrl+Alt+M** | Mostrar valores de memória |
| **Ctrl+Alt+T** | Ativar/Desativar monitoramento de memória |
| **Ctrl+Alt+D** | Debug detalhado X/Y |
| **Ctrl+Alt+R** | Reconectar a outro processo |
| **F2** | Sair do bot |

---

## 📁 Estrutura de Arquivos Necessária

```
darkeden/
├── dk4.py                      # Script principal do bot
├── dk4-requirements.txt        # Lista de dependências
├── INSTALACAO.md              # Este arquivo
├── findItemDK.py              # Módulo de detecção de itens (OCR)
├── findMonsterDK.py           # Módulo de detecção de monstros (cor vermelha)
├── read-memory.py             # Módulo de leitura de memória
└── memory_addresses.json      # Endereços de memória do jogo
```

---

## 🔄 Atualizar Dependências

Para atualizar todos os pacotes para as versões mais recentes:

```powershell
pip install --upgrade -r dk4-requirements.txt
```

---

## 📚 Bibliotecas Padrão (Não Precisam Instalar)

Estas bibliotecas já vêm com o Python:

- `threading` - Execução de tarefas em paralelo
- `time` - Controle de tempo e delays
- `os` - Operações do sistema operacional
- `sys` - Parâmetros e funções do sistema
- `ctypes` - Chamadas de funções C (Windows API)
- `struct` - Conversão de dados binários
- `json` - Manipulação de arquivos JSON
- `random` - Geração de números aleatórios
- `importlib` - Importação dinâmica de módulos

---

## 🆘 Suporte

Se encontrar problemas durante a instalação:

1. **Verifique a versão do Python:**
   ```powershell
   python --version
   ```
   Deve ser **3.10 ou superior**

2. **Atualize o pip:**
   ```powershell
   python -m pip install --upgrade pip
   ```

3. **Reinstale todas as dependências:**
   ```powershell
   pip uninstall -r dk4-requirements.txt -y
   pip install -r dk4-requirements.txt
   ```

---

## ✅ Checklist de Instalação

- [ ] Python 3.10+ instalado
- [ ] Arquivo `dk4-requirements.txt` presente
- [ ] Executado `pip install -r dk4-requirements.txt`
- [ ] Tesseract OCR instalado em `C:\Program Files\Tesseract-OCR\`
- [ ] Comando `tesseract --version` funciona (ou caminho configurado em `findItemDK.py`)
- [ ] Teste de importação passou com sucesso
- [ ] Dark Eden está rodando
- [ ] Todos os arquivos do bot estão na mesma pasta

---

## 🎯 Pronto para Usar!

Se todos os itens do checklist foram marcados, você está pronto para executar:

```powershell
python dk4.py
```

**Bom farm! 🚀**
