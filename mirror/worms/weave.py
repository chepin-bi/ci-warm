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

# weave 虫（4h·茧）：织四层——知识谱系/理论核心/范式空间/模型工具
def main():
    latest,_=get_file("chepin-ai/ci-library","weave/crawl/latest.md")
    graph,_=get_file("chepin-ai/ci-library","weave/yoneda/graph.json")
    fleet,_=get_file("chepin-ai/ci-control","bridge/fleet.json")
    ops,_=get_file("chepin-ai/ci-control","inbox/ops.json")
    g=json.loads(graph) if graph else {}
    fl=json.loads(fleet) if fleet else {}
    tr=gh("/repos/chepin-ai/ci-library/git/trees/main?recursive=1")
    wv=[x["path"] for x in (tr or {}).get("tree",[]) if x["path"].startswith("weave/")]
    L=["# 四层织体（weave 虫 %sZ 班）\n" % TS]
    L.append("## 一、知识谱系\n- yoneda 图：%d 节点 / %d 边\n- weave/ 总件数：%d\n" % (len(g.get("nodes",{})), len(g.get("edges",[])), len(wv)))
    for e in g.get("edges",[]): L.append("- 边 %s: %s→%s（%s）" % (e.get("id"), e.get("from"), e.get("to"), e.get("kind")))
    L.append("\n## 二、理论核心\n")
    for p in wv:
        if "yoneda/" in p or "sparks/" in p: L.append("- "+p)
    L.append("\n## 三、范式空间（制度）\n")
    for k,v in (fl.get("fleet") or {}).items(): L.append("- %s｜%s｜%s" % (k, v.get("repo"), v.get("gov")))
    L.append("\n## 四、模型工具\n")
    o=json.loads(ops) if ops else {}
    L.append("- 指令轨 op：%s" % "、".join((o.get("ops") or {}).keys()))
    wf=gh("/repos/chepin-ai/ci-control/contents/.github/workflows") or []
    for w in wf: L.append("- ci-control 工作流："+w["name"])
    put_file("chepin-ai/ci-library","weave/layers.md","\n".join(L),"weave: 四层织体 %s"%TS)
    print("weave 班完")
main()
