#!/usr/bin/env python3

from document_cleaner import chunk_text, remove_duplicates

# 测试文本，包含各种标题格式
test_text = """第一章 总则
一、目的
（一）为规范公司运营
1. 提高管理效率
（1）建立健全制度
① 制定相关规定

第二章 职责
二、部门职责
（二）各部门职责
2. 具体职责
（2）实施细则
② 操作流程
"""

print("=== 标题格式测试 ===")

# 测试分块
print("\n1. 测试分块功能...")
try:
    chunks = chunk_text(test_text, chunk_size=500)
    print(f"成功分块，共 {len(chunks)} 块")
    
    for i, chunk in enumerate(chunks):
        print(f"\n块 {i+1}（长度：{len(chunk)} 字符）：")
        print("=" * 50)
        print(chunk)
        print("=" * 50)
        
except Exception as e:
    print(f"分块测试失败：{str(e)}")

# 测试去重
print("\n2. 测试去重功能...")
try:
    # 创建包含重复内容的测试文本
    duplicate_text = test_text + "\n" + test_text
    print(f"原始文本长度：{len(duplicate_text)} 字符")
    
    cleaned_text = remove_duplicates(duplicate_text)
    print(f"去重后长度：{len(cleaned_text)} 字符")
    print("\n去重后结果：")
    print("=" * 70)
    print(cleaned_text)
    print("=" * 70)
    
    # 验证各种标题格式是否保留
    print("\n3. 验证标题格式保留...")
    title_formats = ["第一章", "一、", "（一）", "1.", "（1）", "①", "第二章", "二、", "（二）", "2.", "（2）", "②"]
    for fmt in title_formats:
        if fmt in cleaned_text:
            print(f"✅ 保留了格式：{fmt}")
        else:
            print(f"⚠️ 丢失了格式：{fmt}")
            
except Exception as e:
    print(f"去重测试失败：{str(e)}")

print("\n=== 测试完成 ===")
