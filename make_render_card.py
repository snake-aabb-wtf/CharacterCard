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

==================== 渲染层（酒馆助手 TavernHelper · 完整 HTML 面板） ====================
本卡带一个【完整 HTML 交互面板】（酒馆助手 iframe 渲染）。

【面板输出规则（最高优先）】【每一轮世界模拟/修改后的回复，结尾都必须输出一次完整面板 HTML】：
面板分为【世界状态 HUD】+【修改器指令条】两部分，都是一个包在 ```html 代码块里的完整网页。
【开场白（首条回复）】也输出一次完整面板。
【面板 HTML 用模板(见下文)，你只需把 __MODE__/__SCENE__/__TIME__/__WEATHER__/__LOC__/__CHAR__/__EVENT__ 这 7 个占位符替换成当前世界最新状态，其余代码【一字不改、原样照抄】】。

【正确做法】
- 在回复【正文叙述结束后】，换行输出一个代码块，内容为：
```html
<HTML 模板，7 个占位符填成最新世界状态，其余原样>
```
- HTML 模板（完整，含 <body></body>；只改 __XX__ 占位符，其余不动）：
<FULL_PANEL_TEMPLATE>

【关键约束】
- 【每一轮都要输出这个完整 HTML 面板】——不要省略、不要精简、不要只输出 HUD 文本、不要改 HTML 结构。堆叠面板是预期行为，不要担心重复。
- 7 个占位符的填法：
  · __MODE__ → 【当前模式，必须准确】未初始化=A；世界模拟=B；修改器=C。
  · 【模式切换时必须在 HUD 里同步更新 __MODE__】：玩家说「开启修改器模式」→ 该轮 HUD 的 __MODE__ 必须填 C；说「关闭修改器」→ 填回 B（或当前所处）。【模式变了但 HUD 还是旧模式 = 严重错误】，改指令能否使用由面板根据 __MODE__ 判定，填错会导致面板误判。
  · __SCENE__ → 当前场景一句话（如：边境村庄·清晨）
  · __TIME__ → 当前时间（如：第1天·卯时）
  · __WEATHER__ → 当前天气（如：晴）
  · __LOC__ → 当前地点（如：村口铁匠铺）
  · __CHAR__ → 主角状态（如：疲惫·铜币×5）
  · __EVENT__ → 当前正在/即将发生的事件（如：挖出会发光的东西）
  · 没有对应信息就填「—」（不要留空占位符）
- 面板只用于展示；修改器指令条由前端自行拼装 & 指令发送，你收到的仍是标准 & 指令，按「指令集」正常执行。【模式前置纪律不变】：未开启修改器模式（模式C）时，即使指令来自前端同样拒绝并提示。
- 【严禁】把面板代码当正文叙述、开戏接戏；面板是独立代码块，永远放在正文之后。
"""

render_instruction = render_instruction.replace('<FULL_PANEL_TEMPLATE>', panel_html)

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
# 关键：酒馆助手只渲染「包在 Markdown 代码块里 + 含 <body></body>」的 HTML，所以必须用 ``` html 包裹
panel_block = "\n\n```html\n" + panel_html + "\n```\n"
data['first_mes'] = data['first_mes'].replace('<render_panel_placeholder>', panel_block)

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
