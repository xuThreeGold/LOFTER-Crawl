# -*- coding: utf-8 -*-
"""
LOFTER爬虫主程序
"""
import os
import argparse
from .config import DEFAULT_LOGIN_AUTH, DEFAULT_SAVE_PATH
from .post_parser import parse_post
from .tag_crawler import crawl_tag_posts
from .author_crawler import crawl_author_posts, get_author_info
from .file_saver import save_posts, save_post_txt, save_post_markdown


def save_single_post(url, save_path=None, file_format="txt", login_auth=None, save_images=True):
    """
    功能1: 保存单篇文章
    :param url: 文章URL
    :param save_path: 保存路径，默认使用result文件夹
    :param file_format: 文件格式 "txt" 或 "md"
    :param login_auth: 登录授权码
    :param save_images: 是否保存图片
    """
    if save_path is None:
        save_path = DEFAULT_SAVE_PATH
    
    print(f"正在解析文章: {url}")
    post_info = parse_post(url, login_auth)
    
    print(f"正在保存文章...")
    if file_format == "md":
        filename = save_post_markdown(post_info, save_path, save_images)
    else:
        filename = save_post_txt(post_info, save_path, save_images)
    
    print(f"文章已保存: {os.path.join(save_path, filename)}")


def crawl_tag(tag_name, sort_type="new", save_path=None, file_format="txt", 
               group_by_author=True, login_auth=None, save_images=True, min_hot=0):
    """
    功能3: 爬取tag下的所有文章
    新逻辑：
    1. 先获取所有文章链接
    2. 调用成熟的保存单篇文章的方法依次保存
    3. 对每个文件查看作者，放到对应的作者文件夹，没有就新建（如果选择按作者保存的话）
    :param tag_name: tag名称
    :param sort_type: 排序类型 "new"(最新), "total"(全部最热), "month"(月榜), "week"(周榜), "date"(日榜)
    :param save_path: 保存路径
    :param file_format: 文件格式 "txt" 或 "md"
    :param group_by_author: 是否按作者分组
    :param login_auth: 登录授权码
    :param save_images: 是否保存图片
    :param min_hot: 最低热度限制
    """
    if save_path is None:
        save_path = DEFAULT_SAVE_PATH
    
    print(f"正在爬取tag: {tag_name}, 排序方式: {sort_type}")
    
    # 步骤1: 先获取所有文章链接
    print("步骤1: 正在获取所有文章链接...")
    post_urls = crawl_tag_posts(tag_name, sort_type, login_auth, min_hot=min_hot)
    
    if not post_urls:
        print("未获取到任何文章链接")
        return
    
    print(f"步骤1完成: 获取到 {len(post_urls)} 篇文章链接")
    
    # 步骤2: 调用成熟的保存单篇文章的方法依次保存
    print(f"\n步骤2: 开始依次保存文章...")
    
    if group_by_author:
        # 按作者分组保存：边解析边保存，不需要先解析完所有文章
        from .utils import sanitize_filename
        author_paths = {}  # {author_name: author_path} 缓存已创建的作者文件夹路径
        total_saved = 0
        
        for i, url in enumerate(post_urls, 1):
            try:
                print(f"\n[{i}/{len(post_urls)}] 正在保存: {url}")
                # 解析文章获取完整信息（包括作者）
                post_info = parse_post(url, login_auth)
                if post_info:
                    author_name = post_info.get("author_name", "未知作者")
                    
                    # 获取或创建作者文件夹
                    if author_name not in author_paths:
                        author_name_safe = sanitize_filename(author_name)
                        author_path = os.path.join(save_path, f"作者_{author_name_safe}")
                        os.makedirs(author_path, exist_ok=True)
                        author_paths[author_name] = author_path
                        print(f"创建作者文件夹: {author_path}")
                    else:
                        author_path = author_paths[author_name]
                    
                    # 立即保存这篇文章
                    if file_format == "md":
                        from .file_saver import save_post_markdown
                        filename = save_post_markdown(post_info, author_path, save_images)
                    else:
                        from .file_saver import save_post_txt
                        filename = save_post_txt(post_info, author_path, save_images)
                    
                    print(f"✓ 已保存: {filename}")
                    total_saved += 1
                else:
                    print(f"✗ 解析文章失败，跳过: {url}")
            except Exception as e:
                print(f"✗ 保存文章失败 {url}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n总共保存了 {total_saved} 篇文章，涉及 {len(author_paths)} 位作者")
    else:
        # 不分组，全部保存在一个文件夹
        print(f"开始保存 {len(post_urls)} 篇文章...")
        
        for i, url in enumerate(post_urls, 1):
            try:
                print(f"[{i}/{len(post_urls)}] 正在保存: {url}")
                save_single_post(url, save_path, file_format, login_auth, save_images)
            except Exception as e:
                print(f"保存文章失败 {url}: {e}")
    
    print(f"\n所有文章保存完成！")


def crawl_author(author_url, target_tags=None, save_path=None, file_format="txt",
                  group_by_author=False, login_auth=None, save_images=True,
                  start_time=None, end_time=None):
    """
    功能4: 爬取作者的文章
    :param author_url: 作者主页URL
    :param target_tags: 目标tags列表，如果指定则只爬取包含这些tag的文章
    :param save_path: 保存路径
    :param file_format: 文件格式 "txt" 或 "md"
    :param group_by_author: 是否按作者分组（对于单个作者通常设为False）
    :param login_auth: 登录授权码
    :param save_images: 是否保存图片
    :param start_time: 开始时间 "YYYY-MM-DD"
    :param end_time: 结束时间 "YYYY-MM-DD"
    """
    if save_path is None:
        save_path = DEFAULT_SAVE_PATH
    
    print(f"正在爬取作者: {author_url}")
    
    tags_filter_mode = "in"  # 默认包含模式
    if target_tags:
        print(f"目标tags: {target_tags}")
    
    posts = crawl_author_posts(author_url, target_tags, tags_filter_mode, 
                               login_auth, start_time=start_time, end_time=end_time)
    
    if not posts:
        print("未获取到任何文章")
        return
    
    print(f"获取到 {len(posts)} 篇文章，开始保存...")
    save_posts(posts, save_path, file_format, group_by_author, save_images)


def crawl_tag_then_author(tag_name, target_tag, sort_type="new", save_path=None,
                           file_format="txt", group_by_author=True, login_auth=None,
                           save_images=True, min_hot=0):
    """
    功能5: 爬取tag下的文件，然后进入这些文件的作者主页，爬取该作者的指定tag的所有文件
    :param tag_name: 初始tag名称
    :param target_tag: 目标tag（作者主页中要爬取的tag）
    :param sort_type: 排序类型
    :param save_path: 保存路径
    :param file_format: 文件格式
    :param group_by_author: 是否按作者分组
    :param login_auth: 登录授权码
    :param save_images: 是否保存图片
    :param min_hot: 最低热度限制
    """
    if save_path is None:
        save_path = DEFAULT_SAVE_PATH
    
    print(f"步骤1: 正在爬取tag '{tag_name}' 下的文章...")
    posts = crawl_tag_posts(tag_name, sort_type, login_auth, min_hot=min_hot)
    
    if not posts:
        print("未获取到任何文章")
        return
    
    # 提取所有作者
    authors = {}
    for post in posts:
        author_name = post.get("author_name", "")
        author_ip = post.get("author_ip", "")
        if author_name and author_ip:
            author_url = f"https://{author_ip}.lofter.com/"
            if author_url not in authors:
                authors[author_url] = {
                    "name": author_name,
                    "ip": author_ip
                }
    
    print(f"\n步骤2: 找到 {len(authors)} 位作者，开始爬取每位作者的tag '{target_tag}' 下的文章...")
    
    all_posts = []
    for author_url, author_info in authors.items():
        print(f"\n正在爬取作者 {author_info['name']} 的tag '{target_tag}' 文章...")
        author_posts = crawl_author_posts(author_url, [target_tag], "in", login_auth)
        all_posts.extend(author_posts)
    
    if not all_posts:
        print("未获取到任何文章")
        return
    
    print(f"\n总共获取到 {len(all_posts)} 篇文章，开始保存...")
    save_posts(all_posts, save_path, file_format, group_by_author, save_images)


def add_common_args(parser):
    """添加通用参数到解析器"""
    parser.add_argument("--login-auth", type=str, default=None,
                        help="登录授权码，如果不指定则使用默认值")
    parser.add_argument("--save-path", type=str, default=None,
                        help=f"保存路径，默认: {DEFAULT_SAVE_PATH}")
    parser.add_argument("--format", type=str, choices=["txt", "md"], default="txt",
                        help="文件格式: txt 或 md (默认: txt)")
    parser.add_argument("--no-images", action="store_true",
                        help="不保存图片文件")
    parser.add_argument("--no-group", action="store_true",
                        help="不按作者分组（所有文件保存在一个文件夹）")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LOFTER爬虫工具")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 命令1: 保存单篇文章
    parser_post = subparsers.add_parser("post", help="保存单篇文章")
    parser_post.add_argument("url", type=str, help="文章URL")
    add_common_args(parser_post)
    
    # 命令2: 爬取tag
    parser_tag = subparsers.add_parser("tag", help="爬取tag下的所有文章")
    parser_tag.add_argument("tag_name", type=str, help="tag名称")
    parser_tag.add_argument("--sort", type=str, choices=["new", "total", "month", "week", "date"],
                           default="new", help="排序方式: new(最新), total(全部最热), month(月榜), week(周榜), date(日榜)")
    parser_tag.add_argument("--min-hot", type=int, default=0, help="最低热度限制")
    add_common_args(parser_tag)
    
    # 命令3: 爬取作者
    parser_author = subparsers.add_parser("author", help="爬取作者的文章")
    parser_author.add_argument("author_url", type=str, help="作者主页URL")
    parser_author.add_argument("--tags", type=str, nargs="+", default=None,
                               help="目标tags（只爬取包含这些tag的文章）")
    parser_author.add_argument("--start-time", type=str, default=None,
                              help="开始时间 YYYY-MM-DD")
    parser_author.add_argument("--end-time", type=str, default=None,
                              help="结束时间 YYYY-MM-DD")
    add_common_args(parser_author)
    
    # 命令4: tag+作者组合
    parser_tag_author = subparsers.add_parser("tag-author", help="爬取tag后爬取作者的指定tag文章")
    parser_tag_author.add_argument("tag_name", type=str, help="初始tag名称")
    parser_tag_author.add_argument("target_tag", type=str, help="目标tag（作者主页中要爬取的tag）")
    parser_tag_author.add_argument("--sort", type=str, choices=["new", "total", "month", "week", "date"],
                                   default="new", help="排序方式")
    parser_tag_author.add_argument("--min-hot", type=int, default=0, help="最低热度限制")
    add_common_args(parser_tag_author)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 设置参数
    login_auth = args.login_auth if args.login_auth else DEFAULT_LOGIN_AUTH
    save_path = args.save_path if args.save_path else DEFAULT_SAVE_PATH
    file_format = args.format
    save_images = not args.no_images
    group_by_author = not args.no_group
    
    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)
    
    # 执行相应命令
    if args.command == "post":
        save_single_post(args.url, save_path, file_format, login_auth, save_images)
    
    elif args.command == "tag":
        crawl_tag(args.tag_name, args.sort, save_path, file_format,
                 group_by_author, login_auth, save_images, args.min_hot)
    
    elif args.command == "author":
        crawl_author(args.author_url, args.tags, save_path, file_format,
                    group_by_author, login_auth, save_images,
                    args.start_time, args.end_time)
    
    elif args.command == "tag-author":
        crawl_tag_then_author(args.tag_name, args.target_tag, args.sort, save_path,
                             file_format, group_by_author, login_auth,
                             save_images, args.min_hot)


if __name__ == "__main__":
    main()
