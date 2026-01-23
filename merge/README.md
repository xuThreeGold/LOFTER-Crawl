# 文件合并工具

用于合并lofter爬取的文件，支持按发表时间排序合并。

## 功能特性

1. 合并一个文件夹里所有的lofter爬取的文件
2. 支持TXT和MD两种格式（文件夹内的文件必须统一格式）
3. 按文章的发表时间先后排序
4. 每个文件作为一章，标题为"第XX章-文件名"
5. 可指定输出文件夹和文件名
6. 支持在开头添加目录（可选）
7. 对于MD格式，支持生成可跳转到对应章节的目录链接（默认启用）

## 使用方法

### 命令行使用

```bash
python merge_files.py <输入文件夹> [选项]
```

### 参数说明

- `input_folder`（必需）：包含所有要合并的文件的文件夹路径
- `-o, --output`：输出文件夹路径（默认为`result`）
- `-n, --name`：输出文件名（不含扩展名），如果未指定则使用输入文件夹名
- `-f, --format`：文件格式，`txt`或`md`（默认为`txt`）
- `--add-toc`：在开头添加目录（可选）
- `--no-toc-links`：如果合并MD文件且添加目录，不使用可跳转的链接（默认使用可跳转链接，仅在`--add-toc`且格式为`md`时有效）

### 使用示例

```bash
# 合并TXT文件（默认格式）
python merge_files.py "./articles"

# 合并MD文件
python merge_files.py "./articles" -f md

# 指定输出文件夹和文件名
python merge_files.py "./articles" -o "./merged" -n "合并后的文件"

# 合并MD文件并指定输出路径
python merge_files.py "./articles" -f md -o "./merged" -n "合并后的文件"

# 合并MD文件并添加可跳转的目录（默认）
python merge_files.py "./articles" -f md --add-toc

# 合并MD文件并添加普通目录（不可跳转）
python merge_files.py "./articles" -f md --add-toc --no-toc-links

# 合并TXT文件并添加目录
python merge_files.py "./articles" -f txt --add-toc
```

### Python代码中使用

```python
from merge_files import merge_files

# 合并TXT文件
merge_files(
    input_folder="./articles",
    output_folder="result",
    output_filename="合并后的文件",
    file_format="txt"
)

# 合并MD文件
merge_files(
    input_folder="./articles",
    output_folder="result",
    output_filename="合并后的文件",
    file_format="md"
)

# 合并MD文件并添加可跳转的目录
merge_files(
    input_folder="./articles",
    output_folder="result",
    output_filename="合并后的文件",
    file_format="md",
    add_toc=True,
    toc_links=True  # 默认值，可省略
)

# 合并MD文件并添加普通目录（不可跳转）
merge_files(
    input_folder="./articles",
    output_folder="result",
    output_filename="合并后的文件",
    file_format="md",
    add_toc=True,
    toc_links=False
)
```

## 注意事项

1. **只能合并本项目爬取的文件**：本工具依赖于文件开头的特定格式信息来提取发表时间和内容。TXT格式需要包含"发表时间："字段，MD格式需要包含YAML Front-Matter中的`date`字段。其他来源的文件可能无法正确解析。

2. 输入文件夹中的文件必须统一格式（要么全是TXT，要么全是MD）

3. 如果无法从文件中提取发表时间，将使用文件的修改时间作为排序依据

4. 合并后的文件会保留原文件的内容，但会去除文件头（TXT格式）或YAML Front-Matter（MD格式）

5. 每个原文件在合并后的文件中作为一章，章节标题格式为"第XX章-文件名"

6. 目录功能说明：
   - 使用`--add-toc`参数可以在合并后的文件开头添加目录
   - 对于MD格式，默认生成可跳转到对应章节的目录链接（支持大多数Markdown解析器）
   - 如果不想使用可跳转链接，可以使用`--no-toc-links`参数
   - TXT格式的目录为纯文本格式，不支持跳转

## 文件格式说明

### TXT格式
- 文件头包含：标题、作者、发表时间、原文链接
- 发表时间格式：`发表时间：YYYY-MM-DD`

### MD格式
- 文件头为YAML Front-Matter
- 发表时间在`date`字段中，格式：`date: 'YYYY-MM-DD'`
