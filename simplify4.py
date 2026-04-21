import json, re

# 读取原文件
with open('湘里情智营·客户决策_v2.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f'原始文件大小: {len(content.encode())/1024/1024:.2f} MB')

# 解析客户数据
data_start = content.find('var customersData = [')
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

customers = json.loads(content[data_start + len('var customersData = '):end_idx])
print(f'原始客户数: {len(customers)}')

# 只保留超期客户（最重要！）
overdue = [c for c in customers if c.get('isOverdue')]
print(f'超期客户数: {len(overdue)}')

# 精简字段 - 只保留最核心的
slimmed = [{
    'id': c.get('id', ''),
    'name': c.get('name', ''),
    'level': c.get('level', ''),
    'nextDate': c.get('nextDate', ''),
    'advice': c.get('advice', ''),
    'isOverdue': c.get('isOverdue', False),
} for c in overdue]

new_data = json.dumps(slimmed, ensure_ascii=False)
print(f'精简后数据大小: {len(new_data)/1024:.0f} KB')

# 替换客户数据
content = content[:data_start] + 'var customersData = ' + new_data + ';' + content[end_idx:]

# 删除产品数据
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
    content = content[:prod_start] + 'var productsData = [];' + content[end_idx:]

# 写入
with open('湘里情智营·客户决策_simple.html', 'w', encoding='utf-8') as f:
    f.write(content)

size = os.path.getsize('湘里情智营·客户决策_simple.html')
print(f'最终文件大小: {size/1024/1024:.2f} MB')
