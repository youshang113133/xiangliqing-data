import json, re

# 读取原文件
with open('湘里情智营·客户决策_v2.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 解析客户数据 - 使用栈匹配括号
data_start = content.find('var customersData = [')
if data_start >= 0:
    bracket_count = 0
    found_start = False
    end_idx = -1
    for i in range(data_start + len('var customersData = '), len(content)):
        if content[i] == '[':
            bracket_count += 1
            found_start = True
        elif content[i] == ']':
            bracket_count -= 1
            if found_start and bracket_count == 0:
                end_idx = i + 1
                break
    
    if end_idx > 0:
        customers_json = content[data_start + len('var customersData = '):end_idx]
        customers = json.loads(customers_json)
        print(f'原始客户数: {len(customers)}')
        
        # 统计超期客户
        overdue = [c for c in customers if c.get('isOverdue')]
        print(f'超期客户数: {len(overdue)}')
        
        # A类核心客户保留所有
        important = [c for c in customers if c.get('level', '').startswith('A类')]
        print(f'A类客户数: {len(important)}')
        
        # 合并：超期客户 + A类客户（去重）
        keep_ids = set(c['id'] for c in overdue)
        keep_ids.update(c['id'] for c in important)
        
        simplified = [c for c in customers if c['id'] in keep_ids]
        print(f'精简后客户数: {len(simplified)}')
        
        # 精简字段
        slimmed = []
        for c in simplified:
            slimmed.append({
                'id': c.get('id', ''),
                'name': c.get('name', ''),
                'level': c.get('level', ''),
                'nextDate': c.get('nextDate', ''),
                'advice': c.get('advice', ''),
                'isOverdue': c.get('isOverdue', False),
                'warning': c.get('warning', ''),
            })
        
        new_data = json.dumps(slimmed, ensure_ascii=False)
        print(f'精简后数据大小: {len(new_data)/1024:.0f} KB')
        
        # 替换
        old_pattern = content[data_start:end_idx]
        content = content.replace(old_pattern, new_data)

# 删除产品数据 - 使用栈匹配
prod_start = content.find('var productsData = [')
if prod_start >= 0:
    bracket_count = 0
    found_start = False
    end_idx = -1
    for i in range(prod_start + len('var productsData = '), len(content)):
        if content[i] == '[':
            bracket_count += 1
            found_start = True
        elif content[i] == ']':
            bracket_count -= 1
            if found_start and bracket_count == 0:
                end_idx = i + 1
                break
    
    if end_idx > 0:
        content = content[:prod_start] + 'var productsData = [];' + content[end_idx:]
        print('已删除产品数据')

# 写入
with open('湘里情智营·客户决策_v2_simple.html', 'w', encoding='utf-8') as f:
    f.write(content)

import os
size = os.path.getsize('湘里情智营·客户决策_v2_simple.html')
print(f'最终文件大小: {size/1024/1024:.2f} MB')
