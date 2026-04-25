#!/usr/bin/env python3

from document_cleaner import remove_duplicates, extract_text_from_file

# 测试文件路径
test_file = "test_duplicate.txt"

print("=== 重复内容去重测试 ===")

# 读取测试文件
print("\n1. 读取测试文件...")
try:
    raw_text = extract_text_from_file(test_file)
    print(f"成功读取文本，长度：{len(raw_text)} 字符")
    print("\n原始内容：")
    print(raw_text)
except Exception as e:
    print(f"读取失败：{str(e)}")

# 测试去重
print("\n2. 测试去重...")
try:
    cleaned_text = remove_duplicates(raw_text)
    print(f"成功去重，长度：{len(cleaned_text)} 字符")
    print("\n去重后内容：")
    print(cleaned_text)
    
    # 验证重复内容是否被删除
    if "2.风力发电" in cleaned_text:
        # 检查重复的2.风力发电是否只出现一次
        count = cleaned_text.count("2.风力发电")
        print(f"\n3. 验证结果：")
        print(f"'2.风力发电'出现次数：{count}")
        if count == 1:
            print("✅ 重复内容已成功删除，只保留一次")
        else:
            print(f"⚠️ 重复内容未完全删除，出现 {count} 次")
    
    # 检查其他序号是否只出现一次
    for i in range(2, 6):
        count = cleaned_text.count(f"{i}.")
        print(f"'{i}.'出现次数：{count}")
        if count > 1:
            print(f"⚠️ 序号 {i} 重复出现")
        else:
            print(f"✅ 序号 {i} 只出现一次")
            
except Exception as e:
    print(f"去重失败：{str(e)}")

print("\n=== 测试完成 ===")
