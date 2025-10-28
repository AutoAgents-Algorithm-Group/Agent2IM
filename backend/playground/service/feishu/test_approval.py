import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from src.service.feishu.approval import create_approval_service_from_config

def main():
    """测试审批事件处理"""
    approval_service = create_approval_service_from_config()
    
    # 模拟审批通过事件
    data = {
        "type": "event_callback",
        "event": {
            "type": "approval_instance",
            "status": "APPROVED",
            "approval_code": "A9D489DC-5F55-4418-99F1-01E1CE734CA1",
            "instance_code": "test_instance_001",
            "user_id": "ou_test_user",
            "open_id": "ou_test_user"
        }
    }
    
    approval_service.handle_approval_event(data)

if __name__ == '__main__':
    main()
