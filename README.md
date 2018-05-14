# pocket48
基于[cq-http-python-sdk](https://github.com/richardchien/cqhttp-python-sdk)和Python3.6制作

监控成员口袋48聚聚房间，微博和摩点项目

目前可用的插件:
* 如果不想使用某插件，只需要在main.py中注释掉相应行即可
* pocket48_plugin(口袋48插件)
* weibo_plugin(微博监听插件)
* modian_plugin（摩点监听插件)
* statistic_plugin (数据收集插件）

口袋48插件1分钟监听一次，微博插件1分钟监听一次，摩点插件20秒监听一次（可以自行调整）

### 前置条件
* 目前需要的Python3 library有：
    + DB操作相关：`pymysql` + `DBUtils`
    + 定时任务相关：`APScheduler`
    + 酷Q HTTP API相关：`cqhttp`
    + 网络相关：`requests`
* 在项目目录的上一级目录新建`logs`文件夹，日志文件会存放在该目录中
* 摩点插件所需的数据库建表语句存放在`data/db.sql`中


### coolq配置
* 具体使用请参照(https://richardchien.github.io/coolq-http-api)
* 先启动coolq_http_server.py, 再启动main.py
* 如果使用了酷Q Pro，在conf.ini的`using_coolq_pro`项中填写"yes"
 

### 口袋48和微博插件使用
* 首先确保你想监控的成员已经开通口袋房间
* 在conf.ini中修改自己想要监控的成员的拼音（目前只有上海地区的成员资料，微博uid暂时没有填写，需要自行找到并data/member.json中）
* 可以给不同的群开放不同的功能(目前有房间消息，房间评论，直播提醒，微博提醒），详情请见conf.ini
* 在conf.ini中修改内容，注意一定要按照格式来写，否则无法解析


### 摩点插件使用
* 需要安装mysql
* 摩点监控数据在data/wds.json中，monitor_activities为监控项目，modian_pk_activities为PK活动的项目
* 接棒活动播报（测试中）：在data/modian_jiebang.json中增加对应的接棒活动，相关数据记录在data/modian.db中
* 金额flag类活动播报（测试中）：在data/modian_flag.json中增加对应的flag活动
* 接棒和金额flag类活动播报类的发送QQ群暂时hardcode在代码中，请自行进行修改


### 数据插件使用
* 目前仅能记录应援群的人数变化情况，使用前需要自行添加记录在statistic/statistics.db的'member'表中（member_id和member_name要和data/member.json中的一致)


### 注意事项
* 仍然在开发中

