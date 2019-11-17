from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required

# from app.forms import LoginForm, RegistrationForm
from server.models.stock.stock import Stocks


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
    return render_template('login.html', title='Sign In', form=form)


def sender():
    return render_template('sender.jinja2', title='Sign In')


def receiver(fname, lname):
    listA = ['a', 'b', 'c', 'd', 'ewrqrewafr']
    return render_template('receiver.jinja2', title='Sign In', fname=fname, lname=lname, listA=listA)


def optiondecision():
    return render_template('OptionDecision.jinja2', title='optiondecision')


def option1():
    return render_template('Option1.jinja2', stock=Stocks())


def option2():
    return render_template('Option2.jinja2', stock=Stocks())


def option3parent():
    return render_template('Option3Parent.jinja2', title='optiondecision')

def contact():
    return render_template('Contact.jinja2', title='Contact Us')


def option3childa():
    return render_template('Option3ChildA.jinja2', title='optiondecision')


def option3childb():
    return render_template('Option3ChildB.jinja2', title='optiondecision')


def option3childc():
    return render_template('Option3ChildC.jinja2')

def sendcontact():
    return render_template('ContactSent.jinja2')

def aboutus():
    return render_template('About.jinja2')

'''
def portfoliio():
    weightings = [0.6,0.4,0,0,0,0,0,0,0,0,0,0,0]
    #initial user input
    histPortValue = [1000,990,1050,1100]
    histVol = 0.12
    expectedReturn = 0.1
    expectedVol = 0.1
    risk = 'High'
    return render_template('portfolio.jinja2', title='Sign In', weightings=weightings, risk=risk,histPortValue=histPortValue,histVOL=histVol, expectedReturn=expectedReturn,expectedVol=expectedVol)
'''

def portfolioview():
    weightings = [0.6, 0.4]
    #initial user input
    expectedReturn = 0.1
    expectedVol = 0.1
    risk = 'High'
    return render_template('portfolio.jinja2', title='Sign In', weightings=weightings, risk=risk, expectedReturn=expectedReturn, expectedVol=expectedVol)
