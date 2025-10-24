# @ 提醒功能说明

## 📢 功能介绍

工时检查服务现在支持在飞书消息中直接 **@未填写工时的人员**，让提醒更有效！

## ✨ 效果展示

### 之前（只显示名字）
```
❗ 需要提醒的人员:
  • 张三
  • 李四
  • 王五
```

### 现在（实际@人）
```
❗ 需要提醒的人员:
  • @张三 张三
  • @李四 李四  
  • @王五 王五
```

收到消息的人会：
- ✅ 在飞书中收到红点通知
- ✅ 看到自己被@了
- ✅ 更容易注意到需要填写工时

## 🔧 技术实现

### 1. 数据获取
从多维表格的历史记录中提取用户ID：

```python
# 获取最近500条记录来建立user_id映射
all_recent_records = self.get_records(page_size=500)

# 提取每个人的user_id
for record in all_recent_records:
    user_info = fields.get('员工', {})
    user_name = user_info.get('name')
    user_id = user_info.get('id')  # 飞书用户ID
    user_id_map[user_name] = user_id
```

### 2. 消息格式
使用飞书的 lark_md 格式中的 @ 语法：

```python
# 飞书@人的语法
content += f"  • <at id={user_id}></at> {name}\n"
```

### 3. 降级处理
如果获取不到某个用户的ID（比如新员工还没填写过任何记录），会优雅降级：

```python
if user_id:
    # 有ID，使用@功能
    content += f"  • <at id={user_id}></at> {name}\n"
else:
    # 没有ID，只显示名字
    content += f"  • {name}\n"
```

## 📊 数据结构

### check_users_filled 返回结果
```python
{
    'all_filled': False,
    'filled': ['张三', '李四'],
    'not_filled': ['王五', '赵六'],
    'not_filled_with_id': [        # 新增字段
        {'name': '王五', 'user_id': 'ou_xxx1'},
        {'name': '赵六', 'user_id': 'ou_xxx2'}
    ],
    'fill_rate': 0.5,
    'on_leave': [],
    'exception_day': []
}
```

## 🎯 适用场景

✅ **适用于:**
- 多维表格中使用了"人员"类型字段
- 人员字段包含飞书用户信息
- 历史记录中有该用户的填写记录

❌ **不适用于:**
- 多维表格中只记录文本姓名
- 新员工还从未填写过记录
- 使用外部人员（非飞书用户）

## 🔍 如何确认是否支持

### 查看多维表格字段类型

1. 打开多维表格
2. 点击"员工"字段
3. 查看字段类型：
   - ✅ **人员** - 支持@功能
   - ❌ **文本** - 不支持@功能

### 测试方法

```bash
cd backend/playground
python run_labor_hour_check.py
```

查看终端输出：
```
🔍 正在获取用户ID映射...
✅ 已建立 15 个用户的ID映射
```

如果看到这个消息，说明成功获取到了user_id！

## 🐛 故障排查

### 问题1: 所有人都没有@效果

**原因**: 多维表格的"员工"字段是文本类型，不是人员类型

**解决**: 
1. 修改字段类型为"人员"
2. 重新选择人员（从飞书通讯录选择）

### 问题2: 部分人没有@效果

**原因**: 这些人从未在多维表格中填写过记录，无法获取user_id

**解决**:
1. 让这些人先填写一次工时
2. 或在 `people.json` 中手动添加 `user_id` 字段（未来功能）

### 问题3: @了但没收到通知

**原因**: 
- 用户关闭了飞书通知
- 用户不在群组中
- user_id 不正确

**解决**:
1. 检查用户的飞书通知设置
2. 确认用户在群组中
3. 查看终端日志确认user_id是否正确

## 📝 配置要求

### 必需条件
- ✅ 飞书应用配置（app_id + app_secret）
- ✅ Webhook配置（url + secret）
- ✅ 多维表格使用人员字段
- ✅ 历史记录中有用户数据

### 可选优化
- 在 `people.json` 中添加 `user_id` 字段（未来功能）
- 配置用户别名映射

## 🚀 使用示例

### 手动测试
```bash
cd backend/playground
python run_labor_hour_check.py
```

### 定时任务
配置 `scheduled_tasks.json`:
```json
{
  "id": "labor_evening_first",
  "name": "工时检查 - 晚上9点",
  "type": "labor_hour",
  "enabled": true,
  "schedule": "21:00"
}
```

启动调度器:
```bash
python start_unified_scheduler.py
```

## 💡 提示

1. **首次使用**: 会扫描最近500条记录建立user_id映射
2. **性能优化**: user_id映射会缓存在内存中（TODO）
3. **数据更新**: 每次检查都会重新获取最新的映射
4. **向后兼容**: 如果获取不到user_id，自动降级为普通文本

## 🎨 样式建议

可以在未来添加更多样式：

```markdown
# 方案1: 突出显示（当前）
❗ 需要提醒的人员:
  • @张三 张三
  • @李四 李四

# 方案2: 表格格式
| 姓名 | 状态 | 提醒 |
|-----|------|------|
| @张三 | 未填写 | 请尽快填写 |

# 方案3: 分组显示
🔴 紧急提醒（连续2天未填写）:
  • @张三
  • @李四
  
⚠️ 今日未填写:
  • @王五
```

## 🔗 相关文档

- [工时检查服务说明](./README_LABOR_HOUR.md)
- [配置说明](../config/README_CONFIG.md)
- [Backend完整文档](../README.md)
- [飞书消息卡片文档](https://open.feishu.cn/document/ukTMukTMukTM/uYzMxEjL2MTMx4iNzETM)

---

**更新日期**: 2025-10-24
**功能状态**: ✅ 已实现



