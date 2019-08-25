# -*- coding: utf-8 -*-
__author__ = 'JUN SHANG'
from SFTP.server.db.user_handle import UserHandle
from SFTP.server.core.server import SftpServer


class Manage():
    def __init__(self):
        pass

    def start_sftp(self):
        server = SftpServer()
        server.run()
        server.close()

    def create_user(self):
        """创建用户（create user）"""
        username = input('用户名>>>').strip()
        UserHandle(username).add_user()

    def exit_func(self):
        exit('用户退出')

    def run(self):
        msg = '''\033[31;0m
                1.启动ftp服务器
                2.创建用户
                3.退出\033[0m\n
                '''
        msg_dic = {'1': 'start_sftp', '2': 'create_user', '3': 'exit_func'}
        while True:
            print(msg)
            num = input('选择>>>').strip()
            if num in msg_dic:
                getattr(self, msg_dic[num])()
            else:
                print('\033[1;31m请重新选择\033[0m')
