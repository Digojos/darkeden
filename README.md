# Dota 1.0 - Aplicação de Combos Automáticos

Uma aplicação PyQt5 para automatizar combos de teclas em jogos, com interface inspirada no Legion Commander do Dota.

## 📋 Características

- Interface gráfica moderna com tema escuro
- 4 slots para Skills (Q, W, E, R por padrão)
- 6 slots para Items (1, 2, 3, 4, 5, 6 por padrão)
- Sistema de combo personalizável com hotkey configurável
- Salvamento automático de configurações
- Feedback visual ao salvar

## 🎮 Como Usar

### 1. Configuração de Skills
- **Seção Superior**: 4 slots para habilidades
- **Valores Padrão**: Q, W, E, R
- **Personalização**: Clique no campo de texto para alterar a tecla
- **Ativação**: Marque o checkbox para incluir no combo

### 2. Configuração de Items
- **Seção Inferior**: 6 slots para itens (2 linhas de 3)
- **Valores Padrão**: 1, 2, 3, 4, 5, 6
- **Personalização**: Clique no campo de texto para alterar a tecla
- **Ativação**: Marque o checkbox para incluir no combo

### 3. Sistema de Combo
- **Tecla do Combo**: Campo personalizável (padrão: space)
- **Ativação**: Checkbox "Nenj" vem marcado por padrão (ativo)
- **Execução**: Pressione a tecla configurada para executar

### 4. Salvando Configurações
- Clique em **"Aceitar"** para salvar todas as configurações
- O botão ficará verde e mostrará "Salvo!" por 2 segundos
- O combo será ativado/desativado conforme configurado

## ⌨️ Teclas Disponíveis

### Teclas Básicas
```
Letras: a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z
Números: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
Espaço: space (também aceita "Space")
```

### Teclas de Função
```
f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12
f13, f14, f15, f16, f17, f18, f19, f20, f21, f22, f23, f24
```

### Teclas Especiais
```
enter       - Enter
return      - Return (alternativa ao Enter)
tab         - Tab ('\t')
esc         - Escape
escape      - Escape (alternativa)
backspace   - Backspace
delete      - Delete
del         - Delete (alternativa)
insert      - Insert
home        - Home
end         - End
pageup      - Page Up
pgup        - Page Up (alternativa)
pagedown    - Page Down
pgdn        - Page Down (alternativa)
```

### Teclas Modificadoras
```
shift       - Shift (qualquer)
shiftleft   - Shift esquerdo
shiftright  - Shift direito
ctrl        - Control (qualquer)
ctrlleft    - Control esquerdo
ctrlright   - Control direito
alt         - Alt (qualquer)
altleft     - Alt esquerdo
altright    - Alt direito
```

### Teclas do Sistema (Windows)
```
win         - Tecla Windows (qualquer)
winleft     - Tecla Windows esquerda
winright    - Tecla Windows direita
apps        - Menu de contexto
```

### Teclas do Sistema (Mac)
```
command     - Command (⌘)
option      - Option (⌥)
optionleft  - Option esquerdo
optionright - Option direito
fn          - Function
```

### Teclas Direcionais
```
up          - Seta para cima
down        - Seta para baixo
left        - Seta para esquerda
right       - Seta para direita
```

### Teclado Numérico
```
num0, num1, num2, num3, num4, num5, num6, num7, num8, num9
numlock     - Num Lock
add         - + (numérico)
subtract    - - (numérico)
multiply    - * (numérico)
divide      - / (numérico)
decimal     - . (numérico)
separator   - Separador numérico
```

### Teclas de Estado
```
capslock    - Caps Lock
scrolllock  - Scroll Lock
pause       - Pause/Break
printscreen - Print Screen
prntscrn    - Print Screen (alternativa)
prtsc       - Print Screen (alternativa)
prtscr      - Print Screen (alternativa)
print       - Print
```

### Símbolos e Pontuação
```
!    "    #    $    %    &    '    (    )    *
+    ,    -    .    /    :    ;    <    =    >
?    @    [    \    ]    ^    _    `    {    |
}    ~
```

### Teclas de Mídia
```
volumeup        - Volume +
volumedown      - Volume -
volumemute      - Mute
playpause       - Play/Pause
nexttrack       - Próxima faixa
prevtrack       - Faixa anterior
stop            - Stop
```

### Teclas de Navegador
```
browserback         - Voltar
browserforward      - Avançar
browserhome         - Página inicial
browserrefresh      - Atualizar
browsersearch       - Pesquisar
browserstop         - Parar
browserfavorites    - Favoritos
```

### Teclas de Aplicativo
```
launchapp1          - Aplicativo 1
launchapp2          - Aplicativo 2
launchmail          - Email
launchmediaselect   - Seletor de mídia
sleep               - Suspender
```

### Teclas Especiais (Asiáticas)
```
hanguel     - Hanguel
hangul      - Hangul
hanja       - Hanja
junja       - Junja
kana        - Kana
kanji       - Kanji
```

### Teclas de Controle
```
accept      - Accept
clear       - Clear
convert     - Convert
execute     - Execute
final       - Final
help        - Help
modechange  - Mode Change
nonconvert  - Non Convert
select      - Select
yen         - Yen
```

## 🔧 Combinações de Teclas

### Formato
Use o sinal `+` para combinar teclas:
```
ctrl+c      - Control + C
alt+1       - Alt + 1
shift+tab   - Shift + Tab
ctrl+alt+d  - Control + Alt + D
```

### Exemplos de Combinações Válidas
```
alt+1           - Alt + número 1
ctrl+space      - Control + espaço
shift+f1        - Shift + F1
alt+tab         - Alt + Tab
ctrl+shift+a    - Control + Shift + A
ctrlleft+c      - Control esquerdo + C
winleft+r       - Windows esquerdo + R
f12             - Tecla F12 simples
pageup          - Page Up simples
volumeup        - Aumentar volume
playpause       - Play/Pause mídia
Space           - Espaço (aceita maiúscula)
Enter           - Enter (aceita maiúscula)
Ctrl+Space      - Combinação com maiúsculas
```

### ⚠️ Observações Importantes
- **Teclas especiais** aceitam variações de maiúscula/minúscula:
  - `space`, `Space`, `SPACE` → todas funcionam
  - `enter`, `Enter`, `ENTER` → todas funcionam
  - `ctrl`, `Ctrl`, `CTRL` → todas funcionam
- **Letras e números** devem ser em minúsculas: `a`, `1`, `f1`
- Não use espaços ao redor do `+` em combinações
- Exemplo correto: `alt+1`, `Space`, `Ctrl+c`
- Exemplo incorreto: `Alt + 1`, `alt + 1`

### 🎯 Teclas Modificadoras Específicas
Para usar teclas modificadoras específicas (esquerda/direita):
```
ctrlleft    - Control esquerdo específico
ctrlright   - Control direito específico
altleft     - Alt esquerdo específico
altright    - Alt direito específico
shiftleft   - Shift esquerdo específico
shiftright  - Shift direito específico
```

**Exemplo para Ctrl esquerdo como hotkey:**
- Digite no campo "Tecla do Combo": `ctrlleft` ou `CtrlLeft`
- Ou use genérico: `ctrl` ou `Ctrl` (funciona com qualquer Ctrl)

### 📋 Variações de Maiúscula/Minúscula Aceitas
Teclas especiais que aceitam diferentes formatações:
```
Space/space/SPACE           → space
Enter/enter/ENTER           → enter
Tab/tab/TAB                 → tab
Ctrl/ctrl/CTRL              → ctrl
Alt/alt/ALT                 → alt
Shift/shift/SHIFT           → shift
Escape/escape/esc/Esc       → esc
CtrlLeft/ctrlleft           → ctrlleft
AltRight/altright           → altright
```

**Nota**: Letras (a-z) e números (0-9) devem sempre ser minúsculos.

## 🎯 Funcionalidades dos Botões

### Botão "Aceitar" (Verde)
- Salva todas as configurações atuais
- Ativa/desativa o sistema de combo
- Mostra feedback visual de confirmação

### Botão "Reset" (Vermelho)
- Reseta todas as configurações para o estado inicial
- Desmarca todos os checkboxes (skills, items e combo)
- Restaura campos de texto aos valores padrão (Q,W,E,R e 1,2,3,4,5,6)
- Limpa a ordem de cliques dos checkboxes
- Para o combo se estiver ativo
- Mostra feedback visual de confirmação

### Botão "Doação" (Laranja)
- Link para suporte ao projeto
- Contribuições para desenvolvimento

## 📦 Dependências

```bash
pip install PyQt5
pip install pyautogui
pip install keyboard
```

## 🚀 Executando a Aplicação

```bash
python dota.py
```

## 🔄 Fluxo de Uso

1. **Abrir Aplicação** → Interface carrega com valores padrão
2. **Configurar Skills** → Alterar teclas e marcar checkboxes desejados
3. **Configurar Items** → Alterar teclas e marcar checkboxes desejados
4. **Definir Combo** → Escolher tecla para ativar combo
5. **Ativar Sistema** → Marcar checkbox do combo
6. **Salvar** → Clicar em "Aceitar"
7. **Usar** → Pressionar tecla do combo para executar sequência
8. **Reset** → Clicar em "Reset" para limpar todas as configurações (opcional)

## ⚡ Estratégias de Ordenação de Teclas

### 1. **Ordem Atual (Sequencial)**
```
Skills primeiro: Q → W → E → R
Items depois: 1 → 2 → 3 → 4 → 5 → 6
```

### 2. **Ordem por Prioridade** (Futura implementação)
Cada tecla terá um número de prioridade (1-10):
```
Prioridade 1: Mais importante (executa primeiro)
Prioridade 10: Menos importante (executa por último)
```

### 3. **Ordem Personalizada**
Arrastar e soltar para reordenar teclas na interface.

### 4. **Ordem por Tipo de Ação**
- **Buffs/Preparação**: Primeiro
- **Dano Principal**: Segundo  
- **Finalizadores**: Terceiro
- **Items de Suporte**: Último

### 6. **Ordem por Clique dos Checkboxes** (Implementado!)
A ordem de execução é determinada pela sequência que você marca os checkboxes:
```
1º checkbox marcado → Executa primeiro
2º checkbox marcado → Executa segundo
3º checkbox marcado → Executa terceiro
...e assim por diante
```

**Como usar:**
1. Marque os checkboxes na ordem desejada de execução
2. O sistema mostra no console: "Ordem atual: Q → 1 → W → 3"
3. Para resetar, desmarque todos e marque novamente na nova ordem

**Exemplo prático:**
- Marcar: Checkbox do item "1" (BKB)
- Marcar: Checkbox do skill "Q" (Overwhelming Odds)  
- Marcar: Checkbox do item "2" (Blink)
- Marcar: Checkbox do skill "R" (Duel)
- **Resultado**: 1 → Q → 2 → R

## 📊 Estrutura de Dados Salvos

```python
{
    'skills': [
        {'index': 0, 'hotkey': 'Q', 'enabled': True},
        {'index': 1, 'hotkey': 'W', 'enabled': False},
        # ... mais skills
    ],
    'items': [
        {'index': 0, 'hotkey': '1', 'enabled': True},
        {'index': 1, 'hotkey': '2', 'enabled': True},
        # ... mais items
    ],
    'combo_hotkey': 'alt+1',
    'combo_enabled': True,
    'click_order': [
        {'id': 'item_0', 'order': 1, 'hotkey': '1', 'timestamp': 1},
        {'id': 'skill_0', 'order': 2, 'hotkey': 'Q', 'timestamp': 2},
        {'id': 'item_1', 'order': 3, 'hotkey': '2', 'timestamp': 3}
    ]  # Ordem baseada nos cliques dos checkboxes
}
```

## 🎮 Melhores Práticas de Ordenação

### Para MOBAs (Dota, LoL)
```
1. Buffs/Preparação (ex: BKB, Armlet)
2. Iniciação (ex: Blink Dagger)
3. Skills principais (Q, W, E)
4. Ultimate (R)
5. Items de dano/finalização
```

### Para MMORPGs
```
1. Buffs de classe
2. Debuffs no inimigo  
3. Skills de dano em ordem de cooldown
4. Potions/consumíveis
5. Skills de escape
```

### Para FPS/Action Games
```
1. Granadas/Utilitários
2. Arma principal
3. Habilidades especiais
4. Arma secundária
5. Recarga/healing
```

## 🐛 Solução de Problemas

### Combo não funciona
- Verifique se o checkbox do combo está marcado
- Certifique-se de ter clicado em "Aceitar" após configurar
- Teste com teclas simples primeiro (ex: "space", "f1")
- **Use o botão "Reset"** para limpar tudo e começar do zero

### Combinação de teclas não reconhecida
- Use apenas minúsculas
- Não coloque espaços ao redor do `+`
- Verifique se as teclas estão na lista de teclas disponíveis
- **Use o botão "Reset"** e configure novamente

### Aplicação crashando
- **Use o botão "Reset"** para limpar configurações corrompidas
- Feche e reabra a aplicação se persistir
- Evite alterar a tecla do combo muito rapidamente
- Execute como administrador se necessário

### Erro ao alterar tecla do combo
- Aguarde 1-2 segundos entre mudanças na tecla do combo
- Se travar, clique em "Reset" e configure novamente
- Não altere a tecla enquanto o combo estiver sendo executado
- Salve sempre com "Aceitar" após alterar a tecla

### Ordem de cliques confusa
- **Use o botão "Reset"** para limpar a ordem
- Marque os checkboxes novamente na ordem desejada
- Verifique no console a mensagem "Ordem atual do combo"

## 📝 Exemplos Práticos

### Combo para MOBA (Dota - Legion Commander) - Por Ordem de Clique
```
1º Clique: Checkbox do item "1" (BKB)
2º Clique: Checkbox do item "2" (Blink Dagger)
3º Clique: Checkbox do skill "Q" (Overwhelming Odds)
4º Clique: Checkbox do skill "W" (Press the Attack)
5º Clique: Checkbox do skill "R" (Duel)
Resultado: 1 → 2 → Q → W → R
```

### Combo Personalizado - Iniciação Complexa
```
1º Clique: Item "4" (Armlet toggle)
2º Clique: Skill "W" (Buff)
3º Clique: Item "1" (BKB)
4º Clique: Item "2" (Blink)
5º Clique: Skill "Q" (Nuke)
6º Clique: Skill "R" (Ultimate)
Resultado: 4 → W → 1 → 2 → Q → R
```

### Como Reorganizar a Ordem
```
Para mudar a ordem:
1. Desmarque TODOS os checkboxes
2. Marque novamente na ordem desejada
3. O sistema automaticamente atualiza a sequência
4. Clique em "Aceitar" para salvar
```

## 🔒 Considerações de Segurança

- Use apenas em jogos que permitem automação
- Respeite os termos de serviço dos jogos
- Teste em ambiente seguro antes do uso
- A aplicação funciona apenas quando tem foco

## 📞 Suporte

Para dúvidas, problemas ou sugestões:
- Abra uma issue no repositório
- Use o botão "Desenvolvedor" na aplicação
- Contribua com melhorias via pull request

---

**Versão**: 1.0  
**Desenvolvido em**: Python + PyQt5  
**Compatibilidade**: Windows, Linux, macOS
