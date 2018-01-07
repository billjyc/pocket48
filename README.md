# pocket48
基于[cq-http-python-sdk](https://github.com/richardchien/cqhttp-python-sdk)制作

监控成员口袋48聚聚房间，微博和微打赏项目

目前可用的插件: 
* pocket48_plugin(口袋48插件)
* weibo_plugin(微博监听插件)
* wds_plugin（微打赏监听插件)

口袋48插件1分钟监听一次，微博插件1分钟监听一次，微打赏插件1分钟监听一次（可以自行调整）

### coolq配置
* 具体使用请参照(https://richardchien.github.io/coolq-http-api/3.3/#/)
* 先启动coolq_http_server.py, 再启动main.py
 
### 口袋48和微博插件使用
* 首先确保你想监控的成员已经开通口袋房间
* 在conf.ini中修改自己想要监控的成员的拼音（目前只有Team SII和NII的资料，如果有其他人的话，可以自行按照里面的格式添加成员的口袋ID，房间ID，微博链接）
* 可以给不同的群开放不同的功能(目前有房间消息，房间评论，直播提醒，微博提醒），详情请见conf.ini
* 暂不支持语音和图片消息
* 在conf.ini中修改内容，注意一定要按照格式来写，否则无法解析


### 微打赏插件使用
* 微打赏监控数据在data/wds.json中，monitor_activities为监控项目，wds_pk_activities为PK活动的项目
* 摩点的插件还在开发中


### 注意事项
* 仍然在开发中

