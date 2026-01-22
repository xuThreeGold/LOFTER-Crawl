#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Markdown文件格式转换工具
支持将 Markdown 文件转换为 PDF、EPUB、TXT、DOCX 等格式
"""

import os
import sys
import argparse
from pathlib import Path


# 导出转换函数供外部调用
__all__ = ['convert_md_to_pdf', 'convert_md_to_epub', 'convert_md_to_txt', 'convert_md_to_docx']


def convert_md_to_pdf(md_file, output_file):
    """将 Markdown 转换为 PDF"""
    # 优先使用 pypandoc
    try:
        import pypandoc
        # 尝试使用 xelatex（支持中文）
        try:
            pypandoc.convert_file(md_file, 'pdf', outputfile=output_file, 
                                extra_args=['--pdf-engine=xelatex', '-V', 'CJKmainfont=Microsoft YaHei'])
            return True
        except:
            # 如果 xelatex 不可用，尝试使用默认引擎
            try:
                pypandoc.convert_file(md_file, 'pdf', outputfile=output_file)
                return True
            except Exception as e:
                print(f"PDF 转换失败: {e}")
                return False
    except ImportError:
        # 备选方案：使用 pdfkit
        try:
            import pdfkit
            import markdown
            
            # 读取 Markdown 文件
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 转换为 HTML
            md_parser = markdown.Markdown(extensions=['codehilite', 'fenced_code', 'tables'])
            html_content = md_parser.convert(md_content)
            
            # 添加基本样式
            html_with_style = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: "Microsoft YaHei", Arial, sans-serif;
                        line-height: 1.6;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    pre {{
                        background-color: #f4f4f4;
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto;
                    }}
                    code {{
                        background-color: #f4f4f4;
                        padding: 2px 4px;
                        border-radius: 3px;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                </style>
            </head>
            <body>
            {html_content}
            </body>
            </html>
            """
            
            # 转换为 PDF
            pdfkit.from_string(html_with_style, output_file, options={
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            })
            return True
        except ImportError:
            print("错误: 需要安装 pypandoc 或 pdfkit 库来转换 PDF")
            print("安装命令: pip install pypandoc 或 pip install pdfkit markdown")
            return False
        except Exception as e:
            print(f"转换 PDF 时出错: {e}")
            print("提示: 如果使用 pdfkit，需要安装 wkhtmltopdf")
            return False


def convert_md_to_epub(md_file, output_file):
    """将 Markdown 转换为 EPUB"""
    try:
        import pypandoc
        pypandoc.convert_file(md_file, 'epub', outputfile=output_file)
        return True
    except ImportError:
        print("错误: 需要安装 pypandoc 库来转换 EPUB")
        print("安装命令: pip install pypandoc")
        return False
    except Exception as e:
        print(f"转换 EPUB 时出错: {e}")
        return False


def convert_md_to_txt(md_file, output_file):
    """将 Markdown 转换为纯文本"""
    try:
        import markdown
        import html2text
        
        # 读取 Markdown 文件
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 转换为 HTML
        md = markdown.Markdown(extensions=['codehilite', 'fenced_code', 'tables'])
        html_content = md.convert(md_content)
        
        # 使用 html2text 转换为纯文本
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0  # 不自动换行
        txt_content = h.handle(html_content)
        
        # 保存为文本文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        return True
    except ImportError:
        # 如果库不可用，直接读取并简单处理
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的 Markdown 到文本转换（移除 Markdown 语法）
            import re
            # 移除标题标记（保留文本）
            content = re.sub(r'^#+\s+(.+)$', r'\1', content, flags=re.MULTILINE)
            # 移除粗体和斜体标记
            content = re.sub(r'\*\*([^\*]+)\*\*', r'\1', content)
            content = re.sub(r'\*([^\*]+)\*', r'\1', content)
            content = re.sub(r'__([^_]+)__', r'\1', content)
            content = re.sub(r'_([^_]+)_', r'\1', content)
            # 移除链接但保留文本
            content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
            # 移除图片标记
            content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', content)
            # 移除代码块标记
            content = re.sub(r'```[\s\S]*?```', '', content)
            content = re.sub(r'`([^`]+)`', r'\1', content)
            # 移除列表标记
            content = re.sub(r'^[\s]*[-*+]\s+', '', content, flags=re.MULTILINE)
            content = re.sub(r'^[\s]*\d+\.\s+', '', content, flags=re.MULTILINE)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"转换 TXT 时出错: {e}")
            return False
    except Exception as e:
        print(f"转换 TXT 时出错: {e}")
        return False


def convert_md_to_docx(md_file, output_file):
    """将 Markdown 转换为 DOCX"""
    try:
        import pypandoc
        pypandoc.convert_file(md_file, 'docx', outputfile=output_file)
        return True
    except ImportError:
        print("错误: 需要安装 pypandoc 库来转换 DOCX")
        print("安装命令: pip install pypandoc")
        print("注意: 还需要安装 Pandoc: https://pandoc.org/installing.html")
        return False
    except Exception as e:
        print(f"转换 DOCX 时出错: {e}")
        print("提示: 确保已安装 Pandoc: https://pandoc.org/installing.html")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Markdown 文件格式转换工具',
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
        print(f"✓ 转换成功: {output_path}")
    else:
        print(f"✗ 转换失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
