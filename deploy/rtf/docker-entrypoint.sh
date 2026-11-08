#!/usr/bin/env bash
# RTF (Runtime Fabric) の app コンテナの起動。init コンテナが置いた jar と、RTF が置いた設定からアプリを起動する。
#   jar  : /mnt/overlay/opt/mule/deployments/<APP_NAME>.jar (RTF の init コンテナが Exchange から取る)
#   設定 : /opt/mule/deployments/conf/<APP_NAME>.yml (JSON。properties の下がアプリのプロパティ)
#   秘密 : /opt/mule/secrets/<id> (安全なプロパティの値。設定には file:///opt/mule/secrets/<id> と入る)
# 先に書いたプロパティが優先されるので、RTF が決める値 (ポートなど) を先に置き、設定のプロパティを後ろにする。
set -eu
APP="${APP_NAME:?APP_NAME is not set}"
JAR="${MULE_APP_JAR:-/mnt/overlay/opt/mule/deployments/${APP}.jar}"
CONF="${CONF_PATH:-/opt/mule/deployments/conf/${APP}.yml}"
export MULE_HOME=/opt/mule

props=()
if [ -f "$CONF" ]; then
  # NUL 区切りで読む (値に空白や改行があってもそのまま渡る)。数値と真偽値は文字列にする
  mapfile -d '' props < <(jq -j '.["mule.agent.application.properties.service"].properties // {}
    | to_entries[] | .key + "=" + (.value | tostring) + "\u0000"' "$CONF")
fi

# 安全なプロパティ (Runtime Manager で Protected にした値) は、設定には file:///opt/mule/secrets/<id> の形で入り、
# 値は RTF がマウントした Secret のファイルにある (本物の Mule はこの参照を読む)。ここで中身に置き換える。
for i in "${!props[@]}"; do
  kv="${props[$i]}"; v="${kv#*=}"
  case "$v" in
    file:///opt/mule/secrets/*)
      f="${v#file://}"
      if [ -f "$f" ]; then props[$i]="${kv%%=*}=$(cat "$f")"; else echo "mulay-rtf: ${kv%%=*}: $f is missing" >&2; fi ;;
  esac
done

# 設定のプロパティ (秘密を含む) はコマンドラインに載せず (ps や /proc/<pid>/cmdline で誰にでも見える)、
# 自分だけが読めるファイルに NUL 区切りで書いて -P で渡す。-P は置いた位置で効くので優先の順は変わらない。
PROPS_FILE=/tmp/mulay/app.props
mkdir -p /tmp/mulay
( umask 077; : > "$PROPS_FILE"; for kv in ${props[@]+"${props[@]}"}; do printf '%s\0' "$kv"; done > "$PROPS_FILE" )

# Anypoint Monitoring のメトリクスのファイル (サイドカーが読む)。設定のプロパティで上書きできるよう後ろに置く
exec mulay run "$JAR" \
  http.port=8081 mulay.admin.port=7777 "mulay.health.app=${APP}" mulay.work.dir=/tmp/mulay \
  -P "$PROPS_FILE" \
  mulay.am.metricFile=/mnt/overlay/opt/mule/logs/_metric.log
