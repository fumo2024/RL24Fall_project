import openai
import re
import json
import os
import random

# 定义文件名
apikey_file = 'apikey.json'

# 检查文件是否存在
if not os.path.exists(apikey_file):
    # 提示用户创建文件并提供示例内容
    print(f"文件 {apikey_file} 不存在，请创建该文件并添加以下内容：")
    example_content = [
        {
            "API_KEY": "YOUR_API_KEY",
            "BASE_URL": "YOUR_BASE_URL",
            "MODEL": "MODEL_NAME"
        }
    ]
    print(json.dumps(example_content, indent=4))
    # 退出程序
    exit(1)

# 从 apikey.json 文件中读取 API_KEY 和 BASE_URL
with open(apikey_file, 'r') as f:
    data = json.load(f)
    api_info = data[0]  # 假设只需要第一个对象的信息

API_KEY = api_info['API_KEY']   # Your API key
BASE_URL = api_info['BASE_URL']  # Your base URL
MODEL = api_info['MODEL']        # Your model name

def main():
    prompt = "你是一位大模型提示词生成专家，请根据用户的需求编写一个智能助手的提示词，来指导大模型进行内容生成，要求：\n1. 以 Markdown 格式输出\n2. 贴合用户需求，描述智能助手的定位、能力、知识储备\n3. 提示词应清晰、精确、易于理解，在保持质量的同时，尽可能简洁\n4. 只输出提示词，不要输出多余解释 "
    print(f"DEBUG: LLM 输入: {prompt}")
    content = "请帮我生成一个“对于一个15x15的五子棋棋局进行评分”的提示词"

    openai.api_key = API_KEY
    openai.api_base = BASE_URL
    response = openai.ChatCompletion.create(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": content}
                        ],
                        temperature=0.3,  # Set temperature to 0 for deterministic output
                        # top_p = 0,   # gpt-4.o
                        stream=False,
                    )
    llm_response = response['choices'][0]['message']['content']
    print(f"DEBUG: LLM 响应: {llm_response}")
    
if __name__ == '__main__':
    main()  