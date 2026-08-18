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

# spider 虫（6h·网）：断边检测 → 修复工单（去重，免刷屏）
def main():
    findings=[]
    now=time.time()
    # 1) directives 超 48h 无 ack
    mb=gh("/repos/chepin-ai/ci-logs/contents/mailbox") or []
    for m_ in mb:
        if not m_["name"].endswith(".json"): continue
        doc,_=get_file("chepin-ai/ci-logs","mailbox/"+m_["name"])
        if not doc: continue
        d=json.loads(doc); acks={a.get("id") for a in (d.get("acks") or [])}
        for dr in (d.get("directives") or []):
            try: age=(now-time.mktime(time.strptime(dr.get("ts","2026-01-01T00:00:00Z"),"%Y-%m-%dT%H:%M:%SZ")))/3600
            except Exception: age=0
            if age>48: findings.append("mailbox %s：directive %s 已 %.0fh 未见回响" % (m_["name"], dr.get("id"), age))
    # 2) backlog 逾期
    bl,_=get_file("chepin-ai/ci-control","bridge/backlog.json")
    if bl:
        for it in (json.loads(bl).get("items") or []):
            if it.get("status") not in ("done","cancelled") and it.get("due") and it["due"]<time.strftime("%Y-%m-%d",time.gmtime()):
                findings.append("backlog 逾期：%s（%s，due %s）" % (it["id"], it["title"][:40], it["due"]))
    # 3) outbox 失联
    reg,_=get_file("chepin-ai/ci-control","bridge/outboxes.json")
    for n,cfg in (json.loads(reg).get("sessions") or {}).items():
        u=cfg.get("url")
        if u and not fetch(u): findings.append("outbox 失联：%s" % n)
    # 去重（state 存 finding 指纹）
    st_text,_=get_file("chepin-ai/ci-library","weave/spider/state.json")
    st=json.loads(st_text) if st_text else {"seen":[]}
    new=[f for f in findings if hashlib.sha256(f.encode()).hexdigest()[:12] not in st["seen"]]
    rpt="# spider 巡检 %sZ\n\n发现 %d 项（新增 %d）\n\n%s\n" % (TS, len(findings), len(new), "\n".join("- "+f for f in findings) or "- 无断边")
    put_file("chepin-ai/ci-library","weave/spider/report-%s.md"%TS,rpt,"spider: 巡检 %s"%TS)
    put_file("chepin-ai/ci-library","weave/spider/latest.md",rpt,"spider: latest")
    if new:
        st["seen"]=(st["seen"]+[hashlib.sha256(f.encode()).hexdigest()[:12] for f in new])[-200:]
        put_file("chepin-ai/ci-library","weave/spider/state.json",json.dumps(st,ensure_ascii=False,indent=1),"spider: 去重状态")
        gh("/repos/chepin-ai/ci-inbox/issues/144/comments","POST",{"body":"thr: SPIDER-工单\ndtag: SPIDER-%s\n\n%s\n\n—— spider（三虫·网，自动工单）" % (TS, "\n".join("- "+f for f in new))})
        # 自动出工单（SPIDER-WO-1）：每条新断边 → mailbox/cisvr.json directive，断边→工单→回响闭环
        mb,_=get_file("chepin-ai/ci-logs","mailbox/cisvr.json")
        doc=json.loads(mb) if mb else {"directives":[]}
        have={d.get("id") for d in doc.get("directives",[])}
        nowz=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for f in new:
            did="SPIDER-"+hashlib.sha256(f.encode()).hexdigest()[:12]
            if did in have: continue
            doc.setdefault("directives",[]).append({"id":did,"prio":"mid","ts":nowz,"todo":"[断边工单] "+f})
        put_file("chepin-ai/ci-logs","mailbox/cisvr.json",json.dumps(doc,ensure_ascii=False,indent=1),"spider: 工单 %d 项"%len(new))
    print("spider 班完：%d 发现 %d 新增" % (len(findings), len(new)))
main()
