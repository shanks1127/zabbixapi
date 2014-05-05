zabbixapi
=========
1、下载脚本
2、编辑脚本，修改17~26行的配置
3、执行

    HELP:
    usage: ./zabbix_api.py [options]

    optional arguments:
        -h
            Show this help message and exit.
        -C [clone source] [host list]
            Cloning way to add a host based on existing machines, multiple machines separated by commas.
            !!!Just clone group&template!!!
            exp:  ./zabbix_api.py -C 192.168.122.1 192.168.122.100,192.168.122.101
        -A [template list] [group list] [ip list]
            Add machines,and set group,template; multiple machines,multiple group,multiple template separated by commas.
            exp:  ./zabbix_api.py -A "template_linux" "group_zabbix_server" 192.168.122.100,192.168.122.101
            exp:  ./zabbix_api.py -A "template_linux,template_lvs" "group_zabbix_server,geoup_lvs_server" 192.168.122.100,192.168.122.101
        -T
            Show you all the template name.
        -G
            Show you all the group name.
        -D [ip list]
            Delete machine from zabbix,multiple machines separated by commas.
            exp:  ./zabbix_api.py -D 192.168.122.100,192.168.122.101
        -V
            Show this program's version.
			
所有操作都是支持批量的
-h：显示帮助
-C：根据现有的机器克隆，克隆后，所有的iplist中的主机都会根据前面的机器克隆，目前版本克隆时只克隆group和template。interface部分采用默认配置。
	interface默认配置："interfaces":[{"type":1,"main":1,"useip":1,"ip":"'+ip+'","dns":"","port":"10050"}]
-A：添加主机，添加之后，host、name都是和ip一样
-T：显示所有可用的模板
-G：显示所有主机组
-D：删除ip，如果存在一个ip对用多个host的情况，都会删除
-V：显示版本

这里所有的添加也好，克隆也好，ip、host、name都一样,采用的都是ip
最后温馨提示：妥善保管，权限甚大。
