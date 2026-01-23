# -*- coding: utf-8 -*-
"""
LOFTER爬虫核心功能模块
包含爬虫相关的功能和命令行解析
"""
import os
import sys
import json
import time
import argparse
from .config import DEFAULT_LOGIN_AUTH, DEFAULT_SAVE_PATH
from .post_parser import parse_post
from .tag_crawler import crawl_tag_posts
from .author_crawler import get_author_info, get_author_blog_urls, check_blog_has_tag
from .file_saver import save_posts, save_post_txt, save_post_markdown


def save_single_post(url, save_path=None, file_format="txt", login_auth=None, save_images=True):
    """
    功能1: 保存单篇文章
    :param url: 文章URL
    :param save_path: 保存路径，如果为None则使用DEFAULT_SAVE_PATH
    :param file_format: 文件格式 "txt" 或 "md"
    :param login_auth: 登录授权码
    :param save_images: 是否保存图片
    """
    if save_path is None:
        save_path = DEFAULT_SAVE_PATH
    
    # 确保保存路径存在
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    print(f"正在解析文章: {url}")
    print(f"保存路径: {save_path}")
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
    功能2: 爬取tag下的所有文章
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
    功能3: 爬取作者的文章（参考lofterSpider-master_v2/src/author_spider.py第265-368行）
    逻辑：
    1. 获得该作者所有文章链接
    2. 一篇一篇地保存，先确定是否符合tag要求，符合调用保存单篇文章的方法保存
    :param author_url: 作者主页URL
    :param target_tags: 目标tags列表，如果指定则只爬取包含这些tag的文章
    :param save_path: 保存路径
    :param file_format: 文件格式 "txt" 或 "md"
    :param group_by_author: 是否按作者分组（对于单个作者通常设为False）
    :param login_auth: 登录授权码
    :param save_images: 是否保存图片
    :param start_time: 开始时间 "YYYY-MM-DD"（暂未实现）
    :param end_time: 结束时间 "YYYY-MM-DD"（暂未实现）
    """
    print(f"正在爬取作者: {author_url}")
    
    if target_tags:
        print(f"只爬取包含tag {target_tags} 的文章")
    
    # 步骤1: 获得该作者所有文章链接（参考lofterSpider-master_v2/src/author_spider.py第292行）
    blog_urls, author_info = get_author_blog_urls(author_url, login_auth)
    
    if not blog_urls:
        print("未获取到任何博客")
        return
    
    # 获取作者名，用于构建默认保存路径
    author_name = author_info['author_name']
    
    # 如果未指定保存路径，或者使用的是默认路径，默认保存到 result/作者_XXX 文件夹
    if save_path is None or save_path == DEFAULT_SAVE_PATH:
        from .utils import sanitize_filename
        author_folder_name = f"作者_{author_name}"
        author_folder_name = sanitize_filename(author_folder_name)
        save_path = os.path.join(DEFAULT_SAVE_PATH, author_folder_name)
        print(f"未指定保存路径，使用默认路径: {save_path}")
    else:
        print(f"使用指定的保存路径: {save_path}")
    
    # 确保保存路径存在
    if not os.path.exists(save_path):
        os.makedirs(save_path)
        print(f"创建保存路径: {save_path}")
    
    print(f"最终保存路径: {save_path}")
    
    print(f"\n开始保存博客到 {save_path}...")
    
    # 步骤2: 一篇一篇地保存，先确定是否符合tag要求，符合调用保存单篇文章的方法保存
    # 参考lofterSpider-master_v2/src/author_spider.py第300-363行
    saved_count = 0
    skipped_count = 0
    
    for i, blog_url in enumerate(blog_urls, 1):
        print(f"\n[{i}/{len(blog_urls)}]")
        
        # 如果指定了tag，验证博客是否包含该tag
        # 通过访问博客页面获取准确的tag信息，确保只保存包含目标tag的文章
        if target_tags:
            if not check_blog_has_tag(blog_url, target_tags, login_auth):
                print(f"博客不包含目标tag，跳过")
                skipped_count += 1
                continue
        
        try:
            # 调用保存单篇文章的方法保存（不要修改）
            save_single_post(blog_url, save_path, file_format, login_auth, save_images)
            saved_count += 1
            
            time.sleep(1)  # 避免请求过快
        except Exception as e:
            print(f"保存博客 {blog_url} 失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n完成！共保存 {saved_count} 篇博客到 {save_path}")
    if target_tags and skipped_count > 0:
        print(f"跳过 {skipped_count} 篇不包含目标tag的博客")


def crawl_tag_then_author(tag_name, target_tag, sort_type="new", save_path=None,
                           file_format="txt", group_by_author=True, login_auth=None,
                           save_images=True, min_hot=0):
    """
    功能4: 爬取tag下的文件，然后进入这些文件的作者主页，爬取该作者的指定tag的所有文件
    新实现逻辑（适配当前crawl_tag_posts与crawl_author实现）：
    1. 使用 crawl_tag_posts(tag_name, ...) 获取文章 URL 列表
    2. 对每个 URL 调用 parse_post，解析出作者名与作者 IP
    3. 去重得到作者列表
    4. 对每位作者调用 crawl_author(author_url, [target_tag], ...) 进行作者级爬取，
       作者级爬取内部会逐篇调用 save_single_post 保存（符合你的要求）
    """
    if save_path is None:
        save_path = DEFAULT_SAVE_PATH
    
    print(f"步骤1: 正在爬取tag '{tag_name}' 下的文章...")
    post_urls = crawl_tag_posts(tag_name, sort_type, login_auth, min_hot=min_hot)
    
    if not post_urls:
        print("未获取到任何文章")
        return
    
    # 步骤2: 解析每篇文章，收集作者信息（作者名 + author_ip）
    print(f"步骤2: 从 {len(post_urls)} 篇文章中提取作者信息...")
    authors = {}  # {author_url: {"name": author_name, "ip": author_ip}}
    
    for i, url in enumerate(post_urls, 1):
        try:
            print(f"[解析作者 {i}/{len(post_urls)}] {url}")
            post_info = parse_post(url, login_auth)
            if not post_info:
                print("  解析失败，跳过")
                continue
            
            author_name = post_info.get("author_name", "").strip()
            author_ip = post_info.get("author_ip", "").strip()
            if not author_ip:
                print("  未获取到作者IP，跳过")
                continue
            
            author_url = f"https://{author_ip}.lofter.com/"
            if author_url not in authors:
                authors[author_url] = {
                    "name": author_name or author_ip,
                    "ip": author_ip,
                }
        except Exception as e:
            print(f"  提取作者信息失败，跳过: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not authors:
        print("未从tag文章中解析到任何作者信息")
        return
    
    print(f"\n步骤3: 找到 {len(authors)} 位作者，开始爬取每位作者主页下、包含 tag '{target_tag}' 的文章...")
    
    # 步骤3: 对每个作者调用 crawl_author，由 crawl_author 内部负责按 tag 过滤并逐篇调用 save_single_post 保存
    for idx, (author_url, author_info) in enumerate(authors.items(), 1):
        print(f"\n[{idx}/{len(authors)}] 正在爬取作者 {author_info['name']} ({author_url}) 的 tag '{target_tag}' 文章...")
        try:
            # crawl_author 会：
            # 1. 获取作者所有文章链接（或按 tag 过滤）
            # 2. 对符合 tag 的文章逐篇调用 save_single_post 保存
            crawl_author(
                author_url=author_url,
                target_tags=[target_tag],
                save_path=save_path,
                file_format=file_format,
                group_by_author=group_by_author,
                login_auth=login_auth,
                save_images=save_images,
            )
        except Exception as e:
            print(f"爬取作者 {author_info['name']} 失败: {e}")
            import traceback
            traceback.print_exc()
            continue


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


def crawler_main(args, login_auth=None):
    """
    爬虫功能的主函数（只处理爬虫相关命令）
    :param args: 命令行参数对象
    :param login_auth: 登录授权码（如果为None，则使用args.login_auth或默认值）
    """
    # 设置通用参数
    if login_auth is None:
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


# ========== 授权码管理功能 ==========

def get_auth_config_path():
    """
    获取授权码配置文件的路径
    :return: 配置文件路径
    """
    # 配置文件保存在项目根目录下的 .lofter_auth.json
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, ".lofter_auth.json")


def load_saved_auth():
    """
    从配置文件加载保存的授权码
    :return: 授权码字符串，如果不存在则返回None
    """
    auth_file = get_auth_config_path()
    if os.path.exists(auth_file):
        try:
            with open(auth_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('login_auth', None)
        except Exception as e:
            print(f"读取授权码配置文件失败: {e}")
            return None
    return None


def save_auth(auth_code):
    """
    保存授权码到配置文件
    :param auth_code: 授权码字符串
    """
    auth_file = get_auth_config_path()
    try:
        config = {'login_auth': auth_code}
        with open(auth_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"授权码已保存到: {auth_file}")
    except Exception as e:
        print(f"保存授权码失败: {e}")


def get_login_auth_interactive():
    """
    交互式获取登录授权码（自动检查已保存的授权码）
    :return: 授权码字符串，如果用户选择不提供则返回None
    """
    print("\n" + "="*60)
    print("登录授权码设置")
    print("="*60)
    
    # 自动检查是否有保存的授权码
    saved_auth = load_saved_auth()
    
    if saved_auth:
        # 显示当前保存的授权码（只显示前后部分，中间用...代替）
        auth_display = saved_auth[:20] + "..." + saved_auth[-10:] if len(saved_auth) > 30 else saved_auth
        print(f"检测到已保存的授权码: {auth_display}")
        print(f"完整授权码长度: {len(saved_auth)} 字符")
        
        # 询问是否需要修改
        need_modify = input("\n是否需要修改授权码？(y/n，直接回车默认n): ").strip().lower()
        
        if need_modify and need_modify in ['y', 'yes']:
            # 需要修改，提示输入新的授权码
            new_auth = input("请输入新的授权码（直接回车保持原值）: ").strip()
            if new_auth:
                save_auth(new_auth)
                print("授权码已更新")
                return new_auth
            else:
                print("未输入新授权码，保持原值")
                return saved_auth
        else:
            # 不需要修改，使用保存的授权码
            print("使用已保存的授权码")
            return saved_auth
    else:
        # 没有保存的授权码，询问是否有授权码
        has_auth = input("您是否有登录授权码？(y/n，直接回车默认n): ").strip().lower()
        
        if not has_auth or has_auth == 'n' or has_auth == 'no':
            print("未提供授权码，程序将继续运行（某些功能可能需要授权码才能正常使用）")
            return None
        
        if has_auth not in ['y', 'yes']:
            print("未提供授权码，程序将继续运行")
            return None
        
        # 用户有授权码，提示输入
        new_auth = input("请输入授权码（直接回车跳过）: ").strip()
        if new_auth:
            save_auth(new_auth)
            print("授权码已保存")
            return new_auth
        else:
            print("未输入授权码，将不使用授权码")
            return None


# ========== 命令行解析主函数 ==========

def main():
    """主函数 - 命令行入口"""
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
    
    # 对于需要登录的命令，交互式获取授权码（如果命令行参数未提供）
    interactive_auth = None
    if not args.login_auth:
        # 命令行未提供授权码，进行交互式询问
        interactive_auth = get_login_auth_interactive()
    else:
        print(f"\n使用命令行参数提供的授权码（前20字符: {args.login_auth[:20]}...）")
    
    # 优先级：命令行参数 > 交互式输入 > 默认值
    login_auth = args.login_auth if args.login_auth else (interactive_auth if interactive_auth else DEFAULT_LOGIN_AUTH)
    
    # 调用爬虫主函数
    crawler_main(args, login_auth)


if __name__ == "__main__":
    main()
