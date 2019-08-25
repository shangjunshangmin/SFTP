# -*- coding: utf-8 -*-
__author__ = 'JUN SHANG'
import configparser
import hashlib
import os
from SFTP.server.conf import settings


class UserHandle():
    def __init__(self, username):
        self.username = username
        self.config = configparser.ConfigParser()
        if not os.path.isfile(settings.ACCOUNT_FILE):
            self.config.write((open(settings.ACCOUNT_FILE, "w")))
        self.config.read(settings.ACCOUNT_FILE)

    @property
    def create_password(self):
        """创建密码"""
        return hashlib.md5('123'.encode()).hexdigest()

    @property
    def quota(self):
        """生成每个用户的磁盘配额"""
        quota = input('输入用户的磁盘配额大小>>>').strip()
        if quota.isdigit() and int(quota) > 0:
            return quota
        else:
            exit('\033[1;31m磁盘配额须是整数\033[0m')

    def add_user(self):
        """创建用户，存到accounts.ini"""
        if not self.config.has_section(self.username):
            self.config.add_section(self.username)
            self.config.set(self.username, 'password', self.create_password)
            self.config.set(self.username, 'homedir',settings.BASE_DIR+'/home/' + self.username)
            self.config.set(self.username, 'quota', self.quota)
            self.config.write((open(settings.ACCOUNT_FILE, "w")))
            os.mkdir(os.path.join(settings.BASE_DIR, 'home', self.username))
            print('\033[1;32m创建用户成功\033[0m')
        else:
            print('\033[1;32m用户已经存在\033[0m')

    def judge_user(self):
        """判断用户是否存在"""
        if self.config.has_section(self.username):
            return self.config.items(self.username)

