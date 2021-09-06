# coding:utf-8
from flask_wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, SelectField,BooleanField
from wtforms.validators import DataRequired, Length, Email, Optional


class CommentForm(Form):
    name = StringField(u'昵称', validators=[DataRequired()])
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64),
                                           Email()])
    content = TextAreaField(u'内容', validators=[DataRequired(), Length(1, 1024)])
    follow = StringField(validators=[DataRequired()])


class CataForm(Form):
    types = SelectField(u'博文分类', coerce=int, validators=[DataRequired()])
    source = SelectField(u'博文来源', coerce=int, validators=[DataRequired()])
    order = SelectField(u'时间排序', coerce=int, validators=[DataRequired()])
    checkbox=BooleanField(u'只看我',validators=[DataRequired(), ])
    submit=SubmitField("筛选")