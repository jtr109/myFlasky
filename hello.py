# !/usr/bin/python
# -*- coding:utf-8 -*-

from flask import Flask
from flask.ext.script import Manager

app = Flask(__name__)  # 定义根目录
manager = Manager(app)  # 命令行解析功能

@app.route('/')  # 修饰视图函数、声明路由,生成映射
def index():  # 视图函数
    return '<h1>Hello world!</h1>'  # 返回响应

@app.route('/user/<name>')  # 动态路由
def user(name):
    return '<h1>Hello, %s!</h1>' % name

if __name__ == '__main__':
    manager.run()
