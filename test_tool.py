#!/usr/bin/env python3

import os
from document_cleaner import extract_text_from_file, clean_level1, clean_level2, clean_level3, verify_content

# 测试文件路径
test_file = "test_long.txt"

print("=== 文档清洗工具测试 ===")

# 1. 测试物理提取
print("\n1. 测试物理提取...")
try:
    raw_text = extract_text_from_file(test_file)
    print(f"成功提取文本，长度：{len(raw_text)} 字符")
except Exception as e:
    print(f"提取失败：{str(e)}")

# 2. 测试级别一清洗
print("\n2. 测试级别一：无损/物理清洗...")
try:
    cleaned_level1 = clean_level1(raw_text)
    print(f"成功清洗，长度：{len(cleaned_level1)} 字符")
except Exception as e:
    print(f"清洗失败：{str(e)}")

# 3. 测试级别二清洗
print("\n3. 测试级别二：结构化清洗...")
try:
    cleaned_level2 = clean_level2(raw_text)
    print(f"成功清洗，长度：{len(cleaned_level2)} 字符")
except Exception as e:
    print(f"清洗失败：{str(e)}")

# 4. 测试级别三清洗
print("\n4. 测试级别三：精粹/观点清洗...")
try:
    cleaned_level3 = clean_level3(raw_text)
    print(f"成功清洗，长度：{len(cleaned_level3)} 字符")
except Exception as e:
    print(f"清洗失败：{str(e)}")

# 5. 测试对账校验
print("\n5. 测试对账校验...")
try:
    verification_result = verify_content(raw_text, cleaned_level1)
    if verification_result["pass"]:
        print("✅ 级别一清洗：内容校验通过，无删减")
    else:
        print("⚠️ 级别一清洗：内容校验发现问题：")
        for issue in verification_result["issues"]:
            print(f"  - {issue}")
    
    verification_result = verify_content(raw_text, cleaned_level2)
    if verification_result["pass"]:
        print("✅ 级别二清洗：内容校验通过，无删减")
    else:
        print("⚠️ 级别二清洗：内容校验发现问题：")
        for issue in verification_result["issues"]:
            print(f"  - {issue}")
    
    # 级别三清洗会提取核心观点，所以可能会有删减，这是正常的
    verification_result = verify_content(raw_text, cleaned_level3)
    if verification_result["pass"]:
        print("✅ 级别三清洗：内容校验通过")
    else:
        print("⚠️ 级别三清洗：内容校验发现问题（这是正常的，因为级别三会提取核心观点）：")
        for issue in verification_result["issues"]:
            print(f"  - {issue}")
except Exception as e:
    print(f"校验失败：{str(e)}")

print("\n=== 测试完成 ===")