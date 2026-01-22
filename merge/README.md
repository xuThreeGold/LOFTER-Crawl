# 文件合并工具

用于合并lofter爬取的文件，支持按发表时间排序合并。

## 功能特性

1. 合并一个文件夹里所有的lofter爬取的文件
2. 支持TXT和MD两种格式（文件夹内的文件必须统一格式）
3. 按文章的发表时间先后排序
4. 每个文件作为一章，标题为"第XX章-文件名"
5. 可指定输出文件夹和文件名

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

### 使用示例

```bash
# 合并TXT文件（默认格式）
python merge_files.py "D:\小说\小说\耽美\题材_风起东宫or太卢"

# 合并MD文件
python merge_files.py "D:\小说\小说\耽美\题材_风起东宫or太卢" -f md

# 指定输出文件夹和文件名
python merge_files.py "D:\小说\小说\耽美\题材_风起东宫or太卢" -o "D:\合并结果" -n "合并后的小说"

# 合并MD文件并指定输出路径
python merge_files.py "D:\小说\小说\耽美\题材_风起东宫or太卢" -f md -o "D:\合并结果" -n "合并后的小说"
```

### Python代码中使用

```python
from merge_files import merge_files

# 合并TXT文件
merge_files(
    input_folder="D:\\小说\\小说\\耽美\\题材_风起东宫or太卢",
    output_folder="result",
    output_filename="合并后的小说",
    file_format="txt"
)

# 合并MD文件
merge_files(
    input_folder="D:\\小说\\小说\\耽美\\题材_风起东宫or太卢",
    output_folder="result",
    output_filename="合并后的小说",
    file_format="md"
)
```

## 注意事项

1. 输入文件夹中的文件必须统一格式（要么全是TXT，要么全是MD）
2. 如果无法从文件中提取发表时间，将使用文件的修改时间作为排序依据
3. 合并后的文件会保留原文件的内容，但会去除文件头（TXT格式）或YAML Front-Matter（MD格式）
4. 每个原文件在合并后的文件中作为一章，章节标题格式为"第XX章-文件名"

## 文件格式说明

### TXT格式
- 文件头包含：标题、作者、发表时间、原文链接
- 发表时间格式：`发表时间：YYYY-MM-DD`

### MD格式
- 文件头为YAML Front-Matter
- 发表时间在`date`字段中，格式：`date: 'YYYY-MM-DD'`
