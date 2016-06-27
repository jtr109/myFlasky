# !/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from flask import render_template, session, redirect, url_for, current_app

from . import main
from .forms import NameForm
from .. import db
from ..models import User
from ..email import send_email

@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()  # 取出User中username与form收到的data相同的一项
        if user is None:
            user = User(username=form.name.data)  # 创建新行
            db.session.add(user)  # 添加会话,这里的session是db的"会话"机制
            session['known'] = False  # 这里的session是Flask的请求上下文
            if current_app.config['FLASKY_ADMIN']:
                send_email(current_app.config['FLASKY_ADMIN'], 'New User',
                          'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('.index'))
    return render_template('index.html',
                           form=form, name=session.get('name'),
                           known=session.get('known', False),
                           current_time=datetime.utcnow())