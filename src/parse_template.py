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
    """通用模板"""
    lines = parse.xpath('/html//text()')
    content = join_word.join(lines)
    if blog_type == "article":
        try:
            title = title.encode("utf-8", errors="replace").decode("utf-8", errors="replace").replace("?", "")
            content = content.split(title, 2)[2]
        except:
            pass
        content = re.split(r"\s评论\s", content)[0].encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    else:
        content = content.split("评论")[0].encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    return content


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
