# coding: utf-8
import hashlib
import random
import string
from datetime import datetime

from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager

article_types = {u'开发语言': ['Python', 'Java', 'JavaScript'],
                 'Linux': [u'Linux成长之路', u'Linux运维实战', 'CentOS', 'Ubuntu'],
                 u'网络技术': [u'思科网络技术', u'其它'],
                 u'数据库': ['MySQL', 'Redis'],
                 u'爱生活，爱自己': [u'生活那些事', u'学校那些事', u'感情那些事'],
                 u'Web开发': ['Flask', 'Django'], }


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    avatar_hash = db.Column(db.String(32))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64), default="匿名")
    location = db.Column(db.String(64), default="CHINA")
    about_me = db.Column(db.Text(), default="待定")
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    confirm_num = db.Column(db.String(64), default="asfhafgsg")
    articles = db.relationship('Article', backref='user', lazy='dynamic')

    @staticmethod
    def insert_admin(email, username, password):
        user = User(email=email, username=username, password=password)
        db.session.add(user)
        db.session.commit()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    # gravater头像网站，和邮箱进行唯一匹配
    def gravatar(self, size=40, default='identicon', rating='g'):
        # if request.is_secure:
        #     url = 'https://secure.gravatar.com/avatar'
        # else:
        #     url = 'http://www.gravatar.com/avatar'
        url = 'https://gravatar.loli.net/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def generate_confirmation_num(self):
        seeds = string.digits
        random_str = random.sample(seeds, k=4)
        self.confirm_num = "".join(random_str)
        db.session.commit()
        return self.confirm_num

    def confirm(self, confirm_num):
        if confirm_num == self.confirm_num:
            self.confirmed = True
            db.session.commit()
            return True
        else:
            return False

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.username


# callback function for flask-login extentsion
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Menu(db.Model):
    __tablename__ = 'menus'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    types = db.relationship('ArticleType', backref='menu', lazy='dynamic')
    order = db.Column(db.Integer, default=0, nullable=False)

    def sort_delete(self):
        for menu in Menu.query.order_by(Menu.order).offset(self.order).all():
            menu.order -= 1
            db.session.add(menu)

    @staticmethod
    def insert_menus():
        menus = [u'目录', u'工具', u'留言', u'关于我']
        for name in menus:
            menu = Menu(name=name)
            db.session.add(menu)
            db.session.commit()
            menu.order = menu.id
            db.session.add(menu)
            db.session.commit()

    @staticmethod
    def return_menus():
        menus = [(m.id, m.name) for m in Menu.query.all()]
        menus.append((-1, u'不选择导航（该分类将单独成一导航）'))
        return menus

    def __repr__(self):
        return '<Menu %r>' % self.name


class ArticleTypeSetting(db.Model):
    __tablename__ = 'articleTypeSettings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    protected = db.Column(db.Boolean, default=False)
    hide = db.Column(db.Boolean, default=False)
    types = db.relationship('ArticleType', backref='setting', lazy='dynamic')

    @staticmethod
    def insert_system_setting():
        system = ArticleTypeSetting(name='system', protected=True, hide=True)
        db.session.add(system)
        db.session.commit()

    @staticmethod
    def insert_default_settings():
        system_setting = ArticleTypeSetting(name='system', protected=True, hide=True)
        common_setting = ArticleTypeSetting(name='common', protected=False, hide=False)
        db.session.add(system_setting)
        db.session.add(common_setting)
        db.session.commit()

    @staticmethod
    def return_setting_hide():
        return [(2, u'公开'), (1, u'隐藏')]

    def __repr__(self):
        return '<ArticleTypeSetting %r>' % self.name


class ArticleType(db.Model):
    __tablename__ = 'articleTypes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    introduction = db.Column(db.Text, default=None)
    articles = db.relationship('Article', backref='articleType', lazy='dynamic')
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), default=None)
    setting_id = db.Column(db.Integer, db.ForeignKey('articleTypeSettings.id'))

    @staticmethod
    def insert_system_articleType():
        articleType = ArticleType(name=u'未分类',
                                  introduction=u'系统默认分类，不可删除。',
                                  setting=ArticleTypeSetting.query.filter_by(protected=True).first()
                                  )
        db.session.add(articleType)
        db.session.commit()

    @staticmethod
    def insert_articleTypes():
        articleTypes = ['Python', 'Java', 'JavaScript', 'Django',
                        'CentOS', 'Ubuntu', 'MySQL', 'Redis',
                        u'Linux成长之路', u'Linux运维实战', u'其它',
                        u'思科网络技术', u'生活那些事', u'学校那些事',
                        u'感情那些事', 'Flask']
        for name in articleTypes:
            articleType = ArticleType(name=name,
                                      setting=ArticleTypeSetting(name=name))
            db.session.add(articleType)
        db.session.commit()

    @property
    def is_protected(self):
        if self.setting:
            return self.setting.protected
        else:
            return False

    @property
    def is_hide(self):
        if self.setting:
            return self.setting.hide
        else:
            return False

    # if the articleType does not have setting,
    # its is_hie and is_protected property will be False.

    def __repr__(self):
        return '<Type %r>' % self.name


class Source(db.Model):
    __tablename__ = 'sources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    articles = db.relationship('Article', backref='source', lazy='dynamic')

    @staticmethod
    def insert_sources():
        sources = (u'原创',
                   u'转载',
                   u'翻译')
        for s in sources:
            source = Source.query.filter_by(name=s).first()
            if source is None:
                source = Source(name=s)
            db.session.add(source)
        db.session.commit()

    def __repr__(self):
        return '<Source %r>' % self.name


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('comments.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('comments.id'),
                            primary_key=True)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    author_name = db.Column(db.String(64))
    author_email = db.Column(db.String(64))
    avatar_hash = db.Column(db.String(32))
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
    disabled = db.Column(db.Boolean, default=False)
    comment_type = db.Column(db.String(64), default='comment')
    reply_to = db.Column(db.String(128), default='notReply')

    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(Comment, self).__init__(**kwargs)
        if self.author_email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.author_email.encode('utf-8')).hexdigest()

    def gravatar(self, size=40, default='identicon', rating='g'):
        # if request.is_secure:
        #     url = 'https://secure.gravatar.com/avatar'
        # else:
        #     url = 'http://www.gravatar.com/avatar'
        url = 'https://gravatar.loli.net/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.author_email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        article_count = Article.query.count()
        for i in range(count):
            a = Article.query.offset(randint(0, article_count - 1)).first()
            c = Comment(content=forgery_py.lorem_ipsum.sentences(randint(3, 5)),
                        timestamp=forgery_py.date.date(True),
                        author_name=forgery_py.internet.user_name(True),
                        author_email=forgery_py.internet.email_address(),
                        article=a)
            db.session.add(c)
        try:
            db.session.commit()
        except:
            db.session.rollback()

    @staticmethod
    def generate_fake_replies(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        comment_count = Comment.query.count()
        for i in range(count):
            followed = Comment.query.offset(randint(0, comment_count - 1)).first()
            c = Comment(content=forgery_py.lorem_ipsum.sentences(randint(3, 5)),
                        timestamp=forgery_py.date.date(True),
                        author_name=forgery_py.internet.user_name(True),
                        author_email=forgery_py.internet.email_address(),
                        article=followed.article, comment_type='reply',
                        reply_to=followed.author_name)
            f = Follow(follower=c, followed=followed)
            db.session.add(f)
            db.session.commit()

    def is_reply(self):
        if self.followed.count() == 0:
            return False
        else:
            return True

    # to confirm whether the comment is a reply or not

    def followed_name(self):
        if self.is_reply():
            return self.followed.first().followed.author_name


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True)
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    create_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    num_of_view = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    articleType_id = db.Column(db.Integer, db.ForeignKey('articleTypes.id'))
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id'))
    comments = db.relationship('Comment', backref='article', lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        import forgery_py

        seed()
        articleType_count = ArticleType.query.count()
        source_count = Source.query.count()
        user_count = User.query.count()
        if user_count>0:
            for i in range(count):
                aT = ArticleType.query.offset(randint(0, articleType_count - 1)).first()
                s = Source.query.offset(randint(0, source_count - 1)).first()
                au = User.query.offset(randint(0, user_count - 1)).first()
                a = Article(title=forgery_py.lorem_ipsum.title(randint(3, 5)),
                            content=forgery_py.lorem_ipsum.sentences(randint(15, 35)),
                            summary=forgery_py.lorem_ipsum.sentences(randint(2, 5)),
                            num_of_view=randint(100, 15000),
                            articleType=aT, source=s,user=au)
                db.session.add(a)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()

    @staticmethod
    def add_view(article, db):
        article.num_of_view += 1
        db.session.add(article)
        db.session.commit()

    def __repr__(self):
        return '<Article %r>' % self.title


class BlogInfo(db.Model):
    __tablename__ = 'blog_info'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    signature = db.Column(db.Text)
    navbar = db.Column(db.String(64))

    @staticmethod
    def insert_blog_info():
        blog_mini_info = BlogInfo(title=u'半亩方塘一鉴开',
                                  signature=u'这里不仅有专业知识，还有解决方案',
                                  navbar='inverse')
        db.session.add(blog_mini_info)
        db.session.commit()


class Plugin(db.Model):
    __tablename__ = 'plugins'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True)
    note = db.Column(db.Text, default='')
    content = db.Column(db.Text, default='')
    order = db.Column(db.Integer, default=0)
    disabled = db.Column(db.Boolean, default=False)

    @staticmethod
    def insert_system_plugin():
        plugin = Plugin(title=u'博客统计',
                        note=u'系统插件',
                        content='system_plugin',
                        order=1)
        db.session.add(plugin)
        db.session.commit()

    def sort_delete(self):
        for plugin in Plugin.query.order_by(Plugin.order.asc()).offset(self.order).all():
            plugin.order -= 1
            db.session.add(plugin)

    def __repr__(self):
        return '<Plugin %r>' % self.title


class BlogView(db.Model):
    __tablename__ = 'blog_view'
    id = db.Column(db.Integer, primary_key=True)
    num_of_view = db.Column(db.BigInteger, default=0)

    @staticmethod
    def insert_view():
        view = BlogView(num_of_view=0)
        db.session.add(view)
        db.session.commit()

    @staticmethod
    def add_view(db):
        view = BlogView.query.first()
        view.num_of_view += 1
        db.session.add(view)
        db.session.commit()
