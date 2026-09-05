#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紫色散文对比：芙宁娜卡 v1.2 同输入对跑 deepseek-r1 vs glm-5.3-flash。"""
import json, urllib.request, re

KEY = open('/home/ubuntu/.openclaw/workspace/.secrets/openrouter-test-o5.key').read().strip()
card = json.load(open('furina_v1.json', encoding='utf-8'))['data']
lb = '\n\n【相关设定】' + '\n'.join(e['content'] for e in card['character_book']['entries'])
SYS = (card['description'] + '\n\n' + card['personality'] + '\n\n【场景】' + card['scenario']
       + '\n\n【示例对话（仅学习语气与格式，勿复述内容）】\n' + card['mes_example'] + lb)

MSGS = [
    {'role': 'system', 'content': SYS},
    {'role': 'assistant', 'content': card['first_mes']},
    {'role': 'user', 'content': '*雨停了。*走，去海边。你上次念叨的幽光星星，我打听到月海有一片特别亮的。'},
]

def call(model, timeout=600):
    body = json.dumps({'model': model, 'messages': MSGS, 'max_tokens': 8000,
                       'temperature': 0.9}).encode()
    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=body,
        headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    m = r['choices'][0]['message']
    return (m.get('content') or ''), r.get('usage', {})

def pick_r1():
    req = urllib.request.Request('https://openrouter.ai/api/v1/models',
        headers={'Authorization': 'Bearer ' + KEY})
    models = json.load(urllib.request.urlopen(req, timeout=60))['data']
    ids = [m['id'] for m in models]
    if 'deepseek/deepseek-r1' in ids:
        return 'deepseek/deepseek-r1'
    cands = [i for i in ids if 'deepseek' in i and 'r1' in i and 'distill' not in i]
    return cands[0] if cands else None

def metrics(t):
    n = len(t)
    dia = sum(len(s) for s in re.findall(r'“[^”]*”', t))
    met = len(re.findall(r'像|仿佛|宛如|如同|好像', t))
    sents = [s for s in re.split(r'[。！？…]', t) if s.strip()]
    avg = round(n / max(len(sents), 1), 1)
    return f'chars={n} 对白占比={dia*100//max(n,1)}% 比喻命中={met} 平均句长={avg}'

out = {}
r1 = pick_r1()
print('R1 选用:', r1, flush=True)
for model in ([r1] if r1 else []) + ['z-ai/glm-5.3-flash']:
    short = model.split('/')[-1]
    for attempt in range(3):
        try:
            c, u = call(model)
            if c.strip():
                out[short] = (c, u)
                det = u.get('completion_tokens_details', {})
                print(f'[{short}] OK 完成tokens={u.get("completion_tokens")} 思考tokens={det.get("reasoning_tokens")} 成本=${u.get("cost")}', flush=True)
                break
            print(f'[{short}] 空响应，重试 {attempt+1}', flush=True)
        except Exception as e:
            print(f'[{short}] ERR: {e}', flush=True)

for short, (c, u) in out.items():
    fn = f'prose_{short.split("-")[0]}.md'
    open(fn, 'w', encoding='utf-8').write(c)
    print(f'== {short} ==', metrics(c))
    print('saved ->', fn, flush=True)
