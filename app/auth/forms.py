# coding: utf-8
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError
from ..models import User


class LoginForm(Form):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64),
                                           Email()])
    password = PasswordField(u'密码', validators=[DataRequired()])

class ConfirmForm(Form):
    confirm_num = StringField(u'四位验证码', validators=[DataRequired(),Length(4)])
    submit = SubmitField('确定')


class RegistrationForm(Form):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                          Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               '用户名只能由字母，数字和下划线组成')])
    password = PasswordField('密码', validators=[
        DataRequired(), EqualTo('password2', message='密码不匹配.')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('邮箱已经被注册.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已经被使用.')

    class ChangePasswordForm(Form):
        old_password = PasswordField('原密码', validators=[DataRequired()])
        password = PasswordField('新密码', validators=[
            DataRequired(), EqualTo('password2', message='密码不匹配.')])
        password2 = PasswordField('确认密码',
                                  validators=[DataRequired()])
        submit = SubmitField('确认更新密码')

    class PasswordResetRequestForm(Form):
        email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                              Email()])
        submit = SubmitField('重设密码')

    class PasswordResetForm(Form):
        password = PasswordField('新密码', validators=[
            DataRequired(), EqualTo('password2', message='密码不匹配')])
        password2 = PasswordField('确认密码', validators=[DataRequired()])
        submit = SubmitField('重设密码')

    class ChangeEmailForm(Form):
        email = StringField('新邮箱', validators=[DataRequired(), Length(1, 64),
                                               Email()])
        password = PasswordField('密码', validators=[DataRequired()])
        submit = SubmitField('更新邮箱')

        def validate_email(self, field):
            if User.query.filter_by(email=field.data.lower()).first():
                raise ValidationError('邮箱已注册.')
