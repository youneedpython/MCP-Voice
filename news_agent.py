"""
네이버 검색 MCP 서버 + 파일시스템 MCP 서버를 함께 붙인 에이전트를 실행하는 모듈.
"""
import os
import platform

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerStdio

from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, MODEL_NAME


def _npx_command_params(extra_args: list[str], env: dict | None = None) -> dict:
    """OS에 따라 npx 실행 방식이 다르므로 여기서 한 번에 처리한다."""
    if platform.system() == "Windows":
        params = {"command": "cmd", "args": ["/c", "npx", "-y", *extra_args]}
    else:
        params = {"command": "npx", "args": ["-y", *extra_args]}
    if env:
        params["env"] = env
    return params


async def run_agent(mcp_servers: list[MCPServer], input_items: list,
                     model_name: str = MODEL_NAME):
    agent = Agent(
        name="News Briefing Assistant",
        model=model_name,
        instructions="""1. filesystem_server : 디렉토리 안의 파일(관심 키워드, 과거 브리핑 로그 등)을 참고해 답변할 때 사용.
2. naver_search_server : 실시간 뉴스/정보 검색이 필요할 때 사용.
답변은 항상 한국어로, 소리 내어 읽었을 때 자연스럽도록 2~3문장 이내로 짧게 요약해라.
이전 대화 내용을 기억하고, "그거", "아까 그건" 같은 표현이 나오면 직전 대화 맥락을 참고해서 답하라.""",
        mcp_servers=mcp_servers,
    )

    print(f"Running: {input_items[-1]['content'] if input_items else ''}")
    return await Runner.run(starting_agent=agent, input=input_items)


async def get_briefing(input_items: list, results_dir: str) -> tuple[str, list]:
    """filesystem + naver_search 두 MCP 서버를 띄우고 에이전트를 실행해 응답과 갱신된 대화 이력을 반환한다.

    input_items는 이전 턴까지의 대화 이력 + 이번 턴 사용자 발화가 담긴 리스트다.
    (agents SDK의 RunResult.to_input_list() 패턴 — 이걸 다음 턴에 그대로 넘기면
    에이전트가 이전 대화 맥락을 기억한 채로 이어서 답할 수 있다.)
    """
    fs_params = _npx_command_params(["@modelcontextprotocol/server-filesystem", results_dir])
    naver_params = _npx_command_params(
        ["@isnow890/naver-search-mcp"],
        env={"NAVER_CLIENT_ID": NAVER_CLIENT_ID, "NAVER_CLIENT_SECRET": NAVER_CLIENT_SECRET},
    )

    async with MCPServerStdio(name="Filesystem Server", params=fs_params) as filesystem_server, \
               MCPServerStdio(name="Naver Search Server", params=naver_params) as naver_search_server:

        trace_id = gen_trace_id()
        with trace(workflow_name="Voice News Briefing", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            result = await run_agent([filesystem_server, naver_search_server], input_items)

    return result.final_output, result.to_input_list()
