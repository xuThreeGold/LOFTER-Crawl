# LOFTER爬虫工具

基于lofterSpider-master项目改进的LOFTER内容爬取工具。

## 功能特性

1. **单篇文章保存**：给定网页链接，将内容保存为文件
2. **Tag爬取**：爬取指定tag下的所有文件，支持按作者分类存储
   - 排序方式：最新、最热
   - 最热排序：日榜、周榜、月榜、全部（默认）
3. **作者爬取**：
   - 爬取某个作者的全部文件
   - 爬取某个作者的指定tag的所有文件
4. **Tag+作者组合爬取**：爬取tag下的文件，然后进入这些文件的作者主页，爬取该作者的指定tag的所有文件
5. **文件格式**：
   - TXT格式：图片链接保存在txt中，图片文件单独保存
   - Markdown格式：图片直接嵌入文件

## 安装

```bash
pip install -r requirements.txt
```

## 配置

默认登录授权码已配置在`src/config.py`中，也可以通过命令行参数`--login-auth`传入新的值。

## 使用方法

### 1. 保存单篇文章

```bash
python run.py post <文章URL> [选项]
```

示例：
```bash
# 保存为TXT格式（默认）
python run.py post https://xxx.lofter.com/post/xxx

# 保存为Markdown格式
python run.py post https://xxx.lofter.com/post/xxx --format md

# 指定保存路径
python run.py post https://xxx.lofter.com/post/xxx --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢"

# 不保存图片
python run.py post https://xxx.lofter.com/post/xxx --no-images
```

### 2. 爬取Tag下的所有文章

```bash
python run.py tag <tag名称> [选项]
```

排序方式：
- `new`: 最新（默认）
- `total`: 全部最热
- `month`: 月榜
- `week`: 周榜
- `date`: 日榜

示例：
```bash
# 爬取最新文章
python run.py tag "风起东宫" --sort new

# 爬取最热文章（全部）
python run.py tag "风起东宫" --sort total

# 爬取月榜文章，按作者分组保存
python run.py tag "风起东宫" --sort month --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢"

# 爬取并保存为Markdown格式，不按作者分组
python run.py tag "风起东宫" --format md --no-group

# 设置最低热度限制
python run.py tag "风起东宫" --sort total --min-hot 100
```

### 3. 爬取作者的文章

```bash
python run.py author <作者主页URL> [选项]
```

示例：
```bash
# 爬取作者的全部文章
python run.py author https://xxx.lofter.com/

# 只爬取包含指定tag的文章
python run.py author https://xxx.lofter.com/ --tags "风起东宫" "太卢"

# 指定时间范围
python run.py author https://xxx.lofter.com/ --start-time "2024-01-01" --end-time "2024-12-31"

# 保存为Markdown格式
python run.py author https://xxx.lofter.com/ --format md
```

### 4. Tag+作者组合爬取

```bash
python run.py tag-author <初始tag> <目标tag> [选项]
```

功能：先爬取初始tag下的文章，然后进入这些文章的作者主页，爬取每位作者的指定tag的所有文章。

示例：
```bash
# 爬取"风起东宫"tag下的文章，然后爬取这些作者的"太卢"tag文章
python run.py tag-author "风起东宫" "太卢" --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢"

# 使用最热排序
python run.py tag-author "风起东宫" "太卢" --sort total
```

## 通用选项

- `--login-auth <授权码>`: 指定登录授权码（覆盖默认值）
- `--save-path <路径>`: 指定保存路径（默认：./result）
- `--format <txt|md>`: 文件格式（默认：txt）
- `--no-images`: 不保存图片文件
- `--no-group`: 不按作者分组（所有文件保存在一个文件夹）

## 文件命名规则

文件命名方式参考lofterSpider-master：
- 有标题的文章：`文章标题 by 作者名.txt`
- 无标题的文章：`作者名-第一个tag-发表时间.txt`

文件开头包含信息：
```
文章标题 by 作者名[作者IP]
发表时间：2024-01-01
原文链接： https://xxx.lofter.com/post/xxx
```

## 注意事项

1. 需要有效的登录授权码才能访问LOFTER内容
2. 大量爬取时请注意控制频率，避免对服务器造成压力
3. 图片下载可能较慢，建议使用`--no-images`选项先测试文本内容
4. 按作者分组时，会在保存路径下为每位作者创建`作者_作者名`文件夹
