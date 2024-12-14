#!/bin/bash

# 创建runs文件夹，如果它不存在
mkdir -p runs

# 获取当前时间信息
timestamp=$(TZ='Asia/Shanghai' date +"%Y%m%d%H%M%S")

# 生成log文件名称
log_file="runs/log_$timestamp.txt"

# 运行python脚本并将输出重定向到log文件
python3 offline_game.py > "$log_file"