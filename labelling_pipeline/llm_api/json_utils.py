# JSON 데이터를 계층 구조로 요약하여 문자열로 반환
def summarize_json_hierarchy(data, level=1):
    summary = ""
    indent = "  " * level
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict) and "name" in value:
                summary += f"{indent}- {value['name']}\n"
                if "children" in value:
                    summary += summarize_json_hierarchy(value["children"], level + 1)
            elif isinstance(value, dict):
                summary += summarize_json_hierarchy(value, level + 1)
            else:
                summary += f"{indent}- {value}\n"
    return summary
