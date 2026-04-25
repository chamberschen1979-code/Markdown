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

# 创建顶部选项卡
tab_options = ["📄 工具一：文档物理提取 (转TXT)", "🏷️ 工具二：Markdown 结构化打标 (转MD)"]
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
        
        # 层级配置表单
        with st.form("hierarchy_config_form"):
            # 1级标题设置
            st.markdown("### 1级标题")
            level1_options = st.multiselect(
                "选择1级标题格式（可多选）",
                list(level_options.keys()),
                key="level1"
            )
            
            # 处理1级标题模式
            level1_patterns = []
            for option in level1_options:
                if option == "自定义前言/附录":
                    custom_level1 = st.text_input('输入精确匹配的词（如"前言"）', key="custom_level1")
                    if custom_level1:
                        level1_patterns.append(r"^\s*({})\s*$".format("|".join(custom_level1.split("|"))))
                else:
                    level1_patterns.append(level_options[option])
            level1_pattern = "|".join([p for p in level1_patterns if p]) if level1_patterns else None
            
            # 2级标题设置
            st.markdown("### 2级标题")
            level2_options = st.multiselect(
                "选择2级标题格式（可多选）",
                list(level_options.keys()),
                key="level2"
            )
            
            # 处理2级标题模式
            level2_patterns = []
            for option in level2_options:
                if option == "自定义前言/附录":
                    custom_level2 = st.text_input('输入精确匹配的词（如"前言"）', key="custom_level2")
                    if custom_level2:
                        level2_patterns.append(r"^\s*({})\s*$".format("|".join(custom_level2.split("|"))))
                else:
                    level2_patterns.append(level_options[option])
            level2_pattern = "|".join([p for p in level2_patterns if p]) if level2_patterns else None
            
            # 3级标题设置
            st.markdown("### 3级标题")
            level3_options = st.multiselect(
                "选择3级标题格式（可多选）",
                list(level_options.keys()),
                key="level3"
            )
            
            # 处理3级标题模式
            level3_patterns = []
            for option in level3_options:
                if option == "自定义前言/附录":
                    custom_level3 = st.text_input('输入精确匹配的词（如"前言"）', key="custom_level3")
                    if custom_level3:
                        level3_patterns.append(r"^\s*({})\s*$".format("|".join(custom_level3.split("|"))))
                else:
                    level3_patterns.append(level_options[option])
            level3_pattern = "|".join([p for p in level3_patterns if p]) if level3_patterns else None
            
            # 4级标题设置
            st.markdown("### 4级标题")
            level4_options = st.multiselect(
                "选择4级标题格式（可多选）",
                list(level_options.keys()),
                key="level4"
            )
            
            # 处理4级标题模式
            level4_patterns = []
            for option in level4_options:
                if option == "自定义前言/附录":
                    custom_level4 = st.text_input('输入精确匹配的词（如"前言"）', key="custom_level4")
                    if custom_level4:
                        level4_patterns.append(r"^\s*({})\s*$".format("|".join(custom_level4.split("|"))))
                else:
                    level4_patterns.append(level_options[option])
            level4_pattern = "|".join([p for p in level4_patterns if p]) if level4_patterns else None
            
            # 提交按钮
            submit_button = st.form_submit_button("保存配置")
            
            if submit_button:
                # 保存配置到会话状态
                st.session_state["level1_pattern"] = level1_pattern
                st.session_state["level2_pattern"] = level2_pattern
                st.session_state["level3_pattern"] = level3_pattern
                st.session_state["level4_pattern"] = level4_pattern
                st.success("配置已保存！")
    
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
                        md_filename = "structured_document.md"
                        md_txt_filename = "structured_document.txt"
                        
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

# 页脚
st.markdown("---")
st.markdown("© 2026 文档清洗工具 - 精准处理，内容无删减")