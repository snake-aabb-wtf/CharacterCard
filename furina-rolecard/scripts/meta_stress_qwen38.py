#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""芙宁娜「元」卡压测：针对元版特有机制的探针 × 2 模型。
探针组：
  P1 默认开局（全空「开始」→ 应锁定默认：终幕后+旅行者+茶会）
  P2 五百年间锁定（同句设定+开始 → 应锁定并切入神明态）
  P3 洪水恐惧触发（延续P2，下雨 → 应漏恐惧+神明威严找补）
  P4 未来信息差（延续P2，告知未来 → 她不得表现得知晓未来）
  P5 期望预设（延续P2，代写她反应 → 应出元叙述区分标注）
  P6 终幕后点破（默认时代，夸奖→点破 → 双轨铁律3）
输出：ROOT/tests/meta_stress_results_qwen38flash.md
"""
import json, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = open('/home/ubuntu/.openclaw/workspace/.secrets/openrouter-test-o5.key').read().strip()
card = json.load(open(ROOT / 'furina_meta.json', encoding='utf-8'))['data']

SYS = card['description'] + '\n\n' + card['personality'] + '\n\n【场景】' + card['scenario']
SYS += '\n\n【示例对话（仅学习语气与格式，勿复述内容）】\n' + card['mes_example']

ENTRIES = card['character_book']['entries']
CONSTANT = '\n'.join(e['content'] for e in ENTRIES if e.get('constant'))

def lorebook_hit(text):
    trig = '\n'.join(e['content'] for e in ENTRIES
                     if not e.get('constant') and any(k in text for k in e['keys']))
    parts = [p for p in (CONSTANT, trig) if p]
    return '\n\n【相关设定】' + '\n'.join(parts) if parts else ''

def call(model, msgs, max_tokens=8000):
    body = json.dumps({"model": model, "messages": msgs, "max_tokens": max_tokens,
                       "temperature": 0.9}).encode()
    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=body,
        headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
    for attempt in range(3):
        r = json.load(urllib.request.urlopen(req, timeout=240))
        c = r['choices'][0]['message'].get('content')
        if c and c.strip():
            return c
    return c or '(empty after retry)'

MODELS = ['qwen/qwen3.8-flash']

# 五百年间锁定开场（P2-P5 共用上下文）
ERA500_INIT = '时代选五百年间，我是刚到枫丹的外邦旅行者，第一次见到水神。场景：某场审判结束后，我混进了欧庇克莱歌剧院的后台。开始'
# 默认时代（终幕后）P6 上下文
DEFAULT_INIT = '开始'

PROBES = {
    'P1_默认开局@独立': {'init': DEFAULT_INIT, 'turns': []},
    'P2_五百年间锁定@独立': {'init': ERA500_INIT, 'turns': []},
    'P3_洪水触发@续P2': {'init': ERA500_INIT, 'turns': ['*这时，窗外下起了瓢泼大雨，雨点砸在后台的天窗上。*']},
    'P4_未来信息差@续P2': {'init': ERA500_INIT, 'turns': ['*我压低声音* 别怕。我知道结局——五百年后预言会化解，枫丹没有人死，而你，会以人类的身份活着。']},
    'P5_期望预设@续P2': {'init': ERA500_INIT, 'turns': ['*我走上前想扶住她的手臂* 她愣了一下，然后红着脸答应跟我去喝茶。']},
    'P6_终幕后点破@独立': {'init': DEFAULT_INIT, 'turns': ['*把一杯刚买的热可可放到她面前* 说真的，刚才你讲新戏构想的时候，整个人都在发光。不是舞台上那种光，是你自己的。'], 'followup': '你刚才那句话很真诚啊，一点都不像平时表演的样子。'},
}

results = {}
for name, spec in PROBES.items():
    for model in MODELS:
        short = model.split('/')[-1]
        key = f'{name}@{short}'
        try:
            msgs = [{'role': 'system', 'content': SYS + lorebook_hit(spec['init'])}]
            msgs.append({'role': 'user', 'content': spec['init']})
            outs = []
            a = call(model, msgs); msgs.append({'role':'assistant','content':a}); outs.append(a)
            for t in spec.get('turns', []):
                lb = lorebook_hit(t)
                if lb: msgs[0]['content'] += lb  # 追加触发条目
                msgs.append({'role': 'user', 'content': t})
                a = call(model, msgs); msgs.append({'role':'assistant','content':a}); outs.append(a)
            if spec.get('followup'):
                msgs.append({'role': 'user', 'content': spec['followup']})
                a = call(model, msgs); outs.append(a)
            results[key] = '\n\n---\n\n'.join(outs)
            print(f'== {key} OK ==', flush=True)
        except Exception as e:
            results[key] = f'ERROR: {e}'
            print(f'== {key} FAIL: {e} ==', flush=True)

out = ROOT / 'tests' / 'meta_stress_results_qwen38flash.md'
out.parent.mkdir(exist_ok=True)
with open(out, 'w', encoding='utf-8') as f:
    f.write('# 芙宁娜「元」卡压测结果（2026-09-06，双模型，max_tokens=8000，temp=0.9）\n')
    for k, v in results.items():
        f.write(f'\n\n===== {k} =====\n{v}\n')
print('done ->', out)
