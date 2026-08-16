#!/bin/bash
# enroll-macos.sh — GRID 展开包（macOS 11+，Intel/Apple Silicon 自适应）
# 用法: ./enroll-macos.sh <注册令牌> [owner/repo] [标签]
set -e
TOKEN="$1"; REPO="${2:-chepin-ai/ci-control}"; LABELS="${3:-grid,macos}"
[ -z "$TOKEN" ] && { echo "用法: $0 <注册令牌> [owner/repo] [标签]"; exit 1; }
[ "$(id -u)" = "0" ] && { echo "请勿用 root 运行（安全硬规）"; exit 1; }

ARCH=$(uname -m); [ "$ARCH" = "arm64" ] && PLAT=osx-arm64 || PLAT=osx-x64
VER=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | python3 -c "import sys,json;print(json.load(sys.stdin)['tag_name'].lstrip('v'))")
DIR="$HOME/actions-runner/$(echo $REPO | tr '/' '_')"
mkdir -p "$DIR" && cd "$DIR"
echo ">> 下载 runner v$VER ($PLAT)"
curl -sL -o runner.tgz "https://github.com/actions/runner/releases/download/v$VER/actions-runner-$PLAT-$VER.tar.gz"
tar xzf runner.tgz && rm runner.tgz
echo ">> 配置: repo=$REPO labels=$LABELS"
./config.sh --unattended --url "https://github.com/$REPO" --token "$TOKEN" \
  --name "$(hostname -s)-$RANDOM" --labels "$LABELS" --work _work --replace
echo ">> 安装为 LaunchAgent 服务"
./svc.sh install && ./svc.sh start
sleep 5
./svc.sh status && echo "✅ GRID 节点上线：$REPO [$LABELS]"
echo "核验: https://github.com/$REPO/settings/actions/runners"
