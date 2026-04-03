# DESIGN_CONTEXT.md — Prospecta CRM
> Leia este arquivo antes de criar ou editar qualquer componente de UI.
> Ele define o design system completo, tokens, padrões e convenções do projeto.

---

## 1. Identidade Visual

**Produto:** Prospecta — Prospecting Suite  
**Tom:** Dark, profissional, orientado a dados. Sem brancos estridentes, sem pastéis. Energia de terminal + dashboard executivo.  
**Tipografia principal:** `Barlow` (corpo) + `Barlow Condensed` (display/headings grandes)  
**Importar no projeto:**
```css
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Barlow+Condensed:wght@600;700;800&display=swap');
```

---

## 2. Tokens CSS — `globals.css`

Cole estas variáveis no `:root` do seu `globals.css` ou `index.css`:

```css
:root {
  /* Brand */
  --pro-orange:       #E8593C;
  --pro-pink:         #C4185A;
  --pro-orange-light: #F07A5F;
  --pro-pink-light:   #D94075;
  --pro-orange-dark:  #B83C22;
  --pro-pink-dark:    #8F0E3F;

  /* Gradiente principal (use como background ou text clip) */
  --pro-grad: linear-gradient(135deg, #E8593C 0%, #C4185A 100%);
  --pro-grad-soft: linear-gradient(135deg, rgba(232,89,60,0.12) 0%, rgba(196,24,90,0.12) 100%);

  /* Superfícies (dark-first) */
  --pro-black:    #0D0D0D;   /* fundo da página */
  --pro-surface:  #161616;   /* sidebar, topbar */
  --pro-surface2: #1F1F1F;   /* cards, modais */
  --pro-surface3: #272727;   /* inputs, itens internos */

  /* Bordas */
  --pro-border:  rgba(255, 255, 255, 0.08);
  --pro-border2: rgba(255, 255, 255, 0.14);

  /* Texto */
  --pro-text:       #F0EEE9;
  --pro-muted:      rgba(240, 238, 233, 0.50);
  --pro-muted2:     rgba(240, 238, 233, 0.28);

  /* Semânticos */
  --pro-success: #4ade80;
  --pro-warning: #fbbf24;
  --pro-danger:  #f87171;
  --pro-info:    #60a5fa;
}
```

---

## 3. Tailwind — Extensões (`tailwind.config.ts`)

```ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans:      ['Barlow', 'sans-serif'],
        condensed: ['Barlow Condensed', 'sans-serif'],
      },
      colors: {
        brand: {
          orange:       '#E8593C',
          pink:         '#C4185A',
          'orange-light': '#F07A5F',
          'pink-light':   '#D94075',
          'orange-dark':  '#B83C22',
          'pink-dark':    '#8F0E3F',
        },
        surface: {
          black:   '#0D0D0D',
          DEFAULT: '#161616',
          2:       '#1F1F1F',
          3:       '#272727',
        },
        border: {
          DEFAULT: 'rgba(255,255,255,0.08)',
          strong:  'rgba(255,255,255,0.14)',
        },
        pro: {
          text:   '#F0EEE9',
          muted:  'rgba(240,238,233,0.50)',
          muted2: 'rgba(240,238,233,0.28)',
        },
      },
      backgroundImage: {
        'brand-grad':      'linear-gradient(135deg, #E8593C 0%, #C4185A 100%)',
        'brand-grad-soft': 'linear-gradient(135deg, rgba(232,89,60,0.12) 0%, rgba(196,24,90,0.12) 100%)',
      },
      borderRadius: {
        sm:  '6px',
        md:  '8px',
        lg:  '12px',
        xl:  '16px',
        '2xl': '20px',
      },
      fontSize: {
        eyebrow: ['10px', { letterSpacing: '0.12em', fontWeight: '700' }],
        label:   ['11px', { letterSpacing: '0.08em', fontWeight: '700' }],
      },
    },
  },
  plugins: [],
} satisfies Config
```

---

## 4. Layout Global

### Estrutura das telas
```
┌─────────────────────────────────────────────────────┐
│  Sidebar (200px fixo)  │  Main (flex-1)             │
│                        │  ┌──────────────────────┐  │
│  Logo Prospecta        │  │ Topbar (52px)         │  │
│  Nav Items             │  ├──────────────────────┤  │
│  ...                   │  │ Content (padding 24px)│  │
│  [Novo Prospecto btn]  │  └──────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Classes Tailwind para o shell:
```tsx
// App shell
<div className="flex h-screen bg-surface-black overflow-hidden">
  <Sidebar />
  <main className="flex-1 flex flex-col overflow-hidden bg-surface-black">
    <Topbar />
    <div className="flex-1 overflow-y-auto p-6">
      {children}
    </div>
  </main>
</div>
```

---

## 5. Componentes — Especificações

### 5.1 Sidebar
```tsx
// Largura: 200px | Fundo: var(--pro-surface) | Border-right: 0.5px var(--pro-border)
// Logo: "PRO" com gradiente brand, "SPECTA" branco — fonte Barlow Condensed 800
// Nav item ativo: bg rgba(232,89,60,0.12), texto #F07A5F
// Nav item hover: bg rgba(255,255,255,0.05)
// Botão "Novo Prospecto": width 100%, bg brand-grad, fonte 13px 700

className para nav item ativo:
"bg-[rgba(232,89,60,0.12)] text-[#F07A5F] rounded-lg"

className para nav item padrão:
"text-pro-muted hover:bg-white/5 hover:text-pro-text rounded-lg transition-colors"
```

### 5.2 Topbar
```tsx
// Altura: 52px | Fundo: var(--pro-surface) | Border-bottom: 0.5px var(--pro-border)
// Esquerda: eyebrow (10px uppercase tracking-widest muted) + título (Barlow Condensed 20px 700)
// Direita: status pill + ícones + avatar

// Status pill desconectado:
"flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 text-[11px] font-semibold"

// Status pill conectado:
"flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-500/10 text-green-400 text-[11px] font-semibold"

// Avatar:
"w-8 h-8 rounded-full bg-brand-grad flex items-center justify-content-center text-[11px] font-bold text-white"
```

### 5.3 Stat Cards
```tsx
// Fundo: var(--pro-surface2) | Border: 0.5px var(--pro-border) | Radius: 12px | Padding: 16px 18px
// Label: 11px uppercase tracking font-700 muted — com ícone à direita
// Valor: Barlow Condensed 32px 700 branco
// Delta: 12px — verde para positivo, vermelho para negativo

className card:
"bg-surface-2 border border-border rounded-xl p-4"

className valor com gradiente brand:
"font-condensed text-3xl font-bold bg-brand-grad bg-clip-text text-transparent"
```

### 5.4 Botões
```tsx
// PRIMARY — gradiente brand
"px-5 py-2.5 bg-brand-grad rounded-lg text-white text-sm font-bold
 flex items-center gap-1.5 hover:opacity-90 transition-opacity active:scale-[0.98]"

// SECONDARY — outline
"px-4 py-2.5 bg-transparent border border-border-strong rounded-lg
 text-pro-muted text-sm font-semibold hover:bg-white/5 transition-colors"

// GHOST — brand soft bg
"px-4 py-2.5 bg-brand-grad-soft border border-brand-orange/20 rounded-lg
 text-brand-orange-light text-sm font-semibold"

// DANGER
"px-4 py-2.5 bg-red-500/8 border border-red-500/20 rounded-lg
 text-red-400 text-sm font-semibold flex items-center gap-1.5"

// ICON (quadrado)
"w-8 h-8 rounded-lg bg-surface-3 border border-border flex items-center justify-center
 text-pro-muted hover:text-pro-text hover:border-border-strong transition-colors"
```

### 5.5 Inputs / Fields
```tsx
// Input padrão
"w-full px-3 py-2.5 bg-surface-3 border border-border-strong rounded-lg
 text-pro-text text-sm font-sans placeholder:text-pro-muted2
 focus:outline-none focus:border-brand-orange focus:ring-1 focus:ring-brand-orange/30
 transition-colors"

// Label do campo
"block text-[10px] font-bold tracking-widest uppercase text-pro-muted mb-1.5"

// Select
"px-3 py-2.5 bg-surface-2 border border-border-strong rounded-lg
 text-pro-muted text-sm appearance-none cursor-pointer"
```

### 5.6 Badges / Status Pills
```tsx
// Base
"inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold"

// Variantes:
success: "bg-green-400/12  text-green-400"
warning: "bg-yellow-400/12 text-yellow-400"
danger:  "bg-red-400/12    text-red-400"
brand:   "bg-brand-orange/12 text-brand-orange-light"
info:    "bg-blue-400/12   text-blue-400"
neutral: "bg-white/6       text-pro-muted"

// Com dot animado (status ao vivo):
<span className="w-1.5 h-1.5 rounded-full bg-current" />
```

### 5.7 Cards Genéricos
```tsx
// Card padrão
"bg-surface-2 border border-border rounded-xl p-[18px]"

// Card com accent (borda esquerda brand)
"bg-surface-2 border border-border border-l-2 border-l-brand-orange rounded-xl p-[18px]"

// Card dark (para stat cards dentro de telas escuras)
"bg-[#0a0a0a] border border-border rounded-lg p-3.5"
```

### 5.8 Tabelas de Dados
```tsx
// Container
"bg-surface-2 border border-border rounded-xl overflow-hidden"

// Thead th
"text-left px-3 py-2 text-[10px] font-bold tracking-widest uppercase
 text-pro-muted border-b border-border"

// Tbody td
"px-3 py-2.5 border-b border-white/[0.04] text-pro-text text-xs"

// Row hover
"hover:bg-white/[0.02] transition-colors"
```

### 5.9 Tabs (navegação interna)
```tsx
// Container
"flex border-b border-border mb-5"

// Tab item padrão
"flex items-center gap-2 px-4 py-2.5 text-sm font-semibold text-pro-muted
 cursor-pointer border-b-2 border-transparent -mb-px hover:text-pro-text transition-colors"

// Tab item ativo
"text-brand-orange-light border-b-2 border-brand-orange"
```

### 5.10 Toggle Switch
```tsx
// Track
"w-8 h-[18px] rounded-full relative transition-colors cursor-pointer"
// OFF: bg-white/10
// ON:  bg-brand-orange

// Thumb
"absolute w-3 h-3 bg-white rounded-full top-[3px] left-[3px] transition-transform shadow-sm"
// OFF: translate-x-0
// ON:  translate-x-[14px]
```

### 5.11 Terminal / Log Component
```tsx
// Fundo: #0a0a0a | Fonte: monospace | Texto: rgba(74,222,128,0.7)
// Header com "traffic light" dots (red/yellow/green 8px circles)
// Texto sucesso: #4ade80 | Texto erro: #f87171 | Destaque: #E8593C
// Cursor piscante: 7×12px bg-brand-orange animate-pulse

"bg-[#0a0a0a] border border-border rounded-xl p-4 font-mono text-[11px]"
```

### 5.12 Modais
```tsx
// Overlay
"fixed inset-0 bg-black/70 flex items-center justify-content-center z-50"

// Modal container
"bg-surface-2 border border-border-strong rounded-2xl w-full max-w-lg overflow-hidden"

// Header
"px-6 py-5 border-b border-border flex items-center justify-between"
// Título: Barlow Condensed 22px 700

// Body
"px-6 py-6"

// Footer
"px-6 py-4 border-t border-border flex items-center justify-end gap-2.5"
```

### 5.13 Progress Bars
```tsx
// Track
"h-[3px] bg-white/8 rounded-full overflow-hidden"

// Fill — gradiente brand
"h-full bg-brand-grad rounded-full transition-all"

// Variante info (azul)
"h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full"

// Variante purple
"h-full bg-gradient-to-r from-violet-700 to-violet-400 rounded-full"
```

---

## 6. Tipografia — Hierarquia

| Uso | Fonte | Tamanho | Peso | Classe Tailwind |
|-----|-------|---------|------|-----------------|
| Logo / Display | Barlow Condensed | 32–56px | 800 | `font-condensed text-5xl font-black` |
| Page title (topbar) | Barlow Condensed | 20px | 700 | `font-condensed text-xl font-bold` |
| Card title | Barlow Condensed | 22px | 700 | `font-condensed text-2xl font-bold` |
| Stat value | Barlow Condensed | 32px | 700 | `font-condensed text-3xl font-bold` |
| Subheading | Barlow | 14–16px | 600 | `text-sm font-semibold` |
| Body | Barlow | 13–14px | 400 | `text-sm` |
| Label campo | Barlow | 10px | 700 | `text-[10px] font-bold tracking-widest uppercase` |
| Eyebrow | Barlow | 10px | 700 | `text-[10px] font-bold tracking-[0.12em] uppercase` |
| Terminal / ID | Monospace | 11–12px | 400 | `font-mono text-xs` |

---

## 7. Espaçamento

| Token | Valor | Uso |
|-------|-------|-----|
| `gap-1.5` | 6px | Entre ícone e texto em badges/botões |
| `gap-2` | 8px | Entre elementos pequenos |
| `gap-3` | 12px | Entre cards numa grid |
| `gap-4` | 16px | Gap padrão de layout |
| `gap-5` | 20px | Entre seções de formulário |
| `p-3.5` | 14px | Padding de stat card compacto |
| `p-4`   | 16px | Padding padrão de card |
| `p-6`   | 24px | Padding da área de conteúdo |

---

## 8. Páginas do Sistema

| Rota | Componente | Descrição |
|------|-----------|-----------|
| `/` ou `/painel` | `PainelPage` | Dashboard com métricas, visão de leads, terminal de logs |
| `/google-maps` | `GoogleMapsPage` | Extrator com configuração, mapa ao vivo, terminal |
| `/facebook-ads` | `FacebookAdsPage` | Extrator de leads via ADS |
| `/leads` | `LeadsPage` | Tab "Leads" + tab "Google Sheets" |
| `/inbox` | `InboxPage` | Inbox Gmail com painel split |
| `/perfil` | `PerfilPage` | Dados do usuário + URL do backend |
| `/configuracoes` | `ConfiguracoesPage` | Config backend (URL + testar) |

---

## 9. Padrões de Componentes Reutilizáveis

Crie estes componentes em `src/components/ui/`:

```
src/
  components/
    ui/
      Sidebar.tsx          ← nav + logo + botão novo prospecto
      Topbar.tsx           ← eyebrow + título + status + avatar
      StatCard.tsx         ← label + valor + delta (props: label, value, delta?, icon?)
      Badge.tsx            ← variantes: success | warning | danger | brand | info | neutral
      Button.tsx           ← variantes: primary | secondary | ghost | danger | icon
      Input.tsx            ← com label + estado focus/error
      Toggle.tsx           ← switch on/off
      ProgressBar.tsx      ← com cor customizável
      Terminal.tsx         ← log ao vivo com cursor piscante
      Modal.tsx            ← overlay + container + header + footer
      DataTable.tsx        ← thead + tbody com row hover
      Tabs.tsx             ← tab list + tab item ativo/inativo
      StatusPill.tsx       ← connected | disconnected | idle | processing
```

---

## 10. Convenções de Código

- **Sempre dark mode first** — não há modo claro neste projeto
- **Gradiente brand como texto:** use `bg-brand-grad bg-clip-text text-transparent`
- **Bordas:** sempre `0.5px` — nunca `1px` para bordas de superfície
- **Sombras:** nenhuma exceto `ring` de focus nos inputs
- **Ícones:** Lucide React (`lucide-react`) com `size={16}` como padrão
- **Animações:** apenas `transition-colors`, `transition-opacity`, `active:scale-[0.98]`
- **Cursor piscante no terminal:** `animate-[blink_1s_step-end_infinite]`
- **Estado de loading:** skeleton com `animate-pulse bg-surface-3`
- **Sem rounded em bordas de um lado só** — `border-l-2` não combina com `rounded-lg`; use apenas se o card tiver borda em todos os lados

---

## 11. Recharts — Configuração Padrão

```tsx
// Cores dos gráficos (seguem brand)
const CHART_COLORS = {
  primary:   '#E8593C',
  secondary: '#C4185A',
  success:   '#4ade80',
  info:      '#60a5fa',
  muted:     'rgba(255,255,255,0.15)',
}

// Estilo padrão de Tooltip
const tooltipStyle = {
  backgroundColor: '#1F1F1F',
  border: '0.5px solid rgba(255,255,255,0.14)',
  borderRadius: '8px',
  color: '#F0EEE9',
  fontSize: '12px',
}

// CartesianGrid
<CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />

// Axes
<XAxis tick={{ fill: 'rgba(240,238,233,0.5)', fontSize: 11 }} axisLine={false} tickLine={false} />
<YAxis tick={{ fill: 'rgba(240,238,233,0.5)', fontSize: 11 }} axisLine={false} tickLine={false} />
```

---

## 12. Prompt Rápido para o Claude Code

Quando abrir o Claude Code no VS Code, cole este contexto no início da conversa:

```
Você está trabalhando no projeto Prospecta CRM.
Leia o arquivo DESIGN_CONTEXT.md na raiz do projeto antes de criar qualquer componente.

Stack: React 19 + Vite + TailwindCSS 4 + Zustand + react-router-dom 7
Backend: FastAPI + Supabase + Playwright

Regras obrigatórias:
1. Dark mode only — fundo base: #0D0D0D
2. Brand: gradiente linear-gradient(135deg, #E8593C, #C4185A)
3. Tipografia: Barlow (corpo) + Barlow Condensed (display/valores)
4. Bordas: sempre 0.5px, nunca 1px
5. Sem sombras (exceto focus ring em inputs)
6. Ícones: lucide-react size={16}
7. Componentes base em src/components/ui/
8. Siga os padrões de className do DESIGN_CONTEXT.md
```

---

*Última atualização: Abr 2026 — Prospecta Design System v1.0*
