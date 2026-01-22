# -*- coding: utf-8 -*-
"""
合并文件使用示例
"""
from merge_files import merge_files

# 示例1: 合并TXT文件（使用默认输出文件夹和文件名）
def example1():
    """合并TXT文件，使用默认设置"""
    input_folder = r"D:\develop\lofter\LOFTER-Crawl\temp"
    merge_files(
        input_folder=input_folder,
        file_format="txt"
    )


# 示例2: 合并MD文件，指定输出文件夹和文件名
def example2():
    """合并MD文件，指定输出路径"""
    input_folder = r"D:\develop\lofter\LOFTER-Crawl\result\作者_一朵独自生存的花椰菜"
    merge_files(
        input_folder=input_folder,
        output_folder=r"D:\develop\lofter\LOFTER-Crawl\result",
        output_filename="合并后的翘单",
        file_format="md"
    )


# 示例3: 合并TXT文件，指定所有参数
def example3():
    """合并TXT文件，指定所有参数"""
    input_folder = r"D:\develop\lofter\LOFTER-Crawl\temp"
    merge_files(
        input_folder=input_folder,
        output_folder=r"D:\develop\lofter\LOFTER-Crawl\result",
        output_filename="合并后的竹抱枝",
        file_format="txt"
    )


if __name__ == "__main__":
    # 取消注释以运行相应示例
    # example1()
    # example2()
    # example3()
    pass
