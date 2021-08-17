# blog
##介绍
    个人用于学习并且修改的博客代码
##使用说明：
    使用需要自己加载数据库，因此步骤也将围绕数据库
##使用步骤：
    在终端中输入以下命令(已经关联上remote分支)
    1.git pull origin main
    2.检查manage.py最后一行manage.run()是否被注释，如有，取消注释
    3.python manage.py db init
    4.python manage.py db migrate -m "initial migration"
    4.python manage.py deploy product
    5.python manage.py runserver