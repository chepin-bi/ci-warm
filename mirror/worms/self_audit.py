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

# self-audit（6h）：cisvr 自省/自审/自检/自纠/自测——元公理的机器化执行
PATS=[r"ghp_[A-Za-z0-9]{20,}",r"gho_[A-Za-z0-9]{20,}",r"ghs_[A-Za-z0-9]{20,}",r"ghr_[A-Za-z0-9]{20,}",
      r"github_pat_[A-Za-z0-9_]{30,}",r"sk-[A-Za-z0-9]{20,}",r"-----BEGIN [A-Z ]*PRIVATE KEY-----"]
def scan(text, where, findings):
    for p in PATS:
        if re.search(p, text): findings.append("E804 疑似密钥泄漏@%s（模式 %s）" % (where, p[:12]))
def main():
    findings=[]
    # 1) 公仓密钥泄漏扫描（cisvr 领地全树）
    for repo in ("chepin-ai/ci-control",):
        tr=gh("/repos/%s/git/trees/main?recursive=1"%repo)
        for x in (tr or {}).get("tree",[]):
            if x["type"]=="blob" and x.get("size",0)<200000:
                t,_=get_file(repo,x["path"])
                if t: scan(t, repo+"/"+x["path"], findings)
    # 2) 大厅最近 50 帖扫描
    for c in (gh("/repos/chepin-ai/ci-inbox/issues/144/comments?per_page=50") or []):
        scan(c.get("body") or "", "lobby#%s"%c["id"], findings)
    # 3) schema 漂移：poller OPS 词表 vs inbox/ops.json（LX-20260816-01 哨兵）
    pol,_=get_file("chepin-ai/ci-control","inbox/poller.py")
    oj,_=get_file("chepin-ai/ci-control","inbox/ops.json")
    if pol and oj:
        m=re.search(r"OPS\s*=\s*\{([^}]*)\}", pol, re.S)
        live=set(re.findall(r'"(.*?)"\s*:', m.group(1))) if m else set()
        docd=set((json.loads(oj).get("ops") or {}).keys())
        if live!=docd: findings.append("schema 漂移：poller-ops.json diff=%s" % (live^docd))
    # 4) mailbox 别名一致性
    for short,repo in {"qgl":"quantum-go-ledger","ucif2":"ucif2-formalization-kernel","vinf":"vinf-market-kernel","cfts":"github-repo-cfts","usrm":"usrm-repo"}.items():
        a,_=get_file("chepin-ai/ci-logs","mailbox/%s.json"%short)
        b_,_=get_file("chepin-ai/ci-logs","mailbox/%s.json"%repo)
        if a and b_:
            da,db=json.loads(a),json.loads(b_)
            if [x.get("id") for x in da.get("directives",[])]!=[x.get("id") for x in db.get("directives",[])]:
                findings.append("mailbox 别名漂移：%s vs %s" % (short, repo))
    # 5) 指令积压：open [CMD] 超 40min
    for i in (gh("/repos/chepin-ai/ci-inbox/issues?state=open&per_page=30") or []):
        if i["title"].startswith("[CMD]"):
            age=(time.mktime(time.gmtime())-time.mktime(time.strptime(i["created_at"],"%Y-%m-%dT%H:%M:%SZ")))/60
            if age>40: findings.append("指令积压：#%d 已 %.0fmin 未处理" % (i["number"], age))
    # TIGER-P2-5：公仓 artifacts 非空即报警（工件元数据=情报面）
    for repo in ("ci-control","ci-control-backup"):
        a=gh("/repos/chepin-ai/%s/actions/artifacts?per_page=1"%repo)
        if a and a.get("total_count",0)>0: findings.append("artifacts 非空：%s 有 %d 件工件（元数据公开面）" % (repo, a["total_count"]))
    # 6) M6-QUOTA-EVENT：provider lane 状态翻转事件化（恢复/跌落必须发事件）
    bench,_=get_file("chepin-ai/ci-control-backup","eye/bench-ext-latest.md")
    if bench:
        lanes={}
        for m in re.finditer(r"^- ([\w.\-]+/[\w.\-]+): (\d+)/(\d+) 成功", bench, re.M):
            ok,tot=int(m.group(2)),int(m.group(3))
            lanes[m.group(1)]=ok/tot if tot else 0.0
        qs_text,_=get_file("chepin-ai/ci-library","weave/quota-state.json")
        qs=json.loads(qs_text) if qs_text else {}
        old=qs.get("lanes",{})
        for model,ratio in lanes.items():
            prev_r=old.get(model)
            if prev_r is None and model in old: prev_r=0.0  # 缺失且之前有记录 → 视同 0
            if prev_r is not None:
                if prev_r==0 and ratio>=0.8:
                    findings.append("[info] QUOTA-LANE-RECOVERED: model=%s 配额 lane 恢复（ratio 0→%.2f，班表 %s）" % (model, ratio, TS))
                elif prev_r>=0.8 and ratio<0.5:
                    findings.append("[warn] QUOTA-LANE-DOWN: model=%s 配额 lane 跌落（ratio %.2f→%.2f，班表 %s）" % (model, prev_r, ratio, TS))
        put_file("chepin-ai/ci-library","weave/quota-state.json",json.dumps({"ts":TS,"lanes":lanes},ensure_ascii=False,indent=1),"audit: quota lane 状态")
    rpt="# 自省自审报告 %sZ\n\n%s\n" % (TS, "\n".join("- "+f for f in findings) or "五项全绿：无泄漏/无漂移/无别名分叉/无积压")
    put_file("chepin-ai/ci-library","weave/audit/last.md",rpt,"audit: %s"%TS)
    if findings:
        gh("/repos/chepin-ai/ci-inbox/issues/144/comments","POST",{"body":"thr: SELF-AUDIT\ndtag: AUDIT-%s\n\n%s\n\n—— cisvr 自省班（自动）" % (TS, "\n".join("- "+f for f in findings))})
    print("audit 班完：%d 项" % len(findings))
main()
