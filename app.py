import os
from flask import Flask, flash, redirect, render_template,session,request, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology,lookup, usd
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from datetime import datetime
try:
    from flask_login import LoginManager,login_user,login_required,UserMixin,logout_user,current_user
    print('pass')
except ImportError:
    print('error')

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure CS50 Library to use SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SECRET_KEY'] = 'nitin'
db = SQLAlchemy(app)
app.app_context().push()
try:
    login_manager = LoginManager(app)
except:
    print('double error')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


try:
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
except:
    print('user_loader error')


try:
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer(), primary_key=True)
        username = db.Column(db.String(length=30), nullable=False, unique=True)
        password_hash = db.Column(db.String(length=60), nullable=False)
        cash = db.Column(db.Integer(), nullable=False, default=10000)
        items = db.relationship('Item', backref='owned_user', lazy=True)

        @property
        def prettier_budget(self):
            if len(str(self.budget)) >= 4:
                return f'{str(self.budget)[:-3]},{str(self.budget)[-3:]}$'
            else:
                return f"{self.budget}$"

        @property
        def password(self):
            return self.password_hash

        @password.setter
        def password(self, plain_text_password):
            self.password_hash =generate_password_hash(plain_text_password)

        def check_password_correction(self, attempted_password):
            return check_password_hash(self.password_hash, attempted_password)
        print('class pass')

except NameError:
    print('usermixin error')

class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    symbol = db.Column(db.String(length=30), nullable=False)
    name = db.Column(db.String(length=30), nullable=False)
    price = db.Column(db.Integer(), nullable=False)
    shares=db.Column(db.Integer(),nullable=False)
    owner = db.Column(db.Integer(), db.ForeignKey('user.id'))
    def __repr__(self):
        return f'Item {self.name}'

class Transactions(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id=db.Column(db.Integer(),db.ForeignKey('user.id'))
    stock=db.Column(db.String(length=100),nullable=False)
    item_id=db.Column(db.Integer(),db.ForeignKey('item.id'))
    shares=db.Column(db.Integer(),nullable=False)
    tot = db.Column(db.String(length=30), nullable=False)
    time = db.Column(DateTime, default=datetime.utcnow) 
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


try:
    @app.route("/")
    def index():
        """Show portfolio of stocks"""
        if not current_user.is_authenticated:
            return redirect('/login')
        items=Item.query.filter_by(owner=current_user.id).all()
        
        total=current_user.cash
        if items:
            for item in items:
                total=total+item.price*item.shares
        print(total)
        return render_template('index.html',items=items,newTotal=total)
except NameError:
    print('route error')


try:
    @app.route("/buy", methods=["GET", "POST"])
    def buy():
        """Buy shares of stock"""
        if request.method=='POST':
            symbol=request.form.get('symbol')
            symbol_result=lookup(symbol)
            if symbol_result==None:
                return apology("Symbol is not correct")
            shares=request.form.get('shares')

            # ID=session.get('id')
            ID=current_user.id
            user=User.query.filter_by(id=ID).first()
            if symbol_result['price']*float(shares) >user.cash: # db.execute('''SELECT cash from users where id=?''',(ID)):  
                return apology("don't have sufficient balance")
            
            new_cash=user.cash-symbol_result['price']*float(shares)
            # db.execute("update users set cash=? where id=?",(new_cash,ID))
            user.cash=new_cash
            items=Item.query.filter_by(owner=user.id,symbol=symbol).all()

            if items:
                for item in items:
                    if item.symbol==symbol:
                        item.shares=int(item.shares)+int(shares)
                        break
            else:
                item=Item(symbol=symbol_result['symbol'],name=symbol_result['name'],price=symbol_result['price'],shares=shares,owner=user.id)
                db.session.add(item)
                db.session.commit()

            trx=Transactions(user_id=user.id,stock=symbol_result['name'],item_id=item.id,shares=shares,tot='BOUGHT')
            db.session.add(trx)
            db.session.commit()
            flash(f'BOUGHT',category='success')
            return redirect("/")
        elif request.method=='GET':
            return render_template('buy.html')
        return apology("TODO")

except:
    print('buy error')


try:
    @app.route("/history")
    def history():
        trx=Transactions.query.filter_by(user_id=current_user.id).all()
        user=User.query.filter_by(id=current_user.id).first()
        items=Item.query.filter_by(owner=current_user.id).all()
        return render_template('history.html',trx=trx,user=user,items=items)
        return apology("TODO")
except:
    print('history error')


try:
    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Log user in"""

        # User reached route via POST (as by submitting a form via POST)
        if request.method == "POST":
            # Ensure username was submitted
            if not request.form.get("username"):
                return apology("must provide username",403)

            # Ensure password was submitted
            elif not request.form.get("password"):
                return apology("must provide password", 403)

            # Query database for username
            user=User.query.filter_by(username=request.form.get('username')).first()
            if user:
                print(user.password)

            if user and check_password_hash(user.password,request.form.get('password')):
                
                login_user(user)
                flash(f'you are now logged in as {user.username}',category='success')
                return redirect("/")
        
            return apology("invalid username and/or password", 403)
            

        # User reached route via GET (as by clicking a link or via redirect)
        else:
            return render_template("login.html")

except:
    print('login error')

try:
    @app.route("/logout")
    def logout():
        """Log user out"""

        # Forget any user_id
        logout_user()
        flash('you have been logged out',category='info')

        # Redirect user to login form
        return redirect("/")
except:
    print('logout error')


try:
    @app.route("/quote", methods=["GET", "POST"])
    def quote():
        """Get stock quote."""
        if request.method=='POST':
            symbol=request.form.get('symbol')
            quote_data=lookup(symbol)
            return render_template('quoted.html',quote_data=quote_data)
        elif request.method=='GET':
            return render_template('quote.html')
        return apology("TODO")
except:
    print('quote error')

try:
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            if not request.form.get("username"):
                return apology("must provide username", 400)
            if not request.form.get("password1"):
                return apology("must provide password", 400)
            if not request.form.get("password2"):
                return apology("must provide password confirmation", 400)
            if request.form.get("password1") != request.form.get("password2"):
                return apology("passwords don't match", 400)
            rows=User.query.filter_by(username=request.form.get("username")).first()
            if rows:
                return apology("username already exists", 400)

            user=User(username=request.form.get('username'),password=request.form.get('password1'))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect("/")

        return render_template('register.html')

except:
    print('register error')

try:
    @app.route("/sell", methods=["GET", "POST"])
    def sell():

        if request.method=='POST':
            item_id=request.form.get('sold')
            shares=int(request.form.get('shares'))
            total_shares=shares
            item=Item.query.filter_by(id=item_id).first()
            user=User.query.filter_by(id=current_user.id).first()
            result=lookup(item.symbol)

            while shares>0:
                user.cash=user.cash+result['price']
                item.shares=item.shares-1
                if item.shares ==0 :
                    db.session.delete(item)
                    db.session.commit()
                    break
                shares=shares-1
            trx=Transactions(user_id=current_user.id,stock=result['name'],item_id=item_id,shares=total_shares,tot='SOLD')
            db.session.add(trx)
            db.session.commit()
            flash(f'SOLD',category='success')
            return redirect('/sell')
        elif request.method=='GET':
            user=User.query.filter_by(id=current_user.id).first()
            items=Item.query.filter_by(owner=current_user.id).all()
            length=len(items)
            return render_template('sell.html',user=user,items=items,length=length)
        return apology("TODO")
except:
    print('sell error')

# if __name__ == '__main__':
#   app.run(debug=True)
