# HBRDatabase — 炽焰天穹本地数据库

**基于 Python + PyQt5 的桌面工具：角色风格搜索、排轴 OD 计算、图片/视频转线稿、seed 自动获取、词条计算、图鉴获取、音乐资源下载等**

![Image text](https://github.com/CCELEND/HBRDatabase/blob/main/show/show.png)
>基于 Python 的 PyQT5 版本已重构完成，**推荐使用 PyQt5 版本**（界面更流畅、启动更快、功能更全）
![Image text](https://github.com/CCELEND/HBRDatabase/blob/main/show/show2.png)

## 目录

- [安装依赖](#安装依赖)
- [使用](#使用)
- [功能模块](#功能模块)
  - [角色](#角色) / [搜索](#搜索) / [持有物](#持有物) / [战斗系统](#战斗系统) / [敌人](#敌人)
  - [工具](#工具)（[排轴OD计算](#排轴od计算) / [图片转线稿工具20](#图片转线稿工具20) / [视频转线稿](#视频转线稿) / [词条获取](#词条获取) / [风格图鉴获取](#风格图鉴获取) / [伤害模拟](#伤害模拟) …）
  - [音乐](#音乐) / [更新](#更新) / [修复](#修复)
- [常见问题](#常见问题)
- [项目结构](#项目结构)
- [免责声明](#免责声明)
- [其他](#其他)

## 安装依赖

* Python3.10 以上
* opencv-python、Pillow、requests、pygame、ttkbootstrap、numpy、pandas、openpyxl、selenium、webdriver-manager
>运行 `install_module.py` 安装依赖模块
>高版本 ttkbootstrap 会导致异常，需要卸载高版本 ttkbootstrap，再安装 ttkbootstrap==1.12.0
* 强烈建议使用 `venv` 虚拟环境运行，直接运行 `run_in_venv.bat` 即可一键安装依赖以及运行

> 依赖都是**按需加载**的：只有真正用到某个功能时才会加载对应的大库（opencv / pandas / pygame / selenium 等），所以启动很快，也不会因为少装某个可选库而开不了主界面。

## 使用

* 推荐运行 PyQt5 版本：`HBRDatabaseGUI_QT.py`
>无控制台窗口运行（**推荐**）：`HBRDatabaseGUI_QT.pyw`
* Tkinter 版本（旧版，保留兼容）：`HBRDatabaseGUI.py` / `HBRDatabaseGUI.pyw`
* 强烈建议使用 `venv` 虚拟环境运行，直接运行 `run_in_venv.bat` 即可一键安装依赖以及运行

## 功能模块

### 角色

* 点击角色菜单栏，选择队伍后弹出队伍窗口，左键点击角色，显示角色的全身画
* 左键点击角色的风格头像，显示风格的**技能信息**，右键可以选择角色风格的**动画**或者**立绘**、**3D立绘**
>数据如有错误请与我联系

### 搜索

* 点击搜索菜单栏，目前支持搜索**角色风格**、**大师技能**和**共鸣天赋**，可以根据关键词的**技能**、**风格名称**和**俗称**进行搜索，多个关键词用逗号分隔
* 搜索技能或者效果时，需要指定**主动**或者**被动**
>关键词如有疏漏请与我联系
![Image text](https://github.com/CCELEND/HBRDatabase/blob/main/show/search_show.png)

### 持有物

* 点击光球可以查看**光球技能**
* 支持查看：主线道具、道具、饰品、饰品材料、活动奖章、奖杯勋章、成长素材、强化素材、增幅器、芯片、入场券、扭蛋材料、碎片、货币

### 战斗系统

* 提供战斗机制的图文说明：**共鸣天赋**、**基础**、**Hit**、**乘区**、**职业**、**武器**、**属性**、**效果、状态**
>图鉴类图片会随窗口大小自动缩放，拉伸窗口即可放大查看细节

### 敌人

* 按类别查看敌人图鉴：**时钟塔**、**主线**、**光球BOSS**、**时之修炼场**、**棱镜战**、**宝石棱镜战**、**恒星扫荡战线**、**高分挑战**、**异时层**、**遭遇战**
* 点击敌人图标打开该敌人的图鉴窗口（含攻略图）
>图鉴窗口支持拉伸自适应，长图可以上下滚动查看

### 工具

> 包含排轴 OD 计算、图片/视频转线稿、词条获取、伤害分计算、风格图鉴获取、伤害模拟等

#### 排轴OD计算

OD、SP排轴工具，支持OD、SP、被动、大师技能自动获取计算
>目前已经实现超越量表、印记等，如有 BUG 请与我联系
* 支持**前置OD / 后置OD**、超频回合、追加回合、特殊回合、占位回合
* 队伍 3 前锋 + 3 后卫，自动计算每回合的**剩余 SP**、OD 条、连击/共鸣等状态
* **光球技能**（除专属的「遗能光球」外）**所有角色都能使用**，可直接在行动列表里选择
* 行动行的「条件触发」下拉框可手动指定触发条件（击破敌人 / 【炸裂！！贝斯独奏】发动等）
* 支持存档读档，可保存/载入排轴方案
![Image text](https://github.com/CCELEND/HBRDatabase/blob/main/show/axle_od_win_show1.png)

#### 图片转线稿工具2.0

>优化图像处理算法，相较于图片转线稿工具基于 Canny 边缘检测，图片转线稿工具2.0则基于最小值滤波和线性减淡
* 可调**线条粗细**、**亮度补偿**、**清晰度增强**（对比度拉伸 / 轻度锐化 / 强锐化+去噪）
* 支持**反相**输出（黑底白线），预览后可保存为 PNG
![Image text](https://github.com/CCELEND/HBRDatabase/blob/main/show/LineArt_show1.png)
![Image text](https://github.com/CCELEND/HBRDatabase/blob/main/show/LineArt_show2.png)
![Image text](https://github.com/CCELEND/HBRDatabase/blob/main/show/LineArt_show3.png)

#### 视频转线稿

把**整段视频**逐帧转成线稿，输出线稿视频或图片序列，算法与「图片转线稿工具2.0」**完全一致**。

* 输出方式：
	* `MP4（H.264，画质好）` —— 可**保留原视频音频**
	* `MP4（内置编码，无需 ffmpeg）` —— 任何环境都能用，但没有声音
	* `PNG 帧序列` —— 存成一个文件夹，方便后续自己合成
* **GPU 加速**：自动使用显卡编码（NVIDIA NVENC / Intel QSV / AMD AMF），实测 1080p 比 CPU x264 快**约 2 倍**；没有可用显卡时自动降级到 CPU，不会报错
* **预览帧滑块**：拖到任意一帧先看效果，点进度条可直接跳到该帧
* 带**进度 / 速度 / 预计剩余时间**，随时可取消（取消后不会留下半成品文件）
* 输出分辨率可缩放到 100% / 75% / 50% / 25%，也可以把视频文件直接拖进窗口
* **不依赖系统安装 ffmpeg**：项目自带（压缩存放），第一次使用时自动解压到本地缓存，之后一直复用

#### 词条获取

计算真实随机值并获取词条保存为 Excel 文件
>第一次运行会生成 `config.ini` 配置文件，修改后再使用，文件路径：`./工具/GetEntriesGUILocal/config.ini`
* 填入洗孔的 seed 和 index：
	ChangeAbility_seed=
	ChangeAbility_index=
* 填入装备的 seed 和 index：
	RandomMainAbility_seed=
	RandomMainAbility_index=
* 控制获取数据数，修改 DataCount，这里默认是获取300条数据
	DataCount=300
#### seed_tools

自动获取 seed 和 index，管理员模式运行：`./工具/GetEntriesGUILocal/seed_tools/seed_tools.exe`，仅支持炽焰天穹PC端
* 根据 seed 获取对应 index，管理员模式运行：`./工具/GetEntriesGUILocal/get_index_by_seed.exe`，仅支持炽焰天穹PC端
* seed 正确值范围应该小于**4294967295**，如果获取值错误需要重启PC端
>不会操作的请与我联系
#### 风格图鉴获取

自动获取炽焰天穹国服风格的 Heaven Burns Red Style Chart 图鉴
* 第一次获取时需要登录，后续会自动登录
* 本项目自带了 chrome 测试版浏览器，其实是我比较懒不想一直更新 chromedriver（惭愧），登录之后可能会出现没有数据的情况，刷新一下网页即可
* 如果图鉴数据错误，就删除目录：`./工具/chrome/chrome_user_data` 再重新运行
#### 伤害模拟

通过添加的技能与填写的能力值来计算出最终伤害。炽焰天穹伤害计算器版本：2.1.0_0
* 第一次运行需要启动开发者模式并加载未打包的拓展程序，然后选择目录：`./工具/HBR伤害模拟/2.1.0_0`
#### 伤害分计算 / 伤害分计算V2

按公式计算战斗伤害分，V2 为改进版本，支持更细的参数与更高的精度
#### hbr-tool

包含一些便利的工具（日文）
#### hbr-tool伤害计算

hbr-tool 配套的伤害计算器
#### hbr-axletool

一个 HBR 的排轴工具网站
#### 词条计算器（在线）

在线计算词条，模拟洗词条，打装备
#### 资源和攻略网站

hbr.quest、o.hbr.quest、入队培训手册、gamekee、game8、附带**等效破坏率与OD计算表**
#### AFSGTools

Web 版全能红烧天堂计算工具箱，支持伤害计算、白值计算、OD/破坏/打分、遭遇战出分、受击伤害等

### 音乐

* 点击音乐菜单栏，双击想听的歌，等待从服务器下载，然后播放即可
![Image text](https://github.com/CCELEND/HBRDatabase/blob/main/show/music_show.png)

### 更新

* 点击更新菜单栏，更新数据和版本
>更新失败的话多更新几次。更新后如果启动失败，需要运行一下 `install_module.py`
* 更新走 HTTPS（服务端证书固定校验），只下载**内容有变化**的文件，不会重复下载

### 修复

* 当主窗口无法成功运行时，运行 `repair.pyw` 修复缺失文件

## 常见问题

**Q：第一次用「视频转线稿」卡了几秒？**
A：项目自带 ffmpeg，第一次使用时会解压到 `%LOCALAPPDATA%\HBRDatabase\ffmpeg\`（约 2~3 秒），之后一直复用，不会再等。想换成自己装的 ffmpeg，把这个缓存目录删掉即可。

**Q：「视频转线稿」怎么知道有没有用上显卡？**
A：窗口底部会显示本机可用的 GPU 编码器（NVIDIA NVENC / Intel QSV / AMD AMF）；「编码器」下拉框里选「自动」就会优先用显卡。手动选了不可用的编码器会自动降级到 CPU 并提示。

**Q：为什么更新时下载量有大有小？**
A：更新只下载**内容有变化**的文件。如果这次更新里包含自带的 ffmpeg（约 63 MB），第一次会多下这么多；之后不再重复。

**Q：主界面打开很慢 / 报缺少模块？**
A：先跑一次 `install_module.py` 安装依赖；ttkbootstrap 必须用 `1.12.0`（高版本会异常）。主窗口起不来就跑 `repair.pyw`。

**Q：「风格图鉴获取」拿不到数据？**
A：第一次需要登录，之后会自动登录；页面没数据就刷新一下。数据异常时删掉 `./工具/chrome/chrome_user_data` 再重新运行。

**Q：seed / index 获取失败？**
A：`seed_tools.exe` 和 `get_index_by_seed.exe` 都需要**管理员模式**运行，且仅支持炽焰天穹 PC 端。seed 正确值应小于 4294967295，取值错误时重启 PC 端再试。

## 项目结构

```
HBRDatabase/
├─ HBRDatabaseGUI_QT.pyw      ← 主程序入口（PyQt5，推荐）
├─ HBRDatabaseGUI.pyw         ← 主程序入口（Tkinter，旧版）
├─ repair.pyw                 ← 主窗口起不来时的修复工具
├─ install_module.py          ← 安装依赖
├─ run_in_venv.bat            ← 一键建 venv + 装依赖 + 运行
├─ 角色/                      ← 角色、风格、技能数据（核心数据）
├─ 工具/                      ← 各子工具（排轴 / 线稿 / 伤害计算 …）
│   └─ LineArt/ffmpeg/        ← 视频转线稿自带的 ffmpeg（压缩存放）
├─ 敌人/ 持有物/ 战斗系统/ 搜索/ 音乐/
└─ 更新/ 修复/ 关于/ 日志/
```

## 免责声明

* 本项目为**非官方**的个人学习交流工具，与游戏官方无关。
* 游戏内的图片、音频等素材版权归原权利方（WFS / Key / bilibili 等）所有，仅供学习交流，**请勿用于商业用途**。
* 仓库内含 GPL-3.0 许可文件（`LICENSE`）；「视频转线稿」自带的 ffmpeg 为 GPL v3 构建（详见 `工具/LineArt/ffmpeg/ffmpeg_info.json`）。

## 其他

如有疑问请与我联系：
- CCELEND — [不吃花椒的汪汪队(B站空间)](https://space.bilibili.com/442776860)
- QQ：2644884626、邮箱：celend2644884626@163.com

参考资料：
- [数据库(hbr.quest)](https://hbr.quest)
- [hbr_calc_web(GitHub)](https://github.com/RoyWu0922/hbr_calc_web)
- [AFSGTools — Heaven Burns Red 伤害计算器(GitHub Pages)](https://roywu0922.github.io/hbr_calc_web/)
- [AFSGTools — Heaven Burns Red 伤害计算器(Vercel Pages)](https://hbrtoolbox.vercel.app/)
- [快查表](https://www.kdocs.cn/l/cvdGm5gwG4Jq?R=L1MvMTM=)
- [日服攻略](https://game8.jp/heavenburnsred)
- [gamekee](https://www.gamekee.com/hbr/)
- [wiki.hbr-hd](https://wiki.hbr-hd.com/)
- [hbr-axletool](https://hbr-axletool.pages.dev/)
- [hbr-tool](https://www.hbr-tool.com/)
- [红烧BOX图鉴](https://ruriro.cc/hbr/StyleChart/)
- [词条计算器](https://hbrapi.fuyumi.xyz/)
- [国服官方工具](https://game.bilibili.com/tool/hbr#/)
- [炽焰天穹_HBR(B站空间)](https://space.bilibili.com/3546599741458758)
- [道家深湖(B站空间)](https://space.bilibili.com/24124162)
- [废纸扔了_快查表(B站空间)](https://space.bilibili.com/61357074)
- [兰叔爱玩炽焰天穹(B站空间)](https://space.bilibili.com/10147172)
- [茅森月哥(B站空间)](https://space.bilibili.com/535889)
