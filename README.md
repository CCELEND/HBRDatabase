## 安装依赖

### python3.8 以上

### opencv-python、Pillow、requests、pygame、ttkbootstrap、numpy、pandas、openpyxl、selenium、webdriver-manager

运行 install_module.py 安装依赖模块

## 使用

运行 HBRDatabaseGUI.py 即可

### 角色

点击角色菜单栏，选择队伍后弹出队伍窗口，左键点击角色，显示角色的全身画。

左键点击角色的风格头像，显示风格的技能信息，右键可以选择角色风格的动画或者静态图。

### 搜索

点击搜索菜单栏，目前支持搜索角色风格，可以根据关键词的技能、风格名称和俗称进行搜索，多个关键词用逗号分隔；  
搜索技能或者效果时，需要指定主动或者被动。（关键词如有疏漏请与我联系）

### 工具

包含词条获取和伤害分计算  
词条获取：计算真实随机值并获取词条保存为 Excel 文件  
使用之前需要修改 config.ini 配置文件，文件路径：HBRDatabase/工具/GetEntriesGUILocal/config.ini）  
填入洗孔的 seed 和 index：  
	ChangeAbility_seed=  
	ChangeAbility_index=  
填入装备的 seed 和 index：  
	RandomMainAbility_seed=  
	RandomMainAbility_index=  
控制获取数据数，修改 DataCount，这里默认是获取300条数据  
	DataCount=300  
（如果想要获取自己账号的装备 seed 和 index、洗孔 seed 和 index，请与我联系）  
风格图鉴获取：自动获取炽焰天穹国服风格的 Heaven Burns Red Style Chart 图鉴  
	需要安装最新版本的 chrome 浏览器
伤害模拟：通过添加的技能与填写的能力值来计算出最终伤害。炽焰天穹伤害计算器  
	需要点击浏览器的拓展程序来运行

### 音乐

点击音乐菜单栏，双击想听的歌，等待从服务器下载，然后播放即可

### 更新

点击更新菜单栏，更新数据和版本，更新失败的话多更新几次。更新后如果启动失败，记得运行一下 install_module.py

![Image text](https://github.com/CCELEND/HBRDatabase/blob/main/show/show.png)