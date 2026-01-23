# -*- coding: utf-8 -*-
"""
合并lofter爬取的文件
支持合并txt或md格式的文件，按发表时间排序
"""
import os
import re
import yaml
from datetime import datetime
from typing import List, Tuple, Optional


def extract_publish_time_txt(file_path: str) -> Optional[str]:
    """
    从TXT文件中提取发表时间
    :param file_path: 文件路径
    :return: 发表时间字符串（YYYY-MM-DD格式），如果提取失败返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取前几行查找发表时间
            for i, line in enumerate(f):
                if i > 10:  # 只检查前10行
                    break
                if '发表时间：' in line or '发表时间:' in line:
                    # 提取日期格式 YYYY-MM-DD
                    match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
                    if match:
                        return match.group(1)
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
    return None


def extract_publish_time_md(file_path: str) -> Optional[str]:
    """
    从MD文件中提取发表时间（从YAML Front-Matter中）
    :param file_path: 文件路径
    :return: 发表时间字符串（YYYY-MM-DD格式），如果提取失败返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 查找YAML Front-Matter
            if content.startswith('---'):
                # 提取第一个---到第二个---之间的内容
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter_str = parts[1]
                    try:
                        front_matter = yaml.safe_load(front_matter_str)
                        if front_matter and 'date' in front_matter:
                            date_str = str(front_matter['date']).strip()
                            # 移除可能的引号
                            date_str = date_str.strip("'\"")
                            # 提取日期部分（可能包含时间）
                            match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
                            if match:
                                return match.group(1)
                    except yaml.YAMLError:
                        pass
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
    return None


def get_file_publish_time(file_path: str, file_format: str) -> Optional[datetime]:
    """
    获取文件的发表时间
    :param file_path: 文件路径
    :param file_format: 文件格式 'txt' 或 'md'
    :return: datetime对象，如果提取失败返回None
    """
    if file_format == 'txt':
        time_str = extract_publish_time_txt(file_path)
    else:  # md
        time_str = extract_publish_time_md(file_path)
    
    if time_str:
        try:
            return datetime.strptime(time_str, '%Y-%m-%d')
        except ValueError:
            pass
    
    # 如果提取失败，使用文件修改时间作为后备
    try:
        return datetime.fromtimestamp(os.path.getmtime(file_path))
    except:
        return datetime.min


def get_file_content(file_path: str, file_format: str) -> str:
    """
    获取文件内容（去除文件头）
    :param file_path: 文件路径
    :param file_format: 文件格式 'txt' 或 'md'
    :return: 文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if file_format == 'txt':
            # 对于TXT格式，跳过文件头
            lines = content.split('\n')
            # 查找"原文链接："行，之后的内容才是正文
            content_start = 0
            for i, line in enumerate(lines):
                if '原文链接：' in line or '原文链接:' in line:
                    content_start = i + 1
                    break
            # 跳过空行
            while content_start < len(lines) and not lines[content_start].strip():
                content_start += 1
            # 如果没找到"原文链接："，尝试跳过前3行（标题、时间、链接）
            if content_start == 0:
                content_start = 3
                # 跳过空行
                while content_start < len(lines) and not lines[content_start].strip():
                    content_start += 1
            return '\n'.join(lines[content_start:])
        else:  # md
            # 对于MD格式，跳过YAML Front-Matter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    body = parts[2].lstrip('\n')
                    return body
            return content
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return ""


def get_filename_without_ext(file_path: str) -> str:
    """
    获取不带扩展名的文件名
    :param file_path: 文件路径
    :return: 不带扩展名的文件名
    """
    return os.path.splitext(os.path.basename(file_path))[0]


def generate_toc(file_info_list: List[Tuple[str, datetime, str]], file_format: str, toc_links: bool = True) -> str:
    """
    生成目录
    :param file_info_list: 文件信息列表，每个元素为(file_path, publish_time, filename)
    :param file_format: 文件格式 'txt' 或 'md'
    :param toc_links: 如果是MD格式，是否生成可跳转的链接（默认True）
    :return: 目录字符串
    """
    toc_lines = []
    
    if file_format == 'txt':
        toc_lines.append("目录\n")
        toc_lines.append("=" * 50 + "\n\n")
        for chapter_num, (_, _, filename) in enumerate(file_info_list, 1):
            chapter_title = f"第{chapter_num}章-{filename}"
            toc_lines.append(f"{chapter_num}. {chapter_title}\n")
    else:  # md
        toc_lines.append("# 目录\n\n")
        for chapter_num, (_, _, filename) in enumerate(file_info_list, 1):
            chapter_title = f"第{chapter_num}章-{filename}"
            if toc_links:
                # 生成Markdown链接（使用章节标题作为锚点）
                # 大多数Markdown解析器（如GitHub Flavored Markdown）会自动为标题生成锚点
                # 锚点格式：将标题转换为小写，空格和特殊字符替换为连字符
                # 对于中文标题，大多数现代解析器（如GitHub、GitLab）会保留中文字符
                # 使用标准格式以确保兼容性
                import re
                anchor = chapter_title.lower()
                # 移除特殊字符（保留字母、数字、中文字符、空格、连字符）
                anchor = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', anchor)
                # 将空格和连字符统一为单个连字符
                anchor = re.sub(r'[-\s]+', '-', anchor)
                # 移除首尾连字符
                anchor = anchor.strip('-')
                toc_lines.append(f"{chapter_num}. [{chapter_title}](#{anchor})\n")
            else:
                toc_lines.append(f"{chapter_num}. {chapter_title}\n")
        toc_lines.append("\n---\n\n")
    
    return ''.join(toc_lines)


def merge_files(
    input_folder: str,
    output_folder: Optional[str] = None,
    output_filename: Optional[str] = None,
    file_format: str = "txt",
    add_toc: bool = False,
    toc_links: bool = True
):
    """
    合并文件夹中的所有文件
    :param input_folder: 输入文件夹路径（包含所有要合并的文件）
    :param output_folder: 输出文件夹路径，如果为None则使用项目根目录下的result文件夹
    :param output_filename: 输出文件名（不含扩展名），如果为None则使用输入文件夹名
    :param file_format: 文件格式 'txt' 或 'md'（默认'txt'）
    :param add_toc: 是否在开头添加目录（默认False）
    :param toc_links: 如果是MD格式，是否生成可跳转的目录链接（默认True，仅在add_toc=True且file_format='md'时有效）
    """
    # 验证输入文件夹
    if not os.path.isdir(input_folder):
        raise ValueError(f"输入文件夹不存在: {input_folder}")
    
    # 确定输出文件夹（默认为项目根目录下的result文件夹）
    if output_folder is None:
        # 获取项目根目录（merge文件夹的父目录）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        output_folder = os.path.join(project_root, "result")
    
    # 确定输出文件名
    if output_filename is None:
        output_filename = os.path.basename(os.path.abspath(input_folder))
    
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取所有文件
    all_files = []
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        if os.path.isfile(file_path):
            # 检查文件扩展名
            ext = os.path.splitext(filename)[1].lower()
            if file_format == 'txt' and ext == '.txt':
                all_files.append(file_path)
            elif file_format == 'md' and ext == '.md':
                all_files.append(file_path)
    
    if not all_files:
        print(f"在文件夹 {input_folder} 中没有找到 {file_format.upper()} 格式的文件")
        return
    
    print(f"找到 {len(all_files)} 个 {file_format.upper()} 文件")
    
    # 提取每个文件的发表时间并排序
    file_info_list: List[Tuple[str, datetime, str]] = []
    for file_path in all_files:
        publish_time = get_file_publish_time(file_path, file_format)
        filename = get_filename_without_ext(file_path)
        file_info_list.append((file_path, publish_time, filename))
    
    # 按发表时间排序
    file_info_list.sort(key=lambda x: x[1])
    
    print(f"按发表时间排序完成，最早: {file_info_list[0][1].strftime('%Y-%m-%d')}, "
          f"最晚: {file_info_list[-1][1].strftime('%Y-%m-%d')}")
    
    # 合并文件内容
    merged_content = []
    
    # 如果启用目录，先添加目录
    if add_toc:
        toc_content = generate_toc(file_info_list, file_format, toc_links)
        merged_content.append(toc_content)
    
    for chapter_num, (file_path, publish_time, filename) in enumerate(file_info_list, 1):
        print(f"处理第 {chapter_num} 章: {filename}")
        content = get_file_content(file_path, file_format)
        
        # 添加章节标题
        chapter_title = f"第{chapter_num}章-{filename}"
        
        if file_format == 'txt':
            merged_content.append(f"\n\n{'='*50}\n")
            merged_content.append(f"{chapter_title}\n")
            merged_content.append(f"{'='*50}\n\n")
        else:  # md
            merged_content.append(f"\n\n## {chapter_title}\n\n")
        
        merged_content.append(content)
    
    # 写入合并后的文件
    output_ext = file_format
    output_path = os.path.join(output_folder, f"{output_filename}.{output_ext}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(merged_content))
    
    print(f"\n合并完成！")
    print(f"输出文件: {output_path}")
    print(f"共合并 {len(file_info_list)} 个文件")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='合并lofter爬取的文件')
    parser.add_argument('input_folder', type=str, help='输入文件夹路径（包含所有要合并的文件）')
    parser.add_argument('-o', '--output', type=str, default=None, 
                       help='输出文件夹路径（默认为项目根目录下的result文件夹）')
    parser.add_argument('-n', '--name', type=str, default=None,
                       help='输出文件名（不含扩展名），如果未指定则使用输入文件夹名')
    parser.add_argument('-f', '--format', type=str, choices=['txt', 'md'], default='txt',
                       help='文件格式：txt或md（默认为txt）')
    parser.add_argument('--add-toc', action='store_true',
                       help='在开头添加目录')
    parser.add_argument('--no-toc-links', action='store_true',
                       help='如果合并MD文件且添加目录，不使用可跳转的链接（默认使用可跳转链接）')
    
    args = parser.parse_args()
    
    # 如果指定了--no-toc-links，则toc_links为False，否则为True（默认）
    toc_links = not args.no_toc_links
    
    merge_files(
        input_folder=args.input_folder,
        output_folder=args.output,
        output_filename=args.name,
        file_format=args.format,
        add_toc=args.add_toc,
        toc_links=toc_links
    )
