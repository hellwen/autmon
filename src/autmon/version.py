# coding=utf-8

__VERSION__ = '2.5'


# change log
"""
v2.5
* 141210 collect_cmd调整异常处理
* 150206 collect_cmd异常处理优化
* 150305 修复add_db_name和add_inst_name两个参数无效BUG
+ 150315 AutmonStart.bat,AutmonStop.bat增加自动创建任务计划，防止客户端因为异常情况终止

v2.4
+ 141112 替换wsadmin为6版本，可支持was6\was7\was8

v2.3

* 140626 db2_tablespace.sql增加auto_resize字段
* 140630 修复was_config.sql中datasourceid有双引号问题
* 140630 修复diskspace.bat判断文件类型（防止cdrom错误）
* 140714 修改collect_cmd的subprocess.Popen的返回方式，防止子程序异常（未验证）

v2.2

* 140611 WAS收集信息中增加Node，数据源增加作用域
* 140624 setup_posix.py去掉pylib的包含
* 140625 diskspace.bat中容量计算BUG修复

v2.1

* 140504 修复subprocess调用脚本会变成僵尸进程（defunct）问题
* 140527 修复was ssl key无法找到问题
+ 140604 ihs收集增加port
+ 140604 增加syscat.columns信息收集

v2.0
+ 140331 增加Linux下系统信息脚本
+ 140320 增加Autmon Handler压缩
+ 140416 增加Autmon Handler压缩开关
+ 140421 增加load收集

v1.9
+ 140210 增加Aix下操作脚本AutmonStart.sh, AutmonStop.sh, AutmonQuery.sh
         其中AutmonStart.sh可以多次执行，可配置crontab调度来实现自动启动
+ 140306 增加db2_datapartition和db2_snapswitches信息收集

v1.8
+ 131217 增加was collector支持
+ 140114 增加wsadmin脚本（从websphare中抽取，用于支持Aix下的wasadmin连接dmgr）
+ 140114 简化setup_nt.py和setup_posix.py编译配置文件

v1.7
+ 131112 分离脚本、SQL语句与程序的关系，支持程序不改动的情况下增加脚本

v1.6
* 131022 多实例切换方式错误，修改成使用编目连接方式
* 131105 db2_history仅取备份历史
* 131105 调整若干调度时间
* 131106 关闭db2diag数据收集

v1.5
* 131010 实例名称转换成大写后db2profile文件路径错误，已修复
* 131010 DB2_application的调度日期修改成周一至五下午15:00获取
* 131011 applications修改获取数据的动态视图

v1.4
* 130927 配置的实例名称和数据库名称自动转换成大写（防止大小写混用）

v1.3
* 130926 支持数据库连接重试，默认三次连接重试（连接池无效后使用常规连接。存在问题是无法释放连接池）

v1.2
+ 130923 增加db2_appl，获取sysibmadm.applications数据
+ 130923 db2_snapdbm中添加product_name，获取db2版本号

v1.1
+ 130922 支持数据版本判断
* 130922 调整部分SQL语句的兼容性

"""