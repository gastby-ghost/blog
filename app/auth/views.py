# coding: utf-8
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from . import auth
from .. import db
from ..email import send_email
from ..models import User
from .forms import LoginForm, RegistrationForm, ConfirmForm


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data) and user.confirmed:
            login_user(user)
            flash(u'登陆成功！欢迎回来，%s!' % user.username, 'success')
            return redirect(request.args.get('next') or url_for('main.index'))
        else:
            flash(u'登陆失败！用户名或密码错误，请重新登陆。', 'danger')
    if form.errors:
        flash(u'登陆失败，请尝试重新登陆.', 'danger')

    return render_template('auth/login.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data.lower(),
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        confirm_num = user.generate_confirmation_num()
        send_email(user.email, '激活您的账户',
                   'auth/email/confirm', user=user, confirm_num=confirm_num)
        flash('邮件已发送到您的邮箱，需要激活后才能登录')
        db.session.commit()

        return redirect(url_for('auth.confirm', email=form.email.data.lower()))

    return render_template('auth/register.html', form=form)


@auth.route('/confirm', methods=['GET', 'POST'])
def confirm():
    form = ConfirmForm()
    if form.validate_on_submit():
        email = request.args['email']
        user = User.query.filter_by(email=email).first()
        if user.confirmed:
            return redirect(url_for('auth.login'))
        if user.confirm(form.confirm_num.data):
            flash('验证码正确,账户已激活')
            return redirect(url_for('auth.login'))
        else:
            flash('验证码错误.')

    return render_template('auth/register.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'您已退出登陆。', 'success')
    return redirect(url_for('main.index'))
