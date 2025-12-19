import os
from openai import OpenAI

try:
    client = OpenAI(
        # The API keys for the Singapore and China (Beijing) regions are different. To obtain an API key, see https://modelstudio.console.alibabacloud.com/?tab=model#/api-key
        # If you have not configured an environment variable, replace the following line with your Model Studio API key: api_key="sk-xxx",
        #api_key=os.getenv("$env:MODELSTUDIO_API_KEY"),
        api_key = "sk-ffbfcf091d86484bb81da4f0e1e39d9c",
        # The following URL is for the Singapore region. If you use a model in the China (Beijing) region, replace the URL with: https://dashscope.aliyuncs.com/compatible-mode/v1
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )

    completion = client.chat.completions.create(
        model="qwen-plus",  
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Who are you?'}
            ]
    )
    print(completion.choices[0].message.content)
except Exception as e:
    print(f"Error message: {e}")
    print("For more information, see https://www.alibabacloud.com/help/en/model-studio/developer-reference/error-code")