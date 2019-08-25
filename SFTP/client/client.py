# -*- coding: utf-8 -*-
__author__ = 'JUN SHANG'
import os
import socket
import hashlib
import pickle
import sys


class FtpClient():
    HOST = "127.0.0.1"  #
    PORT = 22
    MAX_RECV_SIZE = 1024
    DOWMLOAD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'download')
    UPLOAD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'upload')

    def __init__(self):
        self.socket = socket.socket()
        self.connect()

    def connect(self):
        """连接服务端"""
        self.socket.connect((self.HOST, self.PORT))

    def interactive(self):
        """与服务端进行交互"""
        if self.auth():
            while True:
                try:
                    print("""\033[1;31m
                            ls 查看当前文件
                            cd 切换目录
                            mkdir 增加目录
                            remove 删除文件
                            get 从服务端下载文件到客服端
                            put 从客服端上传文件到服务端
                            \033[0m
                            
                            """)
                    user_input = input('[%s]>>>:' % self.username)
                    self.cmds = user_input.split()
                    if not user_input: continue
                    if hasattr(self, self.cmds[0]):
                        # print('接受')
                        self.socket.send(user_input.encode())
                        getattr(self, self.cmds[0])()
                    else:
                        print('请重新输入')
                except Exception as e:
                    print(e)
                    break

    def auth(self):
        """进行用户认证"""
        count = 0
        while count < 3:
            name = input("username>>>:").strip()
            password = input('password>>>:').strip()
            if not name or not password:
                continue
            user_dict = {'username': name, 'password': password}
            self.socket.send(pickle.dumps(user_dict))
            res = self.socket.recv(self.MAX_RECV_SIZE).decode()
            if res == '1':
                self.socket.send('1'.encode())
                print('welcome'.center(20, '-'))
                user_info_dict = self.get_recv()
                self.username = user_info_dict.get('username')
                print(user_info_dict)
                return True
            else:
                print('\033[1;31m用户名或密码不对!\033[0m')
            count += 1

    def get_recv(self):
        """获取服务端返回的数据"""
        return pickle.loads(self.socket.recv(self.MAX_RECV_SIZE))

    def ls(self):
        """查询当前目录下，文件列表"""
        if len(self.cmds) == 1:
            dir_file = self.get_recv()
            if dir_file:
                print(dir_file)
            else:
                print('\033[1;31m查看目录失败\033[0m')
        else:
            print('\033[1;32m请输入有效的命令：ls\033[0m')

    def mkdir(self):
        """增加目录"""
        if len(self.cmds) == 2:
            res = self.socket.recv(self.MAX_RECV_SIZE).decode()
            if res == '1':
                print('\033[1;32m增加目录成功\033[0m')
            else:
                print('\033[1;31m目录已经存在\033[0m')
        else:
            print('\033[1;32m输入有效命令\033[0m')

    def cd(self):
        """切换目录"""
        if len(self.cmds) == 2:
            res = self.socket.recv(self.MAX_RECV_SIZE).decode()
            if res == '1':
                print('\033[1;32m切换目录成功\033[0m')
            else:
                print('\033[1;31m切换目录失败\033[0m')
        else:
            print('\033[1;32m输入有效命令\033[0m')

    def remove(self):
        """删除指定文件或者文件夹"""
        if len(self.cmds) == 2:
            res = self.socket.recv(self.MAX_RECV_SIZE)
            if res == '0':
                print('\033[1;32m命令错误，既不是文件夹也不是文件\033[0m')
            if res == '1':
                print('\033[1;32m删除文件成功\033[0m')
            if res == '2':
                print('\033[1;31m删除目录成功\033[0m')
            if res == '3':
                print('\033[1;31m文件夹非空，不能删除\033[0m')

        else:
            print('\033[1;32m输入有效命令\033[0m')

    def readfile(self):
        """读取文件"""
        with open(self.file_path, 'rb') as f:
            filedata = f.read()
        return filedata

    def progress_bar(self, num, get_size, file_size):
        """进度条显示"""
        float_rate = get_size / file_size
        rate = round(float_rate * 100, 2)  # 95.85%

        if num == 1:  # 1表示下载
            sys.stdout.write('\r已下载:\033[1;32m{0}%\033[0m'.format(rate))
        elif num == 2:  # 2 表示上传
            sys.stdout.write('\r已上传:\033[1;32m{0}%\033[0m'.format(rate))
        sys.stdout.flush()

    def get_file_md5(self):
        """对文件进行md5"""
        return hashlib.md5(self.readfile()).hexdigest()

    def send_file(self, *args, **kwargs):
        return self.socket.send(*args, **kwargs)

    def get(self):
        """从服务端下载文件到客户端"""
        if len(self.cmds) == 2:
            filename = self.cmds[1]
            self.file_path = os.path.join(self.DOWMLOAD_PATH, filename)
            header_dic = self.get_recv()
            # print(header_dic)
            if header_dic:
                file_size = header_dic.get('file_size')
                file_md5 = header_dic.get('file_md5')
                if os.path.isfile(self.file_path):
                    # 如果文件存在，支持断点续传
                    existing_file_size = os.path.getsize(self.file_path)
                else:
                    existing_file_size = 0
                self.socket.send(str(existing_file_size).encode())
                if existing_file_size == file_size:
                    print('\033[1;32m文件已存在\033[0m')
                else:
                    if existing_file_size > 0:
                        print('\033[1;33m正在进行断点续传...\033[0m')
                    else:
                        print('\033[1;33m正在进行文件传输...\033[0m')
                    with open(self.file_path, 'ab') as f:
                        f.seek(existing_file_size, 0)
                        get_size = existing_file_size
                        while get_size < file_size:
                            file_bytes = self.socket.recv(self.MAX_RECV_SIZE)
                            f.write(file_bytes)
                            get_size += len(file_bytes)
                            self.progress_bar(1, get_size, file_size)  # 1表示下载
                    if self.get_file_md5() == file_md5:
                        print('\n\033[1;32m下载成功\033[0m')
                    else:
                        print('\n\033[1;32m下载文件大小与源文件大小不一致，请重新下载，将会支持断点续传\033[0m')
            else:
                print('服务端没有文件')

        else:
            print('\033[1;32m输入有效命令\033[0m')

    def put(self):
        """从客户端上传文件到服务端"""
        if len(self.cmds) == 2:
            filename = self.cmds[1]
            self.file_path = os.path.join(self.UPLOAD_PATH, filename)  # os.getcwd()得到当前工作目录
            existing_file_size = self.get_recv()

            if os.path.isfile(self.file_path):
                # 如果存在这个文件
                file_size = os.path.getsize(self.file_path)
                header_dic = {
                    'file_md5': self.get_file_md5(),
                    'file_size': file_size
                }
                self.send_file(pickle.dumps(header_dic))
                if existing_file_size == file_size:
                    print('\033[1;32m文件已存在\033[0m')
                else:
                    if existing_file_size > 0:
                        print('\033[1;33m正在进行断点续传...\033[0m')
                    else:
                        print('\033[1;33m进行文件传输...\033[0m')
                    with open(self.file_path, 'rb') as f:
                        f.seek(existing_file_size, 0)
                        get_size = existing_file_size
                        for line in f:
                            self.socket.send(line)
                            get_size += len(line)
                            self.progress_bar(2, get_size, file_size)  # 1表示下载
                            print('总大小:%s已下载:%s' % (file_size, get_size))

            else:
                print('输入这个目录下没有这个文件,请重新选择')
                header_dic = ''
                self.send_file(pickle.dumps(header_dic))
        else:
            print('\033[1;32m输入有效命令\033[0m')


if __name__ == '__main__':
    ftp_client = FtpClient()
    ftp_client.interactive()
    ftp_client.socket.close()
