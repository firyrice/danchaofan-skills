# 分镜规划书 · 英伟达财报炸裂，算力板块反而跌（花生 AI 成片输入）
> 口播稿唯一真源：本目录 视频基础信息.md「二、口播稿」一节；分镜断句逐字复用，勿改字改标点。
> 制作方案：B 素材混合 MG 动画

## 一、成片需求（含 MG 画风设计）

### 📋 基础信息
- 视频标题：英伟达财报炸裂，算力板块反而跌
- 内容摘要：英伟达财报炸裂，营收962亿美元、同比涨106%，但A股算力板块反而冲高回落、集体见光死。本片把「财报越好、股价越跌」这个魔咒拆成三层归因：利好提前兑现、光模块抱团太挤浮盈想跑、叠加今晚美联储主席沃什杰克逊霍尔讲话的不确定性；并快评阳光电源、利通电子、医药、成品油、农业五条与持仓直接相关的板块动向，提醒你盯住沃什讲话与30年期美债收益率这两个数。
- 年代背景：2026年 · 现代
- 制作方案：B 素材混合 MG 动画
- 参考风格：严肃财经调查 / 深度解说类 UP 主风格
- BGM 需求：看跌沉稳压抑、冷峻克制、暗流涌动的背景配乐，中段有轻微张力起伏

### 🎥 素材要求
- 素材类型：英伟达财报发布会/数据中心、光模块机房与光纤、光伏厂区、医药实验室、加油站/原油、农田/粮食、美联储/交易所盘面等新闻资料与空镜
- 素材偏好：数据类画面留白给 MG 叠加；避免素人正脸；镜头偏硬朗、审视感
- 素材禁忌（硬规则）：不检索「K 线走势图」「个股行情图」，也不把「具体股价数字」当检索素材——走势、涨跌、股价数字一律改由 MG 动画绘制
- 时效性：使用 2025 年后的近期素材
- 地域限定：中国（美股英伟达 / 美联储部分按美国实际）
- 专名要求：英伟达、中际旭创、新易盛、天孚通信、胜宏科技、阳光电源、利通电子、万邦医药、万向德农（公司中文名）
- 用户硬性要求：无

### 🎨 MG 动画风格
- 固定基因：严肃财经调查 / 硬朗商务；炭灰墨黑底 + 暖金点缀色板；标题极粗黑体、数字用数字展示体、正文硬朗黑体；图标庄重（Serious）
- 情绪温度：看跌·压暗加警示黄（下跌 / 见光死数字用警示黄强调；基底炭灰 + 暖金）
- 视觉母题（本期共振）：蓝色光纤束·中段向下弯折（沿用封面核心意象，暗喻「信号走弱」）——作为全片 MG 的底纹、分割线、转场元素，下跌箭头与走势波形一律用「光纤向下弯折」的形态语言，贯穿全片但不喧宾夺主

```json
{ "visual_style": "严肃财经调查/硬朗商务（取花生风格列表最接近项）", "color_system": {"color_style": "深色/浓郁系", "main_hsb_hue": 45},
  "typography": {"title_font": {"font_family": "极粗黑体", "font_weight": "black"}, "body_font": {"font_family": "硬朗黑体", "font_weight": "regular"}, "number_font": {"font_family": "数字展示体", "font_weight": "semibold"}},
  "icon_library": {"style": "Serious"} }
```

## 二、分镜脚本（JSON 内嵌）

> 场景只承载 `scene_design`（一批检索上下文，一条扁平字符串）。画面类型与画面描述在**每个分镜**上给。

````markdown
```json
{
  "schema_version": "1.0",
  "scenes": [
    {
      "scene_id": "A01",
      "scene_title": "开场·矛盾砸屏",
      "scene_design": "专名清单：英伟达（公司） ／ 国家：美国、中国 ／ 年代：现代 ／ 素材来源：英伟达财报发布会实录、数据中心/机房空镜 ／ 素材偏好：数据画面留白给 MG，避免素人正脸，镜头硬朗审视",
      "shots": [
        { "shot_id": "S01", "visual_type": "mg_frame", "source": "cloud_only", "script": "英伟达财报炸裂，算力板块今天反而跌了。", "visual_description": "左右分屏框架，炭灰墨黑底 + 暖金分割线：左侧暖金向上箭头配「财报炸裂」，右侧警示黄向下弯折光纤配「板块反而跌」，中间一个反转符号；念到「炸裂/跌」时两侧依次高亮，蓝色光纤束向下弯折纹理贯穿作背景。" },
        { "shot_id": "S02", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "昨天英伟达营收962亿美元、同比涨106%，股价先涨8.74%，A股算力跟着狂欢了一天，今天就冲高回落。", "visual_description": "底为英伟达财报发布会/数据中心实拍暗化作衬；MG 叠加：营收962亿、同比涨106%、股价+8.74% 三组数字卡片依次砸屏滚动，念到「冲高回落」时一组向上箭头翻转成向下弯折光纤形态。" },
        { "shot_id": "S03", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "财报越好、股价越跌，这个魔咒，今天应在了整个算力板块头上。", "visual_description": "底为算力机房/光纤空镜暗化；MG 叠加：「魔咒」两字大字报（警示黄描边）落在光纤向下弯折纹理上，106%→-1.85% 上下反差数字闪烁。" }
      ]
    },
    {
      "scene_id": "A02",
      "scene_title": "关注引导·大盘分化",
      "scene_design": "专名清单：上证指数、深证成指、创业板指、科创50（指数） ／ 国家：中国 ／ 年代：现代 ／ 素材来源：交易所交易大厅、盘面数据屏、财经新闻画面 ／ 素材偏好：数据画面留白给 MG，避免素人正脸",
      "shots": [
        { "shot_id": "S04", "visual_type": "b-roll", "source": "cloud_only", "script": "关注蛋炒饭财经，每个交易日陪你把盘面捋一遍。今天是8月28日。", "visual_description": "频道开场引导：演播室式盘面滚动空镜，右下角日期卡「08.28」，硬朗审视的推镜。" },
        { "shot_id": "S05", "visual_type": "b-roll", "source": "cloud_only", "script": "先说大盘。", "visual_description": "大盘全景空镜：交易所交易大厅/盘面数据屏扫过，稳重推镜。" },
        { "shot_id": "S06", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "今天两市成交2.1万亿，比昨天缩了一点点，但还在2万亿上方。", "visual_description": "底为盘面数据屏暗化；MG 叠加：「2.1万亿」数字砸屏，一条2万亿水位线横在下方，缩量用小幅下凹标注。" },
        { "shot_id": "S07", "visual_type": "b-roll", "source": "cloud_only", "script": "涨跌家数2800只涨、2300只跌，中位数微涨。", "visual_description": "盘面涨跌家数画面：上涨/下跌股票列表滚动，节奏平实。" },
        { "shot_id": "S08", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "但指数分化得很厉害：上证只跌了0.1%，几乎平盘，靠两瓶酒、三桶油、四大行这几个权重托着；创业板跌了1.4%，科创50跌了1.85%，全场最惨。", "visual_description": "底为权重股/盘面空镜暗化；MG 叠加：指数分化对比条——上证-0.1%（近平盘）、创业板-1.4%、科创50-1.85%（警示黄高亮「全场最惨」），三条横 bar 依次高亮。" },
        { "shot_id": "S09", "visual_type": "b-roll", "source": "cloud_only", "script": "钱没怎么跑，但从科技里挪出来了。", "visual_description": "资金流向转场空镜：交易所/盘面暗化，画面逐渐收暗引入下一段。" }
      ]
    },
    {
      "scene_id": "A03",
      "scene_title": "主线·英伟达财报魔咒",
      "scene_design": "专名清单：英伟达（公司） ／ 国家：美国 ／ 年代：现代 ／ 素材来源：英伟达财报发布会实录、GTC 大会、数据中心 ／ 素材偏好：财报数字留白给 MG，避免素人正脸",
      "shots": [
        { "shot_id": "S10", "visual_type": "b-roll", "source": "cloud_only", "script": "重点说说这个魔咒。", "visual_description": "英伟达总部/算力机房空镜，冷峻推镜，铺垫进入魔咒讲解。" },
        { "shot_id": "S11", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "英伟达财报26号盘后出的，营收962亿美元，同比涨106%，净利润597亿，同比涨126%，三季度指引1080亿，全都超预期。", "visual_description": "底为英伟达财报发布会截图暗化；MG 叠加：四组数据卡（营收962亿/+106%、净利597亿/+126%、指引1080亿）逐条弹出，最后「全部超预期」暖金对勾定格。" },
        { "shot_id": "S12", "visual_type": "b-roll", "source": "cloud_only", "script": "27号美股英伟达涨了8.74%，A股跟着狂欢，科创50一天涨了3.77%。", "visual_description": "美股英伟达 logo/盘面狂欢空镜，向上情绪铺垫，不叠数字。" },
        { "shot_id": "S13", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "结果今天，科创50跌1.85%，把昨天涨的全吐了回去。", "visual_description": "底为科创50/盘面暗化；MG 叠加：「+3.77%→-1.85%」波形动画，涨的部分被「吐回」——向上柱逐渐回落归零，警示黄标注，光纤向下弯折形态。" }
      ]
    },
    {
      "scene_id": "A04",
      "scene_title": "主线·预期差机制",
      "scene_design": "专名清单：英伟达（公司） ／ 国家：美国 ／ 年代：现代 ／ 素材来源：英伟达发布会/股价新闻画面（底板暗化）、MG 抽象机制示意为主 ／ 素材偏好：底板暗化、MG 占主，避免素人正脸",
      "shots": [
        { "shot_id": "S14", "visual_type": "b-roll", "source": "cloud_only", "script": "为什么会这样？", "visual_description": "疑问过渡空镜：画面收暗，留白呼吸。" },
        { "shot_id": "S15", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "先说英伟达自己，它已经连续四个季度，财报发完第二天股价就跌，业绩一次比一次好，股价一次比一次见光死。", "visual_description": "底为英伟达发布会/股价新闻暗化；MG 叠加：连续四季度时间轴，四个节点依次弹出，每个节点业绩（暖金向上）与次日股价（警示黄向下）形成剪刀差，「见光死」三字逐季浮现。" },
        { "shot_id": "S16", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "这里头有个词叫预期差。市场买的从来不是公司有没有超目标，而是有没有超市场早想好的那个更高的数。", "visual_description": "底为交易员/盘面暗化；MG 叠加：「预期差」名词卡片砸屏，下方两条线示意——「超目标」与「市场早想好的更高数」，后者画得更高，箭头指向差距。" },
        { "shot_id": "S17", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "这次指引超预期，但预期差在收窄，市场早把数算进去了。", "visual_description": "底为盘面暗化；MG 叠加：两条预期线逐渐靠拢，「预期差收窄」四字浮现，配一个向下箭头示意「市场早把数算进去了」。" },
        { "shot_id": "S18", "visual_type": "b-roll", "source": "cloud_only", "script": "财报一落地，赌财报的人就要兑现。", "visual_description": "交易盘面空镜：成交单滚动，收束节奏，引出兑现的动作感。" }
      ]
    },
    {
      "scene_id": "A05",
      "scene_title": "主线·光模块三剑客见光死",
      "scene_design": "专名清单：中际旭创、新易盛、天孚通信、胜宏科技（公司） ／ 国家：中国 ／ 年代：现代 ／ 素材来源：光模块公司厂区/产线、算力机房、光纤产品 ／ 素材偏好：数据画面留白给 MG，避免素人正脸",
      "shots": [
        { "shot_id": "S19", "visual_type": "b-roll", "source": "cloud_only", "script": "A股光模块把这套又演了一遍，更狠。", "visual_description": "光模块/光纤产线空镜，硬朗快切，进入光模块段。" },
        { "shot_id": "S20", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "光模块三剑客\"易中天\"，中际旭创、新易盛、天孚通信，中报全都爆表。", "visual_description": "底为光模块机房/光纤产品实拍暗化；MG 叠加：「三剑客」三张名片卡（中际旭创、新易盛、天孚通信）依次弹出并列，「中报爆表」暖金大字。" },
        { "shot_id": "S21", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "但你回去翻，8月24号它们披露中报的当天，中际旭创就跌了7.72%，三剑客集体见光死。", "visual_description": "底为中际旭创/盘面暗化；MG 叠加：日历卡片「8.24」弹出，「-7.72%」警示黄砸屏，「集体见光死」四字压上。" },
        { "shot_id": "S22", "visual_type": "b-roll", "source": "cloud_only", "script": "今天英伟达再来一波利好，还是没接住，中际旭创冲高回落收跌0.9%，新易盛跌2.47%。", "visual_description": "光模块盘面空镜：冲高回落氛围画面（空镜代指），不叠具体数字，节奏过渡。" },
        { "shot_id": "S23", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "跌得最狠的是胜宏科技，一天跌8.15%，主力净流出20个亿。", "visual_description": "底为胜宏科技/PCB 产线暗化；MG 叠加：「-8.15%」警示黄最大字号砸屏，「主力净流出20亿」数字滚出，配向下光纤纹理。" }
      ]
    },
    {
      "scene_id": "A06",
      "scene_title": "主线·信号·抱团太挤",
      "scene_design": "专名清单：中际旭创、胜宏科技、新易盛（公司） ／ 国家：中国 ／ 年代：现代 ／ 素材来源：光模块机房、盘面、雪球社区界面 ／ 素材偏好：数据画面留白给 MG，避免素人正脸",
      "shots": [
        { "shot_id": "S24", "visual_type": "b-roll", "source": "cloud_only", "script": "不过今天有个信号挺关键。", "visual_description": "转场空镜：画面收暗，一句「信号挺关键」的悬念铺垫。" },
        { "shot_id": "S25", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "中际旭创全天成交280个亿，全市场第一，主力资金还净流入8个多亿，它是冲高回落，不是被砸盘。", "visual_description": "底为中际旭创/盘面暗化；MG 叠加：「成交280亿·全市场第一」大字卡，「净流入8亿多」暖金向上，「冲高回落≠砸盘」逻辑标注。" },
        { "shot_id": "S26", "visual_type": "b-roll", "source": "cloud_only", "script": "真正被抛的是胜宏科技、新易盛。", "visual_description": "胜宏科技/新易盛盘面空镜，简短点名，节奏轻。" },
        { "shot_id": "S27", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "这说明光模块这个位置，市场不是不看好，是涨得太多、抱团太挤，一有风吹草动，浮盈最多的先跑。", "visual_description": "底为光模块/盘面暗化；MG 叠加：「抱团太挤」四字大字报，人群拥挤→风吹草动→浮盈先跑的箭头流程示意。" },
        { "shot_id": "S28", "visual_type": "b-roll", "source": "cloud_only", "script": "雪球上有老哥说得直白，为什么最大最好的反而不涨？筹码问题，机构不干活，没钱。话糙理不糙。", "visual_description": "雪球社区/评论区界面空镜，念出老哥的直白话，画面略作停顿突出「话糙理不糙」。" }
      ]
    },
    {
      "scene_id": "A07",
      "scene_title": "主线·风吹草动·美联储",
      "scene_design": "专名清单：美联储（机构）、沃什（人名）、杰克逊霍尔（地标） ／ 国家：美国 ／ 年代：现代 ／ 素材来源：美联储大楼、杰克逊霍尔会场、国债/宏观新闻画面 ／ 素材偏好：数据画面留白给 MG，避免素人正脸",
      "shots": [
        { "shot_id": "S29", "visual_type": "b-roll", "source": "cloud_only", "script": "那风吹草动是什么？", "visual_description": "悬念过渡空镜：暗场呼吸，引出「风吹草动」。" },
        { "shot_id": "S30", "visual_type": "b-roll", "source": "cloud_only", "script": "今晚22点，美联储主席沃什要在杰克逊霍尔做上任后第一次主旨演讲。", "visual_description": "美联储大楼/杰克逊霍尔会场空镜，冷峻权威感，不叠数字。" },
        { "shot_id": "S31", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "而在此之前，美国30年期国债收益率一度冲到5.3%上方，创2007年以来新高。", "visual_description": "底为美债/宏观新闻暗化；MG 叠加：「30年期收益率 5.3%」数字砸屏，「创2007年以来新高」警示黄标注，向上箭头配一条陡升曲线。" },
        { "shot_id": "S32", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "长端利率这么高，直接压科技股估值——科技股赚的是未来的钱，利率越高越不值钱。", "visual_description": "底为科技股盘面/芯片空镜暗化；MG 叠加：长端利率上升压估值示意——利率向上箭头 vs 科技股估值向下箭头，「利率越高越不值钱」落在交叉点。" },
        { "shot_id": "S33", "visual_type": "b-roll", "source": "cloud_only", "script": "加上7月通胀PCE同比3.7%，还高于美联储2%的目标。", "visual_description": "宏观数据画面：通胀/美联储新闻空镜，简短陈述，节奏平稳。" }
      ]
    },
    {
      "scene_id": "A08",
      "scene_title": "主线·三因素收束与盯两个数",
      "scene_design": "专名清单：美联储（机构）、沃什（人名） ／ 国家：美国 ／ 年代：现代 ／ 素材来源：美联储/杰克逊霍尔、宏观新闻（底板暗化） ／ 素材偏好：MG 框架占主，素材暗化作底，避免素人正脸",
      "shots": [
        { "shot_id": "S34", "visual_type": "mg_frame", "source": "cloud_only", "script": "所以今天科技跌，不是基本面坏了，英伟达的订单、光模块的业绩都好好的，是三个东西叠一起：利好提前兑现、抱团太挤浮盈想跑、还有今晚美联储讲话这个不确定。", "visual_description": "三层堆叠框架，炭灰底 + 暖金分隔：三层依次「利好提前兑现」「抱团太挤浮盈想跑」「今晚美联储讲话不确定」，每层一块面板；念到哪一层哪一层暖金高亮、其余压暗，底部一条「三个东西叠一起」总括条，光纤弯折纹理作层间分隔。" },
        { "shot_id": "S35", "visual_type": "b-roll", "source": "cloud_only", "script": "这三样没变之前，科技就是涨一天歇一天的节奏。", "visual_description": "盘面空镜：涨跌交替，节奏收束，「涨一天歇一天」的平实氛围。" },
        { "shot_id": "S36", "visual_type": "b-roll", "source": "cloud_only", "script": "那接下来该盯什么？不是去猜明天涨还是跌，就盯两个数。", "visual_description": "过渡空镜：画面收暗，引入「盯两个数」的悬念。" },
        { "shot_id": "S37", "visual_type": "mg_frame", "source": "cloud_only", "script": "一个是今晚沃什的讲话，看他怎么定义这轮通胀，是暂时供给冲击还是结构性问题，这决定9月降息还降不降。另一个是长端美债收益率，30年期在5.3%这个高位能不能下来。", "visual_description": "左右两宫格框架，炭灰底 + 暖金分割：左格「今晚沃什讲话」（生图·美联储/杰克逊霍尔会场），右格「30年期美债 5.3%」（生图·收益率曲线图）；念到哪格哪格金框高亮、另一格压暗，下方一条「两个没看清之前不下结论」的收束条。" },
        { "shot_id": "S38", "visual_type": "b-roll", "source": "cloud_only", "script": "这两个没看清之前，科技股的估值压力就还在，我不下结论。", "visual_description": "暗场收束空镜：镜头缓收，沉稳收尾主线，引出快评。" }
      ]
    },
    {
      "scene_id": "A09",
      "scene_title": "快评①阳光电源",
      "scene_design": "专名清单：阳光电源（公司） ／ 国家：中国 ／ 年代：现代 ／ 素材来源：光伏厂区、逆变器产品、储能电站 ／ 素材偏好：数据画面留白给 MG，避免素人正脸",
      "shots": [
        { "shot_id": "S39", "visual_type": "b-roll", "source": "cloud_only", "script": "下面几条，跟你手里可能有的票直接有关。", "visual_description": "快评转场空镜：章节提示感画面，「下面几条」的引入节奏。" },
        { "shot_id": "S40", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "第一条，阳光电源半年报。净利52.59亿，同比降了32%，营收309亿，也降了29%。", "visual_description": "底为阳光电源光伏厂区/逆变器产品实拍暗化；MG 叠加：「净利52.59亿/-32%」「营收309亿/-29%」两组数据卡砸屏，向下警示黄箭头标注双降。" },
        { "shot_id": "S41", "visual_type": "b-roll", "source": "cloud_only", "script": "光伏逆变器龙头，业绩双降。", "visual_description": "光伏逆变器产品/厂区空镜，硬朗快切，「业绩双降」平实陈述。" },
        { "shot_id": "S42", "visual_type": "b-roll", "source": "cloud_only", "script": "但它不是个案，是过去两年光伏整条链价格战的结果。", "visual_description": "光伏产业链空镜：硅片/组件产线，铺垫「价格战」背景，不叠数字。" },
        { "shot_id": "S43", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "这个下滑市场其实早就有预期，今天股价只跌了1.16%，说明这口气早就被消化得差不多了。", "visual_description": "底为阳光电源/盘面暗化；MG 叠加：「今日股价-1.16%」小字（对比说明跌得克制），配「预期早就消化」的进度条示意。" },
        { "shot_id": "S44", "visual_type": "b-roll", "source": "cloud_only", "script": "拿着光伏的朋友，真正要盯的不是它这次赚多少，是下半年海外大储和电价有没有起色。", "visual_description": "海外大储电站/光伏空镜，结尾建议落点，节奏收束。" }
      ]
    },
    {
      "scene_id": "A10",
      "scene_title": "快评②利通电子",
      "scene_design": "专名清单：利通电子（公司）、中际旭创（公司） ／ 国家：中国 ／ 年代：现代 ／ 素材来源：PCB 产线、算力服务器、电子厂区 ／ 素材偏好：数据画面留白给 MG，避免素人正脸",
      "shots": [
        { "shot_id": "S45", "visual_type": "b-roll", "source": "cloud_only", "script": "第二条，利通电子。这条特别能说明今天的主线。", "visual_description": "利通电子/PCB 产线空镜，引入快评②，硬朗审视。" },
        { "shot_id": "S46", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "它上半年净利7个亿，同比涨了1275%，十几倍的增长，绝对的大超预期。", "visual_description": "底为算力服务器/PCB 实拍暗化；MG 叠加：「净利7亿 同比+1275%」数字砸屏，「十几倍」放大定格，暖金向上。" },
        { "shot_id": "S47", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "结果今天股价跌了4.21%。业绩好成这样就这？", "visual_description": "底为利通电子盘面/算力空镜暗化；MG 叠加：「今日-4.21%」警示黄砸屏，「业绩好成这样就这？」问句大字卡浮现。" },
        { "shot_id": "S48", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "对，又一个买预期卖事实的活样本。", "visual_description": "底为盘面暗化；MG 叠加：「买预期 卖事实」六个字大字报砸屏，正反两色（买预期暖金/卖事实警示黄）。" },
        { "shot_id": "S49", "visual_type": "b-roll", "source": "cloud_only", "script": "它做算力经销和PCB，正是这波涨得最凶的方向，财报落地，反而是获利兑现的时候。", "visual_description": "算力经销/PCB 产线空镜，陈述业务方向，节奏过渡。" },
        { "shot_id": "S50", "visual_type": "b-roll", "source": "cloud_only", "script": "跟中际旭创一个剧本：单子是真的，钱也是真的，就是股价早把这份好提前涨完了。", "visual_description": "中际旭创/光模块空镜，收束快评②，「剧本」类比氛围。" }
      ]
    },
    {
      "scene_id": "A11",
      "scene_title": "快评③医药",
      "scene_design": "专名清单：万邦医药（公司）、CRO/疫苗/减肥药/细胞治疗（行业） ／ 国家：中国 ／ 年代：现代 ／ 素材来源：药企/实验室、医疗场景、医药新闻画面 ／ 素材偏好：数据画面留白给 MG，避免素人正脸",
      "shots": [
        { "shot_id": "S51", "visual_type": "b-roll", "source": "cloud_only", "script": "第三条，医药今天崩了。", "visual_description": "医药/药企实验室空镜，引入快评③，冷峻下压。" },
        { "shot_id": "S52", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "医疗服务板块跌2.69%，行业倒数第一，CRO、疫苗、减肥药、细胞治疗全线下杀，万邦医药一天跌了17.55%。", "visual_description": "底为医药板块/盘面暗化；MG 叠加：「医疗服务-2.69% 行业倒数第一」大字卡，「万邦医药-17.55%」警示黄砸屏，CRO/疫苗/减肥药/细胞治疗标签依次弹出下杀。" },
        { "shot_id": "S53", "visual_type": "b-roll", "source": "cloud_only", "script": "我翻了半天，没找到特别明确的利空。", "visual_description": "搜索/翻查画面空镜，「没找到明确利空」的悬念氛围。" },
        { "shot_id": "S54", "visual_type": "b-roll", "source": "cloud_only", "script": "医药这一波更像是被高低切换抽了血，钱从高位的成长股，挪去了农业、化工这些低位方向，医药跟着科技一起被晾在一边。", "visual_description": "医药/盘面空镜，念白陈述资金从高位成长股挪去低位方向，节奏平稳。" },
        { "shot_id": "S55", "visual_type": "b-roll", "source": "cloud_only", "script": "这种没有消息面的普跌，往往比有消息的跌更磨人。", "visual_description": "医药盘面空镜，情绪收束，「普跌更磨人」的压抑氛围。" }
      ]
    },
    {
      "scene_id": "A12",
      "scene_title": "快评④成品油",
      "scene_design": "专名清单：92号汽油（产品）、国际油价/原油（行业） ／ 国家：中国 ／ 年代：现代 ／ 素材来源：加油站、炼油厂、原油/油轮、地缘新闻画面 ／ 素材偏好：数据画面留白给 MG，避免素人正脸",
      "shots": [
        { "shot_id": "S56", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "第四条，今晚24点，国内成品油要上调了，92号汽油每升大概涨0.24到0.35元。", "visual_description": "底为加油站/油价牌实拍暗化；MG 叠加：「92号汽油 +0.24~0.35元/升」数字砸屏，向上箭头配油价牌跳动，晚间上调氛围。" },
        { "shot_id": "S57", "visual_type": "b-roll", "source": "cloud_only", "script": "家用车加满一箱，比平时多花十几块钱。", "visual_description": "家用车加油空镜，生活化画面，「加满多花十几块」的具象。" },
        { "shot_id": "S58", "visual_type": "b-roll", "source": "cloud_only", "script": "背后是国际油价在高位，地缘局势一直没消停。", "visual_description": "国际油价/原油/油轮空镜，地缘新闻画面，铺垫背景。" },
        { "shot_id": "S59", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "油一涨，今天农业、化工这些涨价链条为什么这么强，就说得通了，成本端往上顶，涨价预期就起来了。", "visual_description": "底为农业/化工盘面暗化；MG 叠加：成本端向上顶→涨价预期起来的传导箭头示意，「油一涨」落在箭头起点。" },
        { "shot_id": "S60", "visual_type": "b-roll", "source": "cloud_only", "script": "手里有这些方向的朋友，盯着油价，比盯着每天的涨跌更实在。", "visual_description": "油价/盘面空镜，收束快评④，「盯着油价」的落点。" }
      ]
    },
    {
      "scene_id": "A13",
      "scene_title": "快评⑤农业领涨",
      "scene_design": "专名清单：万向德农（公司）、种植业/供销社/化肥/粮食/大豆/玉米（行业） ／ 国家：中国 ／ 年代：现代 ／ 素材来源：农田、粮食、化肥、农产品交易画面 ／ 素材偏好：数据画面留白给 MG，避免素人正脸",
      "shots": [
        { "shot_id": "S61", "visual_type": "b-roll", "source": "cloud_only", "script": "第五条，所以今天领涨的是谁？", "visual_description": "农业/农田空镜，引入快评⑤，「领涨是谁」的悬念。" },
        { "shot_id": "S62", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "种植业涨2.97%，行业第一；供销社概念涨3.06%，题材第一；化肥、粮食、大豆、玉米全产业链一起上，万向德农9天6板。", "visual_description": "底为农业/粮食盘面暗化；MG 叠加：领涨榜并列卡——种植业+2.97%、供销社+3.06%、化肥/粮食/大豆/玉米、万向德农9天6板，逐条暖金高亮。" },
        { "shot_id": "S63", "visual_type": "b-roll", "source": "cloud_only", "script": "这是资金从科技撤出来后抱团的地方。", "visual_description": "农业盘面/农田空镜，「资金抱团地方」的陈述。" },
        { "shot_id": "S64", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "但我得提醒一句：农业这一波是延续强势，不是今天才启动的，已经涨了好几天的方向，你看到它领涨的时候，往往是别人已经上车的时候。", "visual_description": "底为农业/农田盘面暗化；MG 叠加：「延续强势 ≠ 今天才启动」提醒大字报，「别人已经上车」配一个已加速离场的箭头示意，警示黄提醒。" }
      ]
    },
    {
      "scene_id": "A14",
      "scene_title": "情绪段·掏心窝",
      "scene_design": "专名清单：无 ／ 国家：中国 ／ 年代：现代 ／ 素材来源：散户交易画面、手机盯盘、盘面（情绪铺垫） ／ 素材偏好：情绪氛围，少 MG，避免素人正脸",
      "shots": [
        { "shot_id": "S65", "visual_type": "b-roll", "source": "cloud_only", "script": "最后说点掏心窝的。", "visual_description": "情绪段开场空镜：收暗留白，「掏心窝」的诚恳氛围。" },
        { "shot_id": "S66", "visual_type": "b-roll", "source": "cloud_only", "script": "今天这种盘，最难受的不是亏钱的，是拿着好公司、业绩明明很好、股价却跌的人。", "visual_description": "散户盯盘/手机屏幕空镜（避免正脸），压抑克制的情绪铺垫。" },
        { "shot_id": "S67", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "市场大多数时候不是错杀你手里的公司，是它在给已经涨过的那部分重新定价。", "visual_description": "底为盘面暗化；MG 叠加：「重新定价」四字大字报，配「已经涨过的那部分」高亮框，暖金/警示黄对比。" },
        { "shot_id": "S68", "visual_type": "b-roll", "source": "cloud_only", "script": "财报再好，只要它已经涨在股价里了，出来就是兑现，不是发钱。", "visual_description": "盘面空镜：「兑现不是发钱」的克制陈述，节奏平实。" },
        { "shot_id": "S69", "visual_type": "b-roll", "source": "cloud_only", "script": "反过来，那些跌透了、没人看的，一个不起眼的消息就能弹起来。", "visual_description": "冷门股/盘面空镜：「跌透没人看」的反差铺垫，暗调。" },
        { "shot_id": "S70", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "所以别跟自己的持仓较劲，看清楚你的票现在处在已经涨过了、还是还没被看到的位置，比纠结今天为什么跌更重要。", "visual_description": "底为盘面暗化；MG 叠加：「别跟持仓较劲」大字报，「已经涨过了 vs 还没被看到」左右对比框，核心落点暖金定格。" }
      ]
    },
    {
      "scene_id": "A15",
      "scene_title": "结尾·互动引导",
      "scene_design": "专名清单：蛋炒饭财经（账号） ／ 国家：中国 ／ 年代：现代 ／ 素材来源：盘面、评论区界面 ／ 素材偏好：收尾互动氛围，避免素人正脸",
      "shots": [
        { "shot_id": "S71", "visual_type": "b-roll", "source": "cloud_only", "script": "盘面天天变，看盘的方法不用天天变，咱们明天收盘再聊。", "visual_description": "收尾空镜：盘面收盘画面，「明天再聊」的轻松收束。" },
        { "shot_id": "S72", "visual_type": "b-roll", "source": "cloud_only", "script": "最后照例说一句，今天讲的都是对盘面的观察和归因，不构成任何投资建议，市场有风险，自己的钱自己拿主意。", "visual_description": "风险提示空镜：盘面/字卡氛围，沉稳念白，不叠 MG。" },
        { "shot_id": "S73", "visual_type": "b-roll+mg", "source": "cloud_only", "script": "你手里现在最难受的是哪个板块，评论区说一下，明天挑呼声最高的来讲。", "visual_description": "底为评论区/互动界面暗化；MG 叠加：「评论区说一下」暖金引导条，配点赞/评论图标，收尾互动钩子。" }
      ]
    }
  ]
}
```
````

## 三、场景速览表 + MG 比例自检

| 场景 | 标题 | 分镜范围 | 镜数 | MG 镜数 |
|---|---|---|---|---|
| A01 | 开场·矛盾砸屏 | S01-S03 | 3 | 3（1 mg_frame + 2 b-roll+mg） |
| A02 | 关注引导·大盘分化 | S04-S09 | 6 | 2 |
| A03 | 主线·英伟达财报魔咒 | S10-S13 | 4 | 2 |
| A04 | 主线·预期差机制 | S14-S18 | 5 | 3 |
| A05 | 主线·光模块三剑客见光死 | S19-S23 | 5 | 3 |
| A06 | 主线·信号·抱团太挤 | S24-S28 | 5 | 2 |
| A07 | 主线·风吹草动·美联储 | S29-S33 | 5 | 2 |
| A08 | 主线·三因素收束与盯两个数 | S34-S38 | 5 | 2（2 mg_frame） |
| A09 | 快评①阳光电源 | S39-S44 | 6 | 2 |
| A10 | 快评②利通电子 | S45-S50 | 6 | 3 |
| A11 | 快评③医药 | S51-S55 | 5 | 1 |
| A12 | 快评④成品油 | S56-S60 | 5 | 2 |
| A13 | 快评⑤农业领涨 | S61-S64 | 4 | 2 |
| A14 | 情绪段·掏心窝 | S65-S70 | 6 | 2 |
| A15 | 结尾·互动引导 | S71-S73 | 3 | 1 |

- 场景数：15
- 分镜数：73
- mg_frame：3（S01 开场钩子、S34 三因素信息高潮、S37 盯两个数收尾清单）
- b-roll+mg：29
- 总 MG：32 / 73 = 43.8%
- 每场景分镜数均 ≤ 10；无连续 4 个以上纯 b-roll 分镜堆叠（最长 3 个）。
