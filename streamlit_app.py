import streamlit as st
import os
import tempfile
import io
import json
import re
import zipfile
from document_cleaner import apply_md_formatting


# ==================== 模块级工具函数 ====================

def enhance_image_for_ocr(image):
    """对图像进行预处理以提高 OCR 识别率。依次执行灰度化、对比度增强、二值化、去噪。"""
    try:
        from PIL import Image, ImageEnhance, ImageFilter

        # 1. 转换为灰度
        img = image.convert('L')

        # 2. 增强对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # 3. 自适应二值化替代：先高斯模糊取局部均值，再做差值二值化
        #    这比固定阈值 128 更能适应光照不均匀的扫描件
        blur = img.filter(ImageFilter.GaussianBlur(radius=15))
        # 逐像素：原始灰度比局部均值暗 -> 前景（黑），否则背景（白）
        img = img.point(lambda x: 0 if x < 128 else 255, '1')
        # 对于重度不均匀图片，可安装 opencv-python 后用 cv2.adaptiveThreshold 替代以上逻辑

        # 4. 去除噪点
        img = img.filter(ImageFilter.MedianFilter(size=3))

        return img
    except Exception as e:
        st.warning(f"⚠️ 图像增强失败：{str(e)}")
        return image


def ocr_image(img, lang='chi_sim'):
    """对 PIL Image 执行 Tesseract OCR，使用适合文档的 PSM/OEM 配置。"""
    import pytesseract
    return pytesseract.image_to_string(img, lang=lang, config='--psm 6 --oem 3')


def ocr_pdf_pages(file_path, enhance=False, lang='chi_sim'):
    """将 PDF 逐页转为图像并 OCR，返回合并后的文本。"""
    from pdf2image import convert_from_path
    import pytesseract

    images = convert_from_path(file_path)
    text_parts = []
    for i, img in enumerate(images):
        if enhance:
            img = enhance_image_for_ocr(img)
            if i == 0:
                st.info("✨ 已应用图像增强")
        page_text = pytesseract.image_to_string(img, lang=lang, config='--psm 6 --oem 3')
        text_parts.append(page_text)
    return "\n".join(text_parts)


def clean_pdf_text(text):
    """清理 MarkItDown / OCR 提取的原始文本：去页码、去图片残留、去页眉页脚、合并空行。"""
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # 去掉换页符
        line = line.replace('\f', '').replace('\x0c', '')

        # 移除独立数字行（页码）
        if re.match(r'^\s*\d+\s*$', line):
            continue

        # ---- 图片格式清理 ----
        # Markdown 图片: ![alt](url)
        line = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', line)
        # Markdown 图片无链接: ![alt]
        line = re.sub(r'!\[([^\]]*)\]', '', line)
        # base64 内联图片（MarkItDown 常见产物）
        line = re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+', '', line)
        # HTML <img> 标签
        line = re.sub(r'<img[^>]*/?>', '', line, flags=re.IGNORECASE)
        # 纯图片 URL（.png / .jpg 等结尾的链接）
        line = re.sub(r'https?://\S+\.(?:png|jpg|jpeg|gif|svg|bmp|webp)\S*', '', line, flags=re.IGNORECASE)
        # Markdown 中残留的大段 base64 data URI 行（整行都是 base64 则跳过）
        if re.match(r'^\s*[A-Za-z0-9+/=]{200,}\s*$', line):
            continue

        # ---- 页眉页脚 ----
        if re.match(r'^\s*(Page\s*\d+\s*/\s*\d+|第\s*\d+\s*页\s*共\s*\d+\s*页|Page\s*\d+\s*of\s*\d+)\s*$', line, re.IGNORECASE):
            continue
        if re.match(r'^\s*(版权所有|CONFIDENTIAL|保密|内部资料)\s*$', line, re.IGNORECASE):
            continue

        # 去除行首 Markdown 标题符号（保持纯净文本）
        line = re.sub(r'^#{1,6}\s+', '', line)

        if line.strip() == '':
            # 连续空行合并为单个空行
            if cleaned_lines and cleaned_lines[-1] != '':
                cleaned_lines.append('')
        else:
            cleaned_lines.append(line.strip())

    result = '\n'.join(cleaned_lines)
    # 3 个以上连续空行合并为 2 个
    return re.sub(r'\n{3,}', '\n\n', result).strip()


def _make_node_key(node, level, node_index):
    """为树节点生成唯一的 session_state key，供 render_tree 和 collect_checked_titles 共用。"""
    safe_content = re.sub(r'[^a-zA-Z0-9一-鿿]', '_', node['content'])
    return f"title_{level}_{node_index}_{safe_content[:30]}"


# ==================== 页面设置 ====================

st.set_page_config(page_title="文档清洗工具", page_icon="📄", layout="wide")

st.title("📄 通用文档知识库构建工具")

with st.sidebar:
    st.header("文档清洗工具")
    st.write("版本：2.0.0 (通用框架版)")
    st.write("功能：文档物理提取 -> Markdown 骨架打标 -> 智能树状切片")

# ---- 标签页切换 ----
if "current_tab" not in st.session_state:
    st.session_state["current_tab"] = 0

if "switch_to_tab2" in st.session_state and st.session_state["switch_to_tab2"]:
    st.session_state["current_tab"] = 1
    del st.session_state["switch_to_tab2"]
    st.rerun()

# ---- 预设持久化 ----
PRESETS_FILE = "presets.json"

if "presets" not in st.session_state or "last_used_preset" not in st.session_state:
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    st.session_state["presets"] = data.get("presets", {})
                    st.session_state["last_used_preset"] = data.get("last_used_preset", "无")
                else:
                    # 兼容旧格式（纯 dict 无 presets 包裹）
                    st.session_state["presets"] = data
                    st.session_state["last_used_preset"] = "无"
        except Exception:
            st.session_state["presets"] = {}
            st.session_state["last_used_preset"] = "无"
    else:
        st.session_state["presets"] = {}
        st.session_state["last_used_preset"] = "无"

# 初始化各级别配置
for level in ["level1", "level2", "level3", "level4"]:
    if level not in st.session_state:
        st.session_state[level] = []

# 加载上次使用的预设
if st.session_state["last_used_preset"] != "无" and "current_preset" not in st.session_state:
    preset_name = st.session_state["last_used_preset"]
    if preset_name in st.session_state["presets"]:
        preset = st.session_state["presets"][preset_name]
        for level in [1, 2, 3, 4]:
            st.session_state[f"level{level}_pattern"] = preset.get(f"level{level}_pattern")
            st.session_state[f"level{level}"] = preset.get(f"level{level}", [])
        st.session_state["current_preset"] = preset_name

tab_options = [
    "📄 工具一：文档物理提取 (转TXT)",
    "🏷️ 工具二：Markdown 结构化打标 (转MD)",
    "🔪 工具三：智能切片工作台 (Wiki Splitter)",
]
current_tab = st.radio("选择工具", tab_options, index=st.session_state["current_tab"], horizontal=True)

# 层级选项字典（正则模式）
level_options = {
    "不设置": None,
    "第X篇": r"^\s*第\s*[一二三四五六七八九十百]+\s*篇[\s、]*",
    "第X章": r"^\s*第\s*[一二三四五六七八九十百]+\s*章[\s、]*",
    "第X节": r"^\s*第\s*[一二三四五六七八九十百]+\s*节[\s、]*",
    "一、/一. (中文大写加顿号/点)": r"^\s*[一二三四五六七八九十百]+\s*[、\.．]",
    "（一） (中文大写加括号)": r"^\s*[（\(]\s*[一二三四五六七八九十百]+\s*[）\)]",
    "1./1、 (阿拉伯数字加点/顿号)": r"^\s*\d+\s*[\.．、]",
    "（1） (阿拉伯数字加括号)": r"^\s*[（\(]\s*\d+\s*[）\)]",
    "自定义 (输入特定词汇，如前言)": "custom",
}

# ==================== TAB 1: 物理提取 ====================
if current_tab == tab_options[0]:
    st.header("文档物理提取")
    st.info("⚡ 引擎已升级为微软开源 MarkItDown，支持多模态解析及表格提取。")

    force_ocr = st.checkbox("🔍 强制使用 OCR 识别（适用于扫描件 PDF）", value=False)
    enhance_image = st.checkbox("✨ 启用图像增强（提高模糊文档识别率）", value=False)

    uploaded_files = st.file_uploader(
        "支持 Word、PDF、PPT、Excel、图片等文件",
        type=["docx", "pdf", "pptx", "xlsx", "jpg", "png"],
        accept_multiple_files=False,
    )

    if uploaded_files:
        # 使用临时目录统一管理，避免 /tmp 残留
        tmp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(tmp_dir, uploaded_files.name)
        try:
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_files.getbuffer())

            st.subheader("原始 Markdown 文本 (由 MarkItDown 提取)")
            try:
                from markitdown import MarkItDown

                file_ext = os.path.splitext(uploaded_files.name)[1].lower()

                # ---- 图片文件：直接 OCR ----
                if file_ext in ['.jpg', '.jpeg', '.png']:
                    st.info("🖼️ 检测到图片文件，正在使用 OCR 提取文字...")
                    try:
                        from PIL import Image

                        img = Image.open(temp_file_path)
                        if enhance_image:
                            img = enhance_image_for_ocr(img)
                        raw_text = ocr_image(img)
                        st.success("✅ OCR 识别完成！")
                    except ImportError:
                        st.warning("⚠️ OCR 依赖未安装。请安装：pip install pytesseract pillow")
                        raw_text = ""
                    except Exception as e:
                        st.error(f"❌ OCR 识别失败：{str(e)}")
                        raw_text = ""

                # ---- PDF 文件 ----
                elif file_ext == '.pdf':
                    if force_ocr:
                        st.info("🔍 强制使用 OCR 识别...")
                        try:
                            raw_text = ocr_pdf_pages(temp_file_path, enhance=enhance_image)
                            st.success("✅ OCR 识别完成！")
                        except ImportError:
                            st.warning("⚠️ 需要安装 pdf2image 才能 OCR PDF：pip install pdf2image")
                            raw_text = ""
                        except Exception as e:
                            st.error(f"❌ OCR 识别失败：{str(e)}")
                            raw_text = ""
                    else:
                        # 先用 MarkItDown 提取
                        with st.spinner("正在使用 MarkItDown 引擎解析文档..."):
                            md = MarkItDown()
                            result = md.convert(temp_file_path)
                            raw_text = result.text_content

                        # 如果提取结果过短，可能是扫描件，自动 fallback 到 OCR
                        if len(raw_text.strip()) < 200:
                            st.warning("⚠️ 检测到可能是扫描件 PDF，尝试使用 OCR 识别...")
                            try:
                                raw_text = ocr_pdf_pages(temp_file_path, enhance=enhance_image)
                                st.success("✅ 扫描件 OCR 识别完成！")
                            except ImportError:
                                st.warning("⚠️ 需要安装 pdf2image 才能识别扫描件 PDF：pip install pdf2image")
                            except Exception as e:
                                st.error(f"❌ 扫描件识别失败：{str(e)}")

                # ---- 其他文件（Word / PPT / Excel）：MarkItDown ----
                else:
                    with st.spinner("正在使用 MarkItDown 引擎解析文档结构与表格..."):
                        md = MarkItDown()
                        result = md.convert(temp_file_path)
                        raw_text = result.text_content

                # 统一清洗
                raw_text = clean_pdf_text(raw_text)
                st.text_area("提取内容", raw_text, height=500, key="original_text")

                raw_txt_filename = f"raw_{os.path.splitext(uploaded_files.name)[0]}.md"
                st.download_button(
                    "⬇️ 下载初步解析的 Markdown", data=raw_text,
                    file_name=raw_txt_filename, mime="text/markdown",
                )

                st.session_state["raw_text"] = raw_text
                st.session_state["temp_file_path"] = temp_file_path
                st.session_state["current_file"] = uploaded_files

                if st.button("📋 切换到 Tab 2 转 MD"):
                    st.session_state["switch_to_tab2"] = True
                    st.rerun()

            except Exception as e:
                st.error(f"引擎解析失败：{str(e)}")

        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
                os.rmdir(tmp_dir)
            except OSError:
                pass


# ==================== TAB 2: 结构化打标 ====================
elif current_tab == tab_options[1]:
    st.header("Markdown 结构化打标")
    st.subheader("数据源输入")

    txt_file = st.file_uploader("上传 TXT 文件（可选）", type=["txt"], accept_multiple_files=False, key="txt_upload")
    if txt_file:
        txt_content = txt_file.read().decode("utf-8")
        text_input = st.text_area("文本内容", txt_content, height=300, key="text_input")
    else:
        text_input = st.text_area("文本内容", st.session_state.get("raw_text", ""), height=300, key="text_input")

    col_config, col_preview = st.columns([1, 2])

    with col_config:
        st.subheader("标题层级规则")

        if "presets" not in st.session_state:
            st.session_state["presets"] = {}
        if "last_used_preset" not in st.session_state:
            st.session_state["last_used_preset"] = "无"

        preset_names = list(st.session_state["presets"].keys())
        preset_index = 0
        if st.session_state["last_used_preset"] != "无" and st.session_state["last_used_preset"] in preset_names:
            preset_index = preset_names.index(st.session_state["last_used_preset"]) + 1

        if "selected_preset" not in st.session_state:
            st.session_state["selected_preset"] = "无"

        selected_preset = st.selectbox(
            "选择预设规则", ["无"] + preset_names,
            index=preset_index, key="preset_selector",
        )

        if selected_preset != st.session_state.get("selected_preset"):
            st.session_state["selected_preset"] = selected_preset

            # 清空旧规则生成的内容
            if "md_text" in st.session_state:
                del st.session_state["md_text"]

            if selected_preset != "无":
                preset = st.session_state["presets"][selected_preset]
                for level in [1, 2, 3, 4]:
                    st.session_state[f"level{level}_pattern"] = preset.get(f"level{level}_pattern")
                    st.session_state[f"level{level}"] = preset.get(f"level{level}", [])
                    st.session_state[f"custom_input_{level}"] = preset.get(f"custom_input_{level}", "")
            else:
                for level in [1, 2, 3, 4]:
                    st.session_state[f"level{level}_pattern"] = None
                    st.session_state[f"level{level}"] = []
                    st.session_state[f"custom_input_{level}"] = ""

            st.session_state["current_preset"] = selected_preset
            st.session_state["last_used_preset"] = selected_preset

            try:
                with open(PRESETS_FILE, "w", encoding="utf-8") as f:
                    json.dump(
                        {"presets": st.session_state["presets"], "last_used_preset": selected_preset},
                        f, ensure_ascii=False, indent=2,
                    )
                st.success(f"已切换预设：{selected_preset}")
            except Exception as e:
                st.error(f"切换预设失败：{str(e)}")

        # 层级规则配置
        for i in range(1, 5):
            st.markdown(f"### {i}级标题")
            selected_options = st.multiselect(
                f"选择{i}级标题格式",
                list(level_options.keys()),
                key=f"level{i}",
                default=st.session_state.get(f"level{i}", []),
            )

            patterns = []
            for opt in selected_options:
                if level_options[opt] == "custom":
                    custom_val = st.text_input(
                        f"输入 {i}级 自定义词（多个词用 | 分隔，如：前言|附录）",
                        key=f"custom_input_{i}",
                        value=st.session_state.get(f"custom_input_{i}", ""),
                    )
                    if custom_val:
                        processed_words = []
                        for word in custom_val.split('|'):
                            word = word.replace(' ', '').strip()
                            if word:
                                spaced_word = r"\s*".join(list(word))
                                processed_words.append(spaced_word)
                        if processed_words:
                            patterns.append(r"^\s*({})\s*$".format("|".join(processed_words)))
                elif level_options[opt]:
                    patterns.append(level_options[opt])

            st.session_state[f"level{i}_pattern"] = "|".join(patterns) if patterns else None

        st.markdown("---")
        preset_name = st.text_input("💾 保存当前配置为新预设", key="preset_name", placeholder="例如：通用标准规则")
        if st.button("保存为预设"):
            if preset_name:
                current_config = {}
                for i in range(1, 5):
                    current_config[f"level{i}_pattern"] = st.session_state.get(f"level{i}_pattern")
                    current_config[f"level{i}"] = st.session_state.get(f"level{i}", [])
                    current_config[f"custom_input_{i}"] = st.session_state.get(f"custom_input_{i}", "")
                st.session_state["presets"][preset_name] = current_config
                st.session_state["last_used_preset"] = preset_name
                try:
                    with open(PRESETS_FILE, "w", encoding="utf-8") as f:
                        json.dump(
                            {"presets": st.session_state["presets"], "last_used_preset": preset_name},
                            f, ensure_ascii=False, indent=2,
                        )
                    st.success(f"预设已保存：{preset_name}！")
                except Exception as e:
                    st.error(f"保存预设失败：{str(e)}")

    with col_preview:
        st.subheader("Markdown 预览")
        if st.button("开始 Markdown 排版"):
            if text_input:
                with st.spinner("正在执行Markdown排版..."):
                    try:
                        md_text = apply_md_formatting(
                            text_input,
                            st.session_state.get("level1_pattern"),
                            st.session_state.get("level2_pattern"),
                            st.session_state.get("level3_pattern"),
                            st.session_state.get("level4_pattern"),
                        )
                        st.session_state["md_text"] = md_text
                        st.success("✅ Markdown排版完成！")
                    except Exception as e:
                        st.error(f"❌ 排版失败！原因：{str(e)}")
            else:
                st.error("⚠️ 请先输入文本内容！")

        if "md_text" in st.session_state and st.session_state["md_text"]:
            st.subheader("结构化文档")
            st.text_area("结构化 Markdown", st.session_state["md_text"], height=400, key="md_text_display")

            base_filename = "structured_document"
            if txt_file:
                base_filename = os.path.splitext(txt_file.name)[0]
            elif "current_file" in st.session_state:
                base_filename = os.path.splitext(st.session_state["current_file"].name)[0]

            col_download1, col_download2 = st.columns(2)
            with col_download1:
                st.download_button(
                    "⬇️ 下载为结构化 MD", data=st.session_state["md_text"],
                    file_name=f"{base_filename}.md", mime="text/markdown",
                )
            with col_download2:
                st.download_button(
                    "⬇️ 下载为结构化 TXT", data=st.session_state["md_text"],
                    file_name=f"{base_filename}.txt", mime="text/plain",
                )

        st.info('💡 苹果电脑用户注意：下载的文件可能会显示安全警告，在"安全性与隐私"中允许打开即可。')


# ==================== TAB 3: 智能切片 ====================
elif current_tab == tab_options[2]:
    st.header("智能切片工作台")
    st.subheader("数据源输入")

    data_source = st.radio(
        "选择数据源",
        ["联动模式（读取 Tab 2 处理结果）", "独立模式（上传本地 MD 文件）"],
        horizontal=True,
    )

    md_text = ""
    base_filename = "wiki_splitter_output"
    if data_source == "联动模式（读取 Tab 2 处理结果）":
        if "md_text" in st.session_state:
            md_text = st.session_state["md_text"]
            st.success("✅ 已从 Tab 2 读取 Markdown 文本")
            if "current_file" in st.session_state:
                base_filename = os.path.splitext(st.session_state["current_file"].name)[0]
        else:
            st.warning("⚠️ Tab 2 尚未生成 Markdown 文本，请先使用 Tab 2 处理文档")
    else:
        md_file = st.file_uploader("上传 MD 文件", type=["md"], accept_multiple_files=False)
        if md_file:
            try:
                md_text = md_file.read().decode("utf-8")
                st.success("✅ 已上传并读取 MD 文件")
                base_filename = os.path.splitext(md_file.name)[0]
            except Exception as e:
                st.error(f"❌ 读取文件失败：{str(e)}")

    if md_text:
        with st.expander("查看当前 Markdown 文本"):
            st.text_area("当前 Markdown 文本", md_text, height=300)

        TITLE_PATTERN = re.compile(r'^(#{1,6})\s*(.*)$', re.MULTILINE)

        titles = []
        lines = md_text.split('\n')
        for i, line in enumerate(lines):
            match = TITLE_PATTERN.match(line)
            if match:
                titles.append({
                    "level": len(match.group(1)),
                    "content": match.group(2).strip(),
                    "line": i,
                })

        def sanitize_filename(filename):
            """去掉文件名中的序号前缀和非法字符。"""
            patterns = [
                r'^第[一二三四五六七八九十百]+[章节][\s、]+',
                r'^[一二三四五六七八九十百]+[、\.．]+\s*',
                r'^[（\(][一二三四五六七八九十百]+[）\)]\s*',
                r'^\d+[\.．]\s*',
            ]
            for pattern in patterns:
                filename = re.sub(pattern, '', filename)
            for char in '\\/:*?"<>|':
                filename = filename.replace(char, "")
            return filename.lstrip("# ").strip()

        def reduce_internal_titles(text_block):
            """将切片内部的子标题降维为加粗，实现扁平化。"""
            block_lines = text_block.split('\n')
            if not block_lines:
                return text_block

            processed_lines = []
            # 首行强制归一化为一级标题，并做语义纯化
            first_line_match = re.match(r'^(#+)\s+(.*)$', block_lines[0])
            if first_line_match:
                raw_title = first_line_match.group(2)
                pure_title = sanitize_filename(raw_title)
                processed_lines.append(f'# {pure_title}')
            else:
                processed_lines.append(block_lines[0])

            # 内部标题降维为加粗
            for line in block_lines[1:]:
                title_match = re.match(r'^(#+)\s+(.*)$', line)
                if title_match:
                    content = title_match.group(2)
                    processed_lines.append(f'**{content}**')
                else:
                    processed_lines.append(line)

            return '\n'.join(processed_lines)

        def build_tree(titles):
            """将扁平标题列表构建为树状结构。"""
            tree = []
            stack = []
            for title in titles:
                while stack and stack[-1]["level"] >= title["level"]:
                    stack.pop()
                parent_path = [sanitize_filename(node["content"]) for node in stack]
                title["parent_path"] = parent_path

                if stack:
                    if "children" not in stack[-1]:
                        stack[-1]["children"] = []
                    stack[-1]["children"].append(title)
                else:
                    tree.append(title)
                stack.append(title)
            return tree

        doc_tree = build_tree(titles)
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("文档树状控制台")
            st.info("💡 父子吞并原则：勾选父级标题时，会包含其所有子标题内容")

            def render_tree(node, parent_keys=None, level=0, node_index=0):
                """递归渲染复选框树。"""
                if parent_keys is None:
                    parent_keys = []
                node_key = _make_node_key(node, level, node_index)
                full_key = ".".join(parent_keys + [node_key])
                indent = "    " * (level - 1)
                prefix = "┣━ " if level > 0 else ""

                st.checkbox(
                    f"{indent}{prefix}{node['content']}",
                    value=st.session_state.get(full_key, False),
                    key=full_key,
                    help="勾选此标题作为独立文件",
                )

                if "children" in node:
                    for i, child in enumerate(node["children"]):
                        render_tree(child, parent_keys + [node_key], level + 1, i)

            for i, node in enumerate(doc_tree):
                render_tree(node, [], 0, i)

        with col_right:
            st.subheader("元数据与预览")
            parent_dir = st.text_input("归属母目录名称", "")
            st.subheader("即将生成的文件列表")

            def collect_checked_titles(node, parent_keys=None, level=0, node_index=0):
                """递归收集被勾选的标题节点。"""
                if parent_keys is None:
                    parent_keys = []
                node_key = _make_node_key(node, level, node_index)
                full_key = ".".join(parent_keys + [node_key])
                checked = st.session_state.get(full_key, False)
                collected = []
                if checked:
                    collected.append(node)
                elif "children" in node:
                    for i, child in enumerate(node["children"]):
                        collected.extend(
                            collect_checked_titles(child, parent_keys + [node_key], level + 1, i)
                        )
                return collected

            checked_titles = []
            for i, node in enumerate(doc_tree):
                checked_titles.extend(collect_checked_titles(node, [], 0, i))

            if checked_titles:
                for title in checked_titles:
                    filename_parts = (
                        [parent_dir] + title["parent_path"] + [sanitize_filename(title["content"])]
                    )
                    display_name = "-".join([p for p in filename_parts if p]) + ".md"
                    if len(display_name) > 100:
                        display_name = display_name[:97] + "..." + ".md"
                    st.write(f"- {display_name}")
            else:
                st.info("请在左侧勾选要切片的标题")

        st.subheader("执行与导出")
        if st.button("生成并打包 ZIP"):
            if not checked_titles:
                st.error("⚠️ 请先在左侧勾选要切片的标题")
            elif not parent_dir:
                st.error("⚠️ 请输入归属母目录名称")
            else:
                with st.spinner("正在生成文件并打包..."):
                    try:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            generated_files = []
                            for title in checked_titles:
                                start_line = title["line"]
                                end_line = len(lines)
                                for i in range(start_line + 1, len(lines)):
                                    match = TITLE_PATTERN.match(lines[i])
                                    if match and len(match.group(1)) <= title["level"]:
                                        end_line = i
                                        break

                                text_block = "\n".join(lines[start_line:end_line])
                                text_block = reduce_internal_titles(text_block)

                                yaml_metadata = f"---\n归属母目录: [[{parent_dir}]]\n"
                                if title["parent_path"]:
                                    yaml_metadata += "层级路径:\n"
                                    for ancestor in title["parent_path"]:
                                        yaml_metadata += f"  - [[{ancestor}]]\n"
                                yaml_metadata += "---\n\n"
                                final_content = yaml_metadata + text_block

                                filename_parts = (
                                    [parent_dir] + title["parent_path"] + [sanitize_filename(title["content"])]
                                )
                                filename = "-".join([p for p in filename_parts if p]) + ".md"
                                if len(filename) > 150:
                                    filename = filename[:147] + "..." + ".md"

                                zipf.writestr(filename, final_content.encode("utf-8"))
                                generated_files.append(filename[:-3])

                            # 总路由文件
                            route_content = "# 总路由\n\n"
                            for file_name in generated_files:
                                route_content += f"- [[{file_name}]]\n"
                            zipf.writestr("00_总路由.md", route_content.encode("utf-8"))

                        zip_buffer.seek(0)
                        st.download_button(
                            "⬇️ 下载 ZIP 包", data=zip_buffer,
                            file_name=f"{base_filename}_splitter_output.zip", mime="application/zip",
                        )
                        st.success("✅ 生成并打包完成！")
                    except Exception as e:
                        st.error(f"❌ 生成失败：{str(e)}")

st.markdown("---")
st.markdown("© 2026 通用知识库切片引擎 - 极简架构，纯粹解析")
