import json
import requests
from typing import List, Dict, Any, Callable
import inspect
import os
from dotenv import load_dotenv
from prompts import generate_prompt

# .env 파일 로드
load_dotenv()


class SimpleToolCaller:
    def __init__(self, TOOLS: List[Dict] = None, TOOL_FUNCTIONS: Dict = None):
        self.TOOLS = TOOLS
        self.TOOL_FUNCTIONS = TOOL_FUNCTIONS
        if os.getenv("USE_OPENAI") == "True":
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = "https://api.openai.com/v1"
            # self.model = "gpt-3.5-turbo"
            self.model = "gpt-4o-mini-2024-07-18"
        else:
            self.api_key = "EMPTY"
            self.base_url = "https://5c86-109-61-127-28.ngrok-free.app/v1"
            self.model = "Qwen/Qwen3-32B-AWQ"

    def call_llm(self, messages: List[Dict], tools: List[Dict] = None) -> Dict:
        """LLM API를 호출합니다."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {"model": self.model, "messages": messages, "temperature": 0.7}

        if tools:
            data["tools"] = tools

        response = requests.post(
            f"{self.base_url}/chat/completions", headers=headers, json=data
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API 호출 실패: {response.status_code} - {response.text}")

    def execute_tool(self, tool_call: Dict) -> str:
        """도구를 실행합니다."""
        print("🔧 EXECUTE TOOL-->", tool_call)

        function_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])

        if function_name in self.TOOL_FUNCTIONS:
            func = self.TOOL_FUNCTIONS[function_name]
            return func(**arguments)
        else:
            return f"알 수 없는 도구: {function_name}"

    def chat(self, messages: List[Dict], with_tools: bool = True) -> str:
        """도구를 사용하여 대화합니다."""
        # 시스템 프롬프트로 시작하지 않으면 시스템 프롬프트를 추가합니다.
        if messages[0]["role"] != "system":
            system_messages = generate_prompt("system")
            messages = system_messages + messages

        # 첫 번째 LLM 호출
        if with_tools:
            response = self.call_llm(messages, self.TOOLS)
        else:
            response = self.call_llm(messages)
        assistant_message = response["choices"][0]["message"]
        messages.append(assistant_message)

        # 도구 호출이 있는지 확인 (with_tools가 True인 경우에만)
        if with_tools and assistant_message.get("tool_calls"):
            for tool_call in assistant_message["tool_calls"]:
                # 도구 실행
                tool_result = self.execute_tool(tool_call)

                # 도구 결과를 메시지에 추가
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result,
                    }
                )

            # 도구 결과를 받은 후 두 번째 LLM 호출
            final_response = self.call_llm(messages)
            return final_response["choices"][0]["message"]["content"]
        else:
            return assistant_message["content"]
