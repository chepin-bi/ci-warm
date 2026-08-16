#!/bin/bash
# enroll-linux.sh — GRID 展开包（Debian/Ubuntu 系 x64；Win7 机改装 Linux 后用此）
# 用法: ./enroll-linux.sh <注册令牌> [owner/repo] [标签]
set -e
TOKEN="$1"; REPO="${2:-chepin-ai/ci-control}"; LABELS="${3:-grid,linux}"
[ -z "$TOKEN" ] && { echo "用法: $0 <注册令牌> [owner/repo] [标签]"; exit 1; }
[ "$(id -u)" = "0" ] && { echo "请勿用 root 运行（安全硬规）；请先建专用用户: sudo useradd -m grid && su - grid"; exit 1; }
command -v curl >/dev/null || { echo "缺少 curl: sudo apt-get install -y curl"; exit 1; }

VER=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | python3 -c "import sys,json;print(json.load(sys.stdin)['tag_name'].lstrip('v'))" 2>/dev/null \
  || curl -s https://api.github.com/repos/actions/runner/releases/latest | grep -oP '"tag_name":\s*"v\K[^"]+')
DIR="$HOME/actions-runner/$(echo $REPO | tr '/' '_')"
mkdir -p "$DIR" && cd "$DIR"
echo ">> 下载 runner v$VER (linux-x64)"
curl -sL -o runner.tgz "https://github.com/actions/runner/releases/download/v$VER/actions-runner-linux-x64-$VER.tar.gz"
tar xzf runner.tgz && rm runner.tgz
echo ">> 配置: repo=$REPO labels=$LABELS"
./config.sh --unattended --url "https://github.com/$REPO" --token "$TOKEN" \
  --name "$(hostname)-$RANDOM" --labels "$LABELS" --work _work --replace
echo ">> 安装为 systemd 服务（需要 sudo 一次）"
sudo ./svc.sh install "$USER" && sudo ./svc.sh start
sleep 5
sudo ./svc.sh status && echo "✅ GRID 节点上线：$REPO [$LABELS]"
echo "核验: https://github.com/$REPO/settings/actions/runners"
