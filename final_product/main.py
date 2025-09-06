from flask import Flask, jsonify, render_template, redirect, url_for, request, session
from flask_login import login_user, LoginManager, UserMixin

class User(UserMixin):
    def __init__(self, id, password):
        self.id = id
        self.password = password

    def get_id(self):
        return self.id

    def __repr__(self):
        return f"USER: {self.id}"

userInfo = {'a' : User('a', 'a')}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-super-secret-key' 
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return userInfo.get(str(user_id))

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    print(request)
    print(request.form)
    if request.method == 'GET':
        next = request.args.get('next', '')

    else:
        print(request.form)
        id = request.form.get('id')
        password = request.form.get('password')
        next = request.form.get('next')
        safe_next_redirect = url_for('index')

        if next:
            safe_next_redirect = next

        user = userInfo.get(id)
        print(user, id, password)
        if user and user.password == password:
            login_user(user)
            return redirect(safe_next_redirect)
        else:
            return "<h1>Invalid email or password</h1>"

    return render_template('login.html', next=next)

if __name__ == '__main__':
    app.run(debug=True)