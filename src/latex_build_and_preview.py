import asyncio
import os
import subprocess
from pathlib import Path
from typing import Tuple, List, Dict

from launcher_file import set_launcher_file_value


class LatexEnvironmentError(Exception):
    """当 LaTeX 环境或系统级故障时抛出"""
    pass

latex_engine_path = "../TinyTeX/bin/windows/xelatex.exe"

def detect_latex_engine()->bool:
    result = subprocess.run([latex_engine_path, "--version"], capture_output=True, text=True, timeout=5, encoding='utf-8')
    if result.returncode == 0:
        return True
    else:
        return False

def _sync_build_and_preview(
        cls_content: str, tex_content: str, timeout: int = 60
) -> Tuple[bool, str, List[Dict[str, str]]]:
    """
    使用本地 LaTeX 环境编译项目（同步版本）。
    """
    if not detect_latex_engine():
        set_launcher_file_value("latex_installed", "false")
        raise LatexEnvironmentError("未找到latex环境，请重新启动")

    # 1. 准备本地工作目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 获取项目根目录
    local_output_path = Path(project_root) / "result"
    local_output_path.mkdir(exist_ok=True)

    # 将内容写入临时文件
    main_tex_path = local_output_path / "main.tex"
    template_cls_path = local_output_path / "template.cls"

    with open(template_cls_path, "w", encoding="utf-8") as f:
        f.write(cls_content)

    with open(main_tex_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    # 尝试编译
    try:
        # 先删除main.pdf文件
        if (local_output_path / "main.pdf").exists():
            (local_output_path / "main.pdf").unlink()


        result = subprocess.run([
            latex_engine_path,
            "-interaction=nonstopmode",
            "-output-directory=" + str(local_output_path.as_posix()),
            str(main_tex_path)
        ], capture_output=True, text=True, timeout=timeout, encoding='utf-8')

        if result.returncode == 0:
            # 编译成功
            return True, "编译成功", []
        else:
            # 编译失败
            error_msg = f"LaTeX 编译错误: {result.stderr}\n{result.stdout}"
            return False, error_msg, []

        # 如果有pdf文件生成，则返回成功
        # if (local_output_path / "main.pdf").exists():
        #     return True, "编译成功", []
        # else:
        #     # 编译失败
        #     error_msg = f"LaTeX 编译错误: {result.stderr}\n{result.stdout}"
        #     return False, error_msg, []

    except subprocess.TimeoutExpired:
        raise LatexEnvironmentError(f"LaTeX 编译超时 ({timeout}秒)")
    except Exception as e:
        raise LatexEnvironmentError(f"LaTeX 编译过程中发生错误: {str(e)}")

async def build_and_preview(
        cls_content: str, tex_content: str, timeout: int = 60
) -> Tuple[bool, str, List[Dict[str, str]]]:
    return await asyncio.to_thread(
        _sync_build_and_preview, cls_content, tex_content, timeout
    )
