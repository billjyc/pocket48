# pocket48
基于[Graia Ariadne](https://github.com/GraiaProject/Ariadne/)和Python3.9制作

监控成员口袋48聚聚房间，微博和摩点项目

目前可用的插件:
* 如果不想使用某插件，只需要在`main.py`中注释掉相应行即可
* `pocket48_plugin`(口袋48插件，大概率不能用了)
* `weibo_plugin`(微博监听插件)
* `modian_plugin`（摩点监听插件，大概率不能用，但是调用原理可用来设计新的jz软件)
* `statistic_plugin` (数据收集插件）

口袋48插件1分钟监听一次，微博插件1分钟监听一次，摩点插件20秒监听一次（可以自行调整）

### 前置条件
* 目前需要的Python3 library有：
    + DB操作相关：`pymysql` + `DBUtils`
    + 定时任务相关：`APScheduler`
    + mirai HTTP API相关：`graia-application-mirai`, `graia-component-selector`, `graia-template`
    + 网络相关：`requests`
* 在项目目录的上一级目录新建`logs`文件夹，日志文件会存放在该目录中
* 摩点插件所需的数据库建表语句存放在`data/db.sql`中（数据库名为`card_draw`）


### mirai配置
* 首先需要启动mirai-console-loader
* 参数配置请参照(https://graia.readthedocs.io/projects/ariadne/quickstart/)
* 先启动`mirai_bot.py`, 再启动`main.py`

### 口袋48插件使用
* 首先确保你想监控的成员已经开通口袋房间（否则会拉不到数据）
* `data/pocket48/pocket48.json`
    + `IMEI`: 手机序列号，可以使用真机，也可以使用模拟器
    + `version`: 所使用的口袋48的版本
    + `username`, `password`: 登录口袋48所需的用户名和密码（建议使用小号）
    + `monitor_members`: 监控成员列表，每一项需要填写如下内容：
        * `member_room_msg_groups`：接收成员消息的群号，用分号分隔
        + `member_room_comment_groups`: 接收成员房间评论的群号，用分号分隔
        + `member_live_groups`：如果成员开启直播，接收开播提醒的群号，用分号分隔
        + `member_room_comment_lite_groups`: 如果距离成员上一条房间消息发送超过10分钟后，又有新的成员消息，这时会发送一条提醒到群中
        + `room_msg_lite_notify`: 简易版提醒的提示语，支持多个，随机发送
* `conf.ini`相关配置
    + `performance_notify`: 公演直播提示语，需要在`data/schedule.json`中配置
* 在`conf.ini`中修改内容，注意一定要按照格式来写，否则无法解析


### 微博插件使用
* 微博uid在`data/member.json`中，可以自行填写
* `conf.ini`相关配置
    + `member_weibo_groups`: 接收成员微博提醒的群号，使用分号分隔


### 摩点插件使用
* 需要安装MySQL
* 摩点监控数据在`data/modian.json`中，`monitor_activities`为监控项目，`modian_pk_activities`为PK活动的项目
* 接棒活动播报（测试中）：在`data/modian_jiebang.json`中增加对应的接棒活动，相关数据记录在`data/modian.db`中
* 金额flag类活动播报（测试中）：在`data/modian_flag.json`中增加对应的flag活动
* 接棒和金额flag类活动播报类的发送QQ群暂时hardcode在代码中，请自行进行修改


### 数据插件使用
* 目前仅能记录应援群的人数变化情况，使用前需要自行添加记录在`statistic/statistics.db`的'member'表中（member_id和member_name要和data/member.json中的一致)


### 注意事项
* 仍然在开发中

