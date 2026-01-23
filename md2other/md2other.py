#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Markdown 文件格式转换工具（纯 Python 实现）
支持将 Markdown 文件转换为 PDF、EPUB、DOCX 等格式

参考实现：
- md2docx-master: DOCX 转换思路
- md2epub-master: EPUB 转换思路
- md2pdf-master: PDF 转换思路

不再依赖 pandoc / LaTeX / wkhtmltopdf / weasyprint 等外部程序。
特别注意目录跳转和网页链接的保存。
"""

import os
import sys
import re
import argparse
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import List, Tuple, Optional, Dict

# 设置输出编码（Windows 控制台兼容）
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import markdown
from markdown.extensions import tables, toc, fenced_code, codehilite
from bs4 import BeautifulSoup

from fpdf import FPDF
from ebooklib import epub
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# 导出转换函数供外部调用
__all__ = ['convert_md_to_pdf', 'convert_md_to_epub', 'convert_md_to_txt', 'convert_md_to_docx']


def read_markdown(md_file: str) -> str:
    """读取 Markdown 文件内容"""
    with open(md_file, 'r', encoding='utf-8') as f:
        return f.read()


def generate_anchor_id(text: str) -> str:
    """
    生成锚点 ID，与 Markdown 的标题 ID 生成规则兼容
    参考：Markdown 的 toc 扩展会将标题转换为小写（英文），移除特殊字符，用连字符连接
    特别注意：需要与 Markdown 的 toc 扩展生成的 ID 保持一致
    Python-Markdown 的 toc 扩展使用 slugify 函数生成 ID
    """
    # Python-Markdown 的 toc 扩展通常：
    # 1. 将英文转换为小写
    # 2. 移除特殊字符（保留中文字符、字母、数字、连字符、空格）
    # 3. 将空格和多个连字符替换为单个连字符
    # 4. 移除首尾的连字符和空格
    
    # 先移除特殊字符，保留中文字符、字母、数字、连字符和空格
    anchor_id = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', text)
    # 将多个空格和连字符替换为单个连字符
    anchor_id = re.sub(r'[\s-]+', '-', anchor_id)
    # 移除首尾的连字符
    anchor_id = anchor_id.strip('-')
    
    # 注意：Markdown 的 toc 扩展通常不将中文字符转换为小写
    # 但会将英文转换为小写，这里我们保持原样以匹配实际行为
    return anchor_id


def markdown_to_html(md_text: str) -> str:
    """Markdown 转 HTML（带扩展支持）"""
    extensions = [
        'extra',           # 表格、缩写等
        'tables',          # 表格支持
        'toc',             # 目录生成（会自动为标题添加 id）
        'fenced_code',     # 代码块
        'codehilite',      # 代码高亮
        'nl2br',           # 换行转 <br>
    ]
    # 配置 toc 扩展，确保生成锚点 ID
    extension_configs = {
        'toc': {
            'permalink': False,  # 不添加永久链接
            'baselevel': 1,      # 基础级别
        }
    }
    return markdown.markdown(md_text, extensions=extensions, extension_configs=extension_configs)


def html_to_plain_text(html: str) -> str:
    """HTML 转纯文本，保留基本换行"""
    soup = BeautifulSoup(html, 'html.parser')
    # 用换行连接所有文本块
    lines = [s for s in soup.stripped_strings]
    return '\n'.join(lines)


# ==================== PDF 转换（改进版 FPDF） ==================== #

class PDF(FPDF):
    """改进的 PDF 类，支持更好的 Markdown 渲染，特别注意目录跳转和链接"""
    
    def __init__(self):
        super().__init__()
        self.chinese_font = None
        self.heading_ids = {}  # 存储标题文本到书签的映射
        self.setup_fonts()
    
    def setup_fonts(self):
        """设置中文字体"""
        candidate_fonts = [
            r'C:\Windows\Fonts\msyh.ttc',      # Microsoft YaHei
            r'C:\Windows\Fonts\simhei.ttf',     # 黑体
            r'C:\Windows\Fonts\simsun.ttc',     # 宋体
            r'C:\Windows\Fonts\simkai.ttf',     # 楷体
        ]
        
        for font_path in candidate_fonts:
            if os.path.exists(font_path):
                try:
                    # fpdf2 新版本不再需要 uni 参数
                    self.add_font('CJK', '', font_path)
                    self.chinese_font = 'CJK'
                    break
                except Exception:
                    continue
        
        if not self.chinese_font:
            # 如果没有中文字体，使用 Arial（中文会显示为方框）
            self.chinese_font = 'Arial'
    
    def header(self):
        """页眉（可选）"""
        pass
    
    def footer(self):
        """页脚添加页码"""
        self.set_y(-15)
        if self.chinese_font == 'CJK':
            self.set_font('CJK', size=8)
        else:
            self.set_font('Arial', 'I', 8)
        # 使用新的参数替代已弃用的 ln 参数
        from fpdf.enums import XPos, YPos
        self.cell(0, 10, f'第 {self.page_no()} 页', new_x=XPos.LEFT, new_y=YPos.TOP, align='C')
    
    def add_markdown_content(self, md_text: str, md_path: Path = None):
        """添加 Markdown 内容到 PDF，特别注意处理链接"""
        html = markdown_to_html(md_text)
        soup = BeautifulSoup(html, 'html.parser')
        
        # 首先处理所有标题，生成 ID 映射
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text().strip()
            heading_id = generate_anchor_id(heading_text)
            heading['id'] = heading_id
            self.heading_ids[heading_id] = heading_text
        
        # 处理各个元素
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'table', 'pre', 'blockquote', 'hr', 'img']):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                heading_text = element.get_text().strip()
                heading_id = element.get('id', generate_anchor_id(heading_text))
                self.add_heading(heading_text, level, heading_id)
            elif element.name == 'p':
                self.add_paragraph_with_links(element, md_path)
            elif element.name in ['ul', 'ol']:
                self.add_list(element, md_path)
            elif element.name == 'table':
                self.add_table(element)
            elif element.name == 'pre':
                self.add_code_block(element.get_text())
            elif element.name == 'blockquote':
                self.add_blockquote(element.get_text())
            elif element.name == 'hr':
                self.ln(5)
                self.line(10, self.get_y(), 200, self.get_y())
                self.ln(5)
            elif element.name == 'img':
                self.add_image(element, md_path)
    
    def add_heading(self, text: str, level: int, heading_id: str = None):
        """添加标题（带书签支持目录跳转）"""
        if self.get_y() > 250:
            self.add_page()
        
        sizes = {1: 18, 2: 16, 3: 14, 4: 12, 5: 11, 6: 10}
        size = sizes.get(level, 12)
        
        self.ln(5)
        if self.chinese_font == 'CJK':
            self.set_font('CJK', size=size)
        else:
            self.set_font('Arial', 'B', size)
        
        # 添加书签（支持目录跳转）- 使用 fpdf2 的 start_section 方法
        bookmark_name = text[:50]  # 限制书签名称长度
        if heading_id:
            self.heading_ids[heading_id] = text
        # fpdf2 使用 start_section 方法，level 从 0 开始（0 是顶级）
        self.start_section(bookmark_name, level=level - 1)
        
        self.multi_cell(0, size * 0.6, text)
        self.ln(3)
    
    def add_paragraph_with_links(self, p_element, md_path: Path = None):
        """添加段落，支持链接"""
        if self.get_y() > 270:
            self.add_page()
        
        if self.chinese_font == 'CJK':
            self.set_font('CJK', size=11)
        else:
            self.set_font('Arial', size=11)
        
        # 处理段落中的链接
        text_parts = []
        for content in p_element.contents:
            if isinstance(content, str):
                text_parts.append(('text', content))
            elif hasattr(content, 'name'):
                if content.name == 'a':
                    href = content.get('href', '')
                    link_text = content.get_text()
                    if href.startswith('#'):
                        # 内部锚点链接，显示文本
                        text_parts.append(('link', link_text, href))
                    elif href.startswith(('http://', 'https://')):
                        # 外部链接，显示文本和 URL
                        text_parts.append(('link', link_text, href))
                    else:
                        text_parts.append(('text', link_text))
                else:
                    text_parts.append(('text', content.get_text() if hasattr(content, 'get_text') else str(content)))
        
        # 组合文本（PDF 中链接显示为文本+URL）
        full_text = ''
        for part in text_parts:
            if part[0] == 'text':
                full_text += part[1]
            elif part[0] == 'link':
                link_text = part[1]
                link_url = part[2]
                if link_url.startswith('#'):
                    # 内部链接，只显示文本
                    full_text += link_text
                else:
                    # 外部链接，显示文本和 URL
                    full_text += f"{link_text} ({link_url})"
        
        if full_text.strip():
            self.multi_cell(0, 6, full_text)
            self.ln(2)
    
    def add_list(self, list_element, md_path: Path = None):
        """添加列表，支持链接"""
        items = list_element.find_all('li', recursive=False)
        for item in items:
            if self.get_y() > 270:
                self.add_page()
            
            if self.chinese_font == 'CJK':
                self.set_font('CJK', size=11)
            else:
                self.set_font('Arial', size=11)
            
            # 处理列表项中的链接
            item_text = ''
            for content in item.contents:
                if isinstance(content, str):
                    item_text += content
                elif hasattr(content, 'name') and content.name == 'a':
                    href = content.get('href', '')
                    link_text = content.get_text()
                    if href.startswith(('http://', 'https://')):
                        item_text += f"{link_text} ({href})"
                    else:
                        item_text += link_text
                else:
                    item_text += content.get_text() if hasattr(content, 'get_text') else str(content)
            
            # 使用 set_x 实现缩进
            current_x = self.get_x()
            self.set_x(current_x + 10)  # 缩进 10mm
            
            bullet = '• ' if list_element.name == 'ul' else '1. '
            self.multi_cell(0, 6, bullet + item_text)
            self.ln(1)
    
    def add_image(self, img_element, md_path: Path = None):
        """添加图片到 PDF"""
        src = img_element.get('src', '')
        if not src:
            return
        
        # 解码 URL 编码的路径
        try:
            decoded_src = unquote(src)
        except Exception:
            decoded_src = src
        
        # 处理网络图片
        if src.startswith(('http://', 'https://')):
            try:
                import requests
                from io import BytesIO
                
                response = requests.get(src, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code == 200:
                    img_data = BytesIO(response.content)
                    # 获取图片尺寸
                    from PIL import Image
                    img = Image.open(img_data)
                    img_width, img_height = img.size
                    
                    # 计算适合 PDF 的尺寸（最大宽度 180mm）
                    max_width = 180
                    if img_width > 0:
                        ratio = min(max_width / (img_width * 0.264583), max_width / (img_width * 0.264583))
                        width = img_width * 0.264583 * ratio
                        height = img_height * 0.264583 * ratio
                    else:
                        width = max_width
                        height = max_width
                    
                    img_data.seek(0)
                    self.image(img_data, x=15, y=self.get_y(), w=width, h=height)
                    self.ln(height + 5)
            except ImportError:
                alt = img_element.get('alt', '[图片]')
                self.add_paragraph(f"[图片: {alt}] (需要安装 requests 和 Pillow 库)")
            except Exception as e:
                alt = img_element.get('alt', '[图片]')
                self.add_paragraph(f"[图片: {alt}] (无法加载: {str(e)})")
        
        # 处理本地图片
        else:
            # 尝试多种路径
            possible_paths = []
            if md_path:
                md_dir = md_path.parent
                possible_paths.extend([
                    src,
                    decoded_src,
                    str(md_dir / src),
                    str(md_dir / decoded_src),
                    str(md_dir / 'images' / src),
                    str(md_dir / 'images' / decoded_src),
                ])
            else:
                possible_paths.extend([src, decoded_src])
            
            img_found = False
            for img_path in possible_paths:
                img_path = os.path.normpath(img_path)
                if os.path.exists(img_path) and os.path.isfile(img_path):
                    try:
                        # 获取图片尺寸
                        from PIL import Image
                        img = Image.open(img_path)
                        img_width, img_height = img.size
                        
                        # 计算适合 PDF 的尺寸
                        max_width = 180
                        if img_width > 0:
                            ratio = min(max_width / (img_width * 0.264583), max_width / (img_width * 0.264583))
                            width = img_width * 0.264583 * ratio
                            height = img_height * 0.264583 * ratio
                        else:
                            width = max_width
                            height = max_width
                        
                        self.image(img_path, x=15, y=self.get_y(), w=width, h=height)
                        self.ln(height + 5)
                        img_found = True
                        break
                    except ImportError:
                        # 如果没有 Pillow，尝试直接使用 FPDF 的 image 方法
                        try:
                            self.image(img_path, x=15, y=self.get_y(), w=100)
                            self.ln(50)
                            img_found = True
                            break
                        except Exception:
                            pass
                    except Exception:
                        continue
            
            if not img_found:
                alt = img_element.get('alt', '[图片]')
                self.add_paragraph(f"[图片: {alt}] (未找到: {decoded_src})")
    
    def add_paragraph(self, text: str):
        """添加段落（简单版本）"""
        if self.get_y() > 270:
            self.add_page()
        
        if self.chinese_font == 'CJK':
            self.set_font('CJK', size=11)
        else:
            self.set_font('Arial', size=11)
        
        # 处理粗体和斜体（简单处理）
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 粗体
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # 斜体
        
        self.multi_cell(0, 6, text)
        self.ln(2)
    
    def add_table(self, table_element):
        """添加表格（简化版）"""
        rows = table_element.find_all('tr')
        if not rows:
            return
        
        if self.get_y() > 250:
            self.add_page()
        
        # 获取列数
        first_row_cells = rows[0].find_all(['th', 'td'])
        if not first_row_cells:
            return
        
        cols = len(first_row_cells)
        col_width = 190 / cols if cols > 0 else 190
        
        max_height = 0
        for row_idx, row in enumerate(rows):
            cells = row.find_all(['th', 'td'])
            y_start = self.get_y()
            x_start = 10
            
            row_max_height = 0
            for cell_idx, cell in enumerate(cells):
                if cell_idx >= cols:
                    break
                text = cell.get_text().strip()
                if self.chinese_font == 'CJK':
                    self.set_font('CJK', size=9, style='B' if cell.name == 'th' else '')
                else:
                    self.set_font('Arial', size=9, style='B' if cell.name == 'th' else '')
                
                # 计算文本高度
                text_height = len(text.split('\n')) * 5 + 2
                row_max_height = max(row_max_height, text_height)
                
                self.set_xy(x_start, y_start)
                self.multi_cell(col_width, 5, text, border=1, align='L')
                x_start += col_width
            
            max_height = max(max_height, row_max_height)
            self.set_y(y_start + max_height)
            self.ln(2)
    
    def add_code_block(self, code: str):
        """添加代码块"""
        if self.get_y() > 260:
            self.add_page()
        
        if self.chinese_font == 'CJK':
            self.set_font('CJK', size=9)
        else:
            self.set_font('Courier', size=9)
        
        # 使用 set_x 实现缩进
        current_x = self.get_x()
        self.set_x(current_x + 5)  # 缩进 5mm
        
        # 简单处理：每行代码单独添加
        for line in code.split('\n'):
            if line.strip():
                self.multi_cell(0, 5, line)
            else:
                self.ln(3)
    
    def add_blockquote(self, text: str):
        """添加引用块"""
        if self.get_y() > 270:
            self.add_page()
        
        if self.chinese_font == 'CJK':
            self.set_font('CJK', 'I', size=10)
        else:
            self.set_font('Arial', 'I', size=10)
        
        # 使用 set_x 实现缩进
        current_x = self.get_x()
        self.set_x(current_x + 10)  # 缩进 10mm
        
        self.multi_cell(0, 6, text)
        self.ln(2)


def convert_md_to_pdf(md_file: str, output_file: str) -> bool:
    """将 Markdown 转为 PDF（支持目录跳转和图片）"""
    try:
        md_path = Path(md_file)
        md_text = read_markdown(md_file)
        
        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(15, 15, 15)
        pdf.add_page()
        
        # 设置默认字体
        if pdf.chinese_font == 'CJK':
            pdf.set_font('CJK', size=11)
        else:
            pdf.set_font('Arial', size=11)
        
        # 添加内容（传入 md_path 以便查找图片）
        pdf.add_markdown_content(md_text, md_path)
        
        # 确保输出目录存在
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pdf.output(str(out_path))
        return True
    except Exception as e:
        print(f"转换 PDF 时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== EPUB 转换（参考 md2epub 思路） ====================

def extract_headings_from_html(html: str) -> List[Tuple[str, str, int]]:
    """从 HTML 中提取标题，返回 (标题文本, 锚点ID, 级别) 列表"""
    soup = BeautifulSoup(html, 'html.parser')
    headings = []
    
    # 用于确保ID唯一性
    used_ids = set()
    id_counter = {}
    
    for i in range(1, 7):
        for heading in soup.find_all(f'h{i}'):
            text = heading.get_text().strip()
            
            # 检查标题是否已经有 id 属性（可能是 Markdown toc 扩展添加的）
            existing_id = heading.get('id', '')
            if existing_id:
                heading_id = existing_id
            else:
                # 生成锚点ID（与 Markdown 的标题ID生成规则兼容）
                heading_id = generate_anchor_id(text)
            
            # 如果ID为空或已使用，添加数字后缀
            if not heading_id or heading_id in used_ids:
                base_id = heading_id or 'heading'
                if base_id not in id_counter:
                    id_counter[base_id] = 0
                id_counter[base_id] += 1
                heading_id = f"{base_id}-{id_counter[base_id]}"
            
            used_ids.add(heading_id)
            
            # 确保标题有 id 属性（兼容微信阅读等阅读器）
            heading['id'] = heading_id
            
            headings.append((text, heading_id, i))
    
    return headings


def convert_md_to_epub(md_file: str, output_file: str) -> bool:
    """
    将 Markdown 文件转换为 EPUB（参考 md2epub 实现）
    - 自动从 h1/h2/h3 生成目录
    - 支持图片（网络和本地）
    - 支持代码高亮
    - 特别注意目录跳转和网页链接的保存
    """
    try:
        md_path = Path(md_file)
        md_text = read_markdown(md_file)
        html = markdown_to_html(md_text)
        
        # 创建 EPUB 书籍
        book = epub.EpubBook()
        
        # 设置元数据
        title = md_path.stem
        book.set_title(title)
        book.set_language('zh-CN')
        book.add_author('LOFTER-Crawl')
        book.set_identifier(f'lofter-{title}')
        
        # 提取标题用于生成目录
        headings = extract_headings_from_html(html)
        
        # 处理图片
        soup = BeautifulSoup(html, 'html.parser')
        img_counter = 0
        img_map = {}  # 原始src -> 新路径
        
        # 确保图片目录存在（在 EPUB 结构中）
        images_dir = 'images'
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if not src:
                continue
            
            # 解码 URL 编码的路径
            try:
                decoded_src = unquote(src)
            except Exception:
                decoded_src = src
            
            # 处理网络图片
            if src.startswith(('http://', 'https://')):
                try:
                    try:
                        import requests
                    except ImportError:
                        # 如果没有 requests，跳过网络图片
                        alt = img.get('alt', '[图片]')
                        img.replace_with(alt)
                        continue
                    
                    response = requests.get(src, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                    if response.status_code == 200:
                        img_data = response.content
                        img_ext = os.path.splitext(urlparse(src).path)[1] or '.jpg'
                        if not img_ext or img_ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                            img_ext = '.jpg'
                        img_name = f'image_{img_counter}{img_ext}'
                        img_counter += 1
                        
                        # 确定媒体类型
                        media_type = 'image/jpeg'
                        if img_ext.lower() in ['.png']:
                            media_type = 'image/png'
                        elif img_ext.lower() in ['.gif']:
                            media_type = 'image/gif'
                        
                        # 添加到 EPUB
                        img_item = epub.EpubItem(
                            uid=f'img_{img_counter}',
                            file_name=f'images/{img_name}',
                            media_type=media_type,
                            content=img_data
                        )
                        book.add_item(img_item)
                        img_map[src] = f'images/{img_name}'
                        img['src'] = f'images/{img_name}'
                    else:
                        alt = img.get('alt', '[图片]')
                        img.replace_with(alt)
                except Exception as e:
                    # 如果下载失败，保留原始链接或替换为文本
                    alt = img.get('alt', '[图片]')
                    img.replace_with(alt)
            
            # 处理本地图片
            else:
                # 尝试多种路径解析方式
                possible_paths = []
                md_dir = md_path.parent
                
                # 1. 原始路径（绝对路径或相对于当前工作目录）
                possible_paths.append(src)
                # 2. 解码后的路径
                possible_paths.append(decoded_src)
                # 3. 相对于 Markdown 文件的路径
                possible_paths.append(str(md_dir / src))
                possible_paths.append(str(md_dir / decoded_src))
                # 4. 相对于 Markdown 文件所在目录的 images 子目录
                possible_paths.append(str(md_dir / 'images' / src))
                possible_paths.append(str(md_dir / 'images' / decoded_src))
                # 5. 尝试在 result 目录下查找（如果 Markdown 文件在 result 目录下）
                if 'result' in str(md_dir):
                    # 在同名目录下查找（例如：result/作者_吃瓜惹/图片文件）
                    author_dir = md_dir
                    possible_paths.append(str(author_dir / src))
                    possible_paths.append(str(author_dir / decoded_src))
                    # 在 result 的父目录查找
                    parent_dir = md_dir.parent
                    possible_paths.append(str(parent_dir / src))
                    possible_paths.append(str(parent_dir / decoded_src))
                    # 在 LOFTER-Crawl 目录下查找
                    crawl_dir = parent_dir.parent if parent_dir.name == 'result' else parent_dir
                    possible_paths.append(str(crawl_dir / src))
                    possible_paths.append(str(crawl_dir / decoded_src))
                
                img_found = False
                for img_path in possible_paths:
                    # 去重并检查路径
                    img_path = os.path.normpath(img_path)
                    if os.path.exists(img_path) and os.path.isfile(img_path):
                        try:
                            with open(img_path, 'rb') as f:
                                img_data = f.read()
                            
                            # 获取文件扩展名
                            img_ext = os.path.splitext(img_path)[1] or '.jpg'
                            if not img_ext or img_ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                img_ext = '.jpg'
                            
                            img_name = f'image_{img_counter}{img_ext}'
                            img_counter += 1
                            
                            # 确定媒体类型
                            media_type = 'image/jpeg'
                            if img_ext.lower() in ['.png']:
                                media_type = 'image/png'
                            elif img_ext.lower() in ['.gif']:
                                media_type = 'image/gif'
                            elif img_ext.lower() in ['.webp']:
                                media_type = 'image/webp'
                            
                            # 添加到 EPUB
                            img_item = epub.EpubItem(
                                uid=f'img_{img_counter}',
                                file_name=f'images/{img_name}',
                                media_type=media_type,
                                content=img_data
                            )
                            book.add_item(img_item)
                            img['src'] = f'images/{img_name}'
                            img_found = True
                            print(f"  找到图片: {img_path} -> images/{img_name}")
                            break
                        except Exception as e:
                            # 如果读取失败，继续尝试下一个路径
                            continue
                
                if not img_found:
                    # 无法找到图片文件，保留图片标签但显示替代文本
                    alt = img.get('alt', '[图片]')
                    # 保留 img 标签，但添加 alt 文本和错误信息
                    if not img.get('alt'):
                        img['alt'] = alt
                    # 在 alt 中显示路径信息以便调试
                    img['alt'] = f"{alt} (未找到: {decoded_src})"
                    print(f"  警告: 未找到图片文件: {decoded_src} (原始路径: {src})")
        
        # 确保所有链接都是可点击的（兼容多种阅读器）
        # 特别注意：保持网页链接和目录跳转链接
        # 创建标题 ID 映射表（支持多种匹配方式）
        heading_id_map = {}  # 标题文本 -> id
        heading_id_by_generated = {}  # 生成的ID -> 实际ID
        all_heading_ids = set()  # 所有标题 ID 集合
        
        for heading_text, heading_id, level in headings:
            heading_id_map[heading_text] = heading_id
            all_heading_ids.add(heading_id)
            generated_id = generate_anchor_id(heading_text)
            heading_id_by_generated[generated_id] = heading_id
            # 也存储原始文本的映射
            heading_id_by_generated[heading_text] = heading_id
            # 存储原始 ID 的映射（用于直接匹配）
            heading_id_by_generated[heading_id] = heading_id
        
        # 处理所有链接，确保锚点链接指向正确的标题 ID
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if href:
                # 如果是外部链接（http/https），确保格式正确
                if href.startswith(('http://', 'https://')):
                    # 确保 href 属性存在且正确
                    link['href'] = href
                    # 对于 EPUB，外部链接需要特殊处理
                    # 某些阅读器可能不支持外部链接，但保持格式正确
                    # 移除可能不兼容的属性，但保留 href
                    for attr in ['target', 'rel', 'class', 'style']:
                        if link.get(attr):
                            del link[attr]
                # 如果是内部锚点链接（以 # 开头），确保格式正确
                elif href.startswith('#'):
                    # 确保格式正确
                    anchor_id = href[1:]  # 去掉#
                    original_anchor_id = anchor_id
                    
                    # 如果锚点 ID 不存在于标题 ID 中，尝试匹配
                    if anchor_id and anchor_id not in all_heading_ids:
                        # 尝试从链接文本生成 ID
                        link_text = link.get_text().strip()
                        generated_id = generate_anchor_id(link_text)
                        
                        # 查找匹配的标题 ID
                        matched_id = None
                        # 1. 直接匹配原始锚点 ID（可能是 Markdown toc 生成的，但格式略有不同）
                        if original_anchor_id in heading_id_by_generated:
                            matched_id = heading_id_by_generated[original_anchor_id]
                        # 2. 匹配生成的 ID
                        elif generated_id in heading_id_by_generated:
                            matched_id = heading_id_by_generated[generated_id]
                        # 3. 匹配链接文本
                        elif link_text in heading_id_by_generated:
                            matched_id = heading_id_by_generated[link_text]
                        # 4. 遍历所有标题查找最接近的匹配（模糊匹配）
                        else:
                            for heading_text, heading_id, level in headings:
                                # 尝试多种匹配方式
                                if (generate_anchor_id(heading_text) == generated_id or 
                                    heading_text == link_text or
                                    heading_text.startswith(link_text) or
                                    link_text in heading_text):
                                    matched_id = heading_id
                                    break
                        
                        if matched_id:
                            anchor_id = matched_id
                    
                    # 确保链接格式正确（EPUB 中内部链接使用 #id 格式）
                    if anchor_id:
                        link['href'] = f'#{anchor_id}'
                    else:
                        # 如果找不到匹配，保留原始链接（可能阅读器能处理）
                        link['href'] = f'#{original_anchor_id}'
                    
                    # 移除所有可能不兼容的属性
                    for attr in ['target', 'rel', 'class', 'style']:
                        if link.get(attr):
                            del link[attr]
                # 如果是相对路径
                else:
                    # 移除所有可能不兼容的属性
                    for attr in ['target', 'rel', 'class', 'style']:
                        if link.get(attr):
                            del link[attr]
        
        # 创建主章节
        chapter = epub.EpubHtml(
            title=title,
            file_name='chapter1.xhtml',
            lang='zh-CN'
        )
        
        # 确保 HTML 内容格式正确，特别是链接
        html_content = str(soup)
        # 确保所有链接都是有效的 XHTML 格式
        chapter.content = html_content
        book.add_item(chapter)
        
        # 生成目录结构（兼容多种阅读器）
        # 微信阅读需要更标准的格式，WPS也需要正确的链接格式
        toc_items = []
        nav_map = []
        play_order = 1
        
        current_h1 = None
        for heading_text, heading_id, level in headings:
            # 确保链接格式正确（兼容微信阅读和WPS）
            # 使用相对路径，确保锚点ID正确
            link_href = f'chapter1.xhtml#{heading_id}'
            
            if level == 1:
                # 创建链接，确保格式正确
                nav_point = epub.Link(link_href, heading_text, heading_id)
                nav_map.append((nav_point, []))
                current_h1 = len(nav_map) - 1
                play_order += 1
            elif level == 2 and current_h1 is not None:
                nav_point = epub.Link(link_href, heading_text, heading_id)
                nav_map[current_h1][1].append(nav_point)
                play_order += 1
            elif level >= 3 and current_h1 is not None:
                # 也支持三级标题（如果需要）
                nav_point = epub.Link(link_href, heading_text, heading_id)
                if len(nav_map[current_h1][1]) > 0:
                    # 如果有二级标题，添加到最后一个二级标题下
                    pass  # 简化处理，只支持两级
                else:
                    nav_map[current_h1][1].append(nav_point)
                play_order += 1
        
        # 构建 TOC（确保格式兼容）
        if nav_map:
            toc_items = []
            for h1_item, h2_items in nav_map:
                if h2_items:
                    # 有子项的情况
                    toc_items.append((h1_item, h2_items))
                else:
                    # 只有一级标题
                    toc_items.append(h1_item)
            book.toc = toc_items
        else:
            # 如果没有找到标题，创建一个默认的目录项
            book.toc = [epub.Link('chapter1.xhtml', title, 'chapter1')]
        
        # 设置书脊
        book.spine = ['nav', chapter]
        
        # 添加导航文件
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 添加 CSS 样式
        style = '''
        body {
            font-family: "Microsoft YaHei", "SimSun", serif;
            line-height: 1.6;
            margin: 1em;
        }
        h1, h2, h3, h4, h5, h6 {
            margin-top: 1em;
            margin-bottom: 0.5em;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
        }
        pre {
            background-color: #f4f4f4;
            padding: 1em;
            border-radius: 5px;
            overflow-x: auto;
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        table th, table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        table th {
            background-color: #f2f2f2;
        }
        img {
            max-width: 100%;
            height: auto;
        }
        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 1em;
            margin-left: 0;
            color: #666;
        }
        a {
            color: #0066cc;
            text-decoration: underline;
            cursor: pointer;
        }
        a:visited {
            color: #551a8b;
        }
        a:hover {
            color: #0052a3;
        }
        a[href^="http://"], a[href^="https://"] {
            color: #0066cc;
            text-decoration: underline;
        }
        '''
        
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)
        chapter.add_item(nav_css)
        
        # 保存 EPUB
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        epub.write_epub(str(out_path), book, {})
        return True
    except Exception as e:
        print(f"转换 EPUB 时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== TXT 转换 ====================

def convert_md_to_txt(md_file: str, output_file: str) -> bool:
    """将 Markdown 转为纯文本"""
    try:
        md_text = read_markdown(md_file)
        html = markdown_to_html(md_text)
        plain_text = html_to_plain_text(html)
        
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(plain_text)
        return True
    except Exception as e:
        print(f"转换 TXT 时出错: {e}")
        return False


# ==================== DOCX 转换（参考 md2docx 思路，改进版） ====================

def add_hyperlink(paragraph, text: str, url: str):
    """
    在段落中添加超链接
    参考：https://github.com/python-openxml/python-docx/issues/74
    """
    part = paragraph.part
    r_id = part.relate_to(url, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink', is_external=True)
    
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)
    
    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    
    # 设置链接样式（蓝色、下划线）
    c = OxmlElement('w:color')
    c.set(qn('w:val'), '0000FF')
    rPr.append(c)
    
    u = OxmlElement('w:u')
    u.set(qn('w:val'), 'single')
    rPr.append(u)
    
    new_run.append(rPr)
    new_run.text = text
    hyperlink.append(new_run)
    
    paragraph._p.append(hyperlink)
    return hyperlink


def parse_markdown_to_docx_elements(md_text: str, md_file: str = None) -> List[dict]:
    """解析 Markdown 文本，返回结构化元素列表，特别注意链接处理"""
    html = markdown_to_html(md_text)
    soup = BeautifulSoup(html, 'html.parser')
    
    elements = []
    
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'table', 'pre', 'blockquote', 'hr', 'img']):
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(element.name[1])
            heading_text = element.get_text().strip()
            heading_id = generate_anchor_id(heading_text)
            elements.append({
                'type': 'heading',
                'level': level,
                'text': heading_text,
                'id': heading_id
            })
        elif element.name == 'p':
            # 处理段落中的格式（粗体、斜体、链接等）
            runs = []
            for content in element.contents:
                if isinstance(content, str):
                    runs.append({'text': content, 'bold': False, 'italic': False})
                elif content.name == 'strong' or content.name == 'b':
                    runs.append({'text': content.get_text(), 'bold': True, 'italic': False})
                elif content.name == 'em' or content.name == 'i':
                    runs.append({'text': content.get_text(), 'bold': False, 'italic': True})
                elif content.name == 'a':
                    href = content.get('href', '')
                    link_text = content.get_text()
                    runs.append({
                        'text': link_text, 
                        'bold': False, 
                        'italic': False, 
                        'link': href,
                        'is_link': True
                    })
                else:
                    runs.append({'text': content.get_text() if hasattr(content, 'get_text') else str(content), 'bold': False, 'italic': False})
            
            elements.append({
                'type': 'paragraph',
                'runs': runs
            })
        elif element.name in ['ul', 'ol']:
            items = []
            for li in element.find_all('li', recursive=False):
                # 处理列表项中的链接
                item_runs = []
                for content in li.contents:
                    if isinstance(content, str):
                        item_runs.append({'text': content, 'bold': False, 'italic': False})
                    elif hasattr(content, 'name') and content.name == 'a':
                        href = content.get('href', '')
                        link_text = content.get_text()
                        item_runs.append({
                            'text': link_text,
                            'bold': False,
                            'italic': False,
                            'link': href,
                            'is_link': True
                        })
                    else:
                        item_runs.append({'text': content.get_text() if hasattr(content, 'get_text') else str(content), 'bold': False, 'italic': False})
                items.append(item_runs)
            elements.append({
                'type': 'list',
                'style': 'bullet' if element.name == 'ul' else 'number',
                'items': items
            })
        elif element.name == 'table':
            rows = []
            for tr in element.find_all('tr'):
                cells = []
                for cell in tr.find_all(['th', 'td']):
                    cells.append(cell.get_text())
                rows.append(cells)
            elements.append({
                'type': 'table',
                'rows': rows,
                'header': rows[0] if rows else []
            })
        elif element.name == 'pre':
            elements.append({
                'type': 'code',
                'text': element.get_text()
            })
        elif element.name == 'blockquote':
            elements.append({
                'type': 'quote',
                'text': element.get_text()
            })
        elif element.name == 'hr':
            elements.append({
                'type': 'hr'
            })
        elif element.name == 'img':
            elements.append({
                'type': 'image',
                'src': element.get('src', ''),
                'alt': element.get('alt', '')
            })
    
    return elements


def convert_md_to_docx(md_file: str, output_file: str) -> bool:
    """
    将 Markdown 转为 DOCX（参考 md2docx 思路，改进版）
    - 支持标题层级
    - 支持粗体、斜体、链接（真正的超链接）
    - 支持列表（有序和无序）
    - 支持表格
    - 支持代码块
    - 支持图片
    - 特别注意目录跳转和网页链接的保存
    """
    try:
        md_path = Path(md_file)
        md_text = read_markdown(md_file)
        elements = parse_markdown_to_docx_elements(md_text, md_file)
        
        doc = Document()
        
        # 设置默认字体
        style = doc.styles['Normal']
        font = style.font
        font.name = '宋体'
        font.size = Pt(12)
        style._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        
        # 存储标题的书签 ID，用于内部链接跳转
        heading_bookmarks = {}  # heading_id -> bookmark_name
        bookmark_id_counter = 0  # 书签 ID 计数器
        
        for elem in elements:
            if elem['type'] == 'heading':
                level = elem['level']
                heading_text = elem['text']
                heading_id = elem.get('id', generate_anchor_id(heading_text))
                
                # 添加标题
                para = doc.add_heading(heading_text, level=level)
                
                # 为标题添加书签，以便内部链接可以跳转
                # 在 Word 中，书签用于内部跳转
                bookmark_name = heading_id[:50]  # 限制长度
                bookmark_id_counter += 1
                bookmark_id = str(bookmark_id_counter)
                
                # 创建书签
                run = para.runs[0] if para.runs else para.add_run(heading_text)
                start = run._element
                bookmark_start = OxmlElement('w:bookmarkStart')
                bookmark_start.set(qn('w:id'), bookmark_id)
                bookmark_start.set(qn('w:name'), bookmark_name)
                start.addprevious(bookmark_start)
                
                bookmark_end = OxmlElement('w:bookmarkEnd')
                bookmark_end.set(qn('w:id'), bookmark_id)
                start.addnext(bookmark_end)
                
                heading_bookmarks[heading_id] = bookmark_name
            
            elif elem['type'] == 'paragraph':
                para = doc.add_paragraph()
                for run_data in elem['runs']:
                    if run_data.get('is_link') and run_data.get('link'):
                        # 添加真正的超链接
                        href = run_data['link']
                        link_text = run_data['text']
                        if href.startswith(('http://', 'https://')):
                            # 外部链接
                            add_hyperlink(para, link_text, href)
                        elif href.startswith('#'):
                            # 内部锚点链接 - 在 DOCX 中使用书签跳转
                            anchor_id = href[1:]  # 去掉 #
                            if anchor_id in heading_bookmarks:
                                # 创建内部链接到书签
                                bookmark_name = heading_bookmarks[anchor_id]
                                # 使用 Word 的内部链接格式
                                part = para.part
                                r_id = part.relate_to(f'#{bookmark_name}', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink', is_external=False)
                                
                                hyperlink = OxmlElement('w:hyperlink')
                                hyperlink.set(qn('w:anchor'), bookmark_name)
                                
                                new_run = OxmlElement('w:r')
                                rPr = OxmlElement('w:rPr')
                                c = OxmlElement('w:color')
                                c.set(qn('w:val'), '0000FF')
                                rPr.append(c)
                                u = OxmlElement('w:u')
                                u.set(qn('w:val'), 'single')
                                rPr.append(u)
                                new_run.append(rPr)
                                new_run.text = link_text
                                hyperlink.append(new_run)
                                para._p.append(hyperlink)
                            else:
                                # 如果找不到书签，显示为蓝色文本
                                run = para.add_run(link_text)
                                run.font.color.rgb = RGBColor(0, 0, 255)  # 蓝色
                        else:
                            # 其他链接
                            run = para.add_run(link_text)
                            run.font.color.rgb = RGBColor(0, 0, 255)  # 蓝色
                    else:
                        # 普通文本
                        run = para.add_run(run_data['text'])
                        if run_data.get('bold'):
                            run.bold = True
                        if run_data.get('italic'):
                            run.italic = True
            
            elif elem['type'] == 'list':
                for item_runs in elem['items']:
                    para = doc.add_paragraph(style='List Bullet' if elem['style'] == 'bullet' else 'List Number')
                    for run_data in item_runs:
                        if run_data.get('is_link') and run_data.get('link'):
                            # 添加超链接
                            href = run_data['link']
                            link_text = run_data['text']
                            if href.startswith(('http://', 'https://')):
                                add_hyperlink(para, link_text, href)
                            elif href.startswith('#'):
                                # 内部锚点链接
                                anchor_id = href[1:]
                                if anchor_id in heading_bookmarks:
                                    bookmark_name = heading_bookmarks[anchor_id]
                                    part = para.part
                                    hyperlink = OxmlElement('w:hyperlink')
                                    hyperlink.set(qn('w:anchor'), bookmark_name)
                                    new_run = OxmlElement('w:r')
                                    rPr = OxmlElement('w:rPr')
                                    c = OxmlElement('w:color')
                                    c.set(qn('w:val'), '0000FF')
                                    rPr.append(c)
                                    u = OxmlElement('w:u')
                                    u.set(qn('w:val'), 'single')
                                    rPr.append(u)
                                    new_run.append(rPr)
                                    new_run.text = link_text
                                    hyperlink.append(new_run)
                                    para._p.append(hyperlink)
                                else:
                                    run = para.add_run(link_text)
                                    run.font.color.rgb = RGBColor(0, 0, 255)
                            else:
                                run = para.add_run(link_text)
                                run.font.color.rgb = RGBColor(0, 0, 255)  # 蓝色
                        else:
                            run = para.add_run(run_data['text'])
                            if run_data.get('bold'):
                                run.bold = True
                            if run_data.get('italic'):
                                run.italic = True
            
            elif elem['type'] == 'table':
                rows = elem['rows']
                if not rows:
                    continue
                
                table = doc.add_table(rows=len(rows), cols=len(rows[0]))
                table.style = 'Light Grid Accent 1'
                
                for row_idx, row_data in enumerate(rows):
                    for col_idx, cell_data in enumerate(row_data):
                        cell = table.rows[row_idx].cells[col_idx]
                        cell.text = cell_data
                        if row_idx == 0:  # 表头
                            for paragraph in cell.paragraphs:
                                for run in paragraph.runs:
                                    run.bold = True
            
            elif elem['type'] == 'code':
                para = doc.add_paragraph(elem['text'])
                para.style = 'No Spacing'
                for run in para.runs:
                    run.font.name = 'Consolas'
                    run.font.size = Pt(10)
            
            elif elem['type'] == 'quote':
                para = doc.add_paragraph(elem['text'])
                para.style = 'Quote'
            
            elif elem['type'] == 'hr':
                para = doc.add_paragraph('─' * 50)
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            elif elem['type'] == 'image':
                src = elem['src']
                alt = elem.get('alt', '图片')
                
                # 解码 URL 编码的路径
                try:
                    decoded_src = unquote(src)
                except Exception:
                    decoded_src = src
                
                # 处理网络图片（需要下载）
                if src.startswith(('http://', 'https://')):
                    try:
                        try:
                            import requests
                            from io import BytesIO
                            
                            response = requests.get(src, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                            if response.status_code == 200:
                                img_data = BytesIO(response.content)
                                doc.add_picture(img_data, width=Inches(5))
                            else:
                                para = doc.add_paragraph(f"[图片: {alt}]")
                                para.add_run(f" (无法下载: HTTP {response.status_code})")
                        except ImportError:
                            para = doc.add_paragraph(f"[图片: {alt}]")
                            para.add_run(f" (需要安装 requests 库来下载网络图片)")
                    except Exception as e:
                        para = doc.add_paragraph(f"[图片: {alt}]")
                        para.add_run(f" (无法下载: {str(e)})")
                
                # 处理本地图片
                else:
                    # 获取 Markdown 文件所在目录
                    md_path = Path(md_file)
                    md_dir = md_path.parent
                    
                    # 尝试多种路径解析方式
                    possible_paths = []
                    # 1. 原始路径（绝对路径或相对于当前工作目录）
                    possible_paths.append(src)
                    # 2. 解码后的路径
                    possible_paths.append(decoded_src)
                    # 3. 相对于 Markdown 文件的路径
                    possible_paths.append(str(md_dir / src))
                    possible_paths.append(str(md_dir / decoded_src))
                    # 4. 相对于 Markdown 文件所在目录的 images 子目录
                    possible_paths.append(str(md_dir / 'images' / src))
                    possible_paths.append(str(md_dir / 'images' / decoded_src))
                    # 5. 尝试在 result 目录下查找（如果 Markdown 文件在 result 目录下）
                    if 'result' in str(md_dir):
                        # 在同名目录下查找（例如：result/作者_吃瓜惹/图片文件）
                        author_dir = md_dir
                        possible_paths.append(str(author_dir / src))
                        possible_paths.append(str(author_dir / decoded_src))
                        # 在 result 的父目录查找
                        parent_dir = md_dir.parent
                        possible_paths.append(str(parent_dir / src))
                        possible_paths.append(str(parent_dir / decoded_src))
                        # 在 LOFTER-Crawl 目录下查找
                        crawl_dir = parent_dir.parent if parent_dir.name == 'result' else parent_dir
                        possible_paths.append(str(crawl_dir / src))
                        possible_paths.append(str(crawl_dir / decoded_src))
                    
                    img_found = False
                    for img_path in possible_paths:
                        # 去重并检查路径
                        img_path = os.path.normpath(img_path)
                        if os.path.exists(img_path) and os.path.isfile(img_path):
                            try:
                                doc.add_picture(img_path, width=Inches(5))
                                img_found = True
                                print(f"  找到图片: {img_path}")
                                break
                            except Exception as e:
                                # 如果加载失败，继续尝试下一个路径
                                continue
                    
                    if not img_found:
                        para = doc.add_paragraph(f"[图片: {alt}]")
                        if src:
                            para.add_run(f" (未找到: {decoded_src})")
        
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out_path))
        return True
    except Exception as e:
        print(f"转换 DOCX 时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Markdown 文件格式转换工具（纯 Python 实现）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python md2other.py input.md --format pdf
  python md2other.py input.md --format epub --output custom_output.epub
  python md2other.py input.md --format txt --output-dir ./output
  python md2other.py input.md --format docx
        """
    )
    
    parser.add_argument('input_file',
                        help='输入的 Markdown 文件路径')
    parser.add_argument('--format', '-f',
                        choices=['pdf', 'epub', 'txt', 'docx'],
                        required=True,
                        help='输出格式: pdf, epub, txt, docx')
    parser.add_argument('--output', '-o',
                        help='输出文件路径（可选，默认在 result 目录下）')
    parser.add_argument('--output-dir', '-d',
                        default='result',
                        help='输出目录（默认: result）')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {args.input_file}")
        sys.exit(1)
    
    if not input_path.is_file():
        print(f"错误: 输入路径不是文件: {args.input_file}")
        sys.exit(1)
    
    # 确定输出文件路径
    if args.output:
        output_path = Path(args.output)
        output_dir = output_path.parent
    else:
        # 默认输出到 result 目录
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名
        input_stem = input_path.stem
        output_path = output_dir / f"{input_stem}.{args.format}"
    
    # 确保输出目录存在
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"输入文件: {input_path}")
    print(f"输出格式: {args.format}")
    print(f"输出文件: {output_path}")
    print("正在转换...")
    
    # 根据格式调用相应的转换函数
    success = False
    if args.format == 'pdf':
        success = convert_md_to_pdf(str(input_path), str(output_path))
    elif args.format == 'epub':
        success = convert_md_to_epub(str(input_path), str(output_path))
    elif args.format == 'txt':
        success = convert_md_to_txt(str(input_path), str(output_path))
    elif args.format == 'docx':
        success = convert_md_to_docx(str(input_path), str(output_path))
    
    if success:
        print(f"转换成功: {output_path}")
    else:
        print(f"转换失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
