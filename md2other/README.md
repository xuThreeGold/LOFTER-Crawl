# Markdown 格式转换工具

将 Markdown 文件转换为其他格式的工具，支持 PDF、EPUB、TXT、DOCX 等格式。

## 功能特性

- ✅ 支持多种输出格式：PDF、EPUB、TXT、DOCX（通过 `--format` 参数指定）
- ✅ 可指定输入 Markdown 文件（必需参数）
- ✅ 可指定输出文件路径（`--output` 参数）
- ✅ 默认输出到 `result` 目录（可通过 `--output-dir` 参数修改）
- ✅ 自动创建输出目录

## 安装依赖

### 1. 安装 Python 依赖包

```bash
pip install -r requirements.txt
```

### 2. 安装 Pandoc（推荐）

为了支持所有格式转换，需要安装 Pandoc：

**Windows:**
1. 下载安装包：https://github.com/jgm/pandoc/releases
2. 下载最新版本的 `.msi` 安装包并安装
3. 确保 `pandoc` 命令在系统 PATH 中

**Linux:**
```bash
sudo apt-get install pandoc  # Ubuntu/Debian
# 或
sudo yum install pandoc      # CentOS/RHEL
```

**macOS:**
```bash
brew install pandoc
```

### 3. PDF 转换额外要求（如果使用 pdfkit）

如果使用 `pdfkit` 作为 PDF 转换的备选方案，还需要安装 `wkhtmltopdf`：
- 下载地址：https://wkhtmltopdf.org/downloads.html

## 使用方法

### 基本用法

```bash
# 转换为 PDF（输出到 result 目录）
python md2other.py input.md --format pdf

# 转换为 EPUB
python md2other.py input.md --format epub

# 转换为 TXT
python md2other.py input.md --format txt

# 转换为 DOCX
python md2other.py input.md --format docx
```

### 指定输出文件

```bash
# 指定输出文件路径
python md2other.py input.md --format pdf --output custom_output.pdf

# 指定输出目录
python md2other.py input.md --format epub --output-dir ./my_output
```

### 命令行参数

- `input_file`: 输入的 Markdown 文件路径（必需）
- `--format, -f`: 输出格式，可选值：`pdf`, `epub`, `txt`, `docx`（必需）
- `--output, -o`: 输出文件路径（可选，默认在 result 目录下）
- `--output-dir, -d`: 输出目录（可选，默认：`result`）

## 示例

```bash
# 示例 1: 将 README.md 转换为 PDF
python md2other.py README.md --format pdf

# 示例 2: 转换为 EPUB 并指定输出文件
python md2other.py article.md --format epub --output my_book.epub

# 示例 3: 转换为 DOCX 并指定输出目录
python md2other.py document.md --format docx --output-dir ./documents

# 示例 4: 转换为 TXT
python md2other.py notes.md --format txt
```

## 支持的格式

| 格式 | 说明 | 依赖 |
|------|------|------|
| PDF | 便携式文档格式 | pypandoc 或 pdfkit |
| EPUB | 电子书格式 | pypandoc |
| TXT | 纯文本格式 | markdown, html2text |
| DOCX | Word 文档格式 | pypandoc |

## 注意事项

1. **Pandoc 安装**: 推荐安装 Pandoc 以获得最佳转换效果，特别是对于 PDF 和 EPUB 格式
2. **中文字体**: PDF 转换时，如果使用 pypandoc，需要系统安装中文字体（如 Microsoft YaHei）
3. **文件编码**: 输入文件应为 UTF-8 编码
4. **图片处理**: 转换时，Markdown 中的图片链接会保留，但图片文件需要可访问

## 故障排除

### 问题：转换 PDF 时出错

**解决方案：**
1. 确保已安装 Pandoc
2. 如果使用 pdfkit，确保已安装 wkhtmltopdf
3. 检查系统是否安装了中文字体

### 问题：转换 EPUB 时出错

**解决方案：**
1. 确保已安装 Pandoc
2. 检查输入文件格式是否正确

### 问题：转换 DOCX 时出错

**解决方案：**
1. 确保已安装 Pandoc
2. 检查输出目录是否有写入权限

## 许可证

本工具为 LOFTER-Crawl 项目的一部分。
