#!/usr/bin/env python3
# worms 公共件：零凭证脚本本体，App token 经 env 注入（公仓分钟，免费面）
import os, json, base64, time, urllib.request, urllib.error, hashlib, re
GH="https://api.github.com"; TOK=os.environ["GH_TOKEN"]
H={"Authorization": f"Bearer {TOK}", "Accept":"application/vnd.github+json"}
def gh(p, m="GET", b=None):
    r=urllib.request.Request(p if p.startswith("http") else GH+p, method=m,
        data=json.dumps(b).encode() if b is not None else None, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=25) as x:
            d=x.read(); return json.loads(d or b"{}")
    except urllib.error.HTTPError as e: print("gh",m,p,"->",e.code); return None
    except Exception as e: print("gh",m,p,"->",type(e).__name__); return None
def get_file(repo, path):
    d=gh("/repos/%s/contents/%s"%(repo,path))
    return (base64.b64decode(d["content"]).decode(), d["sha"]) if d and "content" in d else (None,None)
def put_file(repo, path, text, msg):
    _,sha=get_file(repo,path)
    b={"message":msg,"content":base64.b64encode(text.encode()).decode()}
    if sha: b["sha"]=sha
    return bool(gh("/repos/%s/contents/%s"%(repo,path),"PUT",b))
def fetch(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"ci-worm/1.0"}),timeout=15).read().decode("utf-8","replace")
    except Exception: return None
TS=time.strftime("%Y%m%d-%H%M", time.gmtime())

# crawl 虫（2h·穴）：遍历采集体系原料 → 爬单
def main():
    out=["# 爬单 %sZ\n" % TS]
    cs=gh("/repos/chepin-ai/ci-inbox/issues/144/comments?per_page=25") or []
    out.append("## 大厅最近 %d 帖" % len(cs))
    for c in cs: out.append("- #%s %s %s: %s" % (c["id"], c["created_at"][:16], c["user"]["login"], (c["body"] or "")[:120].replace("\n"," ")))
    cm=gh("/repos/chepin-ai/ci-control/commits?per_page=5") or []
    out.append("\n## ci-control 最近提交")
    for c in cm: out.append("- %s %s" % (c["sha"][:8], c["commit"]["message"][:80].replace("\n"," ")))
    tr=gh("/repos/chepin-ai/ci-library/git/trees/main?recursive=1")
    wv=[x["path"] for x in (tr or {}).get("tree",[]) if x["path"].startswith("weave/")]
    out.append("\n## ci-library weave/ 现状（%d 件）" % len(wv))
    for p in wv[:60]: out.append("- "+p)
    reg,_=get_file("chepin-ai/ci-control","bridge/outboxes.json")
    out.append("\n## outbox 注册表实测")
    for n,cfg in (json.loads(reg).get("sessions") or {}).items():
        u=cfg.get("url"); st="未注册" if not u else ("可达" if fetch(u) else "不可达")
        out.append("- %s: %s" % (n, st))
    mb=gh("/repos/chepin-ai/ci-logs/contents/mailbox") or []
    out.append("\n## mailbox（%d 件）" % len(mb))
    for m_ in mb: out.append("- "+m_["name"])
    iss=gh("/repos/chepin-ai/ci-inbox/issues?state=open&per_page=10") or []
    out.append("\n## ci-inbox open（%d+）" % len(iss))
    for i in iss: out.append("- #%d %s" % (i["number"], i["title"][:70]))
    body="\n".join(out)
    put_file("chepin-ai/ci-library","weave/crawl/raw-%s.md"%TS,body,"crawl: 爬单 %s"%TS)
    put_file("chepin-ai/ci-library","weave/crawl/latest.md",body,"crawl: latest 爬单")
    print("crawl 班完，爬单 %d 行" % len(out))
main()
