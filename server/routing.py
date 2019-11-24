from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required

# from app.forms import LoginForm, RegistrationForm


# Render home page
# @app.route('/')
def home():
    return render_template('home.jinja2')


def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.jinja2', title='Sign In', form=form)
    
def sender():
    return render_template('sender.jinja2', title='Sign In')


def receiver(fname, lname):
    listA = ['a', 'b', 'c', 'd', 'ewrqrewafr']
    return render_template('receiver.jinja2', title='Sign In', fname=fname, lname=lname, listA=listA)


def contact():
    return render_template('Contact.jinja2', title='Contact Us')


def sendcontact():
    return render_template('ContactSent.jinja2')

def aboutus():
    return render_template('About.jinja2')
