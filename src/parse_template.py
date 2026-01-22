# -*- coding: utf-8 -*-
"""
文章内容解析模板
参考lofterSpider-master的parse_template.py
"""
import re
import html2text


def template1(parse, join_word=""):
    """模板1: //div[@class="content"]/div[@class="text"]"""
    lines = parse.xpath('//div[@class="content"]/div[@class="text"]//text()')
    content = join_word.join(lines)
    return content


def template2(parse, join_word=""):
    """模板2: //div[@class="cont"]/div[@class="text"]"""
    lines = parse.xpath('//div[@class="cont"]/div[@class="text"]//text()')
    content = join_word.join(lines)
    return content


def template3(parse, join_word=""):
    """模板3: //div[@class="cont"]/div[@class]"""
    lines = parse.xpath('//div[@class="cont"]/div[@class]//text()')
    content = join_word.join(lines).split("评论")[0]
    return content


def template4(parse, join_word=""):
    """模板4: //div[@class="txtcont"]"""
    lines = parse.xpath('//div[@class="txtcont"]//text()')
    content = join_word.join(lines)
    return content


def template5(parse, join_word=""):
    """模板5: //div[@class="text"]"""
    lines = parse.xpath('//div[@class="text"]//text()')
    content = join_word.join(lines)
    return content


def template6(parse, join_word=""):
    """模板6: //div[@class="text"]/p/text()"""
    lines = parse.xpath('//div[@class="text"]/p/text()')
    content = (join_word + "\n\n").join(lines)
    return content


def template7(parse, join_word=""):
    """模板7: //div[contains(@class,'post-ctc box')]"""
    lines = parse.xpath("//div[contains(@class,'post-ctc box')]//p//text()")
    content = join_word.join(lines)
    return content


def all_purpose_template(parse, title, blog_type, join_word=""):
    """通用模板：只提取html-body下的框架中的main-content或main-cont区域内容，排除side、tag、link等区域"""
    content = ""
    
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
                        # 跳过评论和热度信息
                        if re.match(r'^(评论|热度)\(', line):
                            continue
                        # 跳过标签格式（● 开头）
                        if line.startswith('●'):
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
                        if re.match(r'^(评论|热度)\(', line):
                            continue
                        if line.startswith('●'):
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
