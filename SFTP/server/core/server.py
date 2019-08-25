# -*- coding: utf-8 -*-
__author__ = 'JUN SHANG'
import os
import hashlib
import socket
import pickle
import queue
from threading import Thread
from SFTP.server.conf import settings
from SFTP.server.db.user_handle import UserHandle


class SftpServer():
    MAX_SOCKET_LISTEN = 5
    MAX_RECV_SIZE = 1024

    def __init__(self):
        self.socket = socket.socket()
        self.socket.bind((settings.HOST, settings.PORT))
        self.socket.listen(self.MAX_SOCKET_LISTEN)
        self.q = queue.Queue(settings.MAX_concurrent_COUNT)

    def run(self):
        self.server_accept()

    def server_accept(self):
        """等待连接"""
        while True:
            self.conn, self.addr = self.socket.accept()
            try:
                t = Thread(target=self.server_handle, args=(self.conn,))
                self.q.put(t)
                t.start()
            except Exception as e:
                print(e)
                self.conn.close()
                self.q.get()

    def server_handle(self, conn):
        """处理与用户的交互"""
        if self.auth():
            print('用户登录成功')
            while True:
                try:
                    user_input = self.conn.recv(self.MAX_RECV_SIZE).decode()
                    self.cmds = user_input.split()
                    if hasattr(self, self.cmds[0]):
                        getattr(self, self.cmds[0])()
                    else:
                        print('\033[1;31m请用户重复输入\033[0m')
                except Exception as e:
                    break

    def ls(self):
        if len(self.cmds) == 1:
            sub = os.listdir(os.getcwd())
            print(sub, '当前目录下文件列表')
            self.conn.send(pickle.dumps(sub))

    def mkdir(self):
        """在当前目录下，增加目录"""
        if len(self.cmds) == 2:
            mkdir_path = os.path.join(os.getcwd(), self.cmds[1])
            if not os.path.exists(mkdir_path):
                os.makedirs(mkdir_path)
                print('ok')
                self.conn.send('1'.encode())
            else:
                print('目录已经存在')
                self.conn.send('0'.encode())
        else:
            print('用户没有')

    def cd(self):
        """切换目录"""
        if len(self.cmds) == 2:
            dir_path = os.path.join(os.getcwd(), self.cmds[1])
            if os.path.exists(dir_path):
                if self.homedir_path in dir_path:
                    os.chdir(dir_path)
                    self.conn.send('1'.encode())
                    print('切换成功')
                else:
                    print('切换失败')
                    self.conn.send('0'.encode())
            else:
                print('要切换的目录不在这个目录之下')
                self.conn.send('0'.encode())
        else:
            print('请输入有效的命令')

    def remove(self):
        """删除指定的文件,或者空文件夹"""
        if len(self.cmds) == 2:
            file_name = self.cmds[1]
            file_path = '%s\%s' % (os.getcwd(), file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
                self.conn.send('1'.encode())
            elif os.path.isdir(file_path):  # 删除空目录
                if not len(os.listdir(file_path)):
                    os.removedirs(file_path)
                    print('删除成功')
                    self.conn.send('2'.encode())
                else:
                    print('文件夹非空，不能删除')
                    self.conn.send('3'.encode())
            else:
                print('不是文件也不是文件夹')
                self.conn.send('0'.encode())
        else:
            print('没有输入要删除的文件')

    def auth(self):
        """
        进行用户认证，看是否存在这个用户

        认证成功后，将程序切换到用户目录
        返回详细的用户信息
        """
        while True:
            user_dict = self.get_recv()
            username = user_dict.get('username')
            user_handle = UserHandle(username)
            user_data = user_handle.judge_user()
            # 判断用户是否存在，并且返回列表
            if user_data:
                if user_data[0][1] == hashlib.md5(user_dict.get('password').encode()).hexdigest():
                    self.conn.send('1'.encode())
                    print('ok', self.conn.recv(self.MAX_RECV_SIZE), user_data[1][1])
                    self.username = username
                    self.homedir_path = '%s\%s\%s' % (settings.BASE_DIR, 'home', self.username)
                    print(user_data[1][1])
                    os.chdir(self.homedir_path)  # 将程序运行的目录名修改到用户home目录下
                    self.quota_bytes = int(user_data[2][1]) * 1024 * 1024
                    user_info_dict = {'username': username, 'homedir': user_data[1][1], 'quota': user_data[2][1]}
                    self.conn.send(pickle.dumps(user_info_dict))  # 将详细用户数据发送到客服端
                    return True
                else:
                    self.conn.send('0'.encode())
            else:
                self.conn.send('0'.encode())

    def get_recv(self):
        """接受client发来的数据"""
        return pickle.loads(self.conn.recv(self.MAX_RECV_SIZE))

    def send_file(self, *args, **kwargs):
        return self.conn.send(*args, **kwargs)

    def getfile_md5(self):
        """对文件内容md5"""
        return hashlib.md5(self.readfile()).hexdigest()

    def readfile(self):
        """读取文件"""
        with open(self.filepath, 'rb') as f:
            filedata = f.read()
        return filedata

    def get(self):
        """从服务端下载到客户端"""
        # if len(self.cmds) == 2:
        #     filename = self.cmds[1]
        #     self.filepath = os.path.join(os.getcwd(), filename)  # os.getcwd()得到当前工作目录
        #     if os.path.isfile(self.filepath):
        #         # 如果存在这个文件
        #         self.conn.send('1'.encode())
        #         existing_file_size = self.conn.recv(self.MAX_RECV_SIZE).decode()
        #         header_dic = {
        #             'filename': filename,
        #             'file_md5': self.getfile_md5(),
        #             'file_size': os.path.getsize(self.filepath)
        #         }
        #         self.send_file(pickle.dumps(header_dic))
        #         if int(existing_file_size) == os.path.getsize(self.filepath):
        #             print('\033[1;32m文件已存在\033[0m')
        #         else:
        #             print('\033[1;33m正在进行断点续传...\033[0m')
        #             print(self.filepath, '文件地址')
        #             with open(self.filepath, 'rb') as f:
        #                 f.seek(int(existing_file_size), 0)
        #                 for line in f:
        #                     self.conn.send(line)
        #     else:
        #         print('输入这个目录下没有这个文件')
        #         self.conn.send('0'.encode())
        # else:
        #     print('\033[1;32m输入有效命令\033[0m')
        if len(self.cmds) == 2:
            filename = self.cmds[1]
            self.filepath = os.path.join(os.getcwd(), filename)  # os.getcwd()得到当前工作目录
            if os.path.isfile(self.filepath):
                # 如果存在这个文件
                header_dic = {
                    'file_md5': self.getfile_md5(),
                    'file_size': os.path.getsize(self.filepath)
                }
                self.send_file(pickle.dumps(header_dic))
                existing_file_size = self.conn.recv(self.MAX_RECV_SIZE).decode()
                if int(existing_file_size) == os.path.getsize(self.filepath):
                    print('\033[1;32m文件已存在\033[0m')
                else:
                    print('\033[1;33m正在进行断点续传...\033[0m')
                    print(self.filepath, '文件地址')
                    with open(self.filepath, 'rb') as f:
                        f.seek(int(existing_file_size), 0)
                        for line in f:
                            self.conn.send(line)
            else:
                print('输入这个目录下没有这个文件')
                header_dic = ''
                self.send_file(pickle.dumps(header_dic))
        else:
            print('\033[1;32m输入有效命令\033[0m')

    def put(self):
        """从客户端上传文件到服务端"""
        if len(self.cmds) == 2:
            filename = self.cmds[1]
            self.filepath = os.path.join(os.getcwd(), filename)
            if os.path.isfile(self.filepath):
                # 如果文件存在，支持断点续传
                print('\033[1;33m正在进行断点续传...\033[0m')
                existing_file_size = os.path.getsize(self.filepath )
                self.send_file(pickle.dumps(existing_file_size))
            else:
                existing_file_size = 0
                print('\033[1;33m正在进行文件传输...\033[0m')
                self.send_file(pickle.dumps(existing_file_size))

            header_dic = self.get_recv()
            if header_dic:
                file_size = header_dic.get('file_size')
                file_md5 = header_dic.get('file_md5')
                print(file_size,file_md5)

                if existing_file_size == file_size:
                    print('\033[1;32m文件已存在\033[0m')
                else:
                    with open(self.filepath , 'ab') as f:
                        f.seek(existing_file_size, 0)
                        get_size = existing_file_size
                        while get_size < file_size:
                            file_bytes = self.conn.recv(self.MAX_RECV_SIZE)
                            f.write(file_bytes)
                            get_size += len(file_bytes)
                            print(get_size,file_size)
                        print('ok')

                    if self.getfile_md5() == file_md5:
                        print('\n\033[1;32m下载成功\033[0m')
                    else:
                        print('\n\033[1;32m下载文件大小与源文件大小不一致，请重新下载，将会支持断点续传\033[0m')
            else:
                print('客户端没有这个文件')
        else:
            print('\033[1;32m输入有效命令\033[0m')
