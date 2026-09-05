#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""芙宁娜卡压测：针对 design.md 三铁律的 4 探针 × 2 模型。"""
import json, urllib.request, sys

KEY = open('/home/ubuntu/.openclaw/workspace/.secrets/openrouter-test-o5.key').read().strip()
card = json.load(open('furina_v1.json', encoding='utf-8'))['data']

SYS = card['description'] + '\n\n' + card['personality'] + '\n\n【场景】' + card['scenario']
SYS += '\n\n【示例对话（仅学习语气与格式，勿复述内容）】\n' + card['mes_example']

def lorebook_hit(text):
    return '\n'.join(e['content'] for e in card['character_book']['entries']
                     if any(k in text for k in e['keys']))

def call(model, msgs, max_tokens=700):
    body = json.dumps({"model": model, "messages": msgs, "max_tokens": max_tokens,
                       "temperature": 0.9}).encode()
    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=body,
        headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
    # GLM-5.3-flash 默认思考模式可能吞掉 max_tokens 导致 content=None：重试至多 3 次
    for attempt in range(3):
        r = json.load(urllib.request.urlopen(req, timeout=180))
        c = r['choices'][0]['message'].get('content')
        if c and c.strip():
            return c
    return c or '(empty after retry)'

MODELS = ['z-ai/glm-5.3-flash', 'deepseek/deepseek-v4-flash-0731']

# 探针定义：P1 真心夸奖(触发①)+第二轮点破(铁律3)；P2 中性话题(不得乱触发)；P3 五百年(触发②)；P4 要走(触发⑤)
PROBES = {
    'P1_夸奖与点破': [
        [{'role':'user','content':'*把一杯刚买的热可可放到她面前* 说真的，刚才你讲新戏构想的时候，整个人都在发光。不是舞台上那种光，是你自己的。'}],
    ],
    'P2_中性话题': [
        [{'role':'user','content':'最近枫丹廷有什么热闹？'}],
    ],
    'P3_五百年': [
        [{'role':'user','content':'有时候我会想，那五百年，你是一个人怎么撑过来的。'}],
    ],
    'P4_要走': [
        [{'role':'user','content':'*看了看窗外的天色* 差不多了，我得回旅馆了，明天一早还要赶路。'}],
    ],
}

# P1 追加第二轮：点破
FOLLOWUP = {'P1_夸奖与点破': '你刚才那句话很真诚啊，一点都不像平时表演的样子。'}

results = {}
for name, turns in PROBES.items():
    for model in MODELS:
        short = model.split('/')[-1]
        msgs = [{'role':'system','content': SYS}]
        # 场景上下文注入 lorebook（按开场首条 user 消息关键词命中）
        lb = lorebook_hit(turns[0][0]['content'] + ' 茶会 排练 芙宁娜')
        if lb: msgs[0]['content'] += '\n\n【相关设定】' + lb
        key = f'{name}@{short}'
        try:
            for t in turns:
                msgs += t
                a1 = call(model, msgs)
                msgs.append({'role':'assistant','content':a1})
            if name in FOLLOWUP:
                msgs.append({'role':'user','content':FOLLOWUP[name]})
                a2 = call(model, msgs)
                msgs.append({'role':'assistant','content':a2})
            results[key] = '\n'.join(m['content'] for m in msgs[1:] if m['role']=='assistant')
            print(f'== {key} OK ==')
        except Exception as e:
            results[key] = f'ERROR: {e}'
            print(f'== {key} FAIL: {e} ==')

with open('stress_results.md','w',encoding='utf-8') as f:
    for k,v in results.items():
        f.write(f'\n\n===== {k} =====\n{v}\n')
print('done ->', 'stress_results.md')
