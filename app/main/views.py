# coding:utf-8
from flask import render_template, request, current_app, redirect, \
    url_for, flash, session
from flask_login import current_user

from . import main
from ..models import Article, ArticleType, article_types, Comment, \
    Follow, User, Source, BlogView
from .forms import CommentForm, CataForm
from .. import db


@main.route('/')
def index():
    BlogView.add_view(db)
    page = request.args.get('page', 1, type=int)
    pagination = Article.query.order_by(Article.create_time.desc()).paginate(
        page, per_page=current_app.config['ARTICLES_PER_PAGE'],
        error_out=False)
    articles = pagination.items
    return render_template('index.html', articles=articles,
                           pagination=pagination, endpoint='.index')


@main.route('/about_author')
def about_author():
    BlogView.add_view(db)
    page = request.args.get('page', 1, type=int)
    pagination = User.query.paginate(
        page, per_page=current_app.config['ARTICLES_PER_PAGE'],
        error_out=False)
    authors = pagination.items
    return render_template('about_author.html', authors=authors,
                           pagination=pagination, endpoint='.about_author')


@main.route('/author_detail', methods=['GET', 'POST'])
def author_detail():
    BlogView.add_view(db)
    user_id = request.args.get('user_id', type=int)
    page = request.args.get('page', 1, type=int)

    form = CataForm()
    sources = [(s.id, s.name) for s in Source.query.all()]
    sources = [(0, "全部")] + sources
    form.source.choices = sources
    types = [(t.id, t.name) for t in ArticleType.query.all()]
    types = [(0, "全部")] + types
    form.types.choices = types
    orders = [(1, "时间降序"), (2, "时间升序")]
    form.order.choices = orders

    if form.is_submitted():
        session['source_id'] = form.source.data
        session['type_id'] = form.types.data
        session['order_id'] = form.order.data
        session['old'] = True

        return redirect(url_for('main.author_detail', user_id=user_id))

    if not session.get('old'):
        session['source_id'] = 0
        session['type_id'] = 0
        session['order_id'] = 1
    else:
        form.source.data = session['source_id']
        form.types.data = session['type_id']
        form.order.data = session['order_id']

    if session['order_id'] == 1:
        query_result = Article.query.order_by(Article.create_time.desc())
    else:
        query_result = Article.query.order_by(Article.create_time.asc())
    query_result = query_result.filter_by(user_id=user_id)
    if session['type_id'] != 0:
        query_result = query_result.filter_by(
            articleType_id=session['type_id'])
    if session['source_id'] != 0:
        query_result = query_result.filter_by(
            source_id=session['source_id'])

    pagination = query_result.paginate(
        page, per_page=current_app.config['ARTICLES_PER_CATA'],
        error_out=False)
    articles = pagination.items
    user = User.query.filter_by(id=user_id).first()
    return render_template('author_detail.html', articles=articles, user=user,
                           pagination=pagination, endpoint='.author_detail', form=form)


@main.route('/cata', methods=['GET', 'POST'])
def cata():
    BlogView.add_view(db)
    page = request.args.get('page', 1, type=int)

    form = CataForm()
    sources = [(s.id, s.name) for s in Source.query.all()]
    sources = [(0, "全部")] + sources
    form.source.choices = sources
    types = [(t.id, t.name) for t in ArticleType.query.all()]
    types = [(0, "全部")] + types
    form.types.choices = types
    orders = [(1, "时间降序"), (2, "时间升序")]
    form.order.choices = orders

    if form.is_submitted():
        session['source_id'] = form.source.data
        session['type_id'] = form.types.data
        session['order_id'] = form.order.data
        session['only_me'] = form.checkbox.data
        session['old'] = True

        return redirect(url_for('main.cata'))

    if not session.get('old'):
        session['source_id'] = 0
        session['type_id'] = 0
        session['order_id'] = 1
        session['only_me'] = False
    else:
        form.source.data = session['source_id']
        form.types.data = session['type_id']
        form.order.data = session['order_id']
        form.checkbox.data = session['only_me']

    if session['order_id'] == 1:
        query_result = Article.query.order_by(Article.create_time.desc())
    else:
        query_result = Article.query.order_by(Article.create_time.asc())
    if session['only_me']:
        query_result = query_result.filter_by(
            user_id=current_user.id)
    if session['type_id'] != 0:
        query_result = query_result.filter_by(
            articleType_id=session['type_id'])
    if session['source_id'] != 0:
        query_result = query_result.filter_by(
            source_id=session['source_id'])

    pagination = query_result.paginate(
        page, per_page=current_app.config['ARTICLES_PER_CATA'],
        error_out=False)
    articles = pagination.items
    return render_template('cata.html', articles=articles,
                           pagination=pagination, endpoint='.cata', form=form)


@main.route('/article-types/<int:id>/')
def articleTypes(id):
    BlogView.add_view(db)
    page = request.args.get('page', 1, type=int)
    pagination = ArticleType.query.get_or_404(id).articles.order_by(
        Article.create_time.desc()).paginate(
        page, per_page=current_app.config['ARTICLES_PER_PAGE'],
        error_out=False)
    articles = pagination.items
    return render_template('index.html', articles=articles,
                           pagination=pagination, endpoint='.articleTypes',
                           id=id)


@main.route('/article-sources/<int:id>/')
def article_sources(id):
    BlogView.add_view(db)
    page = request.args.get('page', 1, type=int)
    pagination = Source.query.get_or_404(id).articles.order_by(
        Article.create_time.desc()).paginate(
        page, per_page=current_app.config['ARTICLES_PER_PAGE'],
        error_out=False)
    articles = pagination.items
    return render_template('index.html', articles=articles,
                           pagination=pagination, endpoint='.article_sources',
                           id=id)


@main.route('/article-detials/<int:id>', methods=['GET', 'POST'])
def articleDetails(id):
    BlogView.add_view(db)
    form = CommentForm(request.form, follow=-1)
    article = Article.query.get_or_404(id)

    if form.validate_on_submit():
        comment = Comment(article=article,
                          content=form.content.data,
                          author_name=form.name.data,
                          author_email=form.email.data)
        db.session.add(comment)
        db.session.commit()
        followed_id = int(form.follow.data)
        if followed_id != -1:
            followed = Comment.query.get_or_404(followed_id)
            f = Follow(follower=comment, followed=followed)
            comment.comment_type = 'reply'
            comment.reply_to = followed.author_name
            db.session.add(f)
            db.session.add(comment)
            db.session.commit()
        flash(u'提交评论成功！', 'success')
        return redirect(url_for('.articleDetails', id=article.id, page=-1))
    if form.errors:
        flash(u'发表评论失败', 'danger')

    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (article.comments.count() - 1) // \
               current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = article.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    article.add_view(article, db)
    return render_template('article_detials.html', User=User, article=article,
                           comments=comments, pagination=pagination, page=page,
                           form=form, endpoint='.articleDetails', id=article.id)
    # page=page, this is used to return the current page args to the
    # disable comment or enable comment endpoint to pass it to the articleDetails endpoint
