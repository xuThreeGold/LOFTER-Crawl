# -*- coding: utf-8 -*-
"""
文章内容解析模板
参考lofterSpider-master的parse_template.py
"""
import re
import html2text


def extract_content_with_links(parse, selector, join_word="", root=None):
    """
    从指定选择器提取内容，并在链接文本后附加链接URL
    标题（h1, h2, h3等）中的链接不需要附加
    :param parse: 解析后的HTML树
    :param selector: XPath选择器
    :param join_word: 连接词
    :param root: 可选的根元素，如果提供则在该元素内搜索
    """
    result_parts = []
    
    # 获取选择器对应的元素
    if root is not None:
        elements = root.xpath(selector)
    else:
        elements = parse.xpath(selector)
    if not elements:
        return ""
    
    # 递归处理元素，按DOM顺序提取
    def process_element(elem, is_in_heading=False):
        parts = []
        
        # 检查当前元素是否是标题
        if hasattr(elem, 'tag') and elem.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            is_in_heading = True
        
        # 先添加当前元素的直接文本（在第一个子元素之前的文本）
        if hasattr(elem, 'text') and elem.text:
            text = elem.text.strip()
            if text:
                parts.append(text)
        
        # 遍历子节点
        for child in elem:
            if hasattr(child, 'tag'):
                if child.tag == 'a':
                    # 链接
                    link_text = ''.join(child.xpath('.//text()')).strip()
                    link_url = child.get('href', '')
                    if link_text:
                        if not is_in_heading and link_url:
                            # 不在标题中，附加链接URL
                            parts.append(f"{link_text} [{link_url}]")
                        else:
                            # 在标题中，不附加链接URL
                            parts.append(link_text)
                elif child.tag in ['script', 'style']:
                    # 跳过脚本和样式
                    continue
                else:
                    # 递归处理子元素
                    parts.extend(process_element(child, is_in_heading))
            else:
                # 文本节点（这种情况在lxml中很少见，因为文本通常作为元素的text属性）
                text = str(child).strip() if child else ""
                if text:
                    parts.append(text)
        
        # 添加当前元素的尾部文本（在最后一个子元素之后的文本）
        if hasattr(elem, 'tail') and elem.tail:
            text = elem.tail.strip()
            if text:
                parts.append(text)
        
        return parts
    
    # 处理所有元素
    for element in elements:
        result_parts.extend(process_element(element))
    
    # 如果上面的方法没有提取到内容，使用原来的方法作为后备
    if not result_parts:
        lines = parse.xpath(f'{selector}//text()')
        content = join_word.join(lines)
        return content
    
    return join_word.join(result_parts)


def template1(parse, join_word=""):
    """模板1: //div[@class="content"]/div[@class="text"]"""
    return extract_content_with_links(parse, '//div[@class="content"]/div[@class="text"]', join_word)


def template2(parse, join_word=""):
    """模板2: //div[@class="cont"]/div[@class="text"]"""
    return extract_content_with_links(parse, '//div[@class="cont"]/div[@class="text"]', join_word)


def template3(parse, join_word=""):
    """模板3: //div[@class="cont"]/div[@class]"""
    content = extract_content_with_links(parse, '//div[@class="cont"]/div[@class]', join_word)
    return content.split("评论")[0]


def template4(parse, join_word=""):
    """模板4: //div[@class="txtcont"]"""
    return extract_content_with_links(parse, '//div[@class="txtcont"]', join_word)


def template5(parse, join_word=""):
    """模板5: //div[@class="text"]"""
    return extract_content_with_links(parse, '//div[@class="text"]', join_word)


def template6(parse, join_word=""):
    """模板6: //div[@class="text"]/p/text()"""
    # 对于模板6，需要特殊处理，因为它是按p标签提取的
    return extract_content_with_links(parse, '//div[@class="text"]', join_word)


def template7(parse, join_word=""):
    """模板7: //div[contains(@class,'post-ctc')] 支持 post-ctc 和 post-ctc box
    只提取pic和text区域，排除其他无关内容（如tag、link、comment、hot等）
    """
    result_parts = []
    
    # 先尝试 post-ctc box
    post_ctc_elements = parse.xpath("//div[contains(@class,'post-ctc box')]")
    if not post_ctc_elements:
        # 如果没有，尝试 post-ctc（不带box）
        post_ctc_elements = parse.xpath("//div[@class='post-ctc']")
    
    if not post_ctc_elements:
        return ""
    
    post_ctc = post_ctc_elements[0]
    
    # 只提取pic和text区域的内容，排除tag、link、comment、hot等区域
    # 1. 提取pic区域的描述（如果有）
    pic_elements = post_ctc.xpath('.//div[@class="pic"]')
    for pic in pic_elements:
        # 提取pic下的desc或text区域
        desc_elements = pic.xpath('.//div[@class="desc"] | .//div[@class="text"]')
        for desc in desc_elements:
            desc_text = ''.join(desc.xpath('.//text()')).strip()
            if desc_text:
                result_parts.append(desc_text)
    
    # 2. 提取text区域的内容（只提取post-ctc内的text，排除其他区域的text）
    # 使用相对路径，只在post-ctc内查找text
    text_elements = post_ctc.xpath('.//div[@class="text"]')
    if text_elements:
        # 只处理第一个text元素，且确保它在post-ctc的直接子元素或pic/text结构中
        for text_elem in text_elements:
            # 检查text元素是否在post-ctc的直接子元素中，或者是否在pic/text结构中
            # 排除tag、link、comment、hot等区域的text
            parent_classes = text_elem.xpath('./ancestor::div/@class')
            parent_classes_str = ' '.join(parent_classes) if parent_classes else ''
            
            # 如果text在tag、link、comment、hot等区域，跳过
            if any(keyword in parent_classes_str for keyword in ['tag', 'link', 'comment', 'hot', '热度', '评论', '收藏', 'collection']):
                continue
            
            # 提取text内容
            text_content = extract_content_with_links(parse, f'//div[@class="post-ctc"]//div[@class="text"]', join_word)
            if text_content:
                result_parts.append(text_content)
                break  # 只取第一个有效的text区域
    
    # 如果既没有pic描述也没有text区域，返回空（不提取其他内容）
    return join_word.join(result_parts)


def all_purpose_template(parse, title, blog_type, join_word=""):
    """通用模板：只提取html-body下的框架中的main-content或main-cont区域内容，排除side、tag、link等区域"""
    content = ""
    
    # 方法0: 优先尝试从post-ctc区域提取（这是最常见的图片博文结构）
    try:
        # 尝试从post-ctc -> pic -> text 提取
        post_ctc_elements = parse.xpath('//div[@class="post-ctc"] | //div[contains(@class,"post-ctc")]')
        if post_ctc_elements:
            # 只提取post-ctc内的文本，排除pic区域（图片单独处理）
            # 提取text区域或直接文本
            text_elements = parse.xpath('//div[@class="post-ctc"]//div[@class="text"] | //div[contains(@class,"post-ctc")]//div[@class="text"]')
            if text_elements:
                content = extract_content_with_links(parse, '//div[@class="post-ctc"]//div[@class="text"] | //div[contains(@class,"post-ctc")]//div[@class="text"]', join_word)
                if content and content.strip():
                    return content.strip()
            else:
                # 如果没有text区域，尝试提取post-ctc内的所有文本（排除pic、tag、link等）
                content_lines = parse.xpath(
                    '//div[@class="post-ctc"]//text()['
                    'not(parent::style) and '
                    'not(parent::script) and '
                    'not(ancestor::div[@class="pic"]) and '
                    'not(ancestor::div[@class="tag"]) and '
                    'not(ancestor::div[contains(@class,"tag")]) and '
                    'not(ancestor::div[@class="link"]) and '
                    'not(ancestor::div[contains(@class,"link")]) and '
                    'not(ancestor::div[contains(@class,"comment")]) and '
                    'not(ancestor::div[contains(@class,"hot")]) and '
                    'not(ancestor::div[contains(@class,"热度")]) and '
                    'not(ancestor::div[contains(@class,"评论")]) and '
                    'not(ancestor::div[contains(@class,"收藏")]) and '
                    'not(ancestor::div[contains(@class,"collection")])'
                    ']'
                )
                if content_lines:
                    filtered_lines = [line.strip() for line in content_lines if line.strip()]
                    final_lines = []
                    for line in filtered_lines:
                        if line.isdigit() and len(line) <= 2:
                            continue
                        if re.match(r'^(评论|热度|收藏)\(', line):
                            continue
                        if line.startswith('●') or line.startswith('*'):
                            continue
                        if '很喜欢此图片' in line or '推荐了此图片' in line or '收藏了此图片' in line:
                            continue
                        if '加载中' in line or '查看更多' in line:
                            continue
                        final_lines.append(line)
                    if final_lines:
                        content = join_word.join(final_lines)
                        if content.strip():
                            if title and content.startswith(title):
                                content = content[len(title):].strip()
                            content = re.split(r"\s评论\s", content)[0].strip()
                            if content:
                                return content
    except Exception as e:
        pass
    
    # 方法1: 从body下的main区域中的content子区域提取（排除side、tag、link等）
    # 路径：html-body-block-main-content（排除side、tag、link）
    try:
        # 优先提取main下的content区域，排除side、tag、link等子区域
        selectors = [
            '//body//div[contains(@class,"main")]//div[@class="content"]',
            '//body//div[contains(@class,"main")]//div[contains(@class,"content")]',
            '//body//div[contains(@class,"main-content")]',
        ]
        
        for selector in selectors:
            content_elements = parse.xpath(selector)
            if content_elements:
                # 只提取content区域内的文本，排除tag、link等子区域
                # 排除：tag区域、link区域、side区域、评论区域、热度区域
                content_lines = parse.xpath(
                    f'{selector}//text()['
                    'not(parent::style) and '
                    'not(parent::script) and '
                    'not(parent::noscript) and '
                    'not(ancestor::div[@class="tag"]) and '
                    'not(ancestor::div[contains(@class,"tag")]) and '
                    'not(ancestor::div[@class="link"]) and '
                    'not(ancestor::div[contains(@class,"link")]) and '
                    'not(ancestor::div[@class="side"]) and '
                    'not(ancestor::div[contains(@class,"side")]) and '
                    'not(ancestor::div[contains(@class,"comment")]) and '
                    'not(ancestor::div[contains(@class,"hot")]) and '
                    'not(ancestor::div[contains(@class,"热度")]) and '
                    'not(ancestor::div[contains(@class,"评论")])'
                    ']'
                )
                if content_lines:
                    # 过滤掉空行和只有空白字符的行
                    filtered_lines = [line.strip() for line in content_lines if line.strip()]
                    # 进一步过滤：排除纯数字（可能是日期）、评论、热度等
                    final_lines = []
                    for line in filtered_lines:
                        # 跳过纯数字（可能是日期）
                        if line.isdigit() and len(line) <= 2:
                            continue
                        # 跳过评论、热度、收藏信息
                        if re.match(r'^(评论|热度|收藏)\(', line):
                            continue
                        # 跳过标签格式（● 开头）和列表标记（* 开头）
                        if line.startswith('●') or line.startswith('*'):
                            continue
                        # 跳过收藏列表相关文本
                        if '很喜欢此图片' in line or '推荐了此图片' in line or '收藏了此图片' in line:
                            continue
                        if '共' in line and '人收藏了此图片' in line:
                            continue
                        if '加载中' in line or '查看更多' in line:
                            continue
                        # 跳过导航链接文本
                        if line in ['私信', '归档', '只展示最近三个月数据']:
                            continue
                        # 跳过版权信息
                        if 'Powered by' in line or 'LOFTER' in line:
                            continue
                        final_lines.append(line)
                    
                    if final_lines:
                        content = join_word.join(final_lines)
                        if content.strip():
                            # 移除标题（如果存在且出现在开头）
                            if title and content.startswith(title):
                                content = content[len(title):].strip()
                            # 移除评论部分
                            content = re.split(r"\s评论\s", content)[0].strip()
                            if content:
                                return content
    except Exception as e:
        pass
    
    # 方法2: 从body下的main-cont区域提取（排除side、tag、link等）
    try:
        selectors = [
            '//body//div[contains(@class,"main-cont")]',
            '//body//div[@class="main-cont"]',
        ]
        
        for selector in selectors:
            main_cont_elements = parse.xpath(selector)
            if main_cont_elements:
                # 排除tag、link、side等区域
                main_cont_lines = parse.xpath(
                    f'{selector}//text()['
                    'not(parent::style) and '
                    'not(parent::script) and '
                    'not(parent::noscript) and '
                    'not(ancestor::div[@class="tag"]) and '
                    'not(ancestor::div[contains(@class,"tag")]) and '
                    'not(ancestor::div[@class="link"]) and '
                    'not(ancestor::div[contains(@class,"link")]) and '
                    'not(ancestor::div[@class="side"]) and '
                    'not(ancestor::div[contains(@class,"side")])'
                    ']'
                )
                if main_cont_lines:
                    # 过滤掉空行和只有空白字符的行
                    filtered_lines = [line.strip() for line in main_cont_lines if line.strip()]
                    # 进一步过滤
                    final_lines = []
                    for line in filtered_lines:
                        if line.isdigit() and len(line) <= 2:
                            continue
                        if re.match(r'^(评论|热度|收藏)\(', line):
                            continue
                        if line.startswith('●') or line.startswith('*'):
                            continue
                        if '很喜欢此图片' in line or '推荐了此图片' in line or '收藏了此图片' in line:
                            continue
                        if '共' in line and '人收藏了此图片' in line:
                            continue
                        if '加载中' in line or '查看更多' in line:
                            continue
                        if line in ['私信', '归档', '只展示最近三个月数据']:
                            continue
                        if 'Powered by' in line or 'LOFTER' in line:
                            continue
                        final_lines.append(line)
                    
                    if final_lines:
                        content = join_word.join(final_lines)
                        if content.strip():
                            if title and content.startswith(title):
                                content = content[len(title):].strip()
                            content = re.split(r"\s评论\s", content)[0].strip()
                            if content:
                                return content
    except Exception as e:
        pass
    
    # 方法3: 如果以上都失败，返回空内容
    return ""


def matcher(parse):
    """匹配模板"""
    template_id = 0
    if template1(parse) != "":
        template_id = 1
    elif template2(parse) != "":
        template_id = 2
    elif template3(parse) != "":
        template_id = 3
    elif template4(parse) != "":
        template_id = 4
    elif template5(parse) != "":
        template_id = 5
    elif template6(parse) != "":
        template_id = 6
    elif template7(parse) != "":
        template_id = 7
    return template_id


def get_content(parse, template_id, title, blog_type, join_word=""):
    """根据模板ID获取内容"""
    content = ""
    if template_id == 1:
        content = template1(parse, join_word)
        content = content.replace(title, "", 1)
    elif template_id == 2:
        content = template2(parse, join_word)
        content = content.replace(title, "", 1)
    elif template_id == 3:
        content = template3(parse, join_word)
        content = content.replace(title, "", 1)
    elif template_id == 4:
        content = template4(parse, join_word)
    elif template_id == 5:
        content = template5(parse, join_word)
    elif template_id == 6:
        content = template6(parse, join_word)
    elif template_id == 7:
        content = template7(parse, join_word)
    elif template_id == 0:
        content = all_purpose_template(parse, title, blog_type, join_word)
        content = content.replace("    ", "").replace("\t", "")
    content = content.strip()
    return content
