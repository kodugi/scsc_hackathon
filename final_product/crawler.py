import random, requests, json, os, time, pandas as pd

class Problem:
    def __init__(self):
        self.idx = []
        self.input_hash = []
        self.input_title = []
        self.input_level = []
        self.input_tag = []
        self.solver_handle = []
handles = []

SAMPLE_SIZE_PER_PAGE = 5
MAX_PAGE = 249 #249
MAX_USER_PAGE = 4500
PAGE_SAMPLE_SIZE = 5

def appending(problem, hash, title, level, tags, solver):
    problem.idx.append(hash)
    problem.input_hash.append(hash)
    problem.input_title.append(title)
    problem.input_level.append(level)
    problem.input_tag.append(tags)
    problem.solver_handle.append(solver)

def crawlUserList(page):
    time.sleep(1)
    url = "https://solved.ac/api/v3/ranking/class"
    querystring = {"query": "", "page": f"{page}"}

    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers, params=querystring)

    temp = dict()
    temp["item"] = json.loads(response.text).get("items")
    for item in random.sample(temp["item"], k=min(SAMPLE_SIZE_PER_PAGE, len(temp["item"]))):
        handles.append(item["handle"])
    
def crawlProblem(page, problem, handle=None):
    time.sleep(0.5)
    url = "https://solved.ac/api/v3/search/problem"
    if(handle is None):
        querystring = {"query": "", "page": f"{page}"}
    else:
        querystring = {"query": f"solved_by:{handle}", "page": f"{page}"}

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.request("GET", url, headers=headers, params=querystring)

        temp = dict()
        temp["item"] = json.loads(response.text).get("items")
        for item in temp["item"]:
            #print(item)
            hash = int(item.get("problemId"))
            title = item.get("titleKo")
            level = item.get("level")
            tags = ""

            info = item.get("tags")
            length = len(info)
            for idx, tag in enumerate(info):
                temp_tag = tag.get("displayNames")
                tags += temp_tag[1].get("short").replace(' ', '_')

                if idx == length - 1:
                    continue
                tags += " "

            appending(problem, hash, title, level, tags, handle)
        return len(temp["item"])
    except:
        return None

def main():
    PATH = os.path.dirname(__file__)
    '''
    #이용자 크롤링
    problemForEachUser = Problem()
    for i in random.sample(range(1, MAX_USER_PAGE), k=PAGE_SAMPLE_SIZE):
        print(i)
        crawlUserList(i)
    #이용자별로 푼 문제 크롤링
    for handle in handles:
        for i in range(1, MAX_PAGE):
            print(f"crawling from {handle} page {i}")
            if(crawlProblem(i, problemForEachUser, handle) == 0):
                break
    
    df = pd.DataFrame({"SOLVER_HANDLE" : problemForEachUser.solver_handle, "PROBLEM_ID" : problemForEachUser.idx, "TITLE_NM" : problemForEachUser.input_title, "TAGS_NM" : problemForEachUser.input_tag, "SOLVED_LVL" : problemForEachUser.input_level, "HASH_ID" : problemForEachUser.input_hash})
    df.to_csv(PATH + "/static/problem_for_each_user.csv", index=False, encoding="utf8")
    '''
    #모든 문제 크롤링
    allProblem = Problem()
    i = 1
    while(True):
        print(f"crawling {i} page")
        result = crawlProblem(i, allProblem)
        print(result)
        if(not result):
            break
        i += 1
    df = pd.DataFrame({"PROBLEM_ID" : allProblem.idx, "TITLE_NM" : allProblem.input_title, "TAGS_NM" : allProblem.input_tag, "SOLVED_LVL" : allProblem.input_level, "HASH_ID" : allProblem.input_hash})
    df.to_csv(PATH + "/static/problem_all.csv", encoding="utf8")

if __name__ == "__main__":
    main()