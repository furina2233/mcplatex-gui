import json
import logging


class log_util:
    # 日志文件将在程序启动时被刷新，仅记录程序该次运行时产生的日志
    has_init = False  # 如果程序刚启动，则先配置日志并刷新日志

    @staticmethod
    def __init_log():
        # 先清空日志文件
        with open("llm_request.log", "w", encoding='utf-8'):
            pass
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,  # 设置最低日志级别
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 定义格式
            filename="llm_request.log",  # 日志输出到文件而非控制台
            filemode='a'  # 'w' 为覆盖写，'a' 为追加写
        )
        log_util.has_init = True

    # 辅助函数：递归删除JSON中的所有"url"键，因为在实际测试中发现url占据了日志的大部分空间
    @staticmethod
    def __remove_url_keys(obj):
        if isinstance(obj, dict):
            # 创建新的字典，排除"url"键
            new_dict = {}
            for key, value in obj.items():
                if key != "url":
                    new_dict[key] = log_util.__remove_url_keys(value)
            return new_dict
        elif isinstance(obj, list):
            # 递归处理列表中的每个元素
            return [log_util.__remove_url_keys(item) for item in obj]
        else:
            # 基本类型直接返回
            return obj

    @staticmethod
    def log_request_body(request_body):
        log_util.__log_request_body_and_response_body(request_body, "request")

    @staticmethod
    def log_response_body(response_body):
        log_util.__log_request_body_and_response_body(response_body, "response")

    @staticmethod
    def __log_request_body_and_response_body(body, info_type):
        if not log_util.has_init:
            log_util.__init_log()
        try:
            parsed_json = json.loads(body)
            # 删除所有"url"键
            cleaned_json = log_util.__remove_url_keys(parsed_json)
            # 美化输出
            formatted_body = json.dumps(cleaned_json, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # 如果不是有效JSON，直接使用原始内容
            formatted_body = body
        logging.info(f"--- LLM {info_type} Body ---\n{formatted_body}\n--- End {info_type} Body ---")

        # 添加事件：持续跟踪latex_output/template.cls文件的变化
