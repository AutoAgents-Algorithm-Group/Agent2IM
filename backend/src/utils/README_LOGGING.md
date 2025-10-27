# 日志系统使用指南

基于 `loguru` 的统一日志系统，提供彩色控制台输出、文件记录、阶段标记等功能。

## 📋 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [阶段定义](#阶段定义)
- [使用方法](#使用方法)
- [日志级别](#日志级别)
- [日志文件](#日志文件)
- [最佳实践](#最佳实践)

## ✨ 功能特性

- ✅ **彩色控制台输出** - 不同级别使用不同颜色，易于区分
- ✅ **阶段标记** - 通过 Stage 标记不同的业务阶段
- ✅ **文件记录** - 自动保存到日志文件，支持轮转和压缩
- ✅ **异常追踪** - 自动记录异常堆栈信息
- ✅ **多级别** - DEBUG, INFO, SUCCESS, WARNING, ERROR
- ✅ **上下文管理** - 支持 with 语句临时切换阶段

## 🚀 快速开始

### 基本使用

```python
from src.utils.logging import logger

# 直接使用（默认 SYSTEM 阶段）
logger.info("这是一条信息")
logger.success("操作成功")
logger.warning("注意警告")
logger.error("发生错误")
```

### 使用阶段标记

```python
from src.utils.logging import set_stage
from src.models import Stage

# 设置阶段
labor_log = set_stage(Stage.LABOR_CHECK)
labor_log.info("开始检查工时")
labor_log.success("检查完成")

# 飞书 API 阶段
feishu_log = set_stage(Stage.FEISHU_API)
feishu_log.info("正在调用飞书 API...")
feishu_log.success("✅ API 调用成功")
```

### 使用上下文管理器

```python
from src.utils.logging import logger
from src.models import Stage

# 临时切换阶段
with logger.contextualize(stage=Stage.BITABLE):
    logger.info("正在查询多维表格...")
    logger.success("查询成功")
# 自动恢复到默认阶段
```

## 🏷️ 阶段定义

| 阶段 | 说明 | 使用场景 |
|------|------|---------|
| `SYSTEM` | 系统级别 | 默认阶段，通用日志 |
| `INIT` | 初始化 | 系统启动、模块初始化 |
| `CONFIG` | 配置加载 | 读取配置文件 |
| `FEISHU_API` | 飞书API | 飞书 API 调用 |
| `FEISHU_AUTH` | 飞书认证 | 获取访问令牌 |
| `BITABLE` | 多维表格 | 查询、更新多维表格 |
| `CARD_CREATE` | 卡片生成 | 创建消息卡片 |
| `MESSAGE_SEND` | 消息发送 | 发送飞书消息 |
| `LABOR_CHECK` | 工时检查 | 检查工时填写 |
| `LABOR_SUMMARY` | 工时统计 | 生成工时报表 |
| `LEAVE_CHECK` | 请假检查 | 检查请假状态 |
| `APPROVAL` | 审批处理 | 处理审批事件 |
| `APPROVAL_CALLBACK` | 审批回调 | Webhook 回调处理 |
| `SCHEDULER` | 定时任务 | 任务调度 |
| `TASK_EXEC` | 任务执行 | 执行具体任务 |
| `NEWS_SCRAPER` | 新闻爬取 | 爬取新闻数据 |
| `NEWS_PROCESS` | 新闻处理 | 处理新闻数据 |
| `WEBHOOK` | Webhook | Webhook 请求处理 |
| `EVENT_CALLBACK` | 事件回调 | 事件处理 |
| `ERROR` | 错误处理 | 错误处理 |
| `EXCEPTION` | 异常捕获 | 异常记录 |

## 📝 使用方法

### 1. 在服务类中使用

```python
# labor_hour_service.py
from src.utils.logging import set_stage
from src.models import Stage

class LaborHourChecker:
    def __init__(self):
        self.log = set_stage(Stage.LABOR_CHECK)
    
    def check_users_filled(self, date_str):
        self.log.info(f"开始检查 {date_str} 的工时")
        
        # ... 业务逻辑 ...
        
        if not_filled:
            self.log.warning(f"发现 {len(not_filled)} 人未填写")
        else:
            self.log.success("所有人已填写")
        
        return result
```

### 2. 在 API 路由中使用

```python
# main.py
from fastapi import FastAPI
from src.utils.logging import set_stage
from src.models import Stage

app = FastAPI()

@app.post("/feishu/callback")
async def handle_callback(request: Request):
    log = set_stage(Stage.WEBHOOK)
    log.info("收到 Webhook 回调")
    
    try:
        # 处理回调
        result = process_callback(data)
        log.success("回调处理成功")
        return result
    except Exception as e:
        error_log = set_stage(Stage.ERROR)
        error_log.exception("回调处理失败")
        raise
```

### 3. 在定时任务中使用

```python
# scheduler.py
from src.utils.logging import set_stage
from src.models import Stage

def run_labor_hour_check():
    scheduler_log = set_stage(Stage.SCHEDULER)
    scheduler_log.info("定时任务 [工时检查] 触发")
    
    task_log = set_stage(Stage.TASK_EXEC)
    task_log.info("开始执行任务...")
    
    try:
        # 执行任务
        result = check_labor_hours()
        task_log.success("✅ 任务执行完成")
    except Exception as e:
        error_log = set_stage(Stage.EXCEPTION)
        error_log.exception("任务执行失败")
```

### 4. 在飞书客户端中使用

```python
# client.py
from src.utils.logging import set_stage
from src.models import Stage

class FeishuClient:
    def __init__(self):
        self.log = set_stage(Stage.FEISHU_API)
    
    def get_access_token(self):
        auth_log = set_stage(Stage.FEISHU_AUTH)
        auth_log.info("正在获取访问令牌...")
        
        try:
            token = self._request_token()
            auth_log.success("✅ 访问令牌获取成功")
            return token
        except Exception as e:
            auth_log.error(f"❌ 获取令牌失败: {e}")
            raise
```

## 📊 日志级别

| 级别 | 说明 | 控制台 | 文件 |
|------|------|--------|------|
| `DEBUG` | 调试信息 | ❌ | ✅ |
| `INFO` | 一般信息 | ✅ | ✅ |
| `SUCCESS` | 成功信息 | ✅ | ✅ |
| `WARNING` | 警告信息 | ✅ | ✅ |
| `ERROR` | 错误信息 | ✅ | ✅ |

### 使用示例

```python
from src.utils.logging import logger

# DEBUG - 仅保存到文件
logger.debug("详细的调试信息")

# INFO - 控制台和文件都显示
logger.info("一般信息")

# SUCCESS - 操作成功（绿色）
logger.success("✅ 操作成功")

# WARNING - 警告信息（黄色）
logger.warning("⚠️ 注意警告")

# ERROR - 错误信息（红色）
logger.error("❌ 发生错误")

# EXCEPTION - 记录异常堆栈
try:
    risky_operation()
except Exception as e:
    logger.exception("捕获到异常")
```

## 📁 日志文件

### 文件位置

```
backend/logs/
├── debug_2025-10-27.log    # 调试日志（DEBUG 及以上）
└── error_2025-10-27.log    # 错误日志（ERROR 及以上）
```

### 文件格式

```
2025-10-27 20:41:16.451 | DEBUG    | Stage.SYSTEM | __main__:test_basic_logging:24 | 这是 DEBUG 级别
2025-10-27 20:41:16.452 | INFO     | Stage.FEISHU_API | client:get_token:45 | 正在获取访问令牌...
2025-10-27 20:41:16.453 | SUCCESS  | Stage.FEISHU_API | client:get_token:52 | ✅ 访问令牌获取成功
```

### 轮转策略

- **debug 日志**: 每天午夜轮转，保留 7 天，自动压缩
- **error 日志**: 每天午夜轮转，保留 30 天，自动压缩

## 💡 最佳实践

### 1. 为每个模块/类创建专用 logger

```python
class LaborHourService:
    def __init__(self):
        # 创建专用 logger
        self.log = set_stage(Stage.LABOR_CHECK)
```

### 2. 使用有意义的阶段标记

```python
# 👍 好的做法
labor_log = set_stage(Stage.LABOR_CHECK)
labor_log.info("开始检查工时")

# 👎 不好的做法
logger.info("开始检查工时")  # 使用默认 SYSTEM 阶段
```

### 3. 记录关键操作和状态变化

```python
log.info(f"开始检查 {date_str} 的工时")
log.info(f"需要检查 {len(users)} 名人员")
log.warning(f"发现 {len(not_filled)} 人未填写")
log.success("工时检查完成")
```

### 4. 使用表情符号增强可读性

```python
log.success("✅ 操作成功")
log.warning("⚠️ 注意警告")
log.error("❌ 发生错误")
log.info("📋 找到 10 条记录")
log.info("🔍 正在搜索...")
log.info("📤 正在发送消息...")
```

### 5. 异常处理时记录完整堆栈

```python
try:
    result = risky_operation()
except Exception as e:
    error_log = set_stage(Stage.EXCEPTION)
    error_log.exception("操作失败")  # 自动记录堆栈
    raise
```

### 6. 使用上下文管理器处理临时阶段

```python
# 临时切换到 BITABLE 阶段
with logger.contextualize(stage=Stage.BITABLE):
    logger.info("查询第 1 页...")
    logger.info("查询第 2 页...")
# 自动恢复到之前的阶段
```

### 7. 记录性能指标

```python
import time

start = time.time()
log.info("开始执行任务...")

# 执行任务
result = execute_task()

elapsed = time.time() - start
log.success(f"✅ 任务执行完成，耗时 {elapsed:.2f} 秒")
```

## 📖 完整示例

```python
# labor_hour_service.py
from src.utils.logging import set_stage
from src.models import Stage

class LaborHourService:
    def __init__(self):
        self.init_log = set_stage(Stage.INIT)
        self.init_log.success("工时检查服务初始化完成")
    
    def check_labor_hours(self, date_str: str):
        """检查工时填写情况"""
        log = set_stage(Stage.LABOR_CHECK)
        log.info(f"开始检查 {date_str} 的工时")
        
        try:
            # 1. 获取人员名单
            log.info("正在加载人员名单...")
            users = self._load_users()
            log.info(f"需要检查 {len(users)} 名人员")
            
            # 2. 查询多维表格
            with logger.contextualize(stage=Stage.BITABLE):
                logger.info("正在查询多维表格...")
                records = self.bitable.get_records(date_str)
                logger.success(f"✅ 查询成功，找到 {len(records)} 条记录")
            
            # 3. 检查填写情况
            filled, not_filled = self._check_filled(users, records)
            
            if not_filled:
                log.warning(f"⚠️ 发现 {len(not_filled)} 人未填写")
                
                # 4. 检查请假
                leave_log = set_stage(Stage.LEAVE_CHECK)
                leave_log.info("正在检查请假状态...")
                on_leave = self._check_leave(not_filled, date_str)
                leave_log.success(f"✅ {len(on_leave)} 人请假")
                
                # 5. 发送提醒
                msg_log = set_stage(Stage.MESSAGE_SEND)
                msg_log.info("正在发送提醒消息...")
                self._send_reminder(not_filled, on_leave)
                msg_log.success("✅ 消息发送成功")
            else:
                log.success("✅ 所有人已填写工时")
            
            log.success("工时检查完成")
            return {
                'filled': len(filled),
                'not_filled': len(not_filled),
                'on_leave': len(on_leave)
            }
            
        except Exception as e:
            error_log = set_stage(Stage.EXCEPTION)
            error_log.exception("工时检查失败")
            raise
```

## 🔧 自定义配置

如需自定义日志配置，可以修改 `src/utils/logging.py` 中的 `_setup_handlers` 方法：

```python
def _setup_handlers(self):
    # 修改日志格式
    console_format = "..."
    
    # 修改日志级别
    _logger.add(sys.stdout, level="DEBUG")  # 控制台也显示 DEBUG
    
    # 修改轮转策略
    _logger.add(
        self.log_dir / "debug_{time}.log",
        rotation="1 MB"  # 按文件大小轮转
    )
```

## 🆘 常见问题

### Q: 为什么控制台看不到 DEBUG 日志？

A: 为了保持控制台清爽，DEBUG 日志仅保存到文件。如需在控制台查看，可修改配置。

### Q: 日志文件在哪里？

A: 默认保存在 `backend/logs/` 目录下。

### Q: 如何添加新的阶段？

A: 在 `src/models.py` 的 `Stage` 枚举中添加新的阶段定义即可。

### Q: 可以同时使用多个阶段吗？

A: 不建议。每次只使用一个阶段标记，通过上下文管理器可以临时切换。

---

更多信息请参考：
- [loguru 官方文档](https://loguru.readthedocs.io/)
- [项目 README](../../../README.md)

