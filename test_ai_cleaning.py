#!/usr/bin/env python3

import os
from document_cleaner import extract_text_from_file, clean_with_ai, verify_content

# 测试文件路径
test_file = "test_long.txt"

print("=== AI清洗功能测试 ===")

# 1. 测试物理提取
print("\n1. 测试物理提取...")
try:
    raw_text = extract_text_from_file(test_file)
    print(f"成功提取文本，长度：{len(raw_text)} 字符")
except Exception as e:
    print(f"提取失败：{str(e)}")

# 2. 测试AI清洗（模拟模式）
print("\n2. 测试AI清洗...")
try:
    # 使用模拟API调用，避免实际API请求
    # 直接调用remove_duplicates函数测试去重逻辑
    from document_cleaner import remove_duplicates
    cleaned_ai = remove_duplicates(raw_text)
    print(f"成功清洗，长度：{len(cleaned_ai)} 字符")
except Exception as e:
    print(f"清洗失败：{str(e)}")

# 3. 测试对账校验
print("\n3. 测试对账校验...")
try:
    verification_result = verify_content(raw_text, cleaned_ai)
    if verification_result["pass"]:
        print("✅ AI清洗：内容校验通过，无删减")
    else:
        print("⚠️ AI清洗：内容校验发现问题：")
        for issue in verification_result["issues"]:
            print(f"  - {issue}")
        for issue in verification_result["severe_issues"]:
            print(f"  ⚠️ 严重问题：{issue}")
    
    # 打印关键词统计
    print("\n4. 关键词统计对比：")
    print("原始文本关键词数量：")
    for keyword, count in verification_result["original_counts"].items():
        print(f"  {keyword}: {count}")
    print("清洗后文本关键词数量：")
    for keyword, count in verification_result["cleaned_counts"].items():
        print(f"  {keyword}: {count}")
except Exception as e:
    print(f"校验失败：{str(e)}")

print("\n=== 测试完成 ===")
