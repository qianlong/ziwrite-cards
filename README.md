# 汉字笔顺卡片 PDF 生成器 | Chinese Stroke-Order Card PDF Generator

## 项目简介 | Description

一个 Python 工具：输入 8 个汉字，自动生成可打印的汉字笔顺卡片（8.7 × 5.8 cm），包含拼音和分步笔顺图。

A Python tool that generates printable Chinese stroke-order cards (8.7×5.8 cm) from 8 input characters, with pinyin and step-by-step stroke frames.

输入 **8 个汉字** 后，脚本会从 **Hanzi Writer Data（jsDelivr CDN）** 下载每个字的笔画中线数据（medians），并生成卡片 PDF。

Enter a set of **8 Chinese characters**. The script downloads stroke-order data (medians) for each character from **Hanzi Writer Data (jsDelivr CDN)** and generates a PDF with **8.7 × 5.8 cm (landscape)** cards.

## 快速开始 | Quick Start

### 1) 安装依赖 | Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 2) 运行方式 | Usage

### 交互式输入 | Interactive Input

```bash
python hanzi.py
```

### 命令行传参 | Pass Text via Command Line

```bash
python hanzi.py --text "你好世界学习成长" --output "cards.pdf"
```

## 功能特性 | Features

- 每个汉字生成一张卡片，固定尺寸：8.7 × 5.8 cm（横向）。
- One card per character, fixed size: 8.7 × 5.8 cm (landscape).
- 拼音显示在汉字左侧。
- Pinyin is shown to the left of the character.
- 保留拼音声调（例如：`nǐ`）；多音字显示常见读音（最多 3 个），例如：`xíng / háng`。
- Tone marks are preserved (for example: `nǐ`), and polyphonic characters show all common readings (up to 3), e.g. `xíng / háng`.
- 笔顺按步骤逐帧绘制（当前笔画为红色，不显示步骤数字）。
- Stroke-order frames are rendered step by step (current stroke in red, no step numbers).
- 自动按 A4 页面排版，数量超出时自动续页。
- A4 pages are auto-laid out and continue across pages when needed.

## 数据来源 | Data Source

- Hanzi Writer Data（官方数据集）
- Hanzi Writer Data (official dataset)
- CDN 基础地址 | CDN base URL:
  - `https://cdn.jsdelivr.net/npm/hanzi-writer-data@latest`

> 如果某个汉字在数据源中不存在，脚本会返回清晰的错误提示。
>
> If a character is missing in the data source, the script returns a clear error.
