from flask import Flask, jsonify, render_template, redirect, url_for, request, session
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin
import requests
import json

class User(UserMixin):
    def __init__(self, id, password):
        self.id = id
        self.password = password

    def get_id(self):
        return self.id

    def __repr__(self):
        return f"USER: {self.id}"

userInfo = {'a' : User('a', 'a')}
user = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-super-secret-key'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 
loggedIn = False

def makeRequest(url, querystring):
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
        response.raise_for_status()
        return response
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"API Error: {e}")
        return None
    
def findUser(handle):
    response = makeRequest("https://solved.ac/api/v3/search/user", {"query": handle})
    temp = response.json().get("items", [])
    if(temp is None):
        return False
    if len(temp) == 1 and temp[0].get("handle").lower() == handle.lower():
        return True
    else:
        return False

def findProblem(problemId):
    response = makeRequest("https://solved.ac/api/v3/problem/show", {"problemId": problemId})
    if(response is None):
        return None
    else:
        return response.json() # JSON 객체를 바로 반환

@app.route('/getTagList', methods = ['GET'])
def getTagList():
    tagList = []
    page = 1
    while(True):
        print(page)
        response = makeRequest("https://solved.ac/api/v3/tag/list", {"page": page})
        if(response is None):
            break
        temp = response.json().get("items", [])
        if(len(temp) == 0):
            break
        tagList += ([{"ko": tag.get("displayNames")[0].get("short"), "en_short": tag.get("displayNames")[1].get("short").replace(' ', '_')} for tag in temp])
        page += 1
    return jsonify({"items": tagList})

@login_manager.user_loader
def load_user(user_id):
    return userInfo.get(str(user_id))

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id = request.form.get('id')
        password = request.form.get('password')
        
        global user
        user = userInfo.get(id)
        
        if user and user.password == password:
            login_user(user)
            global loggedIn
            loggedIn = True
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            return "<h1>Invalid ID or password</h1>"

    return render_template('login.html')

@app.route('/getLogin', methods=['GET'])
def getLogin():
    if loggedIn and user:
        return jsonify({"items": [True, user.id, user.password]})
    else:
        return jsonify({"items": [False]})
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id = request.form.get('id')
        password = request.form.get('password')
        
        if id in userInfo:
            return "<h1>This ID is already taken.</h1>"
        
        if not findUser(id):
            return f"<h1>User '{id}' not found on solved.ac</h1>"

        new_user = User(id, password)
        userInfo[id] = new_user

        global user
        user = new_user
        login_user(user)
        global loggedIn
        loggedIn = True
        
        print(f"New user registered: {id}, Total users: {len(userInfo)}")
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    
    global loggedIn, user
    loggedIn = False
    user = None
    
    return redirect(url_for('index'))

@app.route('/search', methods = ['GET', 'POST'])
def search():
    if(request.method == 'GET'):
        return render_template('search.html')
    else:
        problems = {"items": []}
        reccommendList = recommend("query")
        for p in reccommendList:
            problems["items"].append(findProblem(p))
            print(problems["items"])

def crawlSolved(handle):
    url = "https://solved.ac/api/v3/search/problem"
    headers = {"Content-Type": "application/json"}
    page = 1
    items = []
    while(True):
        querystring = {"query": f"solved_by:{handle}", "page": f"{page}"}
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            temp = dict()
            temp["item"] = json.loads(response.text).get("items")
            if(len(temp["item"]) == 0):
                break
            for item in temp["item"]:
                items.append(item)
            page += 1
        except:
            break
    return {"items": items}

@app.route('/getRecommendation', methods = ['GET'])
def getRecommendation():
    if(loggedIn):
        solvedProblems = crawlSolved(user.get_id())
        print(solvedProblems)
    problems = {"items": []}
    reccommendList = recommend("query")
    for p in reccommendList:
        problems["items"].append(findProblem(p))
    return jsonify(problems)

def recommend(query):
    return [1000, 1001, 1002, 1003]

@app.route('/pvp', methods = ['GET', 'POST'])
def pvp():
    if(request.method == 'GET'):
        return render_template("pvp.html")

if __name__ == '__main__':
    app.run(debug=True)
