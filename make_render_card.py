#!/usr/bin/env python3
"""生成世界模拟器·渲染版角色卡：基于指令版原卡 + 追加渲染层指令 + 交互面板 HTML。
纯文本原卡不动，产出独立 world-simulator-render.json。
"""
import json, os, sys

BASE = os.path.join(os.path.dirname(__file__), 'world-simulator-rolecard', 'world-simulator-modifier-command.json')
OUT = os.path.join(os.path.dirname(__file__), 'world-simulator-rolecard', 'world-simulator-render.json')
PANEL = os.path.join(os.path.dirname(__file__), 'panel_template.html')

d = json.load(open(BASE, encoding='utf-8'))
data = d['data']

# ---- 1. 读取面板 HTML ----
panel_html = open(PANEL, encoding='utf-8').read()

# ---- 2. 渲染层指令（追加到 description 末尾）----
render_instruction = """

==================== 渲染层（酒馆助手 TavernHelper · 前端界面） ====================
本卡带一个【交互式前端面板】（由酒馆助手以 iframe 渲染），分两部分：
【A. 世界状态 HUD（顶栏）】
- 常驻显示：场景 / 时间 / 天气 / 地点 / 主角状态 / 当前事件。
- 【你必须在世界发生实质变化时（初始化完成、时间推进、天气变化、地点切换、主角状态改变、事件发生）输出一次状态面板更新】。
- 状态面板用 HTML 代码块输出，交给前端渲染，格式如下（必须含 <body></body> 才被识别渲染）：
```html
<body>
<script>
window.updateHUD({
  mode: 'B', scene: '边境村庄·清晨', time: '第1天·卯时', weather: '晴',
  loc: '村口铁匠铺', char: '疲惫·铜币×5', event: '北边矿场挖出会发光的东西'
});
</script>
</body>
```
- 【重要】：状态面板放在【回复末尾】独立代码块里；正文叙述照常写在面板之前。面板是给玩家看的世界 HUD，与正文不重复、不冲突。
- 未初始化（模式A）时 HUD 显示『（尚未初始化世界）』，不输出面板。

【B. 修改器指令条（底栏）】
- 面板自带一个下拉指令栏（26 条 & 指令全部内置）+ 输入框 + 发送按钮。
- 玩家点选指令、填入内容、点发送 → 前端自动拼成 `&指令 内容` 并作为玩家消息发给你。
- 你【收到的仍是标准的 & 前缀指令】，按上面「指令集」正常执行即可，前端不改变任何指令语义。
- 【模式前置纪律不变】：即使指令来自前端发送，未开启修改器模式（模式C）时【同样拒绝】并提示『修改器指令需要先「开启修改器模式」才能使用』。
- 前端面板仅负责把用户输入拼成 & 指令并发送，【不绕过、不改变】任一条指令的生效规则与前置纪律。
"""

data['description'] = data['description'].rstrip() + render_instruction

# ---- 3. 替换 first_mes 为带面板的开场 ----
data['first_mes'] = """（世界引擎已就绪 · 渲染版）

欢迎。这是带【交互面板】的世界模拟器：上方是实时世界状态 HUD，下方是修改器指令栏——点选指令、填内容、发送即可修改世界，全程不用手打指令前缀。

在你喊出「开始」之前，我们先完成初始化。请按以下清单告诉我设定（可逐项回复或一次性填充，留空的我自动补全）：

【1. 世界观】世界类型（科幻/奇幻/现代/末世/架空…）、时代风格、舞台规模
【2. 世界规则】有无超自然力量、科技水平、世界基调
【3. 背景与势力】生物/种族/势力/格局
【4. 初始人物】姓名、身份、外貌、能力与局限、目的、起点状态
【5. 时间起点】从哪个时刻/场景切入

填得差不多，对我说「开始」——世界即固化并开始运转。

💡 世界内任何时候说「开启修改器模式」打开修改器，然后直接用下方指令栏改世界；不带指令的发言照常游玩。

<render_panel_placeholder>"""

# 面板放 first_mes 末尾（渲染版开机即显示 HUD + 指令条）
data['first_mes'] = data['first_mes'].replace('<render_panel_placeholder>', panel_html)

# ---- 4. 元数据更新（区分渲染版）----
data['name'] = '世界模拟器·修改器(渲染版)'
data['creator_notes'] = data['creator_notes'] + ' 【渲染版】带酒馆助手(TavernHelper/JS-Slash-Runner)交互面板：世界HUD + 26指令下拉条（自动拼&指令发送）。依赖酒馆助手≥1.12.14+JS-Slash-Runner。游玩核心逻辑与指令版100%一致，仅叠加前端界面。'
data['tags'] = list(data['tags']) + ['render', 'iframe', 'tavernhelper', '交互面板']

# ---- 5. 输出 ----
json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('生成完成:', OUT)
print('name:', data['name'])
print('description 长度:', len(data['description']))
print('first_mes 长度:', len(data['first_mes']))
print('character_book entries:', len(data['character_book']['entries']))
