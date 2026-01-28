# LOFTER爬虫工具

基于 [lofterSpider](https://github.com/IshtarTang/lofterSpider) 项目改进，并参考  
[lofter-helper](https://github.com/SrakhiuMeow/lofter-helper)、  
[Loftify](https://github.com/Robert-Stackflow/Loftify) 等项目实现的 LOFTER 内容爬取与管理工具。

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

在实现合集爬取、彩蛋获取和部分接口访问时，还参考了以下项目的思路和实现：

- [lofter-helper](https://github.com/SrakhiuMeow/lofter-helper)：用于理解网页版 Lofter 合集列表与合集详情相关接口（`postCollection.api`）、合集展示逻辑等
- [Loftify](https://github.com/Robert-Stackflow/Loftify)：用于参考 LOFTER 移动端/第三方客户端中对非公开 API 的调用方式（如帖子详情、礼物/合集等接口），特别是彩蛋（打赏返礼）相关的 API 调用和请求头设置

## 功能特性

1. **单篇文章保存**：给定网页链接，将内容保存为文件
   - **自动检测和保存彩蛋内容**：如果文章包含已解锁的彩蛋（打赏返礼），会自动提取并附加到文章末尾
   - 支持TXT和Markdown两种格式
2. **Tag爬取**：爬取指定tag下的所有文件，支持按作者分类存储
   - 排序方式：最新、最热
   - 最热排序：日榜、周榜、月榜、全部（默认）
3. **作者爬取**：
   - 爬取某个作者的全部文件
   - 爬取某个作者的指定tag的所有文件
4. **Tag+作者组合爬取**：爬取tag下的文件，然后进入这些文件的作者主页，爬取该作者的指定tag的所有文件
5. **合集爬取**：
   - 根据**单个合集ID**，保存该合集中的所有文章
   - 根据**作者主页URL**，获取该作者的所有合集，并分别保存每个合集中的所有文章
6. **文件合并**：合并一个文件夹中的所有lofter爬取文件
   - 支持TXT和MD两种格式
   - 按发表时间排序合并
   - 每个文件作为一章，标题为"第XX章-文件名"
7. **Markdown格式转换**：将Markdown文件转换为其他格式
   - 支持转换为PDF、EPUB、TXT、DOCX格式
   - 可指定输入文件和输出路径
   - 默认输出到result目录
8. **文件格式**：
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

项目分为两部分依赖：

1. **核心爬虫功能依赖（必须）**  
   安装根目录下的依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. **Markdown 转其他格式功能依赖（可选，仅在使用 `md2other` 或 EPUB/PDF/DOCX 时需要）**  
   进入 `md2other` 目录安装：
   ```bash
   cd md2other
   pip install -r requirements.txt
   ```

说明：
- `md2other` 是**纯 Python 实现**的转换工具，不再依赖 Pandoc / LaTeX / wkhtmltopdf 等外部程序。
- TXT 转换几乎零额外依赖，PDF / EPUB / DOCX 转换所需的第三方库都已在 `md2other/requirements.txt` 中列出（如 `fpdf2`、`ebooklib`、`python-docx`、`markdown`、`beautifulsoup4`、`Pillow` 等）。

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

**功能说明**：
- 解析并保存单篇文章，支持自动检测和保存彩蛋内容
- 如果文章包含已解锁的彩蛋（打赏返礼），会自动提取并附加到文章末尾
- 支持TXT和Markdown两种格式

示例：
```bash
# 保存为TXT格式（默认）
python run.py post https://xxx.lofter.com/post/xxx

# 保存为Markdown格式（推荐，彩蛋内容会以更好的格式显示）
python run.py post https://xxx.lofter.com/post/xxx --format md

# 指定保存路径
python run.py post https://xxx.lofter.com/post/xxx --save-path "./my_articles"

# 不保存图片
python run.py post https://xxx.lofter.com/post/xxx --no-images
```

**彩蛋功能说明**：
- 如果文章包含已解锁的彩蛋内容，程序会自动检测并在文章末尾附加彩蛋文字
- 彩蛋内容会以清晰的格式显示（Markdown格式下会以代码块或正文形式展示）
- 如果彩蛋未解锁，会在文章末尾显示提示信息
- 彩蛋检测需要有效的登录授权码（必须是已解锁该彩蛋的账号）

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

**注意**：
- `merge` 命令不需要授权码，可以直接使用
- **只能合并本项目爬取的文件**：本工具依赖于文件开头的特定格式信息来提取发表时间和内容。TXT格式需要包含"发表时间："字段，MD格式需要包含YAML Front-Matter中的`date`字段。其他来源的文件可能无法正确解析

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

# 合并MD文件并添加可跳转的目录（默认）
python run.py merge "./articles" -f md --add-toc

# 合并MD文件并添加普通目录（不可跳转）
python run.py merge "./articles" -f md --add-toc --no-toc-links

# 合并TXT文件并添加目录
python run.py merge "./articles" -f txt --add-toc
```

### 6. 合集相关功能

#### 6.1 根据合集ID保存合集内所有文章

```bash
python run.py collection <合集ID或合集分享链接> [选项]
```

**默认保存规则**：

- 如果使用默认保存路径（不传 `--save-path` 或传入 `./result`）：
  - 单个合集会保存到 `result/合集_合集名(合集ID)-作者名/` 目录下  
  - 例如：  
    - 合集链接：`https://www.lofter.com/front/blog/collection/share?collectionId=合集ID&incantation=xxx`  
    - 合集名：`示例合集名`，作者名：`示例作者名`  
    - 文章将保存到：`result/合集_示例合集名(合集ID)-示例作者名/`

示例：

```bash
# 保存为TXT格式（默认）
python run.py collection 12345678

# 也可以直接使用合集分享链接
python run.py collection "https://www.lofter.com/front/blog/collection/share?collectionId=12345678&incantation=xxx"

# 保存为Markdown格式
python run.py collection 12345678 --format md

# 提供作者主页URL，以更准确获得合集名和作者名（推荐）
python run.py collection 12345678 --author-url https://example.lofter.com/

# 指定根保存路径（仍会在其下创建“合集名(合集ID)-作者名”文件夹）
python run.py collection 12345678 --save-path "./my_result"
```

#### 6.2 根据作者主页保存该作者的所有合集及其文章

```bash
python run.py author-collections <作者主页URL> [选项]
```

**默认保存规则**：

- 如果使用默认保存路径（不传 `--save-path` 或传入 `./result`）：
  - 会在 `result/作者_作者名/` 目录下，为每个合集创建子文件夹：  
    `合集_合集名(合集ID)-作者名/`
  - 例如：  
    - 作者主页：`https://example.lofter.com/`  
    - 假设作者名是 `示例作者名`，合集 `示例合集名(合集ID)`  
    - 所有合集文章最终路径类似：
      - `result/作者_示例作者名/合集_示例合集名(合集ID)-示例作者名/`

示例：

```bash
# 保存某作者的所有合集里的文章为TXT格式
python run.py author-collections https://example.lofter.com/

# 保存为Markdown格式
python run.py author-collections https://example.lofter.com/ --format md

# 指定根保存路径（会在其下创建“作者名/合集名(合集ID)-作者名/”结构）
python run.py author-collections https://example.lofter.com/ --save-path "./my_result"
```

### 7. 合集相关功能（续）

#### 合集合并逻辑说明

当使用 `--merge` / `--merge-add-toc` 选项时，合集内合并文件的规则如下：

- **合并范围**：
  - `collection`：只合并当前这个合集目录下的所有已保存文章文件。
  - `author-collections`：对该作者的**每一个合集目录**各自独立合并一份。

- **排序方式（默认）**：
  - 合并时按**发表时间升序**排序（越早的章节越靠前）。
  - 发表时间来自每个文件头部的“发表时间”字段（TXT）或 Front-Matter 中的 `date` 字段（MD）；若无法解析，则退回到文件修改时间。

- **文件格式与命名**：
  - 当 `--format txt` 或 `--format md` 时：
    - 直接调用内部的合并逻辑，输出一个大文件：
      - `合并_合集_合集名(合集ID)-作者名.txt`
      - 或 `合并_合集_合集名(合集ID)-作者名.md`
  - 当 `--format epub` 时：
    - 先按照上面规则合并出一个 Markdown 文件：
      - `合并_合集_合集名(合集ID)-作者名.md`
    - 再基于这个 MD 调用 `md2other` 转换为：
      - `合并_合集_合集名(合集ID)-作者名.epub`

- **目录（TOC）控制**：
  - 仅对 TXT/MD 合并时生效（EPUB 的目录来自合并后的 MD 结构）：
    - 不加 `--merge-add-toc`：合并文件**不**自动生成目录。
    - 加上 `--merge-add-toc`：
      - TXT：在文件开头生成一个纯文本目录。
      - MD：在文件开头生成一个 Markdown 目录（章节标题可点击跳转）。

**彩蛋功能**：
- 合集爬取功能同样支持自动检测和保存彩蛋内容
- 如果合集内的文章包含已解锁的彩蛋，会自动提取并附加到对应文章末尾
- 使用方法与单篇文章保存相同，只需提供有效的登录授权码

### 8. Markdown格式转换

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

### 合集相关功能超参数

合集相关功能（`collection` 和 `author-collections`）支持所有通用超参数，此外还有：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--author-url` | 字符串 | `None` | 作者主页URL（仅 `collection` 命令支持，用于更准确获取合集名和作者名） |

#### `--author-url <URL>`
- **类型**: 字符串（URL）
- **默认值**: `None`
- **说明**: 作者主页URL，用于更准确获取合集名和作者名（仅 `collection` 命令支持）
- **使用场景**: 当无法从合集ID直接获取准确的合集名和作者名时使用
- **示例**: `--author-url https://chaoxinian.lofter.com/`

**注意**：
- 合集爬取功能同样支持彩蛋检测，如果合集内的文章包含已解锁的彩蛋，会自动提取并保存
- 彩蛋检测需要有效的登录授权码（必须是已解锁该彩蛋的账号）

### 文件合并超参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `input_folder` | 字符串（必需） | - | 输入文件夹路径（包含所有要合并的文件） |
| `-o, --output` | 字符串 | `项目根目录/result` | 输出文件夹路径 |
| `-n, --name` | 字符串 | 输入文件夹名 | 输出文件名（不含扩展名） |
| `-f, --format` | 选择项 | `txt` | 文件格式：`txt` 或 `md` |
| `--add-toc` | 标志 | `False` | 在开头添加目录 |
| `--no-toc-links` | 标志 | `False` | 如果合并MD文件且添加目录，不使用可跳转的链接（默认使用可跳转链接，仅在`--add-toc`且格式为`md`时有效） |

**注意事项**：
- **只能合并本项目爬取的文件**：本工具依赖于文件开头的特定格式信息来提取发表时间和内容。TXT格式需要包含"发表时间："字段，MD格式需要包含YAML Front-Matter中的`date`字段。其他来源的文件可能无法正确解析
- 输入文件夹中的文件必须统一格式（要么全是TXT，要么全是MD）
- 如果无法从文件中提取发表时间，将使用文件的修改时间作为排序依据
- 合并后的文件会保留原文件的内容，但会去除文件头（TXT格式）或YAML Front-Matter（MD格式）
- 每个原文件在合并后的文件中作为一章，章节标题格式为"第XX章-文件名"
- 目录功能说明：
  - 使用`--add-toc`参数可以在合并后的文件开头添加目录
  - 对于MD格式，默认生成可跳转到对应章节的目录链接（支持大多数Markdown解析器）
  - 如果不想使用可跳转链接，可以使用`--no-toc-links`参数
  - TXT格式的目录为纯文本格式，不支持跳转

### Markdown格式转换专用超参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--format` 或 `-f` | 选择项 | **必需** | 输出格式：`pdf`、`epub`、`txt`、`docx` |
| `--output` 或 `-o` | 字符串 | `result/文件名.格式` | 输出文件路径（可选） |
| `--output-dir` 或 `-d` | 字符串 | `result` | 输出目录（当未指定--output时使用） |

**格式说明**：
- `pdf`: 便携式文档格式，使用 `fpdf2` 等纯 Python 库生成（依赖见 `md2other/requirements.txt`）
- `epub`: 电子书格式，使用 `ebooklib` 等库生成
- `txt`: 纯文本格式，无需额外系统依赖
- `docx`: Word文档格式，使用 `python-docx` 等库生成

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

### 完整示例6：保存文章并自动获取彩蛋内容

```bash
# 保存文章（如果包含已解锁的彩蛋，会自动附加到文章末尾）
python run.py post "https://xxx.lofter.com/post/xxx" \
    --format md \
    --save-path "./articles"

# 注意：必须使用已解锁彩蛋的账号的授权码
# 如果彩蛋未解锁，会在文章末尾显示提示信息
```

### 完整示例7：保存合集文章（自动获取彩蛋）

```bash
# 保存合集内所有文章，如果文章包含已解锁的彩蛋，会自动附加
python run.py collection 12345678 \
    --format md \
    --author-url https://example.lofter.com/ \
    --save-path "./result"
```

### 完整示例8：合并文件

```bash
# 合并TXT文件
python run.py merge "./articles" -f txt

# 合并MD文件并指定输出
python run.py merge "./articles" \
    -f md \
    -o "./merged" \
    -n "合并后的文件"

# 合并MD文件并添加可跳转的目录
python run.py merge "./articles" \
    -f md \
    --add-toc \
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

## 彩蛋功能说明

### 什么是彩蛋？

LOFTER 的"彩蛋"是指作者设置的打赏返礼内容。读者通过给文章打赏（送礼物），可以获得作者预设的返礼内容，这些内容通常是文章的额外章节、番外、隐藏剧情等。

### 如何获取彩蛋内容？

本工具支持自动检测和保存已解锁的彩蛋内容，使用方法如下：

#### 前置条件

1. **必须使用已解锁彩蛋的账号**：
   - 你需要在 LOFTER 客户端（App）中，通过打赏/送礼的方式解锁该文章的彩蛋
   - 只有已解锁的彩蛋才能被工具检测和保存

2. **获取正确的登录授权码**：
   - 使用**手机号登录**的账号，获取 `LOFTER-PHONE-LOGIN-AUTH` Cookie 值
   - 授权码获取方式见上方"获取登录授权码"章节
   - **重要**：必须使用与解锁彩蛋时相同的账号

#### 使用方法

保存单篇文章时，如果文章包含已解锁的彩蛋，程序会自动检测并附加到文章末尾：

```bash
# 保存文章（自动检测彩蛋）
python run.py post https://xxx.lofter.com/post/xxx --format md
```

#### 彩蛋内容显示方式

- **Markdown格式（推荐）**：
  - 彩蛋内容会以清晰的格式显示在文章末尾
  - 如果彩蛋有标题，会显示标题和正文
  - 如果彩蛋未解锁，会显示提示信息

- **TXT格式**：
  - 彩蛋内容会以文本形式附加在文章末尾
  - 如果彩蛋未解锁，会显示提示信息

#### 彩蛋检测流程

1. 程序会调用 LOFTER API 检测文章是否包含彩蛋配置
2. 如果检测到彩蛋，会检查当前账号是否已解锁（通过 `gainReturnGifts` 字段判断）
3. 如果已解锁，会调用 `myReturnGift` API 获取彩蛋的实际文字内容
4. 将彩蛋内容提取并附加到保存的文件末尾

#### 常见问题

**Q: 为什么我在 App 中已经解锁了彩蛋，但工具检测不到？**

A: 可能的原因：
- 授权码过期或无效，需要重新获取
- 使用的授权码与解锁彩蛋时的账号不一致
- 网络问题导致 API 调用失败

**Q: 彩蛋内容显示为 JSON 数据怎么办？**

A: 这通常表示彩蛋内容提取失败。请检查：
- 授权码是否有效
- 是否使用了正确的账号（与解锁彩蛋时相同的账号）
- 查看终端输出的调试信息（`[彩蛋检测]` 开头的日志）

**Q: 如何确认彩蛋是否已解锁？**

A: 在 LOFTER App 中打开文章，如果能看到彩蛋内容，说明已解锁。工具会使用相同的账号状态进行检测。

#### 技术实现

本工具通过模拟 LOFTER 移动端 App 的请求方式（参考 [Loftify](https://github.com/Robert-Stackflow/Loftify) 项目），使用以下 API 获取彩蛋内容：

1. `/v1.1/trade/gift/post/newSupportInfo`：检测文章是否包含彩蛋配置
2. `/v1.1/trade/gift/myReturnGift`：获取已解锁彩蛋的实际文字内容

这些 API 调用需要：
- 有效的登录授权码（`LOFTER-PHONE-LOGIN-AUTH`）
- 模拟移动端 App 的请求头（User-Agent、设备标识等）

## 注意事项

1. **登录授权码**：
   - 需要有效的登录授权码才能访问LOFTER内容
   - 授权码会定期过期，过期后需要重新获取
   - 授权码是敏感信息，请妥善保管，不要泄露
   - 获取方式见上方"获取登录授权码"章节
   - **彩蛋功能**：必须使用与解锁彩蛋时相同的账号的授权码

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
   - 爬虫相关命令（`post`、`tag`、`author`、`tag-author`、`collection`、`author-collections`）需要授权码
   - 如果未通过命令行提供授权码，程序会交互式询问

9. **彩蛋功能注意事项**：
   - 彩蛋检测和获取需要有效的登录授权码
   - 必须使用已解锁彩蛋的账号的授权码
   - 如果彩蛋未解锁，会在文章末尾显示提示信息，不会影响正文保存
   - 彩蛋内容提取失败时，会显示调试信息，便于排查问题

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

本项目基于并参考以下开源项目发展而来，请在使用本项目时一并遵守相关项目的许可证要求：

- [lofterSpider](https://github.com/IshtarTang/lofterSpider)
- [lofter-helper](https://github.com/SrakhiuMeow/lofter-helper)
- [Loftify](https://github.com/Robert-Stackflow/Loftify)
