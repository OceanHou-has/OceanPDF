import json

# 加载DPS数据
with open('storage/parsed/9264v7t0/dps.json', 'r', encoding='utf-8') as f:
    dps = json.load(f)

# 加载parsed数据  
with open('storage/parsed/9264v7t0/dps.json', 'r', encoding='utf-8') as f:
    dps_data = json.load(f)

p0 = dps_data['raw']['pages'][0]
print(f'DPS Page 0:')
print(f'  width: {p0.get("width")}')
print(f'  height: {p0.get("height")}')

with open('storage/parsed/9264v7t0/parsed.json', 'r', encoding='utf-8') as f:
    parsed = json.load(f)

ps = parsed['pages'][0]['page_size']
print(f'\nParsed Page 0:')
print(f'  width: {ps["width"]}')
print(f'  height: {ps["height"]}')

if p0.get('width'):
    scale = ps['width'] / p0['width']
    print(f'\nScale factor: {scale:.6f}')
    print(f'PDF宽度 / DPS宽度 = {ps["width"]} / {p0["width"]} = {scale:.6f}')
