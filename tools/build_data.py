# -*- coding: utf-8 -*-
"""离线构建 hanzi_data.json(游戏数据)。

游戏本身只依赖标准库 + Tkinter;本脚本只在需要重新生成数据时手动运行,
它需要以下第三方库和输入文件:

    pip install pymupdf pypinyin zhconv

    1. MOE 小学高级华文生字表 PDF
       https://www.moe.gov.sg/api/media/394e06b1-f4f3-4e90-adb4-a33efd9e1c5e/
       2024-Character-List-Primary-One-to-Two-Higher-Chinese.pdf
    2. cnchar-order 的笔顺数据(字 -> 笔画字母序列)
       https://cdn.jsdelivr.net/npm/cnchar-order@latest/cnchar.order.min.js
    3. Tatoeba 中文句子库(CC-BY 2.0 FR, 用作例句来源)
       https://downloads.tatoeba.org/exports/per_language/cmn/cmn_sentences.tsv.bz2

用法:
    python build_data.py --pdf <pdf> --order <order.js> --sentences <cmn.tsv> \
        [--out ../hanzi_data.json]
"""
import argparse
import bz2
import collections
import json
import os
import re
import sys

import pymupdf
import zhconv
from pypinyin import Style, pinyin

HANZI_RE = re.compile(r"[\u4e00-\u9fff]")
ONE_HANZI_RE = re.compile(r"^[\u4e00-\u9fff]$")

# cnchar 用同一个字母表示下列几组笔画,无法区分,因此游戏里把每组当成一个笔画:
# 用 (主名, 别名) 表示,槽位只显示主名,按钮上两个名字都列出。
# 另外 cnchar 没有单独的"竖折",字母 b 同时承担 竖折/竖弯(如 山 第二笔是竖折,
# 四 第四笔是竖弯),这里取课本更常见的"竖折"作主名。
AMBIGUOUS_ALT = {
    "横撇|横钩": ("横撇", "横钩"),
    "斜钩|卧钩": ("斜钩", "卧钩"),
    "横折折|横折弯": ("横折折", "横折弯"),
    "横折折折钩|横撇弯钩": ("横折折折钩", "横撇弯钩"),
    "竖折撇|竖折折": ("竖折撇", "竖折折"),
    "竖弯": ("竖折", "竖弯"),
}
# cnchar 的 "点2"(字形 ㇀)不是规范笔画名,规范里就是"点"。
NAME_FIXUP = {"点2": "点"}

# 例句过滤:整词黑名单。注意必须用词而不是单字——"自杀"要挡,但"自"是生字;
# 下面的单字项都会在 main() 里断言不属于生字表,以保证不会把某个生字的例句清空。
BLOCK_TERMS = [
    # 暴力 / 死亡
    "死", "杀", "血", "尸", "枪", "炮", "炸弹", "爆炸", "恐怖", "袭击", "武器",
    "战争", "打仗", "自杀", "暴力", "虐", "伤害", "受伤", "流血", "残",
    # 成人 / 身体
    "性", "色情", "裸", "妓", "强奸", "做爱", "接吻", "亲吻", "怀孕", "屁",
    "尿", "屎", "呕", "吐血",
    # 不良嗜好
    "酒", "醉", "烟", "抽烟", "吸毒", "毒", "赌", "偷", "抢劫", "罪", "监狱",
    "犯人", "警察", "小偷", "骗",
    # 疾病 / 负面
    "癌", "肿瘤", "艾滋", "残疾", "瞎", "聋", "哑", "疯", "傻", "蠢", "笨",
    "白痴", "恨", "骂", "吵架", "打架", "离婚", "失业", "破产", "可怜", "孤独",
    "寂寞", "绝望", "自卑",
    # 宗教 / 政治 / 迷信
    "鬼", "地狱", "上帝", "教堂", "佛", "神", "党", "政府", "共产", "革命",
    "主席", "总统", "选举", "抗议", "示威",
]

MAX_SENTENCES = 4


def parse_syllabus(pdf_path):
    """按版面结构抽取生字表:一行若按空白切分后每个词元都是单个汉字,就是生字行。"""
    doc = pymupdf.open(pdf_path)
    terms, per_term, current = [], {}, None
    for pno in range(doc.page_count):
        for raw in doc[pno].get_text().splitlines():
            line = raw.strip()
            if not line:
                continue
            toks = line.split()
            if toks and all(ONE_HANZI_RE.match(t) for t in toks):
                if current is None:
                    raise SystemExit("生字行出现在学期标题之前,PDF 版面可能变了")
                per_term[current].extend(toks)
            elif re.fullmatch(r"[一二]\s*[上下]", line):
                current = line
                terms.append(line)
                per_term.setdefault(current, [])
    if not terms:
        raise SystemExit("没有解析出任何学期标题,PDF 版面可能变了")
    return terms, per_term


def load_stroke_data(order_js_path):
    """从 cnchar-order 的打包文件里取 字->字母序列 和 字母->笔画名。"""
    js = open(order_js_path, encoding="utf-8").read()
    letter_name = {}
    for letter, blob in re.findall(r'"([a-z])":\{((?:[^{}]|\\")*?)\}', js):
        m = re.search(r'"name":"([^"]+)"', blob)
        if m:
            letter_name[letter] = m.group(1)
    order_map = dict(re.findall(r'"([\u4e00-\u9fff])":"([a-z]+)"', js))
    if not letter_name or not order_map:
        raise SystemExit("cnchar-order 数据解析失败,文件格式可能变了")
    return order_map, letter_name


def stroke_names(ch, order_map, letter_name):
    seq = order_map.get(ch)
    if not seq:
        return None
    out = []
    for letter in seq:
        name = letter_name.get(letter)
        if name is None:
            raise SystemExit(f"未知笔画字母 {letter!r}(字 {ch})")
        name = NAME_FIXUP.get(name, name)
        if name in AMBIGUOUS_ALT:
            name = AMBIGUOUS_ALT[name][0]
        out.append(name)
    return out


def load_sentences(path):
    opener = bz2.open if path.endswith(".bz2") else open
    rows = []
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[2].strip():
                rows.append(parts[2].strip())
    return rows


def hanzi_of(s):
    return HANZI_RE.findall(s)


def pick_sentences(syllabus, sentences):
    """为每个生字挑选简短、简体、用词常见且内容干净的例句。"""
    freq = collections.Counter()
    for s in sentences:
        freq.update(hanzi_of(s))
    top_common = {c for c, _ in freq.most_common(1500)}
    vocab = set(syllabus) | top_common

    def clean(s):
        h = hanzi_of(s)
        if not h or re.search(r"[A-Za-z0-9]", s):
            return None
        # 只要简体:转换后与原文一致才保留,挡掉 Tatoeba 里的繁体句子
        if zhconv.convert(s, "zh-cn") != s:
            return None
        if any(t in s for t in BLOCK_TERMS):
            return None
        return h

    # 分三轮放宽条件,尽量让每个字都有例句
    rounds = [(12, vocab), (16, vocab), (18, None)]
    by_char = {c: [] for c in syllabus}
    pre = []
    for s in sentences:
        h = clean(s)
        if h:
            pre.append((s, set(h), len(h)))

    for maxlen, vset in rounds:
        for s, hset, n in pre:
            if n < 2 or n > maxlen:
                continue
            if vset is not None and not hset <= vset:
                continue
            for c in hset:
                bucket = by_char.get(c)
                if bucket is not None and len(bucket) < MAX_SENTENCES and s not in bucket:
                    bucket.append(s)
    # 短句优先,阅读负担更小
    for c in by_char:
        by_char[c].sort(key=lambda s: len(hanzi_of(s)))
        del by_char[c][MAX_SENTENCES:]
    return by_char


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--order", required=True)
    ap.add_argument("--sentences", required=True)
    ap.add_argument(
        "--out",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hanzi_data.json"),
    )
    args = ap.parse_args()

    terms, per_term = parse_syllabus(args.pdf)
    syllabus = sorted({c for t in terms for c in per_term[t]})
    print(f"生字表: {len(terms)} 个学期, {len(syllabus)} 个不同汉字")

    # 保证黑名单里的单字项都不是生字,否则会把该生字的例句全部挡掉
    bad = [t for t in BLOCK_TERMS if len(t) == 1 and t in set(syllabus)]
    if bad:
        raise SystemExit("黑名单单字与生字表冲突: " + "".join(bad))

    order_map, letter_name = load_stroke_data(args.order)
    print(f"cnchar 笔顺: {len(order_map)} 字, {len(letter_name)} 种笔画字母")

    sentences = load_sentences(args.sentences)
    print(f"例句候选: {len(sentences)} 句")
    by_char = pick_sentences(syllabus, sentences)

    first_term = {}
    for t in terms:
        for c in per_term[t]:
            first_term.setdefault(c, t)

    entries, no_strokes = [], []
    palette = collections.Counter()
    for ch in syllabus:
        strokes = stroke_names(ch, order_map, letter_name)
        if not strokes:
            no_strokes.append(ch)
            continue
        palette.update(strokes)
        py = pinyin(ch, style=Style.TONE)[0][0]
        plain = pinyin(ch, style=Style.NORMAL)[0][0]
        entries.append(
            {
                "character": ch,
                "strokes": strokes,
                "pinyin": py,
                "initial": plain[0],
                "term": first_term.get(ch, ""),
                "sentences": by_char.get(ch, []),
            }
        )
    if no_strokes:
        print("!! 没有笔顺数据,已跳过: " + "".join(no_strokes))

    alt_of = {primary: alt for primary, alt in AMBIGUOUS_ALT.values()}
    data = {
        # 按出现频率排序:常用笔画排在键盘前面
        "stroke_palette": [
            {"name": n, "alt": alt_of[n]} if n in alt_of else {"name": n}
            for n, _ in palette.most_common()
        ],
        "characters": entries,
    }
    out = os.path.abspath(args.out)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)

    n_sent = sum(1 for e in entries if e["sentences"])
    print(f"写出 {out}")
    print(f"  汉字 {len(entries)} 个, 笔画种类 {len(palette)} 种")
    print(f"  有例句 {n_sent} 个, 无例句 {len(entries) - n_sent} 个")
    print(f"  笔画数 {min(len(e['strokes']) for e in entries)}..{max(len(e['strokes']) for e in entries)}")


if __name__ == "__main__":
    main()
