# 快速开始指南

## 安装依赖

```bash
pip install -r requirements.txt
```

## 基本使用

### 1. 保存单篇文章

```bash
python run.py post https://xxx.lofter.com/post/xxx
```

### 2. 爬取Tag下的文章（最新）

```bash
python run.py tag "风起东宫" --sort new --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢"
```

### 3. 爬取Tag下的文章（最热-全部）

```bash
python run.py tag "风起东宫" --sort total --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢"
```

### 4. 爬取Tag下的文章（最热-月榜）

```bash
python run.py tag "风起东宫" --sort month --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢"
```

### 5. 爬取作者的全部文章

```bash
python run.py author https://xxx.lofter.com/ --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢"
```

### 6. 爬取作者的指定tag文章

```bash
python run.py author https://xxx.lofter.com/ --tags "风起东宫" "太卢" --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢"
```

### 7. Tag+作者组合爬取

```bash
python run.py tag-author "风起东宫" "太卢" --save-path "D:\小说\小说\耽美\题材_风起东宫or太卢"
```

## 常用选项

- `--format md`: 保存为Markdown格式（默认是txt）
- `--no-images`: 不保存图片文件
- `--no-group`: 不按作者分组（所有文件保存在一个文件夹）
- `--login-auth <授权码>`: 使用自定义登录授权码

## 文件保存说明

### TXT格式
- 文件命名：`文章标题 by 作者名.txt`
- 图片命名：`文章标题 by 作者名_picture1.jpg`、`文章标题 by 作者名_picture2.jpg` 等
- 图片链接记录在txt文件中

### Markdown格式
- 文件命名：`文章标题 by 作者名.md`
- 图片直接嵌入在Markdown文件中

### 按作者分组
- 如果启用按作者分组，会在保存路径下创建`作者_作者名`文件夹
- 每个作者的文章保存在对应的文件夹中
