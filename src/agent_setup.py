# agent_setup.py
import yaml
import os
from dataclasses import dataclass
from typing import Dict
from atomic_agents.context import SystemPromptGenerator


# =============================================================================
# 1. 定义配置类
# =============================================================================
@dataclass
class AgentConfig:
    name: str
    role: str
    system_prompt_generator: SystemPromptGenerator


# =============================================================================
# 2. 内部加载逻辑
# =============================================================================
def _load_yaml_config(config_path="agent_config.yaml") -> dict:
    """读取 YAML 文件"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _create_agent_config(agent_data: dict) -> AgentConfig:
    """工厂函数：将字典转换为 AgentConfig 对象"""
    raw_prompt = agent_data["system_prompt"]

    # 将 role 注入到 background
    role_description = f"你是指挥官指派的【{agent_data['role']}】。"
    combined_background = [role_description] + raw_prompt["background"]

    generator = SystemPromptGenerator(
        background=combined_background,
        steps=raw_prompt["steps"],
        output_instructions=raw_prompt["output_instructions"],
    )

    return AgentConfig(
        name=agent_data["name"],
        role=agent_data["role"],
        system_prompt_generator=generator,
    )


def load_all_agents() -> Dict[str, AgentConfig]:
    """
    返回类型注解 -> Dict[str, AgentConfig]
    这样 IDE 就知道这个字典里装的都是 AgentConfig 对象
    """
    yaml_data = _load_yaml_config()
    agents_dict = {}

    for agent_data in yaml_data["agents"]:
        config = _create_agent_config(agent_data)
        agents_dict[config.name] = config

    return agents_dict


# =============================================================================
# 3. 模块级导出变量 (关键修改部分)
# =============================================================================

# 加载配置字典
_all_configs = load_all_agents()


def _get_config_safe(name: str) -> AgentConfig:
    """
    辅助函数：确保获取到的配置不为 None。
    如果配置不存在，直接抛出错误，而不是让变量变成 None 类型。
    这能让 IDE 确信返回的一定是 AgentConfig 实例。
    """
    cfg = _all_configs.get(name)
    if cfg is None:
        raise ValueError(f"Critical Error: Agent config '{name}' not found in yaml.")
    return cfg


style_analyzer_config: AgentConfig = _get_config_safe("style_analyzer")
cls_generator_config: AgentConfig = _get_config_safe("cls_generator")
semantic_extractor_config: AgentConfig = _get_config_safe("semantic_extractor")
compiler_debugger_config: AgentConfig = _get_config_safe("compiler_debugger")
visual_auditor_config: AgentConfig = _get_config_safe("visual_auditor")
tex_inspector_config: AgentConfig = _get_config_safe("tex_inspector")
cls_inspector_config: AgentConfig = _get_config_safe("cls_inspector")
combined_inspector_config: AgentConfig = _get_config_safe("combined_inspector")
img_recognizer_config: AgentConfig = _get_config_safe("img_recognizer")
