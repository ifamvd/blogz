from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:tigasep88@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

app.secret_key = 'tigasep88'

# persistent class -- created into a database table
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(5000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

# persistent class -- created into a database table
class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(120), unique = True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref = 'owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)

@app.before_request
def require_login():
    allowed_routes = ['login', 'blog', 'index', 'signup']
    # let's check the seesion information
    print("This is the session:")
    print(session)
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/login', methods = ['POST', 'GET'])
def login():
    error_u = ''
    error_p = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = username).first()
        if not user:
            error_u = 'User does not exist.'
            flash('User does not exist. Please signup for an account.', 'flash-alert')
            return redirect('/signup')
        elif user and not check_pw_hash(password, user.pw_hash):
            error_p = 'Password is incorrect.'
            flash('Password is incorrect.', 'flash-alert')
        elif user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            flash("Logged in successfully.", 'flash-success')
            return redirect('/newpost')
        else:
            error_u = 'Incorrect username.'
            error_p = 'Incorrect password.'
            flash("Incorrect username and password combination.", 'flash-alert')
    return render_template('login.html', title = "Login", error_u = error_u, error_p = error_p)

@app.route('/signup', methods = ['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        # validate
        error_u = ''
        error_p = ''
        error_v = ''
        if not username:
            error_u = 'You left this blank. Please type in your username.'
            flash("You left Username blank.", 'flash-alert')
            username = ''
        elif len(username) < 3 or len(username) > 50:
            error_u = 'Invalid length: either less than 3 or more than 50.'
            flash("Username has invalid length.", 'flash-alert')
            username = ''
        elif check_space(username):
            error_u = 'Space character(s) found. Omit space(s).'
            flash("Space character(s) found in Username.", 'flash-alert')
            username = ''
        if not password:
            error_p = 'You left this blank. Please type in a valid password.'
            flash("You left Password blank.", 'flash-alert')
        elif len(password) < 3 or len(password) > 50:
            error_p = 'Invalid length: either less than 3 or more than 50.'
            flash("Password has invalid length.", 'flash-alert')
        elif check_space(password):
            error_p = 'Space character(s) found. Omit space(s).'
            flash("Space character(s) found in Password.", 'flash-alert')
        if not verify:
            error_v = 'You left this blank. Please verify password.'
            flash("You left Verify Password input blank.", 'flash-alert')
        elif password != verify:
            error_v = 'Passwords don\'t match.'
            flash("Verify Password doesn't match Password.", 'flash-alert')
        if not error_u and not error_p and not error_v:
            # make sure user does not exist
            existing_user = User.query.filter_by(username = username).first()
            if not existing_user:
                new_user = User(username, password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                flash("Registered, and logged in successfully.", 'flash-success')
                return redirect('/newpost')
            else:
                flash("Username already exists. If it is you, please login. Otherwise, choose a different username.", 'flash-alert')
                return render_template('signup.html', title = 'Signup')
        else:
            return render_template('signup.html',
                title = 'Signup',
                username = username,
                error_u = error_u,
                error_p = error_p,
                error_v = error_v)
    return render_template('signup.html', title = 'Signup')

def check_space(token):
    for i in token:
        if i == ' ':
            return True
    return False

@app.route('/logout')
def logout():
    del session['username']
    flash("You have successfully logged out.", 'flash-success')
    return redirect('/blog')

@app.route('/', methods = ['POST', 'GET'])
def index():
    users = User.query.order_by(User.username).all()
    return render_template('index.html', title = 'Blog Users', users = users)

@app.route('/blog')
def blog():
    blog_id = request.args.get("id")
    username = request.args.get("user")
    if blog_id:
        blog_id = int(blog_id)
        post = Blog.query.filter_by(id = blog_id).first()
        return render_template('post.html', title = "Blog Entry", blog_title = post.title, blog_body = post.body, username = post.owner.username)
    elif username:
        owner = User.query.filter_by(username = username).first()
        posts = Blog.query.filter_by(owner = owner).all()
        return render_template('singleUser.html', title = 'Post by User', posts = posts, user = username)
    else:
        posts = Blog.query.order_by(Blog.id).all()
        return render_template('blog.html', title = "List of Blogs", posts = posts)

@app.route('/newpost', methods = ['POST', 'GET'])
def newpost():
    owner = User.query.filter_by(username = session['username']).first()
    error_t = ''
    error_b = ''
    if request.method == 'POST':
        blog_title = request.form['blog_title']
        blog_body = request.form['blog_body']
        # validate
        if not blog_title:
            error_t = 'Please fill in the title'
            flash("You left the title empty. Please fill in the title.", 'flash-alert')
        if not blog_body:
            error_b = 'Please fill in the body'
            flash("You left the body empty. Please fill in the body.", 'flash-alert')
        # add to db
        if not error_t and not error_b:
            new_post = Blog(blog_title, blog_body, owner)
            db.session.add(new_post)
            db.session.commit()
            flash("Blog entry created.", 'flash-success')
            post_id = new_post.id
            return redirect('/blog?id=' + str(post_id))
    return render_template('newpost.html', title = 'Create a Post', error_t = error_t, error_b = error_b)

if __name__ == '__main__':
    app.run()