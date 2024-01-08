import re
import datetime
import requests
import json
import urllib3
import os
import shutil
import git

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
print("[INFO] now start process json file!")
with open('./url3.json', 'r', encoding='utf-8') as f, open('./url_new.json', 'w', encoding='utf-8') as f2:
    lines = f.readlines()  # 逐行读取文件内容并存储到列表lines中
    content = ''.join([line for line in lines if not line.strip().startswith('//')])
    urlJson = json.loads(content)


reList = ["https://ghproxy.com/https://raw.githubusercontent.com", "https://raw.fgit.cf",
          "https://gcore.jsdelivr.net/gh", "https://raw.iqiq.io",
          "https://github.moeyy.xyz/https://raw.githubusercontent.com", "https://fastly.jsdelivr.net/gh",
          "https://cdn.jsdelivr.net/gh"]
reRawList = [False, False,
             True, False,
             False, True,
             True]


def adjust_proxy():
    for reI in range(len(reList)-1, -1, -1):
        try:
            print("[INFO] try proxy: {}".format(reList[reI]))
            requests.get(reList[reI], verify=False)
        except Exception as e:
            print("[Error] proxy url {} can not access!".format(reList[reI]))
            reList.pop(reI)
            reRawList.pop(reI)
            continue


def adjust_url(rawFlag, info, reI, pattern):
    info, num = re.subn(pattern, reList[reI]+'/', info)
    if num != 0:
        if rawFlag:
            if re.findall(r'/raw/', info):
                info = info.replace("/raw/", "@")
            else:
                info = re.sub(r'/(main|master)/', '@'+r'\1/', info)
        else:
            info = info.replace("/raw/", "/")
    return info


def get_conf(urlOri, pattern):
    urlReq = None
    reI = 0
    if re.findall(pattern, urlOri):
        for reI in range(len(reList)):
            url = adjust_url(reRawList[reI], urlOri, reI, pattern)
            try:
                urlReq = requests.get(url, verify=False, timeout=10)
            except Exception:
                print("[ERROR] url {} can not access".format(url))
                continue
            if urlReq.status_code != 200:
                print("[ERROR] response of url {} is not 200".format(url))
                continue
            break
    else:
        try:
            urlReq = requests.get(urlOri, verify=False, timeout=10)
        except Exception:
            print("[ERROR] url {} can not access".format(urlOri))
        if urlReq is not None and urlReq.status_code != 200:
            print("[ERROR] response of url {} is not 200".format(urlOri))
    return urlReq, reI


def adjust_conf(urlItem, info, reI, pattern, index):
        urlName = urlItem["name"]
        urlPath = urlItem["url"].rsplit('/', 1)[0] + '/'
        if urlName != "gaotianliuyun_0707":
            info = info.replace("'./", "'" + urlPath) \
                .replace('"./', '"' + urlPath)
        info = adjust_url(reRawList[reI], info, reI, pattern)
        fp = open("./tv/" + str(index) + ".json", "w+", encoding='utf-8')
        fp.write(info)
        fp.close()


def proc_git():
    repo = git.Repo.init(path='./')
    repo.git.add(all=True)
    repo.git.commit(m="collected for private use")
    print(repo.remotes)
    try:
        remote = repo.create_remote(name='tv', url='https://github.com/zhenzhonghu/duocang.git')
    except:
        remote = repo.remote(name="tv")
    remote_branch = repo.refs['tv/master']
    repo.heads.master.set_tracking_branch(remote_branch)
    remote.pull(rebase=True)
    remote.push()


if __name__ == '__main__':
    if os.path.exists("./tv/"):
        shutil.rmtree("./tv")
    os.mkdir("./tv")
    adjust_proxy()
    if len(reRawList) == 0:
        print("[ERROR] no proxy can access!")
    else:
        fe = open("./tv/error", "w+", encoding='utf-8')
        urlList = []
        pattern = re.compile(
            r'https://.*ghproxy.*/https://.*?github.*?/|https://github.com/|https://raw.githubusercontent.com'
            r'https://raw.iqiq.io/')
        index = 0
        for item in urlJson:
            print("[INFO] try url {} ".format(item["url"]))
            reI = 0
            try:
                urlReq = requests.get(item["url"], verify=False, timeout=10)
            except Exception as e:
                urlReq, reI = get_conf(item["url"], pattern)
            if urlReq is not None and urlReq.status_code == 200:
                adjust_conf(item, urlReq.text, reI, pattern, index)
                urlList.append({"url": "https://gitee.com/zhenzhonghu/tvbox/raw/master/tv/"+ str(index) +".json", "name": item["name"]})
                index += 1
            else:
                fe.write("can not access the url " + item["url"] + "\n")
        fe.close()
        with open("./url_new.json", 'w', encoding='utf-8') as fu:
            data = json.dumps({"warningText": "接口免费，切勿付费。 网络收集，按需取用。", "urls": urlList}, ensure_ascii=False)
            data = re.sub(r'({"url|"urls)', '\n'+r'\1', data)
            fu.write(data)

    proc_git()


