# LOFTER爬虫工具

基于 [lofterSpider](https://github.com/IshtarTang/lofterSpider) 项目改进的LOFTER内容爬取工具。

## 项目介绍

本项目是一个功能完整的LOFTER内容爬取和管理工具集，支持爬取、合并、格式转换等功能。

### 项目设计

项目采用模块化设计，主要分为以下几个部分：

1. **核心爬虫模块** (`src/`): 包含所有爬虫相关的核心功能
   - `post_parser.py`: 文章解析模块
   - `tag_crawler.py`: Tag爬取模块
   - `author_crawler.py`: 作者爬取模块
   - `file_saver.py`: 文件保存模块
   - `main.py`: 爬虫主程序（包含命令行解析和授权码管理）

2. **文件处理模块**:
   - `merge/`: 文件合并功能，支持按时间排序合并多个文件
   - `md2other/`: Markdown格式转换功能，支持转换为PDF、EPUB、TXT、DOCX

3. **统一入口** (`run.py`): 整合所有功能的命令行入口

### 参考项目

本项目基于 [lofterSpider](https://github.com/IshtarTang/lofterSpider) 项目改进，参考了其核心爬取逻辑和文件保存方式，并在此基础上进行了以下改进：

- 统一了命令行接口，所有功能通过 `run.py` 调用
- 添加了交互式授权码管理功能
- 支持Markdown格式输出
- 添加了文件合并功能
- 添加了Markdown格式转换功能
- 改进了代码结构，提高了可维护性

## 功能特性

1. **单篇文章保存**：给定网页链接，将内容保存为文件
2. **Tag爬取**：爬取指定tag下的所有文件，支持按作者分类存储
   - 排序方式：最新、最热
   - 最热排序：日榜、周榜、月榜、全部（默认）
3. **作者爬取**：
   - 爬取某个作者的全部文件
   - 爬取某个作者的指定tag的所有文件
4. **Tag+作者组合爬取**：爬取tag下的文件，然后进入这些文件的作者主页，爬取该作者的指定tag的所有文件
5. **文件合并**：合并一个文件夹中的所有lofter爬取文件
   - 支持TXT和MD两种格式
   - 按发表时间排序合并
   - 每个文件作为一章，标题为"第XX章-文件名"
6. **Markdown格式转换**：将Markdown文件转换为其他格式
   - 支持转换为PDF、EPUB、TXT、DOCX格式
   - 可指定输入文件和输出路径
   - 默认输出到result目录
7. **文件格式**：
   - TXT格式：图片链接保存在txt中，图片文件单独保存
   - Markdown格式：图片直接嵌入文件

## 环境要求

- **Python版本**: Python >= 3.7（推荐 Python 3.8-3.12）
- **操作系统**: Windows / Linux / macOS

### Python版本说明

- **Python 3.8-3.11**: 完全支持，所有依赖包都有预编译wheel
- **Python 3.12**: 支持，但需要确保使用最新版本的依赖包（已在requirements.txt中更新）
- **Python 3.7**: 支持，但部分包可能需要从源码编译

### Windows用户注意事项

如果安装时遇到 `Microsoft Visual C++ 14.0 or greater is required` 错误：

1. **推荐方案**：使用更新的依赖版本（已更新requirements.txt）
2. **备选方案1**：安装 Microsoft C++ Build Tools
   - 下载地址：https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - 安装 "Desktop development with C++" 工作负载
3. **备选方案2**：使用 conda 安装
   ```bash
   conda install lxml
   ```
4. **备选方案3**：使用 Python 3.10 或 3.11（这些版本通常有更多预编译包）

## 安装

### 1. 克隆或下载项目

```bash
cd LOFTER-Crawl
```

### 2. 安装依赖包

```bash
pip install -r requirements.txt
```

**Markdown格式转换功能（可选）**：

如果需要使用 `md2other` 命令进行格式转换，需要额外安装依赖：

```bash
# 进入md2other目录
cd md2other
pip install -r requirements.txt
```

**注意**：
- PDF、EPUB、DOCX格式转换需要安装Pandoc（https://pandoc.org/installing.html）
- TXT格式转换无需额外依赖，可直接使用
- 如果遇到网络问题，可以使用conda安装：`conda install -c conda-forge markdown pypandoc`

**如果遇到编译错误**（特别是 Windows 用户）：

```bash
# 方案1：升级pip和setuptools（推荐）
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 方案2：使用conda安装lxml（如果使用conda环境）
conda install lxml
pip install -r requirements.txt

# 方案3：单独安装可能有问题的包
pip install lxml --upgrade
pip install -r requirements.txt
```

### 3. 验证安装

```bash
python run.py --help
```

如果显示帮助信息，说明安装成功。

## 配置

### 获取登录授权码

使用爬虫功能需要先获取登录授权码。获取方式如下：

1. **登录LOFTER**：在浏览器中登录LOFTER网站
2. **打开开发者工具**：在登录后的任意LOFTER网页上，按 `F12` 打开开发者工具
3. **查看Cookies**：
   - 点击 `Application` 标签（或 `应用程序` 标签）
   - 在左侧找到 `Cookies`，点击展开
   - 点击 `Cookies` 下的 `https://www.lofter.com`（或你访问的lofter域名）
4. **查找授权码**：在右侧的Cookie列表中，找到 `LOFTER-PHONE-LOGIN-AUTH`（或其他登录方式对应的key），复制其 `Value` 值

**操作示例**：

![获取授权码示例](READMEimg/LOFTER-PHONE-LOGIN-AUTH.png)

**注意**：
- 如果使用其他登录方式（如QQ、微信、邮箱等），需要查找对应的Cookie key：
  - 手机号登录：`LOFTER-PHONE-LOGIN-AUTH`
  - Lofter ID登录：`Authorization`
  - QQ/微信/微博登录：`LOFTER_SESS`
  - 邮箱登录：`NTES_SESS`
- 授权码会定期过期，过期后需要重新获取
- 授权码是敏感信息，请妥善保管，不要泄露

**授权码使用方式**：

1. **交互式输入**（推荐）：运行爬虫命令时，如果没有通过命令行参数提供授权码，程序会自动提示输入
2. **命令行参数**：通过 `--login-auth` 参数传入
3. **配置文件**：修改 `src/config.py` 中的 `DEFAULT_LOGIN_AUTH`（不推荐，可能泄露）

## 使用说明

### 命令行使用

所有功能都通过 `run.py` 入口文件调用，基本格式：

```bash
python run.py <命令> <参数> [选项]
```

### 查看帮助

```bash
# 查看所有命令
python run.py --help

# 查看特定命令的帮助
python run.py post --help
python run.py tag --help
python run.py author --help
python run.py tag-author --help
python run.py merge --help
python run.py md2other --help
```

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
python run.py post https://xxx.lofter.com/post/xxx --save-path "./my_articles"

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
python run.py tag "示例tag" --sort new

# 爬取最热文章（全部）
python run.py tag "示例tag" --sort total

# 爬取月榜文章，按作者分组保存
python run.py tag "示例tag" --sort month --save-path "./articles"

# 爬取并保存为Markdown格式，不按作者分组
python run.py tag "示例tag" --format md --no-group

# 设置最低热度限制
python run.py tag "示例tag" --sort total --min-hot 100
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
python run.py author https://xxx.lofter.com/ --tags "tag1" "tag2"

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
# 爬取初始tag下的文章，然后爬取这些作者的目标tag文章
python run.py tag-author "初始tag" "目标tag" --save-path "./articles"

# 使用最热排序
python run.py tag-author "初始tag" "目标tag" --sort total
```

### 5. 合并文件

```bash
python run.py merge <输入文件夹> [选项]
```

功能：合并指定文件夹中的所有lofter爬取文件，按发表时间排序，每个文件作为一章。

**注意**：`merge` 命令不需要授权码，可以直接使用。

示例：
```bash
# 合并TXT文件（默认格式），输出到项目根目录下的result文件夹
python run.py merge "./articles"

# 合并MD文件
python run.py merge "./articles" -f md

# 指定输出文件夹和文件名
python run.py merge "./articles" -o "./merged" -n "合并后的文件"

# 合并MD文件并指定输出路径
python run.py merge "./articles" -f md -o "./merged" -n "合并后的文件"
```

### 6. Markdown格式转换

```bash
python run.py md2other <Markdown文件路径> --format <格式> [选项]
```

功能：将Markdown文件转换为PDF、EPUB、TXT、DOCX等格式。

**注意**：`md2other` 命令不需要授权码，可以直接使用。

示例：
```bash
# 转换为PDF（输出到result目录）
python run.py md2other "result/example.md" --format pdf

# 转换为EPUB
python run.py md2other "result/example.md" --format epub

# 转换为DOCX
python run.py md2other "result/example.md" --format docx

# 转换为TXT
python run.py md2other "result/example.md" --format txt

# 指定输出文件路径
python run.py md2other "result/example.md" --format pdf --output "output/example.pdf"

# 指定输出目录
python run.py md2other "result/example.md" --format epub --output-dir "./output"
```

**注意**：
- PDF、EPUB、DOCX格式转换需要安装Pandoc（https://pandoc.org/installing.html）
- TXT格式转换无需额外依赖，可直接使用
- 转换时如果遇到图片路径警告，不影响转换结果，只是图片可能不会包含在输出文件中

## 超参数说明

### 通用超参数（所有爬虫命令支持）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--login-auth` | 字符串 | 交互式输入或配置文件默认值 | 登录授权码（LOFTER-PHONE-LOGIN-AUTH的值） |
| `--save-path` | 字符串 | `./result` | 文件保存路径 |
| `--format` | 选择项 | `txt` | 文件格式：`txt` 或 `md` |
| `--no-images` | 标志 | `False` | 不保存图片文件（仅保存文本） |
| `--no-group` | 标志 | `False` | 不按作者分组（所有文件保存在同一文件夹） |

#### `--login-auth <授权码>`
- **类型**: 字符串
- **默认值**: 交互式输入或 `src/config.py` 中配置的 `DEFAULT_LOGIN_AUTH`
- **说明**: LOFTER登录授权码，即Cookie中`LOFTER-PHONE-LOGIN-AUTH`的值
- **获取方式**: 见上方"获取登录授权码"章节
- **优先级**: 命令行参数 > 交互式输入 > 配置文件默认值

#### `--save-path <路径>`
- **类型**: 字符串（文件路径）
- **默认值**: `./result`
- **说明**: 文件保存的根目录路径
- **示例**: `--save-path "./my_articles"`

#### `--format <格式>`
- **类型**: 选择项（`txt` 或 `md`）
- **默认值**: `txt`
- **说明**: 文件保存格式
  - `txt`: 纯文本格式，图片链接记录在文件中，图片文件单独保存
  - `md`: Markdown格式，图片直接嵌入文件
- **示例**: `--format md`

#### `--no-images`
- **类型**: 标志（无需参数）
- **默认值**: `False`（保存图片）
- **说明**: 启用后不下载和保存图片文件，仅保存文本内容
- **使用场景**: 快速测试、网络不稳定、只需文本内容时
- **示例**: `--no-images`

#### `--no-group`
- **类型**: 标志（无需参数）
- **默认值**: `False`（按作者分组）
- **说明**: 启用后所有文件保存在同一文件夹，不按作者创建子文件夹
- **使用场景**: 单个作者爬取、不需要分类时
- **示例**: `--no-group`

### Tag爬取专用超参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--sort` | 选择项 | `new` | 排序方式：`new`(最新)、`total`(全部最热)、`month`(月榜)、`week`(周榜)、`date`(日榜) |
| `--min-hot` | 整数 | `0` | 最低热度限制，只爬取热度大于等于此值的文章 |

#### `--sort <排序方式>`
- **类型**: 选择项（`new`、`total`、`month`、`week`、`date`）
- **默认值**: `new`
- **说明**: 文章排序方式
  - `new`: 按最新发布时间排序
  - `total`: 按全部时间最热排序
  - `month`: 按月榜最热排序
  - `week`: 按周榜最热排序
  - `date`: 按日榜最热排序
- **示例**: `--sort total`

#### `--min-hot <热度值>`
- **类型**: 整数
- **默认值**: `0`
- **说明**: 最低热度限制，只爬取热度大于等于此值的文章
- **使用场景**: 过滤低热度文章，提高内容质量
- **示例**: `--min-hot 100`

### 作者爬取专用超参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--tags` | 列表 | `None` | 目标tags列表，只爬取包含这些tag的文章（可指定多个） |
| `--start-time` | 字符串 | `None` | 开始时间，格式：`YYYY-MM-DD`（如：`2024-01-01`） |
| `--end-time` | 字符串 | `None` | 结束时间，格式：`YYYY-MM-DD`（如：`2024-12-31`） |

#### `--tags <tag1> <tag2> ...`
- **类型**: 字符串列表（可指定多个）
- **默认值**: `None`（爬取所有文章）
- **说明**: 目标tags列表，只爬取包含这些tag中任意一个的文章
- **过滤模式**: `in`（包含模式，默认）
- **示例**: `--tags "tag1" "tag2"`

#### `--start-time <日期>`
- **类型**: 字符串（格式：`YYYY-MM-DD`）
- **默认值**: `None`（不限制）
- **说明**: 开始时间，只爬取此日期之后发表的文章
- **示例**: `--start-time "2024-01-01"`

#### `--end-time <日期>`
- **类型**: 字符串（格式：`YYYY-MM-DD`）
- **默认值**: `None`（不限制）
- **说明**: 结束时间，只爬取此日期之前发表的文章
- **示例**: `--end-time "2024-12-31"`

### Tag+作者组合爬取超参数

Tag+作者组合爬取命令支持所有Tag爬取的超参数（`--sort`、`--min-hot`）和通用超参数。

### 文件合并超参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `input_folder` | 字符串（必需） | - | 输入文件夹路径（包含所有要合并的文件） |
| `-o, --output` | 字符串 | `项目根目录/result` | 输出文件夹路径 |
| `-n, --name` | 字符串 | 输入文件夹名 | 输出文件名（不含扩展名） |
| `-f, --format` | 选择项 | `txt` | 文件格式：`txt` 或 `md` |

**注意事项**：
- 输入文件夹中的文件必须统一格式（要么全是TXT，要么全是MD）
- 如果无法从文件中提取发表时间，将使用文件的修改时间作为排序依据
- 合并后的文件会保留原文件的内容，但会去除文件头（TXT格式）或YAML Front-Matter（MD格式）
- 每个原文件在合并后的文件中作为一章，章节标题格式为"第XX章-文件名"

### Markdown格式转换专用超参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--format` 或 `-f` | 选择项 | **必需** | 输出格式：`pdf`、`epub`、`txt`、`docx` |
| `--output` 或 `-o` | 字符串 | `result/文件名.格式` | 输出文件路径（可选） |
| `--output-dir` 或 `-d` | 字符串 | `result` | 输出目录（当未指定--output时使用） |

**格式说明**：
- `pdf`: 便携式文档格式，需要安装Pandoc和pypandoc
- `epub`: 电子书格式，需要安装Pandoc和pypandoc
- `txt`: 纯文本格式，无需额外依赖
- `docx`: Word文档格式，需要安装Pandoc和pypandoc

## 使用示例

### 完整示例1：爬取tag最新文章并按作者分组

```bash
python run.py tag "示例tag" \
    --sort new \
    --save-path "./articles" \
    --format txt \
    --min-hot 0
```

### 完整示例2：爬取tag最热文章（月榜）

```bash
python run.py tag "示例tag" \
    --sort month \
    --save-path "./articles" \
    --format txt \
    --min-hot 50
```

### 完整示例3：爬取作者指定tag的文章

```bash
python run.py author "https://xxx.lofter.com/" \
    --tags "tag1" "tag2" \
    --save-path "./articles" \
    --start-time "2024-01-01" \
    --end-time "2024-12-31"
```

### 完整示例4：Tag+作者组合爬取

```bash
python run.py tag-author "初始tag" "目标tag" \
    --sort total \
    --save-path "./articles" \
    --format txt \
    --min-hot 0
```

### 完整示例5：保存为Markdown格式（不保存图片）

```bash
python run.py post "https://xxx.lofter.com/post/xxx" \
    --format md \
    --no-images \
    --save-path "./articles"
```

### 完整示例6：合并文件

```bash
# 合并TXT文件
python run.py merge "./articles" -f txt

# 合并MD文件并指定输出
python run.py merge "./articles" \
    -f md \
    -o "./merged" \
    -n "合并后的文件"
```

## 高级用法

### 使用自定义登录授权码

```bash
python run.py tag "示例tag" \
    --login-auth "你的授权码" \
    --save-path "./result"
```

### 批量处理多个tag

可以编写脚本循环调用：

```python
import subprocess

tags = ["tag1", "tag2", "tag3"]
for tag in tags:
    subprocess.run([
        "python", "run.py", "tag", tag,
        "--save-path", f"./articles/{tag}",
        "--sort", "total"
    ])
```

### Python代码调用

也可以直接在Python代码中调用：

```python
from src.main import crawl_tag

crawl_tag(
    tag_name="示例tag",
    sort_type="total",
    save_path="./articles",
    file_format="txt",
    group_by_author=True,
    save_images=True,
    min_hot=0
)
```

## 文件命名规则

文件命名方式参考lofterSpider项目：
- 有标题的文章：`文章标题 by 作者名.txt`
- 无标题的文章：`作者名-第一个tag-发表时间.txt`

文件开头包含信息：
```
文章标题 by 作者名[作者IP]
发表时间：2024-01-01
原文链接： https://xxx.lofter.com/post/xxx
```

## 注意事项

1. **登录授权码**：
   - 需要有效的登录授权码才能访问LOFTER内容
   - 授权码会定期过期，过期后需要重新获取
   - 授权码是敏感信息，请妥善保管，不要泄露
   - 获取方式见上方"获取登录授权码"章节

2. **爬取频率**：大量爬取时请注意控制频率，避免对服务器造成压力。程序已内置随机延迟。

3. **图片下载**：图片下载可能较慢，建议：
   - 先使用`--no-images`选项测试文本内容
   - 确认无误后再完整爬取
   - 网络不稳定时可能需要多次运行

4. **文件组织**：
   - 按作者分组时，会在保存路径下为每位作者创建`作者_作者名`文件夹
   - 不分组时，所有文件保存在指定路径的根目录

5. **文件命名**：
   - 如果文件名重复，会自动添加序号：`文件名(2).txt`
   - 特殊字符会被替换为安全字符

6. **错误处理**：
   - 如果某个文章解析失败，会跳过并继续处理其他文章
   - 建议保存日志以便排查问题

7. **数据备份**：重要数据请及时备份，避免因程序异常导致数据丢失

8. **授权码管理**：
   - `merge` 和 `md2other` 命令不需要授权码，可以直接使用
   - 爬虫相关命令（`post`、`tag`、`author`、`tag-author`）需要授权码
   - 如果未通过命令行提供授权码，程序会交互式询问

## 项目结构

```
LOFTER-Crawl/
├── src/                    # 核心爬虫模块
│   ├── main.py            # 爬虫主程序（包含命令行解析）
│   ├── post_parser.py     # 文章解析模块
│   ├── tag_crawler.py     # Tag爬取模块
│   ├── author_crawler.py  # 作者爬取模块
│   ├── file_saver.py      # 文件保存模块
│   └── config.py          # 配置文件
├── merge/                  # 文件合并模块
│   ├── merge_files.py     # 合并功能实现
│   └── README.md          # 合并功能说明
├── md2other/              # Markdown格式转换模块
│   ├── md2other.py        # 转换功能实现
│   └── requirements.txt   # 转换功能依赖
├── result/                # 默认输出目录
├── run.py                 # 统一入口文件
├── requirements.txt       # 项目依赖
└── README.md              # 项目说明文档
```

## 许可证

本项目基于 [lofterSpider](https://github.com/IshtarTang/lofterSpider) 项目改进，请遵守原项目的许可证要求。
