# 文件合并工具

用于合并lofter爬取的文件，支持按发表时间排序或按章节号智能排序合并。

## 功能特性

1. 合并一个文件夹里所有的lofter爬取的文件
2. 支持TXT和MD两种格式（文件夹内的文件必须统一格式）
3. **支持两种排序模式**：
   - 按文章的发表时间先后排序（默认）
   - 按章节号智能排序（适用于小说章节文件）
4. 每个文件作为一章，标题为"第XX章-文件名"
5. 可指定输出文件夹和文件名
6. 支持在开头添加目录（可选）
7. 对于MD格式，支持生成可跳转到对应章节的目录链接（默认启用）
8. **支持关键词过滤**：只合并包含指定关键词的文件（在文件名或内容中搜索）
9. **支持匹配模式**：可选择"和"（AND）或"或"（OR）关系

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
- `-k, --keywords`：关键词列表，只合并包含这些关键词的文件（在文件名或内容中搜索），可以指定多个关键词
- `-m, --match-mode`：匹配模式，`and`表示所有关键词都要包含，`or`表示包含任一关键词即可（默认为`or`）
- `-s, --sort-mode`：排序模式，`time`表示按发表时间排序，`chapter`表示按章节号智能排序（默认为`time`）

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

# 只合并包含"竹抱枝"关键词的文件（或关系，默认）
python merge_files.py "./articles" -f md -k 竹抱枝

# 只合并同时包含"竹抱枝"和"闲泽"关键词的文件（和关系）
python merge_files.py "./articles" -f md -k 竹抱枝 闲泽 -m and

# 只合并包含"竹抱枝"或"庄周梦蝶"关键词的文件（或关系）
python merge_files.py "./articles" -f md -k 竹抱枝 庄周梦蝶 -m or

# 按章节号智能排序合并（适用于小说章节文件）
python merge_files.py "./articles" -f md -s chapter

# 结合关键词过滤和章节排序
python merge_files.py "./articles" -f md -k 绿茶美女 -s chapter
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

# 只合并包含"竹抱枝"关键词的文件（或关系，默认）
merge_files(
    input_folder="./articles",
    output_folder="result",
    output_filename="合并后的文件",
    file_format="md",
    keywords=["竹抱枝"]
)

# 只合并同时包含"竹抱枝"和"闲泽"关键词的文件（和关系）
merge_files(
    input_folder="./articles",
    output_folder="result",
    output_filename="合并后的文件",
    file_format="md",
    keywords=["竹抱枝", "闲泽"],
    match_mode="and"
)

# 按章节号智能排序合并
merge_files(
    input_folder="./articles",
    output_folder="result",
    output_filename="合并后的文件",
    file_format="md",
    sort_mode="chapter"
)

# 结合关键词过滤和章节排序
merge_files(
    input_folder="./articles",
    output_folder="result",
    output_filename="合并后的文件",
    file_format="md",
    keywords=["绿茶美女"],
    sort_mode="chapter"
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

7. 关键词过滤功能说明：
   - 使用`-k`或`--keywords`参数可以指定关键词列表，只合并包含这些关键词的文件
   - 关键词会在文件名（不含扩展名）和文件内容中搜索
   - 使用`-m`或`--match-mode`参数可以指定匹配模式：
     - `or`（默认）：文件包含任一关键词即可被合并
     - `and`：文件必须包含所有关键词才会被合并
   - 如果不指定关键词，则合并文件夹中的所有文件（原有行为）

8. 智能章节排序功能说明：
   - 使用`-s chapter`或`--sort-mode chapter`可以启用智能章节排序
   - 该功能会自动识别文件名中的章节信息，按照章节顺序排序
   - 支持的章节命名规则包括：
     - **数字格式**：
       - 括号中：`（1）`, `（4）`, `（完结）`, `（5完）`, `（5完结）`, `（完结 5）`, `（5 完结）`
       - 文件名末尾：`2`, `3完结`, `5完`, `5完结`
       - 分隔符连接：`标题 12`, `标题-12`, `标题之12`（支持空格、-、之等分隔符）
     - **中文数字**：`（一）`, `（二）`, `（三）`...`（十一）`, `（十二 完）`，支持到万、十万等
     - **上下中格式**：`（上）`, `（中）`, `（下）`, `（上下）`, `（中下）`, `（下上）`, `（下中）`, `（下下）`, `（下下下 完）`等
     - **题材系列**（不限定类型）：
       - 括号格式：`（番外1）`, `（论坛体1）`, `（捡手机文学1）`, `（福利番外1）`, `（日记1）`等任意题材
       - 完结标记：`（番外完结）`, `（论坛体完结）`等
       - 特殊格式：`绿茶番外：鳏夫日记`, `绿茶番外：鳏夫日记2`等
     - **无章节号**：没有章节标记的文件会被识别为第一章
   - 排序规则：
     - **按题材分组排序**：
       - 正文章节（normal）优先，放在最前面
       - 其他题材（番外、论坛体、捡手机文学等）按每个题材的第一篇文的发表时间排序
       - 无法识别章节信息的文件按时间排序，放在最后
     - **题材内排序**：
       - 每个题材内部按章节号排序
       - 同章节号的文件按发表时间排序
   - 如果无法识别章节信息，会自动回退到按时间排序
   - 注意：
     - 括号可能是全角（（））或半角（()），程序会自动识别
     - 支持任意题材类型，不限定为番外、论坛体等
     - 程序会显示识别到的题材分布统计信息

## 文件格式说明

### TXT格式
- 文件头包含：标题、作者、发表时间、原文链接
- 发表时间格式：`发表时间：YYYY-MM-DD`

### MD格式
- 文件头为YAML Front-Matter
- 发表时间在`date`字段中，格式：`date: 'YYYY-MM-DD'`
