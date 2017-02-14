from google.appengine.ext import db
import os
import re
import random
import hashlib
import hmac
from string import letters

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

##### user stuff
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)
class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u

class Post(db.Model):
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    author = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_updated = db.DateTimeProperty(auto_now = True)

    @classmethod
    def addPost(cls, title, content, author):
        p = Post(title = title, content = content,
                 author = author)
        p.put()
        return p.key().id()

    @classmethod
    def editPost(cls, title, content, author, post_id):
        post = Post.get_by_id(int(post_id))
        if post:
            if post.author == author:
                post.title = title
                post.content = content
                post.put()
                return post.key().id()

    @classmethod
    def getPost(cls, post_id):
        return Post.get_by_id(int(post_id))

    @classmethod
    def deletePost(cls, post_id):
        post = Post.get_by_id(int(post_id))
        if post:
            #post.key().delete()
            db.delete(post)
            return True
        else:
            return False


class LikePost(db.Model):
    like_post = db.StringProperty(required = True)
    like_author = db.StringProperty(required = True)
    like_create = db.DateTimeProperty(auto_now_add = True)

    @classmethod
    def addLike(cls, post_id, author):
        l = LikePost(like_post = str(post_id),
                     like_author = str(author))
        l.put()
        return l.key().id()

    @classmethod
    def getLikeByPostAndAuthor(cls, post_id, author):
        likes = LikePost.all().filter('like_post =', post_id).filter('like_author =', author)
        for l in likes:
            return l

    @classmethod
    def countByPost(cls, post_id):
        likes = LikePost.all().filter('like_post =', post_id)
        return likes.count()

    @classmethod
    def deleteLike(cls, like_id):
        like = LikePost.get_by_id(int(like_id))
        if like:
            like.key().delete()
            return True
        else:
            return False



class Comment(db.Model):
    comment_post = db.StringProperty(required = True)
    comment_text = db.StringProperty(required = True)
    comment_author = db.StringProperty(required = True)
    comment_created = db.DateTimeProperty(auto_now_add = True)

    @classmethod
    def getCommentsByPostId(cls, post_id):
        return Comment.all().filter('comment_post =', post_id).order('comment_created')

    @classmethod
    def getComment(cls, comment_id):
        return Comment.get_by_id(int(comment_id))

    @classmethod
    def addComment(cls, post_id, text, author):
        c= Comment(comment_post = str(post_id), 
                   comment_text = str(text), 
                   comment_author = str(author))
        c.put()
        return c.key().id()

    @classmethod
    def deleteComment(cls, comment_id):
        comment = Comment.get_by_id(int(comment_id))
        print "hiii"
        if comment:
            comment.key().delete()
            return True
        else:
            return False