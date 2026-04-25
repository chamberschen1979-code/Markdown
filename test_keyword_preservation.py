#!/usr/bin/env python3

from document_cleaner import remove_duplicates, verify_content

# 创建测试文本，包含重复的关键词内容
test_text = """风险等级：7.0%
保费：100万元
拒保条件：高风险职业

风险等级：7.0%
保费：100万元
拒保条件：高风险职业

2.风力发电
"鼎和保险风险云"系统中台风、暴雨、洪水等自然灾害的风险等级系数低于7.0（含）地区的陆上风电工程。

2.风力发电
"鼎和保险风险云"系统中台风、暴雨、洪水等自然灾害的风险等级系数低于7.0（含）地区的陆上风电工程。
"""

print("=== 关键词保留测试 ===")

# 测试去重
print("\n1. 测试去重...")
try:
    cleaned_text = remove_duplicates(test_text)
    print(f"成功去重，原始长度：{len(test_text)} 字符，去重后长度：{len(cleaned_text)} 字符")
    print("\n去重后内容：")
    print(cleaned_text)
    
    # 验证关键词保留情况
    print("\n2. 验证关键词保留...")
    verification_result = verify_content(test_text, cleaned_text)
    
    if verification_result["pass"]:
        print("✅ 关键词完全保留，无删减")
    else:
        print("⚠️ 关键词有删减：")
        for issue in verification_result["issues"]:
            print(f"  - {issue}")
        for issue in verification_result["severe_issues"]:
            print(f"  ⚠️ 严重问题：{issue}")
    
    # 打印关键词统计
    print("\n3. 关键词统计对比：")
    print("原始文本关键词数量：")
    for keyword, count in verification_result["original_counts"].items():
        print(f"  {keyword}: {count}")
    print("去重后文本关键词数量：")
    for keyword, count in verification_result["cleaned_counts"].items():
        print(f"  {keyword}: {count}")
    
    # 验证重复的关键词行是否被保留
    print("\n4. 验证重复关键词行保留情况：")
    percent_count = cleaned_text.count("7.0%")
    print(f"'7.0%'出现次数：{percent_count}")
    if percent_count >= 2:
        print("✅ 重复的关键词行被保留")
    else:
        print("⚠️ 重复的关键词行被删除")
        
    million_count = cleaned_text.count("100万元")
    print(f"'100万元'出现次数：{million_count}")
    if million_count >= 2:
        print("✅ 重复的关键词行被保留")
    else:
        print("⚠️ 重复的关键词行被删除")
        
except Exception as e:
    print(f"测试失败：{str(e)}")

print("\n=== 测试完成 ===")
