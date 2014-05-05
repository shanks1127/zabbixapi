#!/usr/bin/python
###############################
# data:2014-04-23
# writer:shanks
# only for zabbix 2.0
# add/del host from zabbix
###############################
# -*- coding: UTF-8 -*-
import json
import commands
import os
import sys
import re
import MySQLdb

version='1.0'
api_url="http://192.168.122.27/api_jsonrpc.php"
#zabbix admin.for get the auth.like your login passwd.
user='Admin'
passwd='zabbix'
#zabbix server db.
username='zabbix'
password='zabbix'
hostname='localhost'
dbport=3306
dbname='zabbix'

auth_password = commands.getoutput('curl -s -X POST -H "Content-Type: application/json" -d \'{"jsonrpc": "2.0","method":"user.login","params":{"user":"%s","password":"%s"},"auth": null,"id":0}\' %s|awk -F\\" \'{print $8}\'|grep -v ^$' % (user,passwd,api_url))

def select_group_name():
    conn = MySQLdb.connect(host=hostname,user=username,db=dbname,passwd=password,port=dbport)
    cursor = conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
    cursor.execute('select name from groups')
    groupnames = cursor.fetchall()
    for group in groupnames:
        print group['name']
    cursor.close()
    conn.close()

def select_template_name():
    conn = MySQLdb.connect(host=hostname,user=username,db=dbname,passwd=password,port=dbport)
    cursor = conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
    cursor.execute('select name from hosts where status=3')
    templatenames = cursor.fetchall()
    for template in templatenames:
        print template['name']
    cursor.close() 
    conn.close()

def delete_host(iplist):
    for ip in re.split(',',iplist):
        #check ip exist?
        checkip_exist_result=commands.getoutput('curl -s -X POST -H "Content-Type: application/json" -d \'{"jsonrpc": "2.0","method":"hostinterface.exists","params":{"ip":"%s"},"auth":"%s","id":0}\' %s |grep -w ":true"|wc -l' %(ip,auth_password,api_url))
        if int(checkip_exist_result) == 1: #means it's here.
            #get hostid from table:interface 
            conn = MySQLdb.connect(host=hostname,user=username,db=dbname,passwd=password,port=dbport)
            cursor = conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
            cursor.execute('select interface.hostid,hosts.name from interface,hosts where interface.hostid=hosts.hostid and interface.ip="%s"' % ip)
            hostids = cursor.fetchall()
            for hostid in hostids:
                #now delete those host.
                delete_result=commands.getoutput('curl -s -X POST -H "Content-Type: application/json" -d \'{"jsonrpc": "2.0","method":"host.delete","params":[{"hostid":"%s"}],"auth":"%s","id":0}\' %s |grep -w "result"|wc -l'%(hostid['hostid'],auth_password,api_url))
                if int(delete_result) == 1: #means delete ok.
                    print '[OK]\t'+hostid['name']+' delete done.'
                else:
                    print '[ERROR]\t'+hostid['name']+' delete failed.'
            cursor.close()
            conn.close()
        else:
            print '[ERROR]\t'+ip+' is not here.'
    

def add_host(templatelist,grouplist,iplist):
    #check the ip exists?
    for ip in re.split(',',iplist):
        checkip_exist_result=commands.getoutput('curl -s -X POST -H "Content-Type: application/json" -d \'{"jsonrpc": "2.0","method":"hostinterface.exists","params":{"ip":"%s"},"auth":"%s","id":0}\' %s|grep -w ":true"|wc -l' %(ip,auth_password,api_url))
        if int(checkip_exist_result) == 0: #means not found this ip.
            #create host.
            #get template id and group id.
            template_id='['
            group_id='['
            for template in re.split(',',templatelist):
                #get template id from zabbix db.
                conn = MySQLdb.connect(host=hostname,user=username,db=dbname,passwd=password,port=dbport)
                cursor = conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
                cursor.execute('select hostid from hosts where host="'+template+'"')
                hostids = cursor.fetchall()
                if len(hostids) == 0:
                    show_help()
                else:
                    for templateid in hostids:
                        template_id=template_id+'{"templateid": "'+str(templateid['hostid'])+'"},'
                cursor.close()
                conn.close()
            template_id=template_id[:-1]+']'
            for group in re.split(',',grouplist):
                #get group id from zabbix db.
                conn = MySQLdb.connect(host=hostname,user=username,db=dbname,passwd=password,port=dbport)
                cursor = conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
                cursor.execute('select groupid from groups where name="'+group+'"')
                groupids = cursor.fetchall()
                if len(groupids) == 0:
                    show_help()
                else:
                    for groupid in groupids:
                        group_id=group_id+'{"groupid": "'+str(groupid['groupid'])+'"},'
                cursor.close()
                conn.close()
            group_id=group_id[:-1]+']'
            create_host_result=commands.getoutput('curl -s -X POST -H "Content-Type: application/json" -d \'{"jsonrpc": "2.0","method":"host.create","params":{"host":"'+ip+'","interfaces":[{"type":1,"main":1,"useip":1,"ip":"'+ip+'","dns":"","port":"10050"}],"groups":'+group_id+',"templates":'+template_id+'},"auth":"'+auth_password+'","id":0}\' '+api_url+' |grep -w ":result"|wc -l')
            if int(create_host_result) == 1: #means create ok.
                print '[OK]\t'+ip+" create done."
            else:
                print '[ERROR]\t'+ip+" create failed."
        else:
            print '[ERROR]\t'+ip+" is exist,please check it."
    
def clone_host(cloneip,iplist):
    #check cloneip exist.and if one ip have many host,all host config will copy.
    check_cloneip_result=commands.getoutput('curl -s -X POST -H "Content-Type: application/json" -d \'{"jsonrpc": "2.0","method":"hostinterface.exists","params":{"ip": "'+cloneip+'"},"auth": "'+auth_password+'","id":0}\' '+api_url+' |grep -w ":true"|wc -l')
    if int(check_cloneip_result) != 1: #means cloneip is not exist.
        print '[ERROR] '+cloneip+' is not found!!!'
        sys.exit(0)
    for ip in re.split(',',iplist):
        #check the ip exist.if exist,continue.
        check_ip_result=commands.getoutput('curl -s -X POST -H "Content-Type: application/json" -d \'{"jsonrpc": "2.0","method":"hostinterface.exists","params":{"ip": "'+ip+'"},"auth": "'+auth_password+'","id":0}\' '+api_url+' |grep -w ":true"|wc -l')
        if int(check_ip_result) == 1: #means exist.
            print '[WARNING] '+ip+' is exist.'
            continue
        all_groupid='['
        all_templateid='['
        #get group/template
        conn = MySQLdb.connect(host=hostname,user=username,db=dbname,passwd=password,port=dbport)
        cursor_group = conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
        cursor_group.execute('select groupid from hosts_groups,interface where interface.ip="'+cloneip+'" and interface.hostid=hosts_groups.hostid')
        groupids = cursor_group.fetchall()
        for group_id in groupids:
            all_groupid=all_groupid+'{"groupid": "'+str(group_id['groupid'])+'"},'
        all_groupid=all_groupid[:-1]+']'
        cursor_group.close()
        cursor_template = conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
        cursor_template.execute('select templateid from hosts_templates,interface where interface.ip="'+cloneip+'" and interface.hostid=hosts_templates.hostid')
        templateids = cursor_template.fetchall()
        for template_id in templateids:
            all_templateid=all_templateid+'{"templateid": "'+str(template_id['templateid'])+'"},'
        all_templateid=all_templateid[:-1]+']'
        cursor_template.close()
        conn.close()
        clone_ip_result=commands.getoutput('curl -s -X POST -H "Content-Type: application/json" -d \'{"jsonrpc": "2.0","method":"host.create","params": {"host": "'+ip+'","interfaces": [{"type": 1,"main": 1,"useip": 1,"ip": "'+ip+'","dns": "","port": "10050"}],"groups": '+all_groupid+',"templates": '+all_templateid+'},"auth": "'+auth_password+'","id":0}\' '+api_url+'|grep -w "result"|wc -l')
        if int(clone_ip_result) == 1: #means clone ok.
            print '[OK]\t'+ip+' clone done.'
        else:
            print '[ERROR]\t'+ip+ ' clone failed.'


def show_help():
    print '''
    HELP:
    usage: %s [options]

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

    ''' %(sys.argv[0])
    sys.exit(0)


def main_():
    if len(sys.argv) < 2:
        show_help()
    elif sys.argv[1] == '-h':
        show_help()
    elif sys.argv[1] == '-V':
        print version
    elif sys.argv[1] == '-G':
        select_group_name()
    elif sys.argv[1] == '-T':
        select_template_name()
    elif sys.argv[1] == '-C':
        if len(sys.argv) == 4:
            clone_host(sys.argv[2],sys.argv[3])
        else:
            show_help()
    elif sys.argv[1] == '-D':
        if len(sys.argv) == 3:
            delete_host(sys.argv[2])
        else:
            show_help()
    elif sys.argv[1] == '-A':
        if len(sys.argv) == 5:
            add_host(sys.argv[2],sys.argv[3],sys.argv[4])
        else:
            show_help()
    else:
        show_help()

main_()
