#!/usr/bin/env python3
"""
build_anki_deck.py

功能：
- 从公开 high-frequency 列表抓取前2000词（已固定为 google-10000-english 的 commit 版）
- 把你的“速查表”作为一张卡片加入
- 为每个高频词创建一张 Front=单词, Back=占位（可在 Anki 中补充例句/词性/搭配）
- 输出 .apkg 文件：2000_highfreq_with_cheatsheet.apkg

运行前（本地）：
pip install requests genanki
然后： python3 build_anki_deck.py
"""

import requests
import genanki
import random
import html
import sys

# ----- 配置 -----
# 使用的高频词源（固定到特定 commit 的 raw URL，确保稳定）
WORDLIST_RAW_URL = (
    "https://raw.githubusercontent.com/first20hours/google-10000-english/"
    "d0736d492489198e4f9d650c7ab4143bc14c1e9e/google-10000-english.txt"
)
TOP_N = 2000
OUTPUT_FILE = "2000_highfreq_with_cheatsheet.apkg"

# 请把下面的 CHEATSHEET_MD 替换为你的速查表内容（这里使用简化版，脚本会把它作为单张卡背面）
CHEATSHEET_MD = r"""
# 功能词・常见连词・基础句型 速查表（阅读专用）

说明：本速查表面向“只为看懂英文（阅读）”的学习目的。先记住功能词与连词的作用，配合句型示例，能更快定位句子主干并理解逻辑。

使用步骤：找主干（主语+谓语）→识别时态/被动/否定→划分从句/修饰语→标出连词与逻辑信号→跳回查生词（先猜后查）。

常用功能词示例：
冠词：the, a, an
指示词：this, that, these, those
代词：I, you, he, she, it, we, they / my, your, his...
助动词/情态：be, have, do / can, could, will, would, should, must
常见介词：in, on, at, by, for, with, about, of, to, from...
常见连词（部分）：and, but, or, so, because, although, however, therefore, if, when, while...

基础句型（常见，速查）：
1. S V O：She reads books.
2. S V C：He is happy.
3. There be：There is a book on the table.
4. 被动：The cake was eaten by Tom.（be + 过去分词）
5. 定语从句：The book that I bought...
6. 状语从句：If you study, you'll pass.
7. 非谓语：To win the game, you must train.

常见标点要点：逗号分隔从句/列举；分号连接相关句子；冒号引出说明；破折号插入解释（可先略读主句再回读）。

遇长句拆解流程：
1. 找主句主语+谓语（第一个能独立成句的动词短语）
2. 标出从句/插入语，先临时去除，读主句
3. 识别因果/时间/对比等连词，确定逻辑
4. 若需要查词，先猜词性与大意再查词典

词缀猜词提示：un-/in-/re-/dis- ; -tion/-ment/-ness/-able/-ly 等
"""

# ----- 从在线文件抓取 top N 词 -----
def fetch_top_words(url, top_n):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    lines = r.text.splitlines()
    words = []
    for line in lines:
        # 预期格式 "1| the"
        if "|" in line:
            parts = line.split("|", 1)
            word = parts[1].strip()
        else:
            word = line.strip()
        if word:
            words.append(word)
        if len(words) >= top_n:
            break
    return words

# ----- 构造 Anki Deck -----
def build_deck(words, cheatsheet_md, output_file):
    deck_id = random.randrange(1 << 30, 1 << 31)
    model_id = random.randrange(1 << 30, 1 << 31)

    model = genanki.Model(
        model_id,
        "Simple FrontBack Model",
        fields=[{"name": "Front"}, {"name": "Back"}],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{Front}}<hr id=\"answer\">{{Back}}",
            }
        ],
    )

    deck = genanki.Deck(deck_id, "2000 High-frequency + 速查表")

    # 把速查表做为单张卡片（Front 为标题，Back 为速查表 Markdown，使用 <pre> 保持格式）
    cheatsheet_html = "<pre style='white-space:pre-wrap; font-family:monospace'>{}</pre>".format(
        html.escape(cheatsheet_md)
    )
    deck.add_note(
        genanki.Note(
            model=model,
            fields=["速查表（阅读速查）", cheatsheet_html],
        )
    )

    # 为每个词创建一张卡（Back 预留为占位，方便你导入后补例句/释义/词性）
    for w in words:
        front = w
        back = "词性：\n释义：\n例句：\n搭配："
        deck.add_note(genanki.Note(model=model, fields=[front, back]))

    pkg = genanki.Package(deck)
    pkg.write_to_file(output_file)
    print(f"已生成 {output_file}，共包含 {len(words)+1} 张卡（包含速查表1张 + {len(words)} 高频词卡）")

# ----- 主流程 -----
def main():
    try:
        print("正在下载高频词列表...")
        words = fetch_top_words(WORDLIST_RAW_URL, TOP_N)
        if len(words) < TOP_N:
            print(f"警告：仅抓取到 {len(words)} 个词（未达到 {TOP_N}）")
        print(f"抓取到 {len(words)} 个词，开始生成 Anki 包...")
        build_deck(words, CHEATSHEET_MD, OUTPUT_FILE)
        print("完成。请在 Anki 中打开并同步你的 Deck。")
    except Exception as e:
        print("出错：", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
