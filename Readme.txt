注: "根目录" 指该工具文件夹的根目录, 也就是本 Readme.txt 文件所在的目录

------------
| 工具描述 |
------------
本工具可以实现根据 bilibili 视频 aid 爬取该视频下的所有评论, 包括其子评论.

工具的根目录下有两个主要文件:
spider.py: Python 程序, 需要传入命令行参数 aid, 程序会将爬取的评论数据保存在 data/aid.csv 文件中 (编码为 UTF-8 with BOM), 并在标准输出显示当前进度
run.ps1: Powershell 脚本, 可以批量爬取多个视频的评论, 并将进度信息输出到 data 目录下与 csv 同名的 log 文件中. 文件仅供实例, 实际使用请自行修改文件名 (aid 号)

------------
| 环境要求 |
------------
Python3, 包含以下库: requests

------------
| 使用方法 |
------------
首先, 准备两项数据: 
1. aid. 可以这样获取: 打开需要爬取的B站视频, 按 F12, 在弹出的开发者模式窗口中进入网络 (Network) 选项卡, 点击搜索图标 (或按 CTRL-F), 输入 ?aid= 查询, 就可以看到 aid 信息
2. Cookie. 同样可以在 F12 的网络选项卡中获取, 随意选择一个网络请求, 在标头 (Header) 选项卡中找到 Cookie 项, 复制对应的内容到 Cookie.txt 文件中 (文件应该是一行字符串), 放在根目录下

对于要爬取的单个视频, 请运行命令 `python spider.py <aid>`, 其中 <aid> 是准备的视频 aid, 然后等待程序运行结束, 评论数据已经被写入 data 目录下的 csv 文件, 可以用 Excel 进一步查看和处理

spider.py 默认将 csv 文件输出到 data 目录, 请在运行前保证 data 目录已建立

若要批量运行, 可以参考 run.ps1 脚本, 编写自己的脚本

------------
| 注意事项 |
------------
本工具编写于 2024/3/2, 若B站 API 发生改变, 本工具可能失效.

若爬取出现问题 (比如只爬到了个位数的评论), 可能是 Cookie 失效, 请复制新的 Cookie 到 Cookie.txt 文件
