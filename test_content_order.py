#!/usr/bin/env python3

from document_cleaner import clean_with_ai, chunk_text

# 模拟文档内容，包含用户反馈的章节结构
test_text = """第一章 电源
第一节 企财险
一、财产基本险
（一）一类承保业务
通用情形：过往三年两率和不超80%

（二）二类承保业务
本次承保政策中未列明的险种及风险参照综合篇...

第四章 储能
第四节 信用保证保险
一、工程建设类保证险
南方电网作为投保人，为其下属企业的工程建设项目提供保证保险

二、农民工工资支付保证险
保障农民工工资按时足额支付
"""

print("=== 内容顺序测试 ===")

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

# 测试清洗（模拟模式）
print("\n2. 测试清洗功能...")
try:
    # 模拟AI清洗，直接使用原始文本
    from document_cleaner import configure_api
    # 配置API（使用假的API key）
    configure_api("test_api_key")
    
    # 模拟clean_with_ai函数的处理逻辑
    chunks = chunk_text(test_text, chunk_size=500)
    cleaned_chunks = chunks  # 直接使用原始块
    
    # 拼接结果
    final_result = cleaned_chunks[0]
    for i in range(1, len(cleaned_chunks)):
        current_chunk = cleaned_chunks[i]
        # 直接拼接，确保内容完整
        final_result += "\n" + current_chunk
    
    # 后处理：仅删除连续的完全重复行
    from document_cleaner import remove_duplicates
    final_result = remove_duplicates(final_result)
    
    print("清洗后结果：")
    print("=" * 70)
    print(final_result)
    print("=" * 70)
    
    # 验证内容顺序
    print("\n3. 验证内容顺序...")
    if "第一章 电源" in final_result:
        print("✅ 包含第一章")
    if "第一节 企财险" in final_result:
        print("✅ 包含第一节")
    if "第四章 储能" in final_result:
        print("✅ 包含第四章")
    if "第四节 信用保证保险" in final_result:
        print("✅ 包含第四节")
    
    # 验证章节顺序
    chapter_order = ["第一章 电源", "第一节 企财险", "第四章 储能", "第四节 信用保证保险"]
    positions = []
    for item in chapter_order:
        pos = final_result.find(item)
        if pos != -1:
            positions.append(pos)
        else:
            positions.append(float('inf'))
    
    if positions == sorted(positions):
        print("✅ 章节顺序正确")
    else:
        print("⚠️ 章节顺序错误")
    
    # 验证内容是否重复
    print("\n4. 验证内容重复...")
    test_phrases = ["本次承保政策中未列明的险种及风险参照综合篇", "南方电网作为投保人"]
    for phrase in test_phrases:
        count = final_result.count(phrase)
        print(f"'{phrase}'出现次数：{count}")
        if count == 1:
            print("✅ 内容唯一")
        else:
            print("⚠️ 内容重复")
            
except Exception as e:
    print(f"清洗测试失败：{str(e)}")

print("\n=== 测试完成 ===")
