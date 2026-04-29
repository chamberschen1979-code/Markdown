import streamlit as st
import os
import tempfile
from document_cleaner import extract_text_from_file, apply_md_formatting

# 页面设置
st.set_page_config(
    page_title="文档清洗工具",
    page_icon="📄",
    layout="wide"
)

# 标题
st.title("📄 文档清洗工具")

# 侧边栏
with st.sidebar:
    st.header("文档清洗工具")
    st.write("版本：1.0.0")
    st.write("功能：文档物理提取与Markdown结构化打标")

# 控制当前选中的 tab 索引
if "current_tab" not in st.session_state:
    st.session_state["current_tab"] = 0

# 检查是否需要切换到 Tab 2
if "switch_to_tab2" in st.session_state and st.session_state["switch_to_tab2"]:
    st.session_state["current_tab"] = 1
    del st.session_state["switch_to_tab2"]
    # 强制重新运行应用以更新 tab 选择
    st.rerun()

# 预设规则持久化存储
import json
import os

# 预设规则存储文件
PRESETS_FILE = "presets.json"

# 加载预设规则和上次使用的预设
if "presets" not in st.session_state or "last_used_preset" not in st.session_state:
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 检查 data 是否包含 presets 和 last_used_preset
                if isinstance(data, dict):
                    st.session_state["presets"] = data.get("presets", {})
                    st.session_state["last_used_preset"] = data.get("last_used_preset", "无")
                else:
                    # 兼容旧格式
                    st.session_state["presets"] = data
                    st.session_state["last_used_preset"] = "无"
        except Exception as e:
            st.session_state["presets"] = {}
            st.session_state["last_used_preset"] = "无"
    else:
        st.session_state["presets"] = {}
        st.session_state["last_used_preset"] = "无"

# 确保 session_state 中存在各个级别的键
if "level1" not in st.session_state:
    st.session_state["level1"] = []
if "level2" not in st.session_state:
    st.session_state["level2"] = []
if "level3" not in st.session_state:
    st.session_state["level3"] = []
if "level4" not in st.session_state:
    st.session_state["level4"] = []

# 加载上次使用的预设
if st.session_state["last_used_preset"] != "无" and "current_preset" not in st.session_state:
    preset_name = st.session_state["last_used_preset"]
    if preset_name in st.session_state["presets"]:
        preset = st.session_state["presets"][preset_name]
        # 应用预设
        st.session_state["level1_pattern"] = preset.get("level1_pattern")
        st.session_state["level2_pattern"] = preset.get("level2_pattern")
        st.session_state["level3_pattern"] = preset.get("level3_pattern")
        st.session_state["level4_pattern"] = preset.get("level4_pattern")
        # 加载各个级别的选择选项
        st.session_state["level1"] = preset.get("level1", [])
        st.session_state["level2"] = preset.get("level2", [])
        st.session_state["level3"] = preset.get("level3", [])
        st.session_state["level4"] = preset.get("level4", [])
        st.session_state["current_preset"] = preset_name

# 创建顶部选项卡
tab_options = ["📄 工具一：文档物理提取 (转TXT)", "🏷️ 工具二：Markdown 结构化打标 (转MD)", "🔪 工具三：智能切片工作台 (Wiki Splitter)"]
current_tab = st.radio("选择工具", tab_options, index=st.session_state["current_tab"], horizontal=True)

# 预设选项和对应的正则表达式
level_options = {
    "不设置": None,
    "第X篇": r"^\s*第[一二三四五六七八九十百]+篇[\s、]",
    "第X章": r"^\s*第[一二三四五六七八九十百]+章[\s、]",
    "第X节": r"^\s*第[一二三四五六七八九十百]+节[\s、]",
    "一、 (中文大写加顿号/点)": r"^\s*[一二三四五六七八九十百]+[、\.．]",
    "（一） (中文大写加括号)": r"^\s*[（\(][一二三四五六七八九十百]+[）\)]",
    "1. (阿拉伯数字加点)": r"^\s*\d+[\.．]",
    "自定义前言/附录": "custom"
}

# 根据选择的 tab 执行相应的代码
if current_tab == tab_options[0]:
    # Tab 1: 文档物理提取
    st.header("文档物理提取")
    
    # 文件上传组件
    uploaded_files = st.file_uploader(
        "支持Word、PDF、PPT文件",
        type=["docx", "pdf", "pptx"],
        accept_multiple_files=False
    )
    
    if uploaded_files:
        # 保存上传的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_files.name)[1]) as temp_file:
            temp_file.write(uploaded_files.getbuffer())
            temp_file_path = temp_file.name
        
        # 提取文本
        st.subheader("原始纯净文本")
        try:
            raw_text = extract_text_from_file(temp_file_path)
            st.text_area("", raw_text, height=500, key="original_text")
            
            # 下载为纯净 TXT 按钮
            raw_txt_filename = f"raw_{os.path.splitext(uploaded_files.name)[0]}.txt"
            st.download_button(
                label="⬇️ 下载为纯净 TXT",
                data=raw_text,
                file_name=raw_txt_filename,
                mime="text/plain"
            )
            
            # 保存提取的文本到会话状态
            st.session_state["raw_text"] = raw_text
            st.session_state["temp_file_path"] = temp_file_path
            st.session_state["current_file"] = uploaded_files
            
            # 按钮：切换到 Markdown 知识库排版
            if st.button("📋 切换到 Markdown 知识库排版"):
                # 设置会话状态，标记需要切换到工具二
                st.session_state["switch_to_tab2"] = True
                # 重新运行应用
                st.rerun()
        except Exception as e:
            st.error(f"提取文本失败：{str(e)}")

elif current_tab == tab_options[1]:
    # Tab 2: Markdown 结构化打标
    st.header("Markdown 结构化打标")
    
    # 数据源输入区
    st.subheader("数据源输入")
    
    # TXT 文件上传
    txt_file = st.file_uploader(
        "上传 TXT 文件（可选）",
        type=["txt"],
        accept_multiple_files=False,
        key="txt_upload"
    )
    
    # 文本输入框
    if txt_file:
        # 读取 TXT 文件内容
        with txt_file:
            txt_content = txt_file.read().decode("utf-8")
        text_input = st.text_area("文本内容", txt_content, height=300, key="text_input")
    else:
        # 默认填入 session_state 中的 raw_text
        text_input = st.text_area("文本内容", st.session_state.get("raw_text", ""), height=300, key="text_input")
    
    # 分栏布局
    col_config, col_preview = st.columns([1, 2])
    
    # 左侧配置区
    with col_config:
        st.subheader("标题层级规则")
        
        # 预设规则管理
        if "presets" not in st.session_state:
            st.session_state["presets"] = {}
        if "last_used_preset" not in st.session_state:
            st.session_state["last_used_preset"] = "无"
        
        # 加载预设
        preset_names = list(st.session_state["presets"].keys())
        preset_index = 0
        if st.session_state["last_used_preset"] != "无" and st.session_state["last_used_preset"] in preset_names:
            preset_index = preset_names.index(st.session_state["last_used_preset"]) + 1
        
        if "selected_preset" not in st.session_state:
            st.session_state["selected_preset"] = "无"
        
        selected_preset = st.selectbox("选择预设规则", ["无"] + preset_names, index=preset_index, key="preset_selector")
        
        if selected_preset != st.session_state.get("selected_preset"):
            st.session_state["selected_preset"] = selected_preset
            if selected_preset != "无":
                preset = st.session_state["presets"][selected_preset]
                # 应用预设模式
                st.session_state["level1_pattern"] = preset.get("level1_pattern")
                st.session_state["level2_pattern"] = preset.get("level2_pattern")
                st.session_state["level3_pattern"] = preset.get("level3_pattern")
                st.session_state["level4_pattern"] = preset.get("level4_pattern")
                
                # 加载选择的选项
                st.session_state["level1"] = preset.get("level1", [])
                st.session_state["level2"] = preset.get("level2", [])
                st.session_state["level3"] = preset.get("level3", [])
                st.session_state["level4"] = preset.get("level4", [])
                
                # 加载自定义输入
                st.session_state["custom_level1"] = preset.get("custom_level1", "")
                st.session_state["custom_level2"] = preset.get("custom_level2", "")
                st.session_state["custom_level3"] = preset.get("custom_level3", "")
                st.session_state["custom_level4"] = preset.get("custom_level4", "")
            else:
                # ====== 核心修复：当选择"无"时，清空所有状态 ======
                st.session_state["level1_pattern"] = None
                st.session_state["level2_pattern"] = None
                st.session_state["level3_pattern"] = None
                st.session_state["level4_pattern"] = None
                
                st.session_state["level1"] = []
                st.session_state["level2"] = []
                st.session_state["level3"] = []
                st.session_state["level4"] = []
                
                st.session_state["custom_level1"] = ""
                st.session_state["custom_level2"] = ""
                st.session_state["custom_level3"] = ""
                st.session_state["custom_level4"] = ""
                # ====================================================

            st.session_state["current_preset"] = selected_preset
            st.session_state["last_used_preset"] = selected_preset
            
            try:
                save_data = {
                    "presets": st.session_state["presets"],
                    "last_used_preset": st.session_state["last_used_preset"]
                }
                with open(PRESETS_FILE, "w", encoding="utf-8") as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                st.success(f"已切换预设：{selected_preset}")
                st.rerun()
            except Exception as e:
                st.error(f"切换预设失败：{str(e)}")
        
        # ================= 核心修复：移除 st.form，实现即时生效 =================
        
        # 1级标题设置
        st.markdown("### 1级标题")
        level1_options = st.multiselect("选择1级标题格式（可多选）", list(level_options.keys()), key="level1")
        level1_patterns = []
        for option in level1_options:
            if option == "自定义前言/附录":
                custom_level1 = st.text_input('输入精确匹配的词（如"前言"）', key="custom_level1")
                if custom_level1:
                    level1_patterns.append(r"^\s*({})\s*$".format("|".join(custom_level1.split("|"))))
            else:
                level1_patterns.append(level_options[option])
        st.session_state["level1_pattern"] = "|".join([p for p in level1_patterns if p]) if level1_patterns else None
        
        # 2级标题设置
        st.markdown("### 2级标题")
        level2_options = st.multiselect("选择2级标题格式（可多选）", list(level_options.keys()), key="level2")
        level2_patterns = []
        for option in level2_options:
            if option == "自定义前言/附录":
                custom_level2 = st.text_input('输入精确匹配的词', key="custom_level2")
                if custom_level2:
                    level2_patterns.append(r"^\s*({})\s*$".format("|".join(custom_level2.split("|"))))
            else:
                level2_patterns.append(level_options[option])
        st.session_state["level2_pattern"] = "|".join([p for p in level2_patterns if p]) if level2_patterns else None
        
        # 3级标题设置
        st.markdown("### 3级标题")
        level3_options = st.multiselect("选择3级标题格式（可多选）", list(level_options.keys()), key="level3")
        level3_patterns = []
        for option in level3_options:
            if option == "自定义前言/附录":
                custom_level3 = st.text_input('输入精确匹配的词', key="custom_level3")
                if custom_level3:
                    level3_patterns.append(r"^\s*({})\s*$".format("|".join(custom_level3.split("|"))))
            else:
                level3_patterns.append(level_options[option])
        st.session_state["level3_pattern"] = "|".join([p for p in level3_patterns if p]) if level3_patterns else None
        
        # 4级标题设置
        st.markdown("### 4级标题")
        level4_options = st.multiselect("选择4级标题格式（可多选）", list(level_options.keys()), key="level4")
        level4_patterns = []
        for option in level4_options:
            if option == "自定义前言/附录":
                custom_level4 = st.text_input('输入精确匹配的词', key="custom_level4")
                if custom_level4:
                    level4_patterns.append(r"^\s*({})\s*$".format("|".join(custom_level4.split("|"))))
            else:
                level4_patterns.append(level_options[option])
        st.session_state["level4_pattern"] = "|".join([p for p in level4_patterns if p]) if level4_patterns else None

        # 将【保存为预设】逻辑移动到配置下方，确保抓取的是最新状态
        st.markdown("---")
        preset_name = st.text_input("💾 保存当前配置为新预设", key="preset_name", placeholder="例如：标准核保规则")
        if st.button("保存为预设"):
            if preset_name:
                current_config = {
                    "level1_pattern": st.session_state.get("level1_pattern"),
                    "level2_pattern": st.session_state.get("level2_pattern"),
                    "level3_pattern": st.session_state.get("level3_pattern"),
                    "level4_pattern": st.session_state.get("level4_pattern"),
                    "level1": st.session_state.get("level1", []),
                    "level2": st.session_state.get("level2", []),
                    "level3": st.session_state.get("level3", []),
                    "level4": st.session_state.get("level4", []),
                    # 修复补充：将用户手打的自定义文本也一并保存入库
                    "custom_level1": st.session_state.get("custom_level1", ""),
                    "custom_level2": st.session_state.get("custom_level2", ""),
                    "custom_level3": st.session_state.get("custom_level3", ""),
                    "custom_level4": st.session_state.get("custom_level4", "")
                }
                st.session_state["presets"][preset_name] = current_config
                st.session_state["last_used_preset"] = preset_name
                
                try:
                    save_data = {
                        "presets": st.session_state["presets"],
                        "last_used_preset": st.session_state["last_used_preset"]
                    }
                    with open(PRESETS_FILE, "w", encoding="utf-8") as f:
                        json.dump(save_data, f, ensure_ascii=False, indent=2)
                    st.success(f"预设已保存：{preset_name}！")
                    st.rerun() # 刷新UI让下拉列表更新
                except Exception as e:
                    st.error(f"保存预设失败：{str(e)}")
    
    # 右侧预览区
    with col_preview:
        st.subheader("Markdown 预览")
        
        # 开始 Markdown 排版按钮
        if st.button("开始 Markdown 排版"):
            if text_input and all(key in st.session_state for key in ["level1_pattern", "level2_pattern", "level3_pattern", "level4_pattern"]):
                with st.spinner("正在执行Markdown排版..."):
                    try:
                        # 应用MD格式
                        md_text = apply_md_formatting(
                            text_input,
                            st.session_state["level1_pattern"],
                            st.session_state["level2_pattern"],
                            st.session_state["level3_pattern"],
                            st.session_state["level4_pattern"]
                        )
                        
                        # 保存MD文本到会话状态
                        st.session_state["md_text"] = md_text
                        st.success("✅ Markdown排版完成！")
                        
                        # 显示MD格式文本
                        st.subheader("结构化文档")
                        st.text_area("", md_text, height=400, key="md_text_display")
                        
                        # 提供下载选项
                        # 以上传的文件名作为基础命名
                        base_filename = "structured_document"
                        if txt_file:
                            base_filename = os.path.splitext(txt_file.name)[0]
                        elif "current_file" in st.session_state:
                            base_filename = os.path.splitext(st.session_state["current_file"].name)[0]
                        md_filename = f"{base_filename}.md"
                        md_txt_filename = f"{base_filename}.txt"
                        
                        col_download1, col_download2 = st.columns(2)
                        with col_download1:
                            st.download_button(
                                label="⬇️ 下载为结构化 MD",
                                data=md_text,
                                file_name=md_filename,
                                mime="text/markdown"
                            )
                        with col_download2:
                            st.download_button(
                                label="⬇️ 下载为结构化 TXT",
                                data=md_text,
                                file_name=md_txt_filename,
                                mime="text/plain"
                            )
                    except Exception as e:
                        st.error(f"❌ 排版失败！原因：{str(e)}")
            elif not text_input:
                st.error("⚠️ 请先输入文本内容！")
            else:
                st.error("⚠️ 请先配置层级规则并保存！")
        
        # 添加苹果电脑安全警告说明
        st.info('💡 苹果电脑用户注意：下载的文件可能会显示安全警告。解决方法：\n1. 按住Control键并点击文件，选择"打开"\n2. 在弹出的警告窗口中点击"打开"\n3. 或者在"系统偏好设置" → "安全性与隐私"中允许打开此文件')

elif current_tab == tab_options[2]:
    # Tab 3: 智能切片工作台 (Wiki Splitter)
    st.header("智能切片工作台")
    
    # 数据输入区
    st.subheader("数据源输入")
    
    # 选择数据源方式
    data_source = st.radio(
        "选择数据源",
        ["联动模式（读取 Tab 2 处理结果）", "独立模式（上传本地 MD 文件）"],
        horizontal=True
    )
    
    # 读取 Markdown 文本
    md_text = ""
    base_filename = "wiki_splitter_output"
    if data_source == "联动模式（读取 Tab 2 处理结果）":
        if "md_text" in st.session_state:
            md_text = st.session_state["md_text"]
            st.success("✅ 已从 Tab 2 读取 Markdown 文本")
            # 使用 Tab 2 的基础文件名
            if "current_file" in st.session_state:
                base_filename = os.path.splitext(st.session_state["current_file"].name)[0]
        else:
            st.warning("⚠️ Tab 2 尚未生成 Markdown 文本，请先使用 Tab 2 处理文档")
    else:
        # 独立模式：上传本地 MD 文件
        md_file = st.file_uploader(
            "上传 MD 文件",
            type=["md"],
            accept_multiple_files=False
        )
        if md_file:
            try:
                md_text = md_file.read().decode("utf-8")
                st.success("✅ 已上传并读取 MD 文件")
                # 使用上传的 MD 文件名作为基础
                base_filename = os.path.splitext(md_file.name)[0]
            except Exception as e:
                st.error(f"❌ 读取文件失败：{str(e)}")
    
    # 显示读取的 Markdown 文本（可选）
    if md_text:
        with st.expander("查看当前 Markdown 文本"):
            st.text_area("", md_text, height=300)
    
    # 左侧栏：可视化树状控制台
    if md_text:
        # 解析 Markdown 标题
        import re
        
        # 提取所有标题及其层级（兼容 # 和标题之间有无空格的情况）
        title_pattern = re.compile(r'^(#{1,6})\s*(.*)$', re.MULTILINE)
        titles = []
        lines = md_text.split('\n')
        for i, line in enumerate(lines):
            match = title_pattern.match(line)
            if match:
                level = len(match.group(1))
                content = match.group(2).strip()
                titles.append({"level": level, "content": content, "line": i})
        
        # 过滤文件名非法字符并清洗前缀（提前定义，供 build_tree 使用）
        def sanitize_filename(filename):
            import re
            patterns = [
                r'^第[一二三四五六七八九十百]+[章节][\s、]+',
                r'^[一二三四五六七八九十百]+[、\.．]+\s*',
                r'^[（\(][一二三四五六七八九十百]+[）\)]\s*',
                r'^\d+[\.．]\s*'
            ]
            for pattern in patterns:
                filename = re.sub(pattern, '', filename)
            illegal_chars = '\\/:*?"<>|'
            for char in illegal_chars:
                filename = filename.replace(char, "")
            filename = filename.lstrip("# ")
            return filename.strip()
        
        # 构建文档树，每个节点记录 parent_path
        def build_tree(titles):
            tree = []
            stack = []
            for title in titles:
                # 先清理栈（移除级别 >= 当前级别的节点）
                while stack and stack[-1]["level"] >= title["level"]:
                    stack.pop()
                
                # 再计算当前节点的祖先路径（此时栈中只有级别 < 当前级别的真正祖先）
                parent_path = []
                for node in stack:
                    cleaned_title = sanitize_filename(node["content"])
                    parent_path.append(cleaned_title)
                
                # 添加 parent_path 到当前节点
                title["parent_path"] = parent_path
                
                # 将当前节点添加到树和栈中
                if stack:
                    if "children" not in stack[-1]:
                        stack[-1]["children"] = []
                    stack[-1]["children"].append(title)
                else:
                    tree.append(title)
                stack.append(title)
            return tree
        
        doc_tree = build_tree(titles)
        
        # 分栏布局
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("文档树状控制台")
            st.info("💡 父子吞并原则：勾选父级标题时，会包含其所有子标题内容")
            
            # 渲染树状结构
            def render_tree(node, parent_keys=[], level=0):
                # 生成唯一的 key
                node_key = f"title_{level}_{node['content'][:20]}"
                full_key = ".".join(parent_keys + [node_key])
                
                # 计算缩进和前缀
                indent = "    " * (level - 1)
                prefix = "┣━ " if level > 0 else ""
                
                # 渲染复选框
                checked = st.checkbox(
                    f"{indent}{prefix}{node['content']}",
                    value=st.session_state.get(full_key, False),
                    key=full_key,
                    help="勾选此标题作为独立文件"
                )
                
                # 渲染子节点
                if "children" in node:
                    for i, child in enumerate(node["children"]):
                        # 最后一个子节点使用不同的前缀
                        if i == len(node["children"]) - 1:
                            child_prefix = "┗━ "
                        else:
                            child_prefix = "┣━ "
                        render_tree(child, parent_keys + [node_key], level + 1)
            
            # 渲染整个树
            for node in doc_tree:
                render_tree(node)
        
        with col_right:
            st.subheader("元数据与预览")
            
            # 元数据输入
            parent_dir = st.text_input("归属母目录名称 (例如: 能源板块篇)", "")
            
            # 实时预览
            st.subheader("即将生成的文件列表")
            
            # 收集勾选的标题
            def collect_checked_titles(node, parent_keys=[], level=0):
                node_key = f"title_{level}_{node['content'][:20]}"
                full_key = ".".join(parent_keys + [node_key])
                checked = st.session_state.get(full_key, False)
                
                collected = []
                if checked:
                    collected.append(node)
                    # 父子吞并原则：父级被勾选时，不再收集子级
                else:
                    if "children" in node:
                        for child in node["children"]:
                            collected.extend(collect_checked_titles(child, parent_keys + [node_key], level + 1))
                return collected
            
            checked_titles = []
            for node in doc_tree:
                checked_titles.extend(collect_checked_titles(node))
            
            # 显示文件列表
            if checked_titles:
                for title in checked_titles:
                    # 动态拼接文件名：母目录-祖先1-祖先2-当前标题
                    filename_parts = [parent_dir] + title["parent_path"] + [sanitize_filename(title["content"])]
                    display_name = "-".join([p for p in filename_parts if p]) + ".md"
                    # 截断过长的文件名
                    if len(display_name) > 100:
                        display_name = display_name[:97] + "..." + ".md"
                    st.write(f"- {display_name}")
                    
                    # 如果有子节点，显示前言文件
                    if "children" in title and title["children"]:
                        preface_parts = [parent_dir] + title["parent_path"] + [sanitize_filename(title["content"]), "00_前言总则"]
                        preface_name = "-".join([p for p in preface_parts if p]) + ".md"
                        if len(preface_name) > 100:
                            preface_name = preface_name[:97] + "..." + ".md"
                        st.write(f"  └─ {preface_name}")
            else:
                st.info("请在左侧勾选要切片的标题")
        
        # 执行与导出区
        st.subheader("执行与导出")
        
        if st.button("生成并打包 ZIP"):
            if not checked_titles:
                st.error("⚠️ 请先在左侧勾选要切片的标题")
            elif not parent_dir:
                st.error("⚠️ 请输入归属母目录名称")
            else:
                with st.spinner("正在生成文件并打包..."):
                    try:
                        import zipfile
                        import io
                        
                        # 创建内存中的 ZIP 文件
                        zip_buffer = io.BytesIO()
                        
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            # 存储所有生成的文件名用于路由
                            generated_files = []
                            
                            # 生成每个切片文件
                            for title in checked_titles:
                                # 找到标题的起始和结束位置
                                start_line = title["line"]
                                # 找到下一个同级或高级标题的位置
                                end_line = len(lines)
                                for i in range(start_line + 1, len(lines)):
                                    match = title_pattern.match(lines[i])
                                    if match and len(match.group(1)) <= title["level"]:
                                        end_line = i
                                        break
                                
                                # 截取文本块（从标题开始）
                                text_block = "\n".join(lines[start_line:end_line])
                                
                                # 生成动态 YAML 元数据
                                yaml_metadata = f"---\n归属母目录: [[{parent_dir}]]\n"
                                if title["parent_path"]:
                                    yaml_metadata += "层级路径:\n"
                                    for ancestor in title["parent_path"]:
                                        yaml_metadata += f"  - [[{ancestor}]]\n"
                                yaml_metadata += "---\n\n"
                                final_content = yaml_metadata + text_block
                                
                                # 生成动态文件名：母目录-祖先1-祖先2-当前标题
                                filename_parts = [parent_dir] + title["parent_path"] + [sanitize_filename(title["content"])]
                                filename = "-".join(filename_parts) + ".md"
                                # 截断过长的文件名
                                if len(filename) > 150:
                                    filename = filename[:147] + "..." + ".md"
                                
                                # 写入 ZIP 文件
                                zipf.writestr(filename, final_content.encode("utf-8"))
                                generated_files.append(filename[:-3])  # 移除 .md
                            
                            # 生成总路由文件
                            route_content = "# 总路由\n\n"
                            for file_name in generated_files:
                                route_content += f"- [[{file_name}]]\n"
                            
                            zipf.writestr("00_总路由.md", route_content.encode("utf-8"))
                        
                        # 重置 ZIP 缓冲区指针
                        zip_buffer.seek(0)
                        
                        # 提供下载按钮
                        st.download_button(
                            label="⬇️ 下载 ZIP 包",
                            data=zip_buffer,
                            file_name=f"{base_filename}_splitter_output.zip",
                            mime="application/zip"
                        )
                        
                        st.success("✅ 生成并打包完成！")
                    except Exception as e:
                        st.error(f"❌ 生成失败：{str(e)}")
    
# 页脚
st.markdown("---")
st.markdown("© 2026 文档清洗工具 - 精准处理，内容无删减")