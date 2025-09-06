import pandas as pd
import pickle
import os
from collections import defaultdict, Counter
import math

class SimpleCollaborativeRecommender:
    def __init__(self, csv_file_path=None):
        """
        순수 Python으로 구현한 간단한 협업 필터링 추천 시스템
        numpy, sklearn 없이 동작
        """
        self.trained = False
        self.problem_data = None
        self.user_item_matrix = {}
        self.user_similarity = {}
        
        if csv_file_path and os.path.exists(csv_file_path):
            self.load_data(csv_file_path)
    
    def load_data(self, csv_file_path):
        """CSV 파일에서 데이터 로드"""
        print(f"📊 데이터 로드 중: {csv_file_path}")
        
        # CSV 파일 읽기
        self.problem_data = pd.read_csv(csv_file_path)
        
        # 필요한 컬럼만 선택
        required_columns = ['SOLVER_HANDLE', 'PROBLEM_ID', 'SOLVED_LVL']
        self.problem_data = self.problem_data[required_columns]
        
        # 중복 제거
        self.problem_data = self.problem_data.drop_duplicates(
            subset=['SOLVER_HANDLE', 'PROBLEM_ID']
        )
        
        print(f"✅ 데이터 로드 완료:")
        print(f"   - 사용자 수: {self.problem_data['SOLVER_HANDLE'].nunique()}")
        print(f"   - 문제 수: {self.problem_data['PROBLEM_ID'].nunique()}")
        print(f"   - 총 풀이 기록: {len(self.problem_data)}")
        
        # 사용자-문제 매트릭스 생성
        self._create_user_item_matrix()
    
    def _create_user_item_matrix(self):
        """사용자-문제 매트릭스 생성 (딕셔너리 사용)"""
        print("🔧 사용자-문제 매트릭스 생성 중...")
        
        self.user_item_matrix = defaultdict(dict)
        
        for _, row in self.problem_data.iterrows():
            user = row['SOLVER_HANDLE']
            problem = row['PROBLEM_ID']
            level = row['SOLVED_LVL']
            
            self.user_item_matrix[user][problem] = level
        
        print(f"   - 매트릭스 생성 완료: {len(self.user_item_matrix)}명의 사용자")
    
    def _cosine_similarity(self, user1_problems, user2_problems):
        """두 사용자 간의 코사인 유사도 계산"""
        # 공통 문제 찾기
        common_problems = set(user1_problems.keys()) & set(user2_problems.keys())
        
        if len(common_problems) == 0:
            return 0.0
        
        # 벡터 내적 계산
        dot_product = sum(user1_problems[p] * user2_problems[p] for p in common_problems)
        
        # 벡터 크기 계산
        norm1 = math.sqrt(sum(user1_problems[p] ** 2 for p in user1_problems))
        norm2 = math.sqrt(sum(user2_problems[p] ** 2 for p in user2_problems))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def train_model(self):
        """모델 학습 (사용자 간 유사도 계산)"""
        if not self.user_item_matrix:
            raise ValueError("❌ 먼저 데이터를 로드해주세요!")
        
        print("🤖 모델 학습 시작...")
        
        users = list(self.user_item_matrix.keys())
        self.user_similarity = defaultdict(dict)
        
        # 모든 사용자 쌍에 대해 유사도 계산
        for i, user1 in enumerate(users):
            print(f"   진행률: {i+1}/{len(users)}", end='\r')
            
            for user2 in users:
                if user1 != user2:
                    similarity = self._cosine_similarity(
                        self.user_item_matrix[user1],
                        self.user_item_matrix[user2]
                    )
                    self.user_similarity[user1][user2] = similarity
        
        self.trained = True
        print("\n✅ 모델 학습 완료!")
    
    def get_user_recommendations(self, user_id, n_recommendations=10):
        """특정 사용자에게 문제 추천"""
        if not self.trained:
            raise ValueError("❌ 먼저 모델을 학습해주세요!")
        
        # 사용자가 존재하는지 확인
        if user_id not in self.user_item_matrix:
            print(f"⚠️ 사용자 '{user_id}'를 찾을 수 없습니다.")
            available_users = list(self.user_item_matrix.keys())[:5]
            print(f"   사용 가능한 사용자 예시: {available_users}")
            return []
        
        print(f"🎯 '{user_id}' 사용자를 위한 추천 생성 중...")
        
        # 사용자가 이미 푼 문제들
        solved_problems = set(self.user_item_matrix[user_id].keys())
        print(f"   - 이미 푼 문제 수: {len(solved_problems)}")
        
        # 유사한 사용자들 찾기
        similar_users = sorted(
            self.user_similarity[user_id].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # 상위 10명의 유사한 사용자
        
        # 추천 점수 계산
        recommendations = defaultdict(float)
        
        for similar_user, similarity_score in similar_users:
            if similarity_score <= 0:
                continue
                
            for problem, rating in self.user_item_matrix[similar_user].items():
                if problem not in solved_problems:
                    recommendations[problem] += similarity_score * rating
        
        if not recommendations:
            print("   - 추천할 수 있는 문제가 없습니다.")
            return []
        
        # 추천 점수 기준으로 정렬
        sorted_recommendations = sorted(
            recommendations.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 결과 포맷팅
        result = []
        for problem_id, score in sorted_recommendations[:n_recommendations]:
            result.append({
                'problem_id': int(problem_id),
                'estimated_rating': float(score),
                'actual_rating': None
            })
        
        print(f"✅ 추천 완료! 상위 {len(result)}개 문제:")
        
        return result
    
    def get_recommendations_for_new_user(self, new_user_df, n_recommendations=10):
        """
        새로운 사용자 데이터를 받아서 실시간 추천 생성
        
        Parameters:
        new_user_df: pandas DataFrame with columns ['SOLVER_HANDLE', 'PROBLEM_ID', 'SOLVED_LVL']
        n_recommendations: 추천할 문제 수
        """
        if not self.trained:
            raise ValueError("❌ 먼저 모델을 학습해주세요!")
        
        if new_user_df is None or len(new_user_df) == 0:
            print("❌ 사용자 데이터가 비어있습니다.")
            return []
        
        # 새 사용자 정보 추출
        user_handle = new_user_df['SOLVER_HANDLE'].iloc[0]
        print(f"🎯 새 사용자 '{user_handle}'을 위한 추천 생성 중...")
        
        # 새 사용자의 문제-난이도 매핑 생성
        new_user_problems = {}
        for _, row in new_user_df.iterrows():
            problem_id = row['PROBLEM_ID']
            level = row['SOLVED_LVL']
            new_user_problems[problem_id] = level
        
        solved_problems = set(new_user_problems.keys())
        print(f"   - 새 사용자가 푼 문제 수: {len(solved_problems)}")
        
        # 기존 사용자들과의 유사도 계산
        user_similarities = {}
        
        for existing_user, existing_problems in self.user_item_matrix.items():
            similarity = self._cosine_similarity(new_user_problems, existing_problems)
            if similarity > 0:  # 유사도가 0보다 큰 경우만
                user_similarities[existing_user] = similarity
        
        if not user_similarities:
            print("   - 유사한 사용자를 찾을 수 없습니다.")
            return self._get_popular_recommendations(solved_problems, n_recommendations)
        
        # 유사도 기준으로 상위 사용자들 선택
        similar_users = sorted(
            user_similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # 상위 10명의 유사한 사용자
        
        print(f"   - 유사한 사용자 {len(similar_users)}명 발견")
        
        # 추천 점수 계산
        recommendations = defaultdict(float)
        
        for similar_user, similarity_score in similar_users:
            for problem, rating in self.user_item_matrix[similar_user].items():
                if problem not in solved_problems:  # 아직 안 푼 문제만
                    recommendations[problem] += similarity_score * rating
        
        if not recommendations:
            print("   - 추천할 수 있는 문제가 없습니다.")
            return self._get_popular_recommendations(solved_problems, n_recommendations)
        
        # 추천 점수 기준으로 정렬
        sorted_recommendations = sorted(
            recommendations.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 결과 포맷팅
        result = []
        for problem_id, score in sorted_recommendations[:n_recommendations]:
            result.append({
                'problem_id': int(problem_id),
                'estimated_rating': float(score),
                'actual_rating': None
            })
        
        print(f"✅ 새 사용자 추천 완료! 상위 {len(result)}개 문제:")
        for i, rec in enumerate(result[:5], 1):
            print(f"   {i}. 문제 {rec['problem_id']}: 점수 {rec['estimated_rating']:.2f}")
        
        return result
    
    def _get_popular_recommendations(self, solved_problems, n_recommendations):
        """
        유사한 사용자를 찾을 수 없을 때 인기 문제 추천
        """
        print("   - 인기 문제를 추천합니다...")
        
        # 전체 사용자들이 많이 푼 문제들 중에서 추천
        problem_counts = defaultdict(int)
        problem_avg_levels = defaultdict(list)
        
        for user_problems in self.user_item_matrix.values():
            for problem, level in user_problems.items():
                if problem not in solved_problems:
                    problem_counts[problem] += 1
                    problem_avg_levels[problem].append(level)
        
        # 인기도와 평균 난이도를 고려한 점수 계산
        popular_problems = []
        for problem, count in problem_counts.items():
            if count >= 2:  # 최소 2명 이상이 푼 문제
                avg_level = sum(problem_avg_levels[problem]) / len(problem_avg_levels[problem])
                popularity_score = count * avg_level  # 인기도 * 평균 난이도
                popular_problems.append({
                    'problem_id': int(problem),
                    'estimated_rating': float(popularity_score),
                    'actual_rating': None
                })
        
        # 인기도 기준으로 정렬
        popular_problems.sort(key=lambda x: x['estimated_rating'], reverse=True)
        
        return popular_problems[:n_recommendations]
    
    def get_user_stats(self, user_id):
        """사용자 통계 정보"""
        if user_id not in self.user_item_matrix:
            return None
        
        user_problems = self.user_item_matrix[user_id]
        levels = list(user_problems.values())
        
        return {
            'total_solved': len(levels),
            'avg_level': sum(levels) / len(levels) if levels else 0,
            'min_level': min(levels) if levels else 0,
            'max_level': max(levels) if levels else 0,
            'level_distribution': dict(Counter(levels))
        }
    
    def get_recommendations_for_new_user_by_tag(self, new_user_df, tag_name, n_recommendations=10):
        """
        새로운 사용자에게 특정 태그 문제만 추천
        """
        if not self.trained:
            raise ValueError("❌ 먼저 모델을 학습해주세요!")
        
        if new_user_df is None or len(new_user_df) == 0:
            print("❌ 사용자 데이터가 비어있습니다.")
            return []
        
        # 새 사용자 정보 추출
        user_handle = new_user_df['SOLVER_HANDLE'].iloc[0]
        print(f"🎯 새 사용자 '{user_handle}'에게 '{tag_name}' 태그 문제 추천 중...")
        
        # 새 사용자의 문제-난이도 매핑 생성
        new_user_problems = {}
        for _, row in new_user_df.iterrows():
            problem_id = row['PROBLEM_ID']
            level = row['SOLVED_LVL']
            new_user_problems[problem_id] = level
        
        solved_problems = set(new_user_problems.keys())
        print(f"   - 새 사용자가 푼 문제 수: {len(solved_problems)}")
        
        # 기존 사용자들과의 유사도 계산
        user_similarities = {}

        for existing_user, existing_problems in self.user_item_matrix.items():
            similarity = self._cosine_similarity(new_user_problems, existing_problems)
            if similarity > 0:  # 유사도가 0보다 큰 경우만
                user_similarities[existing_user] = similarity
        
        if not user_similarities:
            print("   - 유사한 사용자를 찾을 수 없습니다.")
            return self._get_popular_recommendations_by_tag(solved_problems, tag_name, n_recommendations)
        
        # 유사도 기준으로 상위 사용자들 선택
        similar_users = sorted(
            user_similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # 상위 10명의 유사한 사용자
        
        print(f"   - 유사한 사용자 {len(similar_users)}명 발견")
        
        # 추천 점수 계산 (태그별 필터링 포함)
        recommendations = defaultdict(float)
        
        for similar_user, similarity_score in similar_users:
            for problem, rating in self.user_item_matrix[similar_user].items():
                if problem not in solved_problems:  # 아직 안 푼 문제만
                    # 간단한 태그 필터링 (문제 번호 범위 기반)
                    if self._is_tag_problem(problem, tag_name):
                        recommendations[problem] += similarity_score * rating

        if not recommendations:
            print(f"   - '{tag_name}' 태그 문제를 찾을 수 없습니다.")
            return self._get_popular_recommendations_by_tag(solved_problems, tag_name, n_recommendations)
        
        # 추천 점수 기준으로 정렬
        sorted_recommendations = sorted(
            recommendations.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 결과 포맷팅
        result = []
        for problem_id, score in sorted_recommendations[:n_recommendations]:
            result.append({
                'problem_id': int(problem_id),
                'estimated_rating': float(score),
                'actual_rating': None
            })
        
        print(f"✅ '{tag_name}' 태그 추천 완료! {len(result)}개 문제:")
        for i, rec in enumerate(result[:5], 1):
            print(f"   {i}. 문제 {rec['problem_id']}: 점수 {rec['estimated_rating']:.2f}")
        
        return result
            

    def _is_tag_problem(self, problem_id, tag_name):
        """
        문제 번호 기반으로 태그 추정 (간단한 버전)
        """
        tag_ranges = {
            'implementation': (1000, 2000),      # 구현
            'math': (1001, 3000),                # 수학  
            'greedy': (1200, 2500),              # 그리디
            'dp': (1000, 3000),                  # DP
            'graph': (1260, 2000),               # 그래프
            'string': (1152, 2000),              # 문자열
            'bruteforce': (1000, 2000),          # 브루트포스
        }
        
        # 태그 이름 정규화
        tag_key = tag_name.lower().replace('_', '').replace(' ', '')
        
        # 일부 태그 별칭 처리
        if 'dynamic' in tag_key or 'programming' in tag_key:
            tag_key = 'dp'
        if 'brute' in tag_key:
            tag_key = 'bruteforce'
        
        if tag_key in tag_ranges:
            min_range, max_range = tag_ranges[tag_key]
            return min_range <= problem_id <= max_range
        
        # 알 수 없는 태그면 모든 문제 허용
        return True
    
    def _get_popular_recommendations_by_tag(self, solved_problems, tag_name, n_recommendations):
        """
        태그별 인기 문제 추천
        """
        print(f"   - '{tag_name}' 태그 인기 문제를 추천합니다...")
        
        # 전체 사용자들이 많이 푼 문제들 중에서 태그별 필터링
        problem_counts = defaultdict(int)
        problem_avg_levels = defaultdict(list)
        
        for user_problems in self.user_item_matrix.values():
            for problem, level in user_problems.items():
                if problem not in solved_problems and self._is_tag_problem(problem, tag_name):
                    problem_counts[problem] += 1
                    problem_avg_levels[problem].append(level)
        
        # 인기도와 평균 난이도를 고려한 점수 계산
        popular_problems = []
        for problem, count in problem_counts.items():
            if count >= 1:  # 최소 1명 이상이 푼 문제
                avg_level = sum(problem_avg_levels[problem]) / len(problem_avg_levels[problem])
                popularity_score = count * avg_level  # 인기도 * 평균 난이도
                popular_problems.append({
                    'problem_id': int(problem),
                    'estimated_rating': float(popularity_score),
                    'actual_rating': None
                })
        
        # 인기도 기준으로 정렬
        popular_problems.sort(key=lambda x: x['estimated_rating'], reverse=True)
        
        return popular_problems[:n_recommendations]


    
    def save_model(self, model_path="simple_recommendation_model.pkl"):
        """학습된 모델 저장"""
        if not self.trained:
            raise ValueError("❌ 저장할 학습된 모델이 없습니다!")
        
        model_data = {
            'user_item_matrix': dict(self.user_item_matrix),
            'user_similarity': dict(self.user_similarity),
            'problem_data': self.problem_data
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 모델이 {model_path}에 저장되었습니다.")
    
    def load_model(self, model_path="simple_recommendation_model.pkl"):
        """저장된 모델 로드"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"❌ {model_path} 파일을 찾을 수 없습니다!")
        
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.user_item_matrix = defaultdict(dict, model_data['user_item_matrix'])
        self.user_similarity = defaultdict(dict, model_data['user_similarity'])
        self.problem_data = model_data['problem_data']
        self.trained = True
        
        print(f"📦 모델이 {model_path}에서 로드되었습니다.")

# 🎯 사용 예시 함수
def demo_simple_recommendation_system():
    """간단한 추천 시스템 데모"""
    print("🚀 순수 Python 추천 시스템 데모 시작")
    
    # 1. 추천 시스템 초기화
    recommender = SimpleCollaborativeRecommender()
    
    # 2. 데이터 로드
    data_path = "static/problem_for_each_user.csv"
    if os.path.exists(data_path):
        recommender.load_data(data_path)
    else:
        print("❌ 데이터 파일이 없습니다.")
        print("📝 테스트 데이터를 생성합니다...")
        create_test_data()
        recommender.load_data(data_path)
    
    # 3. 모델 학습
    recommender.train_model()
    
    # 4. 추천 생성 (예시 사용자)
    if len(recommender.user_item_matrix) > 0:
        sample_users = list(recommender.user_item_matrix.keys())[:3]
        
        for user in sample_users:
            print(f"\n{'='*50}")
            print(f"사용자: {user}")
            
            # 사용자 통계
            stats = recommender.get_user_stats(user)
            print(f"푼 문제 수: {stats['total_solved']}, 평균 난이도: {stats['avg_level']:.1f}")
            
            # 추천
            recommendations = recommender.get_user_recommendations(user, 5)
            
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. 문제 {rec['problem_id']}: "
                    f"추천 점수 {rec['estimated_rating']:.2f}")
    
    # 5. 모델 저장
    recommender.save_model()

def create_test_data():
    """테스트용 데이터 생성"""
    print("📝 테스트 데이터 생성 중...")
    
    import random
    
    # 가상의 사용자와 문제 데이터 생성
    users = [f"user{i}" for i in range(1, 21)]  # 20명의 사용자
    problems = list(range(1000, 1100))  # 100개의 문제
    
    data = []
    for user in users:
        # 각 사용자가 10-30개의 문제를 랜덤하게 풀었다고 가정
        user_problems = random.sample(problems, random.randint(10, 30))
        for problem in user_problems:
            level = random.randint(1, 30)  # 랜덤 난이도
            data.append({
                'SOLVER_HANDLE': user,
                'PROBLEM_ID': problem,
                'SOLVED_LVL': level
            })
    
    # CSV 파일로 저장
    os.makedirs("static", exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv("static/problem_for_each_user.csv", index=False)
    print("✅ 테스트 데이터 생성 완료!")

if __name__ == "__main__":
    demo_simple_recommendation_system()