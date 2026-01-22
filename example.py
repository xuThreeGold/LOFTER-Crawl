# -*- coding: utf-8 -*-
"""
使用示例
"""
from src.main import (
    save_single_post,
    crawl_tag,
    crawl_author,
    crawl_tag_then_author
)
from src.config import DEFAULT_LOGIN_AUTH, DEFAULT_SAVE_PATH

# 示例1: 保存单篇文章
def example1():
    """保存单篇文章"""
    url = "https://xxx.lofter.com/post/xxx"
    save_path = r"D:\小说\小说\耽美\题材_风起东宫or太卢"
    save_single_post(url, save_path, file_format="txt", save_images=True)


# 示例2: 爬取tag下的所有文章（最新）
def example2():
    """爬取tag下的所有文章"""
    tag_name = "风起东宫"
    save_path = r"D:\小说\小说\耽美\题材_风起东宫or太卢"
    crawl_tag(
        tag_name=tag_name,
        sort_type="new",  # 最新
        save_path=save_path,
        file_format="txt",
        group_by_author=True,  # 按作者分组
        save_images=True
    )


# 示例3: 爬取tag下的所有文章（最热-全部）
def example3():
    """爬取tag下的最热文章"""
    tag_name = "风起东宫"
    save_path = r"D:\小说\小说\耽美\题材_风起东宫or太卢"
    crawl_tag(
        tag_name=tag_name,
        sort_type="total",  # 全部最热
        save_path=save_path,
        file_format="txt",
        group_by_author=True,
        save_images=True
    )


# 示例4: 爬取tag下的所有文章（最热-月榜）
def example4():
    """爬取tag下的月榜文章"""
    tag_name = "风起东宫"
    save_path = r"D:\小说\小说\耽美\题材_风起东宫or太卢"
    crawl_tag(
        tag_name=tag_name,
        sort_type="month",  # 月榜
        save_path=save_path,
        file_format="txt",
        group_by_author=True,
        save_images=True
    )


# 示例5: 爬取作者的全部文章
def example5():
    """爬取作者的全部文章"""
    author_url = "https://xxx.lofter.com/"
    save_path = r"D:\小说\小说\耽美\题材_风起东宫or太卢"
    crawl_author(
        author_url=author_url,
        target_tags=None,  # 全部文章
        save_path=save_path,
        file_format="txt",
        group_by_author=False,  # 单个作者不需要分组
        save_images=True
    )


# 示例6: 爬取作者的指定tag文章
def example6():
    """爬取作者的指定tag文章"""
    author_url = "https://xxx.lofter.com/"
    save_path = r"D:\小说\小说\耽美\题材_风起东宫or太卢"
    crawl_author(
        author_url=author_url,
        target_tags=["风起东宫", "太卢"],  # 只爬取包含这些tag的文章
        save_path=save_path,
        file_format="txt",
        group_by_author=False,
        save_images=True
    )


# 示例7: Tag+作者组合爬取
def example7():
    """爬取tag下的文章，然后爬取这些作者的指定tag文章"""
    tag_name = "风起东宫"  # 初始tag
    target_tag = "太卢"  # 目标tag（作者主页中要爬取的tag）
    save_path = r"D:\小说\小说\耽美\题材_风起东宫or太卢"
    crawl_tag_then_author(
        tag_name=tag_name,
        target_tag=target_tag,
        sort_type="total",  # 最热排序
        save_path=save_path,
        file_format="txt",
        group_by_author=True,  # 按作者分组
        save_images=True
    )


# 示例8: 保存为Markdown格式
def example8():
    """保存为Markdown格式"""
    url = "https://xxx.lofter.com/post/xxx"
    save_path = r"D:\小说\小说\耽美\题材_风起东宫or太卢"
    save_single_post(url, save_path, file_format="md", save_images=True)


if __name__ == "__main__":
    # 取消注释以运行相应示例
    # example1()
    # example2()
    # example3()
    # example4()
    # example5()
    # example6()
    # example7()
    # example8()
    pass
