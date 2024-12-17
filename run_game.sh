#!/bin/bash

# 创建runs文件夹，如果它不存在
log_dir="runs"
mkdir -p $log_dir

# 获取当前时间信息
timestamp=$(TZ='Asia/Shanghai' date +"%Y%m%d%H%M%S")

# 生成log文件名称
log_file="$log_dir/log_$timestamp.txt"
result_file="results/result_$timestamp.json"
assets_file="simulator/assets/result_$timestamp.json"

# 运行python脚本并将输出重定向到log文件
python3 offline_game.py --output "$assets_file" > "$log_file"