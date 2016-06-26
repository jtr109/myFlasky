# !/usr/bin/python
# -*- coding:utf-8 -*-

from flask import Flask, render_template, session, redirect, url_for, flash
from flask.ext.script import Manager, Shell
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.wtf import Form
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.mail import Mail, Message
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from datetime import datetime
import os
from threading import Thread

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)  # 定义根目录

app.config['SECRET_KEY'] = 'hard to guess string'  # app.config作为字典存储框架、扩展和程序本身的配置变量,标准字典形式
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')  # 指定数据库URI
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 587  # 465
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = 'Flasky Admin <' + app.config['MAIL_USERNAME'] + '>'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')

manager = Manager(app)  # 命令行解析功能
bootstrap = Bootstrap(app)  # 集成Bootstrap框架
moment = Moment(app)  # 渲染日期和时间
db = SQLAlchemy(app)  # 创建数据库
mail = Mail(app)  # 初始化Flask-Mail

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))  # 对应表格roles的参数

    def __repr__(self):
        return '<User %r>' % self.username

def make_shell_context():  # 在启动shell模式时预先导入app, db, User, Role
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))

def send_mail(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

'''
# The old version of form
@app.route('/',methods=['GET', 'POST'])  # 修饰视图函数、声明路由,生成映射
def index():  # 视图函数
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')  # 上一次POST保存的name
        if old_name is not None and old_name != form.name.data:  # 和此次form中提交的比较
            flash('Looks like you have changed your name!')
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('index.html',  # 返回响应
                           current_time=datetime.utcnow(),
                           form=form, name=session.get('name'))  # 变量传入模板
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()  # 取出User中username与form收到的data相同的一项
        if user is None:
            user = User(username = form.name.data)  # 创建新行
            db.session.add(user)  # 添加会话,这里的session是db的"会话"机制
            session['known'] = False  # 这里的session是Flask的请求上下文
            if app.config['FLASKY_ADMIN']:
                send_mail(app.config['FLASKY_ADMIN'], 'New User',
                          'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html',
                           form=form, name=session.get('name'),
                           known=session.get('known', False),
                           current_time=datetime.utcnow())

@app.route('/user/<name>')  # 动态路由
def user(name):
    return render_template('user.html', name=name)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    manager.run()
