import re

def apply_md_formatting(text, level1_pattern, level2_pattern, level3_pattern, level4_pattern):
    """
    根据用户配置的正则表达式为原文添加Markdown格式。
    已剥离所有硬编码和特殊前言逻辑，仅保留底层洗白与纯粹正则。
    """
    # Unicode 康熙部首强制洗白（解决 MarkItDown 提取 PDF 时的幽灵错码）
    unicode_corrections = {
        '⼀': '一', '⼆': '二', '⼋': '八', '⼗': '十', '⾔': '言', 
        '⽬': '目', '⼈': '人', '⼤': '大', '⼩': '小', '⼝': '口', 
        '⼿': '手', '⼼': '心', '⽔': '水', '⽕': '火', '土': '土', 
        '⽯': '石', '⽊': '木', '⽲': '禾', '⽶': '米', '⻊': '足', '⽿': '耳'
    }
    for bad_char, good_char in unicode_corrections.items():
        text = text.replace(bad_char, good_char)
    
    lines = text.split('\n')
    formatted_lines = []
    
    # 构建层级模式映射
    patterns = [
        (level1_pattern, '#'),
        (level2_pattern, '##'),
        (level3_pattern, '###'),
        (level4_pattern, '####')
    ]
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            formatted_lines.append(line)
            continue
        
        # 检查是否已经有 # 号
        if '#' in line_stripped:
            formatted_lines.append(line)
            continue
        
        # 检查是否匹配任何层级标识
        matched = False
        for pattern, md_format in patterns:
            if pattern:
                try:
                    # 极简正则匹配
                    if re.match(pattern, line_stripped) or re.search(pattern, line_stripped):
                        formatted_line = f"{md_format} {line_stripped}"
                        formatted_lines.append(formatted_line)
                        matched = True
                        break
                except re.error:
                    continue
        
        if not matched:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)