"""
飞书交互式卡片创建
"""


class CardBuilder:
    """飞书卡片构建器"""
    
    @staticmethod
    def create_ai_response_card(ai_response: str, user_message: str = "", timestamp: str = None) -> dict:
        """创建AI回复的交互式卡片"""
        
        # 处理长文本，自动分段
        if len(ai_response) > 1200:
            # 如果内容太长，分成多个段落
            paragraphs = CardBuilder._split_long_text(ai_response, max_length=1200)
            content = paragraphs[0]
            has_more = True
        else:
            content = ai_response
            has_more = False
        
        # 创建卡片元素
        elements = []
        
        # AI回复内容 - 简洁布局
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": content
            }
        })
        
        # 如果内容被截断，添加提示
        if has_more:
            elements.append({
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": "回答内容较长，已显示主要部分。"
                    }
                ]
            })
        
        # 底部信息栏
        footer_text = ""
        if timestamp:
            footer_text += f"回复时间: {timestamp}"
        
        # 添加字数统计
        word_count = len(ai_response)
        if word_count > 0:
            if footer_text:
                footer_text += " • "
            footer_text += f"字数: {word_count}"
        
        if footer_text:
            elements.append({
                "tag": "hr"
            })
            elements.append({
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": footer_text
                    }
                ]
            })
        
        # 构建完整的卡片
        card = {
            "config": {
                "wide_screen_mode": True,
                "enable_forward": True,
                "update_multi": False
            },
            "header": {
                "template": "indigo"
            },
            "elements": elements
        }
        
        return card
    
    @staticmethod
    def _split_long_text(text: str, max_length: int = 800) -> list:
        """将长文本分割成合适的段落"""
        if len(text) <= max_length:
            return [text]
        
        # 尝试按段落分割
        paragraphs = text.split('\n\n')
        result = []
        current = ""
        
        for para in paragraphs:
            if len(current + para) <= max_length:
                if current:
                    current += "\n\n" + para
                else:
                    current = para
            else:
                if current:
                    result.append(current)
                    current = para
                else:
                    # 单个段落太长，强制分割
                    while len(para) > max_length:
                        result.append(para[:max_length])
                        para = para[max_length:]
                    current = para
        
        if current:
            result.append(current)
        
        return result
    
    @staticmethod
    def create_typing_card(content: str, is_typing: bool = False, timestamp: str = None) -> dict:
        """创建打字效果的卡片"""
        elements = []
        
        # AI回复内容
        display_content = content if content else "　"  # 使用全角空格占位
        
        # 如果正在打字，添加打字光标效果
        if is_typing and content:
            display_content += "▋"  # 打字光标
        
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": display_content
            }
        })
        
        # 底部信息栏
        footer_elements = []
        
        if is_typing:
            footer_elements.append({
                "tag": "plain_text",
                "content": "AI正在输入..."
            })
        else:
            footer_text = f"回复时间: {timestamp}" if timestamp else ""
            if content:
                footer_text += f" • 字数: {len(content)}" if footer_text else f"字数: {len(content)}"
            footer_elements.append({
                "tag": "plain_text", 
                "content": footer_text
            })
        
        if footer_elements:
            elements.append({
                "tag": "hr"
            })
            elements.append({
                "tag": "note",
                "elements": footer_elements
            })
        
        # 构建完整的卡片
        card = {
            "config": {
                "wide_screen_mode": True,
                "enable_forward": True,
                "update_multi": False
            },
            "header": {
                "template": "indigo"
            },
            "elements": elements
        }
        
        return card
    
    @staticmethod
    def create_reminder_card(title: str, content: str, footer: str, button_text: str, 
                           button_url: str, button_type: str = "primary", 
                           template_color: str = "blue") -> dict:
        """创建提醒卡片"""
        card = {
            "config": {
                "wide_screen_mode": True,
                "enable_forward": True
            },
            "header": {
                "template": template_color,
                "title": {
                    "tag": "plain_text",
                    "content": title
                }
            },
            "elements": []
        }
        
        # 添加内容
        card["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": content
            }
        })
        
        # 添加分割线
        card["elements"].append({
            "tag": "hr"
        })
        
        # 添加底部信息
        card["elements"].append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": footer
                }
            ]
        })
        
        # 添加按钮
        if button_text and button_url:
            card["elements"].append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": button_text
                        },
                        "type": button_type,
                        "url": button_url
                    }
                ]
            })
        
        return card

