import asyncio
import os
from typing import List

from agents import create_style_analyzer_agent, create_cls_generator_agent, create_semantic_extractor_agent
from agents.cls_inspector import create_cls_inspector_agent
from agents.combined_inspector import create_combined_inspector_agent
from agents.debugger_agent import create_debugger_agent
from agents.img_recognizer import create_img_recognizer_agent
from agents.tex_inspector import create_tex_inspector_agent
from agents.visual_auditor import create_visual_auditor_agent
from llm_client import async_client, MODEL, client, gemini_client, gemini_async_client, GEMINI_MODEL
from services.latex_workflow import LatexReverseEngineeringService


async def async_service(pic_paths: List[str]):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        base_dir = os.getcwd()

    # 2. 创建 Agents (依赖注入准备)
    # Style Agent: 使用同步 Vision Client (visual_client)
    agent_style = create_style_analyzer_agent(gemini_client, GEMINI_MODEL)

    # CLS Agent: 使用异步 Text Client (async_client)
    agent_cls = create_cls_generator_agent(async_client, MODEL)

    # TEX Agent: 使用异步 Vision Client (visual_async_client)
    agent_tex = create_semantic_extractor_agent(gemini_async_client, GEMINI_MODEL)

    # Debugger Agent: 使用同步 Text Client (client)
    agent_debug = create_debugger_agent(client, MODEL)

    # Visual Auditor Agent: 使用同步 Vision Client (visual_client)
    agent_visual = create_visual_auditor_agent(gemini_client, GEMINI_MODEL)

    # TEX Inspector Agent: 使用同步 Text Client (client)
    agent_tex_inspector = create_tex_inspector_agent(client, MODEL)

    # CLS Inspector Agent: 使用同步 Text Client (client)
    agent_cls_inspector = create_cls_inspector_agent(client, MODEL)

    # Combined Inspector Agent: 使用同步 Text Client (client)
    agent_combined_inspector = create_combined_inspector_agent(client, MODEL)

    agent_img_recognizer = create_img_recognizer_agent(gemini_client, GEMINI_MODEL)



    # 3. 实例化服务
    service = LatexReverseEngineeringService(
        style_agent=agent_style,
        cls_agent=agent_cls,
        tex_agent=agent_tex,
        debugger_agent=agent_debug,
        visual_auditor_agent=agent_visual,
        tex_inspector_agent=agent_tex_inspector,
        cls_inspector_agent=agent_cls_inspector,
        combined_inspector_agent=agent_combined_inspector,
        img_recognizer_agent=agent_img_recognizer,
        max_retries=5,
    )

    # 4. 运行服务
    await service.run(base_dir=base_dir, image_paths=pic_paths)

class WorkService:
    def __init__(self,pic_paths: List[str]):
        self.pic_paths = pic_paths

    def run(self):
        asyncio.run(async_service(self.pic_paths))

