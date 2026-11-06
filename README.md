# 笔画猜猜猜

使用 Tkinter 制作的汉字笔画猜谜游戏，覆盖新加坡教育部《欢乐伙伴 2.0》小学高级华文 P1-P2 生字表，共 746 个汉字。一上、一下、二上、二下的字词混合在同一题库中，玩家需要逐笔猜出汉字，而不是猜字母。

## 功能

- 深色主题的图形用户界面
- 根据错误次数逐步绘制六部分 hangman
- 按笔顺显示汉字的笔画槽位，重复笔画需要重复猜测
- 猜对的笔画会在汉字的实际位置逐笔显现
- 24 个笔画按钮，包含六组无法区分的笔画别名
- 显示拼音首字母提示
- 结果窗口显示完整笔顺，并在例句中高亮目标汉字
- 支持开始新游戏

## 运行方法

1. 确保已经安装 Python（标准 Python 安装通常包含 Tkinter）
2. 在命令行进入 `hanzi_hangman` 目录：
   ```bash
   cd hanzi_hangman
   ```
3. 运行游戏：
   ```bash
   python hanzi_hangman.py
   ```

## 玩法

1. 点击笔画按钮，猜测这个汉字里含有的笔画（不必按笔顺猜）
2. 每次猜中只显示该笔画在笔顺中最靠前的一个未显示槽位
3. 同一个笔画可能需要重复猜测，例如“三”需要猜三次“横”
4. 六组笔画别名使用同一个按钮，例如“竖折/竖弯”不作区分
5. 猜错一次会增加一次错误次数并绘制一个 hangman 部分
6. 在六次错误前猜出全部笔画即可获胜
7. 每局可以点击一次“显示提示”，查看汉字拼音的首字母
8. 结果窗口会显示完整笔顺，并在一条例句中高亮目标汉字
9. 点击“再来一局”或“开始新游戏”重新开始

## 在 iPad 上运行

网页版本不需要安装依赖。在项目根目录启动静态服务器：

```bash
python -m http.server
```

然后在 iPad Safari 中打开 `http://<电脑IP>:8000/web/`。点击分享按钮，选择“添加到主屏幕”，即可像独立应用一样启动。离线缓存需要使用 HTTPS 或 localhost；普通局域网 HTTP 地址仍可在线游玩。Tkinter 版本保持不变，仍可按上面的方式运行。

## 环境要求

- Python 3.x
- Tkinter（通常随 Python 一起安装）

游戏本身不需要安装第三方 Python 软件包。`tools/build_data.py` 只用于构建题库数据，运行它需要 PyMuPDF、pypinyin 和 zhconv 等构建时依赖；日常运行游戏不需要这些依赖。

## 数据来源

- 新加坡教育部《欢乐伙伴 2.0》小学高级华文 P1-P2 生字表（746 字）：
  https://www.moe.gov.sg/api/media/394e06b1-f4f3-4e90-adb4-a33efd9e1c5e/2024-Character-List-Primary-One-to-Two-Higher-Chinese.pdf
- cnchar（MIT License；笔顺数据来自其 cnchar-order 软件包）：
  https://github.com/theajack/cnchar
  https://cdn.jsdelivr.net/npm/cnchar-order@latest/cnchar.order.min.js
- Tatoeba 中文例句数据（CC-BY 2.0 FR，按许可证要求提供署名）：
  https://downloads.tatoeba.org/exports/per_language/cmn/cmn_sentences.tsv.bz2
- Noto Sans CJK SC 2.004 笔画图形子集（SIL Open Font License 1.1）：
  https://github.com/notofonts/noto-cjk/releases/tag/Sans2.004
- hanzi-writer-data 2.0.1（源自 Make Me a Hanzi / Arphic 字体，ARPHIC PUBLIC LICENSE）：
  https://www.npmjs.com/package/hanzi-writer-data
  许可证：`ARPHICPL.txt`

数据中的六组笔画无法由底层笔顺来源可靠区分，因此游戏将它们分别作为同一个可猜笔画处理：横撇/横钩、竖折/竖弯、斜钩/卧钩、横折折/横折弯、横折折折钩/横撇弯钩、竖折撇/竖折折。
