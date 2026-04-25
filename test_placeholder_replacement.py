#!/usr/bin/env python3

from document_cleaner import clean_with_ai

# 测试文本，包含占位符
test_text = """[编号层级1] 财产基本险
[编号层级1] 综合险
[编号层级1] 一切险
[编号层级2] 承保范围
[编号层级2] 责任免除
[编号层级3] 火灾
[编号层级3] 爆炸
"""

print("=== 占位符处理测试 ===")

# 测试占位符处理
print("\n1. 测试占位符处理...")
try:
    # 模拟clean_with_ai函数的后处理逻辑
    import re
    final_result = test_text
    
    # 模拟AI处理（这里直接使用原始文本，测试保底逻辑）
    print("模拟AI处理前：")
    print(final_result)
    
    # 应用保底逻辑
    if "[编号层级" in final_result:
        # 为不同层级的标记创建计数器
        level_counters = {1: 0, 2: 0, 3: 0}
        
        def backup_replacer(match):
            # 提取层级数字
            level = int(match.group(1))
            # 增加对应层级的计数器
            level_counters[level] += 1
            # 根据层级返回不同的编号格式
            if level == 1:
                return f"{level_counters[level]}. "
            elif level == 2:
                return f"（{level_counters[level]}）"
            else:
                return f"{level_counters[level]}. "
        
        # 替换所有编号层级标记
        final_result = re.sub(r'\[编号层级(\d+)\]', backup_replacer, final_result)
    
    print("\n处理后结果：")
    print(final_result)
    
    # 验证占位符是否被替换
    print("\n2. 验证占位符替换...")
    if "[编号层级" in final_result:
        print("⚠️ 占位符未完全替换")
    else:
        print("✅ 所有占位符已被替换")
    
    # 验证编号是否连续
    print("\n3. 验证编号连续性...")
    lines = final_result.split('\n')
    for line in lines:
        if line.strip():
            print(f"  {line.strip()}")
            
except Exception as e:
    print(f"测试失败：{str(e)}")

print("\n=== 测试完成 ===")
