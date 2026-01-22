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

默认登录授权码已配置在`src/config.py`中，也可以通过命令行参数`--login-auth`传入新的值。

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

## 超参数说明

### 通用超参数

所有命令都支持的参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--login-auth` | 字符串 | `config.py`中的默认值 | 登录授权码（LOFTER-PHONE-LOGIN-AUTH的值） |
| `--save-path` | 字符串 | `./result` | 文件保存路径 |
| `--format` | 选择项 | `txt` | 文件格式：`txt` 或 `md` |
| `--no-images` | 标志 | `False` | 不保存图片文件（仅保存文本） |
| `--no-group` | 标志 | `False` | 不按作者分组（所有文件保存在同一文件夹） |

### Tag爬取专用超参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--sort` | 选择项 | `new` | 排序方式：`new`(最新)、`total`(全部最热)、`month`(月榜)、`week`(周榜)、`date`(日榜) |
| `--min-hot` | 整数 | `0` | 最低热度限制，只爬取热度大于等于此值的文章 |

### 作者爬取专用超参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--tags` | 列表 | `None` | 目标tags列表，只爬取包含这些tag的文章（可指定多个） |
| `--start-time` | 字符串 | `None` | 开始时间，格式：`YYYY-MM-DD`（如：`2024-01-01`） |
| `--end-time` | 字符串 | `None` | 结束时间，格式：`YYYY-MM-DD`（如：`2024-12-31`） |

### 配置超参数

在 `src/config.py` 中可以配置默认值：

```python
# 登录方式对应的key
LOGIN_KEY = "LOFTER-PHONE-LOGIN-AUTH"

# 默认登录授权码
DEFAULT_LOGIN_AUTH = "0dbD2pHVYgD-VbrqcWd-kmazgxFq_WFQwqQsw60W3VDzx5GJmQADyAQADA1LMHZMzpE5t6U4rHExuhRX3JM0Zxm7nJatHmOI"

# 默认保存路径
DEFAULT_SAVE_PATH = "./result"
```

## 超参数详细说明

### 通用超参数（所有命令支持）

#### `--login-auth <授权码>`
- **类型**: 字符串
- **默认值**: `src/config.py` 中配置的 `DEFAULT_LOGIN_AUTH`
- **说明**: LOFTER登录授权码，即Cookie中`LOFTER-PHONE-LOGIN-AUTH`的值
- **获取方式**: 
  1. 打开LOFTER网站并登录
  2. 按F12打开开发者工具
  3. 切换到Network标签，刷新页面
  4. 找到任意请求，查看Request Headers中的Cookie
  5. 复制`LOFTER-PHONE-LOGIN-AUTH`的值
- **示例**: `--login-auth "0dbD2pHVYgD-VbrqcWd-kmazgxFq_WFQwqQsw60W3VDzx5GJmQADyAQADA1LMHZMzpE5t6U4rHExuhRX3JM0Zxm7nJatHmOI"`

#### `--save-path <路径>`
- **类型**: 字符串（文件路径）
- **默认值**: `./result`
- **说明**: 文件保存的根目录路径
- **示例**: `--save-path "D:\小说\小说\耽美\题材_风起东宫or太卢"`

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

#### `--tags <tag1> <tag2> ...`
- **类型**: 字符串列表（可指定多个）
- **默认值**: `None`（爬取所有文章）
- **说明**: 目标tags列表，只爬取包含这些tag中任意一个的文章
- **过滤模式**: `in`（包含模式，默认）
- **示例**: `--tags "风起东宫" "太卢"`

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

## 通用选项（快速参考）

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

## 使用示例

### 完整示例1：爬取tag最新文章并按作者分组

```bash
python run.py tag "风起东宫" \
    --sort new \
    --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢" \
    --format txt \
    --min-hot 0
```

### 完整示例2：爬取tag最热文章（月榜）

```bash
python run.py tag "风起东宫" \
    --sort month \
    --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢" \
    --format txt \
    --min-hot 50
```

### 完整示例3：爬取作者指定tag的文章

```bash
python run.py author "https://xxx.lofter.com/" \
    --tags "风起东宫" "太卢" \
    --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢" \
    --start-time "2024-01-01" \
    --end-time "2024-12-31"
```

### 完整示例4：Tag+作者组合爬取

```bash
python run.py tag-author "风起东宫" "太卢" \
    --sort total \
    --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢" \
    --format txt \
    --min-hot 0
```

### 完整示例5：保存为Markdown格式（不保存图片）

```bash
python run.py post "https://xxx.lofter.com/post/xxx" \
    --format md \
    --no-images \
    --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢"
```

## 高级用法

### 使用自定义登录授权码

```bash
python run.py tag "风起东宫" \
    --login-auth "你的授权码" \
    --save-path "./result"
```

### 批量处理多个tag

可以编写脚本循环调用：

```python
import subprocess

tags = ["风起东宫", "太卢", "其他tag"]
for tag in tags:
    subprocess.run([
        "python", "run.py", "tag", tag,
        "--save-path", f"D:\\小说\\{tag}",
        "--sort", "total"
    ])
```

### Python代码调用

也可以直接在Python代码中调用（参考 `example.py`）：

```python
from src.main import crawl_tag

crawl_tag(
    tag_name="风起东宫",
    sort_type="total",
    save_path="D:\\小说\\小说\\耽美\\题材_风起东宫or太卢",
    file_format="txt",
    group_by_author=True,
    save_images=True,
    min_hot=0
)
```

## 注意事项

1. **登录授权码**：需要有效的登录授权码才能访问LOFTER内容。获取方式：
   - 打开LOFTER主页，按F12打开开发者工具
   - 切换到Network标签，刷新页面
   - 找到XHR请求，查看Cookies中的`LOFTER-PHONE-LOGIN-AUTH`值
   - 将值复制到`config.py`或通过`--login-auth`参数传入

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
