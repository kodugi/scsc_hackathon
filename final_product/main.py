from flask import Flask, jsonify, render_template, redirect, url_for, request, session
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin, current_user
import requests
import json
import os

# 추천 시스템 임포트 추가
try:
    from simple_recommendation_engine import SimpleCollaborativeRecommender
    RECOMMENDER_AVAILABLE = True
    print("추천 시스템 모듈 로드 성공")
except ImportError as e:
    print(f"추천 시스템 모듈 로드 실패: {e}")
    RECOMMENDER_AVAILABLE = False

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

# 🤖 추천 시스템 전역 변수 추가
recommender = None

def initialize_recommender():
    """추천 시스템 초기화"""
    global recommender
    
    if not RECOMMENDER_AVAILABLE:
        print("❌ 추천 시스템이 비활성화되었습니다.")
        return None
    
    try:
        data_path = "static/problem_for_each_user.csv"
        model_path = "static/simple_recommendation_model.pkl"
        
        print(f"📁 데이터 파일 경로: {data_path}")
        print(f"📁 모델 파일 경로: {model_path}")
        print(f"📁 데이터 파일 존재: {os.path.exists(data_path)}")
        print(f"📁 모델 파일 존재: {os.path.exists(model_path)}")
        
        recommender = SimpleCollaborativeRecommender()
        print("✅ SimpleCollaborativeRecommender 객체 생성 완료")

        if os.path.exists(model_path):
            print("💾 저장된 모델을 로드합니다...")
            recommender.load_model(model_path)
            print("✅ 모델 로드 완료")
        elif os.path.exists(data_path):
            print("🤖 새로운 모델을 학습합니다...")
            recommender.load_data(data_path)
            print("✅ 데이터 로드 완료")
            recommender.train_model()
            print("✅ 모델 학습 완료")
            recommender.save_model(model_path)
            print("✅ 모델 저장 완료")
        else:
            print("❌ 데이터가 없습니다.")
            print("📝 테스트 데이터를 생성합니다...")
            
            # static 폴더가 없으면 생성
            os.makedirs("static", exist_ok=True)
            
            from simple_recommendation_engine import create_test_data
            create_test_data()
            print("✅ 테스트 데이터 생성 완료")
            
            recommender.load_data(data_path)
            print("✅ 데이터 로드 완료")
            recommender.train_model()
            print("✅ 모델 학습 완료")
            recommender.save_model(model_path)
            print("✅ 모델 저장 완료")
        
        print(f"🎯 추천 시스템 초기화 성공! trained: {recommender.trained}")
        return recommender
            
    except Exception as e:
        print(f"❌ 추천 시스템 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

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
    

def getUserSolvedProblems(user_handle, max_pages=5):
    """
    solved.ac API에서 특정 사용자가 푼 문제들을 가져오는 함수
    """
    print(f"🔍 사용자 '{user_handle}'의 풀이 기록을 가져오는 중...")
    
    solved_problems = []
    page = 1
    
    while page <= max_pages:
        try:
            response = makeRequest(
                "https://solved.ac/api/v3/search/problem", 
                {"query": f"solved_by:{user_handle}", "page": page}
            )
            
            if response is None:
                break
                
            temp = response.json().get("items", [])
            if len(temp) == 0:
                break
            
            for item in temp:
                problem_id = item.get("problemId")
                level = item.get("level")
                title = item.get("titleKo")
                
                solved_problems.append({
                    'user_handle': user_handle,
                    'problem_id': problem_id,
                    'level': level,
                    'title': title
                })
            
            page += 1
            
        except Exception as e:
            print(f"❌ 페이지 {page} 가져오기 실패: {e}")
            break
    
    print(f"✅ 총 {len(solved_problems)}개의 문제 풀이 기록 수집 완료")
    return solved_problems

def createUserDataFrame(user_handle):
    """
    특정 사용자의 데이터를 DataFrame 형태로 생성
    """
    import pandas as pd
    
    solved_problems = getUserSolvedProblems(user_handle)
    
    if not solved_problems:
        return None
    
    # DataFrame 생성
    df = pd.DataFrame(solved_problems)
    df.rename(columns={
        'user_handle': 'SOLVER_HANDLE',
        'problem_id': 'PROBLEM_ID',
        'level': 'SOLVED_LVL'
    }, inplace=True)
    
    return df[['SOLVER_HANDLE', 'PROBLEM_ID', 'SOLVED_LVL']]


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
        tagList += ([{"en": tag.get("displayNames")[1].get("short").replace(' ', '_'), "ko": tag.get("displayNames")[0].get("short").replace(' ', '_')} for tag in temp])
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
        recommendation_list = getRecommendation()  # 수정된 부분
        for problem_id in recommendation_list:
            problem_info = findProblem(problem_id)
            if problem_info:
                problems["items"].append(problem_info)
        
        return jsonify(problems)

# 🎯 핵심 수정: getRecommendation 함수를 실제 추천 시스템과 연결
@app.route('/getRecommendation', methods=['GET'])
def parseRecommendation():
    problemList = getRecommendation()
    parsed = []
    for p in problemList:
        parsed.append(findProblem(p))
    return jsonify({"items": parsed})

def getRecommendation():
    """현재 로그인한 사용자에게 맞춤 문제 추천"""
    
    # 로그인 확인
    if not loggedIn or not user:
        print("❌ 로그인되지 않은 사용자")
        return [1000, 1001, 1002, 1003]  # 기본 추천
    
    # 추천 시스템 사용 불가능한 경우
    if recommender is None or not recommender.trained:
        print("❌ 추천 시스템이 초기화되지 않음")
        return [1000, 1001, 1002, 1003]  # 기본 추천
    
    try:
        user_id = user.id
        print(f"🎯 사용자 '{user_id}'에게 문제 추천 중...")
        
        # 1. 실시간으로 사용자 데이터 가져오기
        user_df = createUserDataFrame(user_id)
        
        if user_df is None or len(user_df) == 0:
            print(f"⚠️ 사용자 '{user_id}'의 풀이 기록을 찾을 수 없음")
            return [1000, 1001, 1002, 1003]  # 기본 추천
        
        # 2. 추천 시스템에 실시간 데이터 추가하여 추천받기
        recommendations = recommender.get_recommendations_for_new_user(user_df, n_recommendations=10)
        
        if not recommendations:
            print(f"⚠️ 사용자 '{user_id}'에 대한 추천이 없음")
            return [1000, 1001, 1002, 1003]  # 기본 추천
            
        # 문제 ID만 추출
        problem_ids = [rec['problem_id'] for rec in recommendations]
        print(f"✅ 추천 완료: {problem_ids}")
        
        return problem_ids
        
    except Exception as e:
        print(f"❌ 추천 생성 중 오류: {e}")
        return [1000, 1001, 1002, 1003]  # 기본 추천

@app.route('/getRecommendationByTag', methods=['POST'])
def parseRecommendationByTag():
    tag_name = request.get_json().get('tag')
    print("tag_name:",tag_name)
    problemList = getRecommendationByTag(tag_name)
    parsed = []
    for p in problemList:
        parsed.append(findProblem(p))
    return jsonify({"items": parsed})

def getRecommendationByTag(tag_name):
    """태그별 맞춤 문제 추천 (간단 버전)"""

    print(f"🏷️ 태그 '{tag_name}' 추천 요청")

    # 로그인 확인
    if not loggedIn or not user:
        print("❌ 로그인되지 않은 사용자")
        return [1000, 1001, 1002, 1003]

    # 추천 시스템 확인
    if recommender is None or not recommender.trained:
        print("❌ 추천 시스템이 초기화되지 않음")
        return [1000, 1001, 1002, 1003]

    try:
        user_id = user.id
        print(f"🎯 사용자 '{user_id}'에게 '{tag_name}' 태그 문제 추천 중...")
        
        # 실시간으로 사용자 데이터 가져오기
        user_df = createUserDataFrame(user_id)
        
        if user_df is None or len(user_df) == 0:
            print(f"⚠️ 사용자 '{user_id}'의 풀이 기록을 찾을 수 없음")
            return [1000, 1001, 1002, 1003]
        
        # 태그별 추천 생성
        recommendations = recommender.get_recommendations_for_new_user_by_tag(
            user_df, tag_name, n_recommendations=10
        )
        
        if not recommendations:
            print(f"⚠️ '{tag_name}' 태그 추천이 없음")
            return [1000, 1001, 1002, 1003]
            
        # 문제 ID만 추출
        problem_ids = [rec['problem_id'] for rec in recommendations]
        print(f"✅ '{tag_name}' 태그 추천 완료: {problem_ids}")
        
        return problem_ids
        
    except Exception as e:
        print(f"❌ 태그별 추천 생성 중 오류: {e}")
        return [1000, 1001, 1002, 1003]
    

@app.route('/api/recommendations', methods=['GET'])
@login_required
def api_recommendations():
    """JSON 형태로 추천 결과 반환"""
    if recommender is None:
        return jsonify({
            'error': '추천 시스템이 초기화되지 않았습니다.',
            'recommendations': []
        }), 500
    
    try:
        user_id = current_user.get_id()
        recommendations = recommender.get_user_recommendations(user_id, 10)
        
        if not recommendations:
            available_users = list(recommender.user_item_matrix.keys())[:10]
            return jsonify({
                'message': f'사용자 "{user_id}"의 데이터를 찾을 수 없습니다.',
                'available_users': available_users,
                'recommendations': []
            })
        
        # 추천 결과 포맷팅
        formatted_recs = []
        for rec in recommendations:
            problem_info = findProblem(rec['problem_id'])
            formatted_recs.append({
                'problem_id': int(rec['problem_id']),
                'estimated_preference': round(rec['estimated_rating'], 2),
                'baekjoon_url': f"https://www.acmicpc.net/problem/{rec['problem_id']}",
                'problem_info': problem_info
            })
        
        return jsonify({
            'user_id': user_id,
            'recommendations': formatted_recs,
            'message': f'{len(formatted_recs)}개의 문제를 추천했습니다.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/user_stats', methods=['GET'])
@login_required
def api_user_stats():
    """사용자 통계 정보 API"""
    if recommender is None:
        return jsonify({'error': '추천 시스템이 초기화되지 않았습니다.'}), 500
    
    try:
        user_id = current_user.get_id()
        stats = recommender.get_user_stats(user_id)
        
        if stats is None:
            available_users = list(recommender.user_item_matrix.keys())[:10]
            return jsonify({
                'message': f'사용자 "{user_id}"의 데이터를 찾을 수 없습니다.',
                'available_users': available_users,
                'stats': {}
            })
        
        return jsonify({
            'user_id': user_id,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/status', methods=['GET'])
def api_status():
    """시스템 상태 확인"""
    return jsonify({
        'recommender_available': RECOMMENDER_AVAILABLE,
        'recommender_initialized': recommender is not None and recommender.trained,
        'logged_in': loggedIn,
        'current_user': user.id if user else None,
        'message': '시스템이 정상 작동 중입니다.' if recommender else '추천 시스템이 초기화되지 않았습니다.'
    })

import pvp
pvpManager = pvp.PvpManager()

@app.route("/pvp/", methods = ['GET'])
def pvp():
    return render_template("pvp.html")

@app.route('/pvp/start', methods = ['POST'])
def pvpStart():
    data = request.get_json()
    pvpManager.newPvp(user, data.get("problemId"))

@app.route('/pvp/get', methods = ['POST'])
def pvpGet():
    return jsonify({"items": pvpManager.findPvp(user)})

if __name__ == '__main__':
    print("Flask 앱 시작...")
    initialize_recommender()
    app.run(debug=True)
