#!/bin/bash
# 用法：./same_hub.sh /dev/video50 /dev/video51

set -euo pipefail

video2busport(){
    # 1) 展开软链接并确保存在
    local final
    final=$(realpath -e "$1" 2>/dev/null) || return 1
    [[ -e "$final" ]] || return 1

    # 2) 通过 /sys/class/video4linux/<videoX>/device 向上查找包含 busnum/devpath 的 USB 设备目录
    local v p
    v=${final##*/}
    p=$(realpath -e "/sys/class/video4linux/$v/device" 2>/dev/null) || return 1
    while [[ -n "$p" && ! -f "$p/busnum" ]]; do
        p=${p%/*}
    done
    if [[ -f "$p/busnum" && -f "$p/devpath" ]]; then
        echo "$(cat "$p/busnum")-$(cat "$p/devpath")"
        return 0
    fi
    return 1
}

if [[ $# -ne 2 ]]; then
    echo "用法：$0 /dev/videoX /dev/videoY" >&2
    exit 2
fi

v1=$(video2busport "$1" || true)
v2=$(video2busport "$2" || true)

echo "$1 -> ${v1:-<未找到>}"
echo "$2 -> ${v2:-<未找到>}"

if [[ -z "${v1}" || -z "${v2}" ]]; then
    echo "无法解析其中一个设备的 USB 路径，确保设备存在且具有 /sys 条目。" >&2
    exit 1
fi

# 拆分为 bus 与端口路径（bus-1.3.1.1）
bus1=${v1%%-*}
path1=${v1#*-}
bus2=${v2%%-*}
path2=${v2#*-}

# 不同总线直接判定不在同一 Hub
if [[ "$bus1" != "$bus2" ]]; then
    echo "不在同一 Hub 上（不同 USB 总线：$bus1 vs $bus2）"
    exit 0
fi

IFS='.' read -r -a p1 <<< "$path1"
IFS='.' read -r -a p2 <<< "$path2"

# 计算公共前缀长度（端口层面）
common=0
for (( i=0; i<${#p1[@]} && i<${#p2[@]}; i++ )); do
    if [[ "${p1[i]}" == "${p2[i]}" ]]; then
        common=$((i+1))
    else
        break
    fi
done

# 至少共享首级端口（common>=1）才算在同一 Hub
if (( common >= 1 )); then
    # 还原为形如 3-1.3 的格式
    IFS='.' read -r -a _tmp <<< "${p1[*]:0:common}"
    prefix_joined=$(IFS=.; echo "${p1[*]:0:common}")
    echo "在同一 Hub 上（公共节点 ${bus1}-${prefix_joined}）"
else
    echo "不在同一 Hub 上"
fi

exit 0




