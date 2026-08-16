#!/usr/bin/env python3
# respond 虫（2h·应答面，RESPOND-1/v1）：自动分级分诊 —— 只应答/路由/登记，绝不执行
# 授权矩阵：本虫写面仅限 ci-library/weave/respond/* 与 ci-control/mailbox/cisvr.json；
#           任何实质执行仍只走 [CMD] HMAC 密封轨（C 组凭证公理），本虫无权触碰业务仓。
# 灭活开关：ci-control/bridge/RESPOND_OFF 存在即全线静默（根键仪式位，D 组可逆）。
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
TS=time.strftime("%Y%m%d-%H%M", time.gmtime())
NOW=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

CATS=[("应急", ["应急","紧急","urgent","emerg","宕","泄漏"], "即刻回响+prio:fast 工单"),
      ("指令", ["裁决","指令","决定","通令","发布","下发"], "入裁决队列，当班会签"),
      ("提案", ["提案","建议","方案","要不要","是否可以"], "backlog 候选，72h 内裁决"),
      ("问询", ["？","?","如何","什么","是否","能不能"], "24h 内作答"),
      ("备录", [], "登记入谱，无 SLA")]
SELF_MARKS=("—— cisvr","dtag:","thr:","—— spider","—— respond","📦 密文回执")

def classify(body):
    for name, kws, sla in CATS:
        if any(k in body for k in kws): return name, sla
    return "备录", "登记入谱，无 SLA"

def escalate():
    # M4-ESCALATE：cisvr SLA 超时（>24h）未应答的大厅请求 → 升级 cisbr 按 E5 补位（每班硬上限 10 件，防爆刷）
    est_text,_=get_file("chepin-ai/ci-library","weave/respond/esc-state.json")
    est=json.loads(est_text) if est_text else {"escalated":[]}
    done=set(est.get("escalated",[]))
    cmts=gh("/repos/chepin-ai/ci-inbox/issues/144/comments?per_page=100") or []
    now=time.time()
    cands=[]
    for c in cmts:
        body=c.get("body") or ""
        if not any(k in body for k in ("@cisvr","cisvr，请","REQ.","请 cisvr")): continue
        if c["id"] in done: continue  # 同一评论不重复升级
        age_h=(now-time.mktime(time.strptime(c["created_at"],"%Y-%m-%dT%H:%M:%SZ")))/3600
        if age_h<=24: continue
        answered=False  # 简化判定：之后无任何 cisvr 回帖引用其 id/dtag
        for r in cmts:
            if r["created_at"]<=c["created_at"]: continue
            rb=r.get("body") or ""
            if ("—— cisvr" in rb or "thr:" in rb) and str(c["id"]) in rb:
                answered=True; break
        if answered: continue
        cands.append((c,age_h))
    if not cands:
        print("escalate：无超时件"); return
    cands=cands[:10]  # 硬上限：每班最多升级 10 件
    esc=[]
    for c,age_h in cands:
        eid="ESC-"+hashlib.sha256(("esc%d"%c["id"]).encode()).hexdigest()[:10]
        esc.append({"eid":eid,"id":c["id"],"age_h":age_h,
                    "head":(c.get("body") or "").split("\n")[0][:40]})
    # 1) 注入指令到 mailbox/cisbr.json（沿用 cisvr 注入法，目标改 cisbr）
    mb,_=get_file("chepin-ai/ci-control","mailbox/cisbr.json")
    doc=json.loads(mb) if mb else {"directives":[]}
    have={d.get("id") for d in doc.get("directives",[])}
    n=0
    for e in esc:
        if e["eid"] in have: continue
        doc.setdefault("directives",[]).append({"id":e["eid"],"kind":"escalation","prio":"fast",
            "reason":"cisvr SLA 超时未应答","ref_comment_id":e["id"],"ts":NOW})
        n+=1
    if n: put_file("chepin-ai/ci-control","mailbox/cisbr.json",json.dumps(doc,ensure_ascii=False,indent=1),"respond: ESC 升级 %d 项"%n)
    # 2) 大厅 #144 合并回复帖（一条，防刷屏）
    batch="ESC-"+hashlib.sha256(("|".join(e["eid"] for e in esc)).encode()).hexdigest()[:10]
    gh("/repos/chepin-ai/ci-inbox/issues/144/comments","POST",{"body":
        "thr: ESCALATION-补位\ndtag: %s\n\ncisvr SLA 超时未应答 %d 件，升级 cisbr 按 E5 补位：\n%s\n\n—— cisvr（ESCALATE 块 · cisbr 请按 E5 补位）" % (
        batch, len(esc), "\n".join("- #%d（%s）已超时 %.0fh｜%s" % (e["id"], e["eid"], e["age_h"], e["head"]) for e in esc))})
    # 3) 升级记录落盘（prev/sha 链式约定同 log）
    prev,_=get_file("chepin-ai/ci-library","weave/respond/esc-latest.md")
    prev_sha=hashlib.sha256(prev.encode()).hexdigest()[:16] if prev else "GENESIS"
    ebody="# ESCALATE 补位升级 %sZ\nprev: %s\n\n%s\n" % (TS, prev_sha,
        "\n".join("- %s → comment#%d（超时 %.0fh）｜%s" % (e["eid"], e["id"], e["age_h"], e["head"]) for e in esc))
    put_file("chepin-ai/ci-library","weave/respond/esc-%s.md"%TS,ebody,"respond: 升级 %s"%TS)
    put_file("chepin-ai/ci-library","weave/respond/esc-latest.md",ebody,"respond: esc-latest")
    # 4) 状态去重（ref_comment_id）
    est["escalated"]=(est.get("escalated",[])+[e["id"] for e in esc])[-500:]
    put_file("chepin-ai/ci-library","weave/respond/esc-state.json",json.dumps(est,ensure_ascii=False,indent=1),"respond: 升级水位")
    print("escalate 班完：%d 件已升级 cisbr" % len(esc))

def main():
    if get_file("chepin-ai/ci-control","bridge/RESPOND_OFF")[0] is not None:
        print("RESPOND_OFF 在场，静默下班"); return
    st_text,_=get_file("chepin-ai/ci-library","weave/respond/state.json")
    st=json.loads(st_text) if st_text else {"last_id":0,"triaged":[]}
    items=[]
    cmts=gh("/repos/chepin-ai/ci-inbox/issues/144/comments?per_page=100") or []
    for c in cmts:
        if c["id"]<=st["last_id"]: continue
        body=c.get("body") or ""
        if any(m in body for m in SELF_MARKS): continue  # 只分诊外部来言，防自激循环
        cat,sla=classify(body)
        items.append({"kind":"lobby","ref":"#144/%d"%c["id"],"ts":c["created_at"],
                      "cat":cat,"sla":sla,"head":body[:60].replace("\n"," ")})
    for it in (gh("/repos/chepin-ai/ci-inbox/issues?state=open&per_page=20") or []):
        t=it.get("title","")
        if t.startswith("[CMD]"): continue
        fp=hashlib.sha256(("issue%d"%it["number"]).encode()).hexdigest()[:12]
        if fp in st["triaged"]: continue
        cat,sla=classify(t+"\n"+(it.get("body") or ""))
        items.append({"kind":"issue","ref":"#%d"%it["number"],"ts":it["created_at"],
                      "cat":cat,"sla":sla,"head":t[:60],"fp":fp})
    if cmts: st["last_id"]=max(st["last_id"], max(c["id"] for c in cmts))
    if not items:
        escalate()
        print("respond 班完：无新言"); return
    # 1) 织面日志（链：sha 前行）
    prev,_=get_file("chepin-ai/ci-library","weave/respond/latest.md")
    prev_sha=hashlib.sha256(prev.encode()).hexdigest()[:16] if prev else "GENESIS"
    body="# RESPOND 分诊 %sZ\nprev: %s\n\n%s\n" % (TS, prev_sha,
        "\n".join("- [%s] %s（%s）→ %s｜%s" % (i["cat"], i["ref"], i["ts"], i["sla"], i["head"]) for i in items))
    put_file("chepin-ai/ci-library","weave/respond/log-%s.md"%TS,body,"respond: 分诊 %s"%TS)
    put_file("chepin-ai/ci-library","weave/respond/latest.md",body,"respond: latest")
    # 2) 自我工单：注入 mailbox/cisvr.json（去重）
    mb,_=get_file("chepin-ai/ci-control","mailbox/cisvr.json")
    doc=json.loads(mb) if mb else {"directives":[]}
    have={d.get("id") for d in doc.get("directives",[])}
    for i in items:
        did="RESP-"+hashlib.sha256(i["ref"].encode()).hexdigest()[:10]
        if did in have: continue
        doc.setdefault("directives",[]).append({"id":did,"prio":"fast" if i["cat"]=="应急" else "mid",
            "ts":NOW,"todo":"[%s应答] %s（%s）：%s —— %s"%(i["cat"],i["ref"],i["ts"],i["head"],i["sla"])})
    put_file("chepin-ai/ci-control","mailbox/cisvr.json",json.dumps(doc,ensure_ascii=False,indent=1),"respond: 工单 %d 项"%len(items))
    # 3) 大厅回响（合并一条，防刷屏）
    gh("/repos/chepin-ai/ci-inbox/issues/144/comments","POST",{"body":
        "thr: RESPOND-分诊\ndtag: RESPOND-%s\n\n新言 %d 条，已分级路由：\n%s\n\n—— respond（分级应答虫，只路由不执行）" % (
        TS, len(items), "\n".join("- [%s] %s → %s" % (i["cat"], i["ref"], i["sla"]) for i in items))})
    for i in items:
        if i.get("fp"): st["triaged"].append(i["fp"])
    st["triaged"]=st["triaged"][-300:]
    put_file("chepin-ai/ci-library","weave/respond/state.json",json.dumps(st,ensure_ascii=False,indent=1),"respond: 水位")
    escalate()
    print("respond 班完：%d 条已分诊" % len(items))
main()
