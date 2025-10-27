# 日志系统快速入门 ⚡

5分钟快速上手统一日志系统！

## 🎯 三步开始

### 1️⃣ 导入

```python
from src.utils.logging import set_stage
from src.models import Stage
```

### 2️⃣ 选择阶段

```python
log = set_stage(Stage.LABOR_CHECK)  # 选择合适的阶段
```

### 3️⃣ 记录日志

```python
log.info("开始检查工时")
log.success("✅ 检查完成")
log.warning("⚠️ 发现问题")
log.error("❌ 发生错误")
```

## 📚 常用阶段

| 做什么 | 用什么阶段 | 示例 |
|--------|-----------|------|
| 飞书 API 调用 | `Stage.FEISHU_API` | 获取令牌、调用接口 |
| 查询多维表格 | `Stage.BITABLE` | 查询工时数据 |
| 工时检查 | `Stage.LABOR_CHECK` | 检查填写情况 |
| 请假检查 | `Stage.LEAVE_CHECK` | 检查请假状态 |
| 发送消息 | `Stage.MESSAGE_SEND` | 发送飞书消息 |
| 审批处理 | `Stage.APPROVAL` | 处理审批回调 |
| 定时任务 | `Stage.SCHEDULER` | 任务调度 |

完整阶段列表查看 [README_LOGGING.md](./README_LOGGING.md#阶段定义)

## 💡 实用技巧

### ✅ 在类中使用

```python
class LaborHourService:
    def __init__(self):
        self.log = set_stage(Stage.LABOR_CHECK)
    
    def check(self):
        self.log.info("开始检查")
        self.log.success("✅ 完成")
```

### ✅ 临时切换阶段

```python
from src.utils.logging import logger

with logger.contextualize(stage=Stage.BITABLE):
    logger.info("查询数据...")
# 自动恢复
```

### ✅ 记录异常

```python
try:
    risky_operation()
except Exception as e:
    log.exception("操作失败")  # 自动记录堆栈
```

### ✅ 使用表情符号

```python
log.success("✅ 成功")
log.warning("⚠️ 警告")
log.error("❌ 错误")
log.info("📋 数据")
log.info("🔍 查询")
log.info("📤 发送")
```

## 📁 日志文件

日志自动保存到 `backend/logs/`:

- `debug_2025-10-27.log` - 所有日志（DEBUG 及以上）
- `error_2025-10-27.log` - 错误日志（ERROR 及以上）

控制台只显示 INFO 及以上级别。

## 🎨 效果预览

### 控制台输出

```
20:43:56 | INFO    | 工时检查   | 开始检查 2025-10-27 的工时
20:43:56 | SUCCESS | 工时检查   | ✅ 查询完成: 已填 7 人，未填 9 人
20:43:56 | WARNING | 工时检查   | ⚠️ 发现 9 人未填写
20:43:56 | SUCCESS | 消息发送   | ✅ 消息发送成功
```

### 文件输出

```
2025-10-27 20:43:56.452 | INFO     | Stage.LABOR_CHECK | service:check:45 | 开始检查 2025-10-27 的工时
2025-10-27 20:43:56.453 | SUCCESS  | Stage.BITABLE | bitable:query:120 | ✅ 查询成功，找到 422 条记录
```

## 🔥 完整示例

```python
from src.utils.logging import set_stage
from src.models import Stage

class LaborHourChecker:
    def __init__(self):
        self.log = set_stage(Stage.LABOR_CHECK)
        self.log.info("工时检查器初始化")
    
    def check(self, date_str: str):
        self.log.info(f"开始检查 {date_str} 的工时")
        
        try:
            # 查询数据
            records = self.query_bitable(date_str)
            self.log.success(f"✅ 查询成功，{len(records)} 条")
            
            # 分析结果
            filled, not_filled = self.analyze(records)
            
            if not_filled:
                self.log.warning(f"⚠️ {len(not_filled)} 人未填写")
                self.send_reminder(not_filled)
            else:
                self.log.success("✅ 所有人已填写")
            
        except Exception as e:
            self.log.exception("检查失败")
            raise
```

## 📖 更多信息

- 完整文档: [README_LOGGING.md](./README_LOGGING.md)
- 测试脚本: `python backend/playground/test_logging.py`
- 集成示例: `python backend/playground/example_integrate_logging.py`

---

🚀 开始使用吧！有问题随时查看完整文档。

