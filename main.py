# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import random
import hashlib
import hmac
from string import letters

import webapp2
import jinja2
import time

from google.appengine.ext import db
from database import User, Post, Comment, Like

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = 'JvWGciEbUQp4X1SsD5f0'

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))


class MainPage(Handler):
  def get(self):
        posts = Post.all()
        self.render('blogs.html', posts = posts)





def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class Signup(Handler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username,
                      email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError





class Register(Signup):
    def done(self):
        #make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username = msg, username=self.username, email=self.email)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/blog')

class Login(Handler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/blog')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)

class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect('/blog')

class BlogFront(Handler):
    def get(self):
        if self.user:
            print self.user.name
            self.response.write('Welcome %s to Multi User Blog!' % self.user.name.title())
        else:
            self.redirect("/login")
        
class NewPostHandler(Handler):
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            return self.redirect('/')
        print self.user.name
        post_id = Post.addPost(title = self.request.get('title'),
                                        content = self.request.get('content'),
                                        author = self.user.name)
        self.redirect('/blog/' + str(post_id))

class BlogHandler(Handler):
    def get(self, post_id):
        post = Post.getPost(int(post_id))
        if not post:
            return self.error()
        #comments = None
        likes = None
        comments = Comment.getCommentsByPostId(post_id)
        comments_count = comments.count()
        like_text = 'Like'
        # if self.user:
        #     user = self.user
        #     like = LikePost.getLikeByPostAndAuthor(post_id, user.user_name)
        #     if like:
        #         like_text = 'Liked'
        self.render("post.html", post=post, likes=likes,
                    post_comments=comments, comments_count=comments_count)
    def post(self, post_id):
        if not self.user:
            return self.redirect('/')
        post = Post.getPost(int(post_id))

        if self.request.get("edit"):
            if post.author == self.user.name:
                    # take the user to edit post page
                    self.redirect('/blog/edit/%s' % post_id)

        elif self.request.get("delete"):
            if post.author == self.user.name:
                ret = Post.deletePost(post_id)
                time.sleep(0.1)
            if ret:
                return self.redirect('/')

        elif self.request.get("add_comment"):
            comment_text = self.request.get("comment_text")
            # check if there is anything entered in the comment text area
            if comment_text:
                # add comment to the comments database and refresh page
                Comment.addComment(post_id = post_id, text = comment_text,
                 author = self.user.name)
                
                self.redirect('/blog/%s' % str(post.key().id()))
            # otherwise if nothing has been entered in the text area throw
            # an error
            else:
                comment_error = "Please enter a comment in the text area to post"
                self.render(
                    "post.html",
                    post=post,
                    likes=likes,
                    unlikes=unlikes,
                    comments_count=comments_count,
                    post_comments=post_comments,
                    comment_error=comment_error)

class DeletePostHandler(Handler):
    pass
class PostHandler(Handler):
    pass
class EditPostHandler(Handler):
    def post(self, post_id):
        if not self.user:
            return self.redirect('/')

        Post.editPost(title = self.request.get('title'),
                               content = self.request.get('content'),
                               author = self.user.name,
                               post_id = post_id)
        self.redirect('/blog/' + str(post_id))

    def get(self, post_id):
        post = Post.getPost(int(post_id))

        # check if the user is logged in
        if self.user:
            # check if this user is the author of this post
            if post.author == self.user.name:
                # take the user to the edit post page
                self.render("editpost.html", post=post)
            # otherwise if this user is not the author of this post throw an
            # error
            else:
                self.response.out.write("You cannot edit other user's posts")
        # otherwise if the user is not logged in take them to the login page
        else:
            self.redirect("/login")

class EditCommentHandler(Handler):
    def get(self, post_id, comment_id):
        # get the blog and comment from blog id and comment id
        comment = Comment.get_by_id(int(comment_id))
        # check if there is a comment associated with that id
        if comment:
            # check if this user is the author of this comment
            if comment.comment_author == self.user.name:
                # take the user to the edit comment page and load the content
                # of the comment
                self.render("editcomment.html", comment_text=comment.comment_text)
            # otherwise if this user is the author of this comment throw and
            # error
            else:
                error = "You cannot edit other users' comments'"
                self.render("editcomment.html", edit_error=error)
        # otherwise if there is no comment associated with that ID throw an
        # error
        else:
            error = "This comment no longer exists"
            self.render("editcomment.html", edit_error=error)

    def post(self, post_id, comment_id):
        # if the user clicks on update comment
        if self.request.get("update_comment"):
            # get the comment for that comment id
            comment = Comment.get_by_id(int(comment_id))
            # check if this user is the author of this comment
            if comment.comment_author == self.user.name:
                # update the text of the comment and redirect to the post page
                comment.comment_text = self.request.get('comment_text')
                comment.put()
                time.sleep(0.1)
                self.redirect('/blog/%s' % str(post_id))
            # otherwise if this user is the author of this comment throw and
            # error
            else:
                error = "You cannot edit other users' comments'"
                self.render(
                    "editcomment.html",
                    comment_text=comment.text,
                    edit_error=error)
        # if the user clicks on cancel take the user to the post page
        elif self.request.get("cancel"):
            self.redirect('/blog/%s' % str(post_id))

class DeleteCommentHandler(Handler):
    def get(self, post_id, comment_id):
        # get the comment from the comment id
        comment = Comment.get_by_id(int(comment_id))
        # check if there is a comment associated with that id
        if comment:
            # check if this user is the author of this comment
            if comment.comment_author == self.user.name:
                # delete the comment and redirect to the post page
                db.delete(comment)
                time.sleep(0.1)
                self.redirect('/blog/%s' % str(post_id))
            # otherwise if this user is not the author of this comment throw an
            # error
            else:
                self.write("You cannot delete other user's comments")
        # otherwise if there is no comment associated with that id throw an
        # error
        else:
            self.write("This comment no longer exists")

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signup', Register),
    ('/login', Login),
    ('/logout', Logout),
    ('/blog/?', BlogFront),
    ('/blog', BlogHandler),
    ('/blog/delete', DeletePostHandler),
    ('/blog/newpost', NewPostHandler),
    ('/blog/([0-9]+)', BlogHandler),
    ('/blog/edit/([0-9]+)', EditPostHandler),
    ('/blog/([0-9]+)/editcomment/([0-9]+)', EditCommentHandler),
    ('/blog/([0-9]+)/deletecomment/([0-9]+)', DeleteCommentHandler)
], debug=True)
