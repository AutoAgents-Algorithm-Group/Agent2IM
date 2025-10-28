# Playground 飞书服务测试

本目录包含飞书服务相关的测试脚本，镜像 `src/service/feishu` 的目录结构。

## 测试文件

### test_labor_hour_daily.py
测试日常工时检查功能

**使用方法：**
```bash
# 从 backend 目录运行
cd backend
python playground/service/feishu/test_labor_hour_daily.py
```

**功能：**
- 检查指定日期的工时填写情况
- 支持通过修改 `offset` 变量来检查不同日期（0=今天, -1=昨天, 1=明天）
- 显示填写率、未填写人员、请假人员等统计信息
- 自动发送提醒消息到飞书群聊

### test_labor_hour_monthly.py
测试月度工时总结功能

**使用方法：**
```bash
# 测试上个月的月度总结
python playground/service/feishu/test_labor_hour_monthly.py

# 测试指定结束日期的月度总结
python playground/service/feishu/test_labor_hour_monthly.py 2025-10-27
```

**功能：**
- 汇总整个月的工时填写情况
- 统计全勤人员、部分填写、完全未填写的人员
- 自动发送月度总结到飞书群聊
- 支持 @提醒指定人员

### test_approval.py
测试审批事件处理功能

**使用方法：**
```bash
python playground/service/feishu/test_approval.py
```

**功能：**
- 测试 URL 验证
- 测试审批通过事件处理
- 测试审批拒绝事件处理
- 测试直接创建请假日历

### test_news.py
测试新闻采集和推送功能

**使用方法：**
```bash
cd backend
python playground/service/feishu/test_news.py
```

**功能：**
- 从多个新闻源采集 AI 相关新闻
- 使用 AI 进行翻译和总结
- 自动推送到配置的飞书群组
- 显示推送结果统计

## 配置要求

所有测试脚本都需要正确配置 `src/config/labor_hour.yaml`：
- 飞书应用凭证（app_id, app_secret）
- 多维表格 URL
- 群聊 chat_id
- 例外日期配置（可选）

## 注意事项

1. 测试前确保配置文件正确
2. 确保飞书应用有相应权限
3. 测试会真实发送消息到群聊，请谨慎使用
4. 可以修改脚本中的参数来测试不同场景

