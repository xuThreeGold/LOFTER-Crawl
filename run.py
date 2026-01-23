# -*- coding: utf-8 -*-
"""
LOFTER工具统一入口
整合爬虫、文件合并、格式转换等功能
"""
import os
import sys
import json
import argparse
from pathlib import Path
from src.main import crawler_main, add_common_args
from src.config import DEFAULT_LOGIN_AUTH, DEFAULT_SAVE_PATH


def get_auth_config_path():
    """
    获取授权码配置文件的路径
    :return: 配置文件路径
    """
    # 配置文件保存在项目根目录下的 .lofter_auth.json
    project_root = os.path.dirname(os.path.abspath(__file__))
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LOFTER工具集（爬虫、文件合并、格式转换）")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # ========== 爬虫相关命令 ==========
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
    
    # ========== 文件处理相关命令 ==========
    # 命令5: 合并文件
    parser_merge = subparsers.add_parser("merge", help="合并文件夹中的所有lofter爬取文件")
    parser_merge.add_argument("input_folder", type=str, help="输入文件夹路径（包含所有要合并的文件）")
    parser_merge.add_argument("-o", "--output", type=str, default=None,
                             help="输出文件夹路径（默认为项目根目录下的result文件夹）")
    parser_merge.add_argument("-n", "--name", type=str, default=None,
                             help="输出文件名（不含扩展名），如果未指定则使用输入文件夹名")
    parser_merge.add_argument("-f", "--format", type=str, choices=["txt", "md"], default="txt",
                             help="文件格式：txt或md（默认为txt）")
    
    # 命令6: Markdown格式转换
    parser_md2other = subparsers.add_parser("md2other", help="将Markdown文件转换为其他格式（PDF、EPUB、TXT、DOCX）")
    parser_md2other.add_argument("input_file", type=str, help="输入的Markdown文件路径")
    parser_md2other.add_argument("-f", "--format", type=str, choices=["pdf", "epub", "txt", "docx"],
                                required=True, help="输出格式: pdf, epub, txt, docx")
    parser_md2other.add_argument("-o", "--output", type=str, default=None,
                                help="输出文件路径（可选，默认在result目录下）")
    parser_md2other.add_argument("-d", "--output-dir", type=str, default=None,
                                help="输出目录（默认: result）")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # ========== 处理merge命令（不需要授权码） ==========
    if args.command == "merge":
        # 导入merge模块
        project_root = os.path.dirname(os.path.abspath(__file__))
        merge_path = os.path.join(project_root, "merge")
        if merge_path not in sys.path:
            sys.path.insert(0, merge_path)
        from merge_files import merge_files
        
        merge_files(
            input_folder=args.input_folder,
            output_folder=args.output,
            output_filename=args.name,
            file_format=args.format
        )
        return
    
    # ========== 处理md2other命令（不需要授权码） ==========
    if args.command == "md2other":
        # 导入md2other模块
        project_root = os.path.dirname(os.path.abspath(__file__))
        md2other_path = os.path.join(project_root, "md2other")
        if md2other_path not in sys.path:
            sys.path.insert(0, md2other_path)
        
        from md2other import convert_md_to_pdf, convert_md_to_epub, convert_md_to_txt, convert_md_to_docx
        
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
        else:
            # 默认输出到 result 目录（相对于项目根目录）
            if args.output_dir:
                output_dir = Path(args.output_dir)
            else:
                output_dir = Path(project_root) / "result"
            
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{input_path.stem}.{args.format}"
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
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
        return
    
    # ========== 处理爬虫相关命令（需要授权码） ==========
    # 对于需要登录的命令，交互式获取授权码（如果命令行参数未提供）
    # 注意：merge 和 md2other 命令已经在上面处理并返回，不会执行到这里
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
