import requests, time, json, pandas as pd

idx, input_hash, input_title, input_level, input_tag = [], [], [], [], []

def appending(hash, title, level, tags):
    idx.append(hash)
    input_hash.append(hash)
    input_title.append(title)
    input_level.append(level)
    input_tag.append(tags)

def crawl(page):
    url = "https://solved.ac/api/v3/search/problem"
    querystring = {"query": " ", "page": f"{page}"}

    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers, params=querystring)

    temp = dict()
    temp["item"] = json.loads(response.text).get("items")
    for item in temp["item"]:
        print(item)
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

        appending(hash, title, level, tags)

def make_csv():
    df = pd.DataFrame({"PROBLEM_ID" : idx, "TITLE_NM" : input_title, "TAGS_NM" : input_tag, "SOLVED_LVL" : input_level, "HASH_ID" : input_hash})
    df.to_csv("problem.csv", index=False, encoding="utf8")

def main():
    for i in range(1, 2):
        print(f"crawling {i} page now still {249 - i} to go")
        crawl(i)

        time.sleep(12)

    make_csv()

if __name__ == "__main__":
    main()