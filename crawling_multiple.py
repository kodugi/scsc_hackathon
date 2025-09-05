import random, requests, time, json, pandas as pd

idx, input_hash, input_title, input_level, input_tag, solver_handle = [], [], [], [], [], []
handles = []

SAMPLE_SIZE = 5
MAX_PAGE = 249
MAX_USER_PAGE = 10
PAGE_SAMPLE_SIZE = 1

def appending(hash, title, level, tags, solver):
    idx.append(hash)
    input_hash.append(hash)
    input_title.append(title)
    input_level.append(level)
    input_tag.append(tags)
    solver_handle.append(solver)

def crawlUserList(page):
    url = "https://solved.ac/api/v3/search/user"
    querystring = {"query": "", "page": f"{page}"}

    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers, params=querystring)

    temp = dict()
    temp["item"] = json.loads(response.text).get("items")
    for item in random.sample(temp["item"], k=SAMPLE_SIZE):
        handles.append(item["handle"])
    
def crawl(page, handle):
    url = "https://solved.ac/api/v3/search/problem"
    querystring = {"query": f"solved_by:{handle}", "page": f"{page}"}

    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers, params=querystring)

    temp = dict()
    temp["item"] = json.loads(response.text).get("items")
    for item in temp["item"]:
        hash = int(item.get("problemId"))
        title = item.get("titleKo")
        level = item.get("level")
        tags = ""

        info = item.get("tags")
        length = len(info)
        for idx, tag in enumerate(info):
            temp_tag = tag.get("displayNames")
            tags += temp_tag[1].get("short")

            if idx == length - 1:
                continue
            tags += " "

        appending(hash, title, level, tags, handle)
    return len(temp["item"])

def make_csv():
    df = pd.DataFrame({"SOLVER_HANDLE" : solver_handle, "PROBLEM_ID" : idx, "TITLE_NM" : input_title, "TAGS_NM" : input_tag, "SOLVED_LVL" : input_level, "HASH_ID" : input_hash})
    df.to_csv("problem_multiple.csv", index=False, encoding="utf8")

def main():
    for i in random.sample(range(1, MAX_USER_PAGE), k=PAGE_SAMPLE_SIZE):
        print(i)
        crawlUserList(i)
    
    for handle in handles:
        for i in range(1, MAX_PAGE):
            print(f"crawling from {handle} page {i}")
            if(crawl(i, handle) == 0):
                break
    
    make_csv()

if __name__ == "__main__":
    main()