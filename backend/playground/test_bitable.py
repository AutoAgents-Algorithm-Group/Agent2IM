import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.utils.feishu.client import FeishuClient
from src.utils.feishu.bitable import BitableAPI


def main():
    print("=" * 60)
    print("  检查人员填写情况（含节假日和例外日期判断）")
    print("=" * 60)
    
    feishu_client = FeishuClient(
        app_id="cli_a82e97f4de29501c", 
        app_secret="nEoauWe1YEt5luG6J4Ij8cvlTZKb3po3"
    )

    bitable = BitableAPI(
        client=feishu_client, 
        url="https://uxkpl4cba3j.feishu.cn/base/UfDPbov0Eai3RpsWAEBcyfe1nAb?table=tbla3OuZeDczpqZx&view=vewGyZRz6D"
    )

    # 🎯 自动从配置文件读取人员名单（排除请假人员和例外日期）
    result = bitable.check_users_filled(date_str="2025-09-30")
    
    # 如果是节假日，直接返回
    if result.get('is_holiday'):
        print(f"\n🎉 {result.get('message', '今天是节假日')}")
        return
    
    # 显示详细信息
    print(f"\n📊 检查结果:")
    print(f"  应填写人数: {len(result['filled']) + len(result['not_filled'])}")
    print(f"  已填写: {len(result['filled'])} 人")
    print(f"  未填写: {len(result['not_filled'])} 人")
    print(f"  填写率: {result['fill_rate']:.1%}")
    
    if result['on_leave']:
        print(f"\n🏖️ 请假人员 ({len(result['on_leave'])} 人): {', '.join(result['on_leave'])}")
    
    if result['exception_day']:
        print(f"\n📅 例外日期人员 ({len(result['exception_day'])} 人): {', '.join(result['exception_day'])}")
    
    # 根据结果做处理
    if result['all_filled']:
        print("\n✅ 太棒了！所有人都已填写！")
    else:
        print(f"\n⚠️ 还有 {len(result['not_filled'])} 人未填写")
        print(f"📋 需要提醒的人员: {', '.join(result['not_filled'])}")
    
    print("\n" + "=" * 60)
        

if __name__ == "__main__":
    main()