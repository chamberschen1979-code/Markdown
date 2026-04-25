#!/usr/bin/env python3

import os
from document_cleaner import extract_text_from_file, clean_level1, clean_level2, clean_level3, verify_content, annotate_differences

# 创建一个模拟的大文档
def create_large_test_document():
    """创建一个模拟的大文档，包含多个章节和表格"""
    content = []
    
    # 添加标题
    content.append("# 鼎和能源板块承保政策")
    content.append("")
    
    # 添加多个章节
    for i in range(1, 6):
        content.append(f"## 第{i}章 电源")
        content.append("")
        
        # 添加章节内容
        content.append(f"### {i}.1 承保条件")
        content.append("")
        content.append(f"本章节介绍第{i}章的承保条件。")
        content.append("")
        
        # 添加表格
        content.append("| 风险等级 | 费率 | 免赔额 |")
        content.append("|---------|------|--------|")
        for j in range(1, 11):
            content.append(f"| 等级{j} | {j*5}% | {j*10}万元 |")
        content.append("")
        
        # 添加更多内容
        content.append(f"### {i}.2 核保标准")
        content.append("")
        content.append("核保标准如下：")
        content.append("")
        for j in range(1, 11):
            content.append(f"- 标准{j}：风险评级不超过{j*10}%，保额不超过{j*100}万元")
        content.append("")
    
    # 保存为测试文件
    with open("test_large.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(content))
    
    return "test_large.txt"

print("=== 大文档清洗测试 ===")

# 创建测试文件
test_file = create_large_test_document()
print(f"创建测试文件：{test_file}")

# 1. 测试物理提取
print("\n1. 测试物理提取...")
try:
    raw_text = extract_text_from_file(test_file)
    print(f"成功提取文本，长度：{len(raw_text)} 字符")
    # 统计关键词数量
    keyword_count = raw_text.count('%')
    print(f"原文中'%'的数量：{keyword_count}")
except Exception as e:
    print(f"提取失败：{str(e)}")

# 2. 测试级别一清洗
print("\n2. 测试级别一：无损/物理清洗...")
try:
    cleaned_level1 = clean_level1(raw_text)
    print(f"成功清洗，长度：{len(cleaned_level1)} 字符")
    # 统计关键词数量
    keyword_count_level1 = cleaned_level1.count('%')
    print(f"级别一清洗后'%'的数量：{keyword_count_level1}")
except Exception as e:
    print(f"清洗失败：{str(e)}")

# 3. 测试级别二清洗
print("\n3. 测试级别二：结构化清洗...")
try:
    cleaned_level2 = clean_level2(raw_text)
    print(f"成功清洗，长度：{len(cleaned_level2)} 字符")
    # 统计关键词数量
    keyword_count_level2 = cleaned_level2.count('%')
    print(f"级别二清洗后'%'的数量：{keyword_count_level2}")
except Exception as e:
    print(f"清洗失败：{str(e)}")

# 4. 测试级别三清洗
print("\n4. 测试级别三：精粹/观点清洗...")
try:
    cleaned_level3 = clean_level3(raw_text)
    print(f"成功清洗，长度：{len(cleaned_level3)} 字符")
    # 统计关键词数量
    keyword_count_level3 = cleaned_level3.count('%')
    print(f"级别三清洗后'%'的数量：{keyword_count_level3}")
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
        for issue in verification_result.get("severe_issues", []):
            print(f"  - ❌ {issue}")
    
    verification_result = verify_content(raw_text, cleaned_level2)
    if verification_result["pass"]:
        print("✅ 级别二清洗：内容校验通过，无删减")
    else:
        print("⚠️ 级别二清洗：内容校验发现问题：")
        for issue in verification_result["issues"]:
            print(f"  - {issue}")
        for issue in verification_result.get("severe_issues", []):
            print(f"  - ❌ {issue}")
    
    # 级别三清洗会提取核心观点，所以可能会有删减，这是正常的
    verification_result = verify_content(raw_text, cleaned_level3)
    if verification_result["pass"]:
        print("✅ 级别三清洗：内容校验通过")
    else:
        print("⚠️ 级别三清洗：内容校验发现问题（这是正常的，因为级别三会提取核心观点）：")
        for issue in verification_result["issues"]:
            print(f"  - {issue}")
        for issue in verification_result.get("severe_issues", []):
            print(f"  - ❌ {issue}")
except Exception as e:
    print(f"校验失败：{str(e)}")

# 6. 测试差异标注
print("\n6. 测试差异标注...")
try:
    annotated_text = annotate_differences(raw_text, cleaned_level2)
    print(f"成功生成标注版文本，长度：{len(annotated_text)} 字符")
    # 保存标注版文本
    with open("test_large_annotated.md", "w", encoding="utf-8") as f:
        f.write(annotated_text)
    print("标注版文本已保存为 test_large_annotated.md")
except Exception as e:
    print(f"标注失败：{str(e)}")

print("\n=== 测试完成 ===")
