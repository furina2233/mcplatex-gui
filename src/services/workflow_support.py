import copy
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.cls_generator import CLSGeneratorOutput
from agents.semantic_extractor import SemanticExtractorOutput
from schemas.cls_schema import (
    AbstractSettings,
    AuthorSettings,
    CaptionSettings,
    FontSettings,
    GeometrySettings,
    HeaderFooterSettings,
    ParagraphSettings,
    SectionSettings,
    TitleSettings,
)
from schemas.style_schema import StyleAnalysisReport

HEADER_FOOTER_RESTORATION_GUIDANCE = (
    "Pay special attention to the page header and footer. If the header contains a journal name or other running text, "
    "restore that structure exactly instead of dropping it, including any multi-line header. If there is a horizontal "
    "rule directly between the header and the body text, preserve it as well. Do not assume the footer contains only a "
    "page number: when visible, restore page numbers, footer notes or annotations, and footer rules, whether they are "
    "full-width rules or shorter lines."
)

HEADER_FOOTER_AUDIT_GUIDANCE = (
    "Treat header and footer fidelity as mandatory during visual audit. Check whether the rendered page preserves the "
    "journal name or other running text at the top, including multi-line headers; any horizontal rule directly between "
    "the header and the body; and footer content including page numbers, notes or annotations, and footer rules of any "
    "length. Missing, merged, shortened, or misplaced header/footer text and lines must be reported as layout issues."
)

HEADER_FOOTER_REVISION_GUIDANCE = (
    "During revision, keep the same restoration requirements: preserve header journal names or other running text, "
    "multi-line headers, any horizontal rule directly below the header, and footer content including page numbers, "
    "notes or annotations, and footer rules whenever they are visible in the source image."
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def work_dir() -> Path:
    path = project_root() / "work"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cls_dir() -> Path:
    path = work_dir() / "cls"
    path.mkdir(parents=True, exist_ok=True)
    return path


def tex_dir() -> Path:
    path = work_dir() / "tex"
    path.mkdir(parents=True, exist_ok=True)
    return path


def pdf_dir() -> Path:
    path = work_dir() / "pdf"
    path.mkdir(parents=True, exist_ok=True)
    return path


def temp_dir() -> Path:
    path = work_dir() / "temp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_work_name() -> str:
    """基于当前时间戳生成工作名称，格式：YYYYMMDD_HHMMSS"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def extract_documentclass_name(tex_code: str, default: str = "template") -> str:
    match = re.search(r"\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}", tex_code)
    if match:
        return match.group(1).strip() or default
    return default


def normalize_tex_documentclass(tex_code: str, class_name: str | None = None) -> str:
    resolved_class_name = class_name or extract_documentclass_name(tex_code)
    pattern = r"\\documentclass(\[[^\]]*\])?\{[^}]+\}"

    if re.search(pattern, tex_code):
        tex_code = re.sub(pattern, rf"\\documentclass\1{{{resolved_class_name}}}", tex_code, count=1)
    else:
        tex_code = f"\\documentclass{{{resolved_class_name}}}\n" + tex_code.lstrip()

    return sanitize_generated_tex(tex_code)


def sanitize_generated_tex(tex_code: str) -> str:
    patterns = [
        r"(?is)%\s*Placeholders for figures and tables.*$",
        r"(?is)\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
        r"(?im)^\s*\\bibliographystyle\{.*\}\s*$",
        r"(?im)^\s*\\bibliography\{.*\}\s*$",
        r"(?is)\\section\*?\{References\}.*$",
        r"(?is)\\section\*?\{参考文献\}.*$",
    ]

    cleaned = tex_code
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned)

    return normalize_latex_source(cleaned)


def normalize_cls_output(cls_output: CLSGeneratorOutput, class_name: str = "template") -> CLSGeneratorOutput:
    from schemas.cls_schema import HeaderLineConfig, FootnoteSettings

    def normalize_value(value):
        if isinstance(value, str):
            return value.replace("\\\\", "\\")
        if isinstance(value, list):
            return [normalize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: normalize_value(item) for key, item in value.items()}
        return value

    normalized = normalize_value(copy.deepcopy(cls_output.model_dump()))
    normalized["class_name"] = class_name

    # 使用 model_validate 创建对象
    result = CLSGeneratorOutput.model_validate(normalized)

    # 确保 header_footer.journal_header_lines 中的元素是 HeaderLineConfig 对象
    if result.header_footer and result.header_footer.journal_header_lines:
        result.header_footer.journal_header_lines = [
            line if isinstance(line, HeaderLineConfig) else HeaderLineConfig.model_validate(line)
            for line in result.header_footer.journal_header_lines
        ]

    # 确保 footnote 是 FootnoteSettings 对象
    if hasattr(result, "footnote") and result.footnote and isinstance(result.footnote, dict):
        result.footnote = FootnoteSettings.model_validate(result.footnote)

    return result


def normalize_latex_source(source: str) -> str:
    normalized = source.replace("\r\n", "\n").strip()
    return normalized + "\n"


def work_item_paths(work_name: str) -> dict[str, Path]:
    return {
        "cls": cls_dir() / f"{work_name}.cls",
        "tex": tex_dir() / f"{work_name}.tex",
        "pdf": pdf_dir() / f"{work_name}.pdf",
        "temp_cls": temp_dir() / f"{work_name}.cls",
        "temp_tex": temp_dir() / f"{work_name}.tex",
        "temp_log": temp_dir() / f"{work_name}.log",
        "temp_aux": temp_dir() / f"{work_name}.aux",
        "temp_out": temp_dir() / f"{work_name}.out",
        "temp_preview_prefix": temp_dir() / f"{work_name}_page_",
        "cls_config": temp_dir() / f"{work_name}.cls_config.json",
        "style_report": temp_dir() / f"{work_name}.style_report.json",
        "images_meta": temp_dir() / f"{work_name}.images.json",
    }


def write_working_sources(work_name: str, cls_code: str, tex_code: str) -> tuple[str, str]:
    paths = work_item_paths(work_name)
    paths["cls"].write_text(normalize_latex_source(cls_code), encoding="utf-8")
    paths["tex"].write_text(normalize_latex_source(tex_code), encoding="utf-8")
    return str(paths["cls"]), str(paths["tex"])


def overwrite_working_source(work_name: str, source_type: str, content: str) -> str:
    paths = work_item_paths(work_name)
    target_path = paths["cls"] if source_type == "cls" else paths["tex"]
    target_path.write_text(normalize_latex_source(content), encoding="utf-8")
    return str(target_path)


def save_iteration_snapshot(work_name: str, attempt: int, cls_code: str, tex_code: str) -> None:
    snapshot_cls = temp_dir() / f"{work_name}_attempt_{attempt}.cls"
    snapshot_tex = temp_dir() / f"{work_name}_attempt_{attempt}.tex"
    snapshot_cls.write_text(normalize_latex_source(cls_code), encoding="utf-8")
    snapshot_tex.write_text(normalize_latex_source(tex_code), encoding="utf-8")


def save_work_item(
        work_name: str,
        cls_code: str,
        tex_code: str,
        cls_output: CLSGeneratorOutput | None = None,
        style_report: StyleAnalysisReport | None = None,
        source_images: list[str] | None = None,
) -> dict[str, str]:
    paths = work_item_paths(work_name)
    paths["cls"].write_text(normalize_latex_source(cls_code), encoding="utf-8")
    paths["tex"].write_text(normalize_latex_source(tex_code), encoding="utf-8")

    if cls_output is not None:
        normalized_cls = normalize_cls_output(cls_output, class_name=work_name)
        paths["cls_config"].write_text(normalized_cls.model_dump_json(indent=2), encoding="utf-8")

    if style_report is not None:
        paths["style_report"].write_text(style_report.model_dump_json(indent=2), encoding="utf-8")

    if source_images is not None:
        paths["images_meta"].write_text(json.dumps(source_images, indent=2, ensure_ascii=False), encoding="utf-8")

    return {key: str(value) for key, value in paths.items()}


def save_final_results(
        work_name: str,
        cls_output: CLSGeneratorOutput,
        tex_output: SemanticExtractorOutput | None,
        cls_code: str,
        tex_code: str,
        images,
        style_report: StyleAnalysisReport | None = None,
        source_images: list[str] | None = None,
) -> dict[str, str]:
    return save_work_item(
        work_name=work_name,
        cls_code=cls_code,
        tex_code=tex_code,
        cls_output=cls_output,
        style_report=style_report,
        source_images=source_images,
    )


def list_template_files() -> list[Path]:
    """列出所有模板文件，按文件名倒序排列（最新的在前）"""
    return sorted(cls_dir().glob("*.cls"), reverse=True)


def list_tex_files() -> list[Path]:
    """列出所有TEX文档文件，按文件名倒序排列（最新的在前）"""
    return sorted(tex_dir().glob("*.tex"), reverse=True)


def load_work_item_sources(work_name: str) -> tuple[str | None, str | None]:
    paths = work_item_paths(work_name)
    cls_code = paths["cls"].read_text(encoding="utf-8") if paths["cls"].exists() else None
    tex_code = paths["tex"].read_text(encoding="utf-8") if paths["tex"].exists() else None
    return cls_code, tex_code


def load_cls_output(work_name: str) -> CLSGeneratorOutput | None:
    path = work_item_paths(work_name)["cls_config"]
    if not path.exists():
        cls_path = work_item_paths(work_name)["cls"]
        if not cls_path.exists():
            return None
        return parse_generated_cls_code(cls_path.read_text(encoding="utf-8"), class_name=work_name)
    # 加载后确保嵌套对象类型正确
    result = CLSGeneratorOutput.model_validate_json(path.read_text(encoding="utf-8"))
    return ensure_cls_output_proper_types(result)


def ensure_cls_output_proper_types(cls_output: CLSGeneratorOutput) -> CLSGeneratorOutput:
    """
    确保 CLSGeneratorOutput 中的嵌套对象是正确类型而非 dict。
    这在从 JSON 加载或从 LLM 返回后特别有用。
    """
    from schemas.cls_schema import HeaderLineConfig, FootnoteSettings

    # 确保 header_footer.journal_header_lines 中的元素是 HeaderLineConfig
    if cls_output.header_footer and cls_output.header_footer.journal_header_lines:
        cls_output.header_footer.journal_header_lines = [
            line if isinstance(line, HeaderLineConfig) else HeaderLineConfig.model_validate(line)
            for line in cls_output.header_footer.journal_header_lines
        ]

    # 确保 footnote 是 FootnoteSettings
    if hasattr(cls_output, "footnote") and cls_output.footnote:
        if isinstance(cls_output.footnote, dict):
            cls_output.footnote = FootnoteSettings.model_validate(cls_output.footnote)

    return cls_output


def load_style_report(work_name: str) -> StyleAnalysisReport | None:
    path = work_item_paths(work_name)["style_report"]
    if not path.exists():
        return None
    return StyleAnalysisReport.model_validate_json(path.read_text(encoding="utf-8"))


def load_source_images(work_name: str) -> list[str]:
    path = work_item_paths(work_name)["images_meta"]
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def parse_generated_cls_code(cls_code: str, class_name: str | None = None) -> CLSGeneratorOutput:
    lines = cls_code.splitlines()
    resolved_class_name = class_name or _extract_first_group(r"\\ProvidesClass\{([^}]+)\}", cls_code, "template")
    load_class_options = _extract_first_group(r"\\LoadClass\[([^\]]+)\]\{([^}]+)\}", cls_code, None, group=1)
    base_class = _extract_first_group(r"\\LoadClass\[([^\]]+)\]\{([^}]+)\}", cls_code, "article", group=2)
    options = [item.strip() for item in (load_class_options or "").split(",") if item.strip()]
    base_font_size = next((item for item in options if item.endswith("pt")), "10pt")
    is_twocolumn = "twocolumn" in options

    geometry_options = _parse_option_string(
        _extract_first_group(r"\\RequirePackage\[([^\]]+)\]\{geometry\}", cls_code, ""))
    geometry = GeometrySettings(
        paper_size=geometry_options.get("paper_size", "a4paper"),
        top_margin=geometry_options.get("top", "72pt"),
        bottom_margin=geometry_options.get("bottom", "72pt"),
        left_margin=geometry_options.get("left", "72pt"),
        right_margin=geometry_options.get("right", "72pt"),
        column_sep=geometry_options.get("columnsep"),
        head_height=geometry_options.get("headheight", "14pt"),
        head_sep=geometry_options.get("headsep", "18pt"),
        foot_skip=geometry_options.get("footskip", "24pt"),
    )

    main_font_family = "sans-serif" if "\\setmainfont{Arial}" in cls_code else "serif"
    math_font_package = _extract_first_group(r"\\setmathfont\{([^}]+)\}", cls_code, "Cambria Math")
    fonts = FontSettings(
        base_font_size=base_font_size,
        main_font_family=main_font_family,
        math_font_package=math_font_package,
        use_microtype="\\RequirePackage{microtype}" in cls_code,
    )

    additional_packages = []
    core_packages = {"geometry", "fontspec", "xeCJK", "unicode-math", "microtype", "fancyhdr", "titlesec", "caption",
                     "xcolor", "graphicx"}
    for package in re.findall(r"\\RequirePackage(?:\[[^\]]+\])?\{([^}]+)\}", cls_code):
        if package not in core_packages and package not in additional_packages:
            additional_packages.append(package)

    paragraph = ParagraphSettings(
        line_spread=_extract_first_group(r"\\linespread\{([^}]+)\}", cls_code, "1.0"),
        paragraph_indent=_extract_first_group(r"\\setlength\{\\parindent\}\{([^}]+)\}", cls_code, "0pt"),
        paragraph_skip=_extract_first_group(r"\\setlength\{\\parskip\}\{([^}]+)\}", cls_code, "0pt"),
        text_justification="ragged-right" if "\\raggedright" in cls_code else "justified",
        caption_skip=_extract_first_group(r"skip=([^,\n}]+)", cls_code, "6pt"),
    )

    firstpage_block = _extract_first_group(r"\\fancypagestyle\{firstpage\}\{%(.*?)\n\}", cls_code, "", flags=re.S)
    header_footer = HeaderFooterSettings(
        first_page_header_left=_extract_fancy_value(firstpage_block, "head", "L"),
        first_page_header_center=_extract_fancy_value(firstpage_block, "head", "C"),
        first_page_header_right=_extract_fancy_value(firstpage_block, "head", "R"),
        first_page_footer_center=_extract_fancy_value(firstpage_block, "foot", "C"),
        first_page_has_rule=_extract_first_group(r"\\renewcommand\{\\headrulewidth\}\{([^}]+)\}", firstpage_block,
                                                 "0pt") != "0pt",
        running_header_left=_extract_fancy_value(cls_code, "head", "L"),
        running_header_center=_extract_fancy_value(cls_code, "head", "C"),
        running_header_right=_extract_fancy_value(cls_code, "head", "R", default="\\thepage"),
        running_footer_center=_extract_fancy_value(cls_code, "foot", "C"),
        header_rule_width=_extract_first_group(r"\\renewcommand\{\\headrulewidth\}\{([^}]+)\}", cls_code, "0.4pt"),
        footer_rule_width=_extract_first_group(r"\\renewcommand\{\\footrulewidth\}\{([^}]+)\}", cls_code, "0pt"),
    )

    section_font_line = _find_line_after(lines, "\\titleformat{\\section}")
    section_spacing_line = _find_line_after(lines, "\\titlespacing*{\\section}")
    subsection_font_line = _find_line_after(lines, "\\titleformat{\\subsection}")
    subsection_spacing_line = _find_line_after(lines, "\\titlespacing*{\\subsection}")

    section_alignment, section_font = _parse_alignment_and_font(_strip_outer_braces(section_font_line))
    _, subsection_font = _parse_alignment_and_font(_strip_outer_braces(subsection_font_line))
    section_before, section_after = _parse_titlespacing_values(section_spacing_line)
    subsection_before, subsection_after = _parse_titlespacing_values(subsection_spacing_line)
    sections = SectionSettings(
        section_font_size=section_font["size"],
        section_font_weight=section_font["weight"],
        section_font_family=section_font["family"],
        section_alignment=section_alignment,
        section_numbering_format="arabic",
        section_space_before=section_before,
        section_space_after=section_after,
        subsection_font_size=subsection_font["size"],
        subsection_font_weight=subsection_font["weight"],
        subsection_font_style=subsection_font["style"],
        subsection_space_before=subsection_before,
        subsection_space_after=subsection_after,
    )

    title_space_before = _extract_first_group(r"\\vspace\*\{([^}]+)\}%", cls_code, "0pt")
    title_space_after = _extract_nth_group(r"\\vspace\{([^}]+)\}%", cls_code, 1, "12pt")
    author_space_after = _extract_nth_group(r"\\vspace\{([^}]+)\}%", cls_code, 2, "12pt")
    title_line = _find_line_containing(lines, "\\@title\\par")
    author_line = _find_line_containing(lines, "\\@author\\par")
    title_alignment, title_font = _parse_alignment_and_font(_extract_inner_title_block(title_line, "\\@title\\par"))
    author_alignment, author_font = _parse_alignment_and_font(_extract_inner_title_block(author_line, "\\@author\\par"))
    title = TitleSettings(
        font_size=title_font["size"],
        font_weight=title_font["weight"],
        font_family=title_font["family"],
        alignment=title_alignment,
        space_before=title_space_before,
        space_after=title_space_after,
    )
    author = AuthorSettings(
        name_font_size=author_font["size"],
        name_font_weight=author_font["weight"],
        affiliation_font_size=author_font["size"],
        affiliation_font_style="italic",
        alignment=author_alignment,
        space_after=author_space_after,
    )

    abstract_before = _extract_first_group(r"\\vspace\{([^}]+)\}%\s*\\begin\{list\}", cls_code, "12pt", flags=re.S)
    abstract_after = _extract_first_group(r"\\end\{list\}%\s*\\vspace\{([^}]+)\}%", cls_code, "12pt", flags=re.S)
    left_indent = _extract_first_group(r"\\setlength\{\\leftmargin\}\{([^}]+)\}", cls_code, "0pt")
    right_indent = _extract_first_group(r"\\setlength\{\\rightmargin\}\{([^}]+)\}", cls_code, "0pt")
    abstract_line = _find_line_containing(lines, "\\item[]{\\noindent")
    abstract_heading = _extract_first_group(r"\\item\[\]\{\\noindent(?:\\bfseries\s+)?([^}]+)\}", abstract_line,
                                            "Abstract")
    abstract_font = _parse_font_fragment(_extract_first_group(r"\\par\\noindent(.*)", abstract_line, "", flags=re.S))
    abstract = AbstractSettings(
        font_size=abstract_font["size"],
        font_style=abstract_font["style"],
        left_indent=left_indent,
        right_indent=right_indent,
        heading_text=abstract_heading,
        heading_font_weight="bold" if "\\bfseries" in abstract_line else "normal",
        space_before=abstract_before,
        space_after=abstract_after,
    )

    caption_font = _extract_first_group(r"font=\{([^}]+)\}", cls_code, "small")
    caption = CaptionSettings(
        font_size=f"\\{caption_font}" if not caption_font.startswith("\\") else caption_font,
        label_font_weight="bold" if "labelfont={bf}" in cls_code else "normal",
        label_separator=_parse_label_separator(_extract_first_group(r"labelsep=\{([^}]+)\}", cls_code, "colon")),
        figure_position="below",
        table_position="above",
    )

    custom_commands = ""
    if "% Custom commands" in cls_code:
        custom_commands = cls_code.split("% Custom commands", 1)[1].split("\\endinput", 1)[0].strip()

    return CLSGeneratorOutput(
        class_name=resolved_class_name,
        base_class=base_class,
        is_twocolumn=is_twocolumn,
        geometry=geometry,
        fonts=fonts,
        title=title,
        author=author,
        abstract=abstract,
        sections=sections,
        header_footer=header_footer,
        paragraph=paragraph,
        caption=caption,
        additional_packages=additional_packages,
        custom_commands=custom_commands,
    )


def _extract_first_group(pattern: str, text: str, default: Any = "", group: int = 1, flags: int = 0):
    match = re.search(pattern, text, flags)
    if not match:
        return default
    return match.group(group)


def _extract_nth_group(pattern: str, text: str, index: int, default: Any = "", flags: int = 0):
    matches = re.findall(pattern, text, flags)
    if len(matches) <= index:
        return default
    return matches[index]


def _parse_option_string(option_string: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in [part.strip() for part in option_string.split(",") if part.strip()]:
        if "=" in item:
            key, value = item.split("=", 1)
            result[key.strip()] = value.strip()
        else:
            result["paper_size"] = item
    return result


def _extract_fancy_value(text: str, position_type: str, slot: str, default: str = "") -> str:
    return _extract_first_group(
        rf"\\fancy{position_type}\[{slot}\]\{{([^}}]*)\}}",
        text,
        default,
    )


def _find_line_after(lines: list[str], anchor: str) -> str:
    for index, line in enumerate(lines):
        if line.strip() == anchor and index + 1 < len(lines):
            return lines[index + 1].strip()
    return ""


def _find_line_containing(lines: list[str], keyword: str) -> str:
    for line in lines:
        if keyword in line:
            return line.strip()
    return ""


def _strip_outer_braces(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped[1:-1]
    return stripped


def _parse_titlespacing_values(line: str) -> tuple[str, str]:
    match = re.search(r"\{0pt\}\{([^}]+)\}\{([^}]+)\}", line)
    if not match:
        return "0pt", "0pt"
    return match.group(1), match.group(2)


def _extract_inner_title_block(line: str, tail_marker: str) -> str:
    stripped = line.strip()
    if stripped.startswith("{") and stripped.endswith("}%"):
        stripped = stripped[1:-2]
    return stripped.split(tail_marker, 1)[0]


def _parse_alignment_and_font(fragment: str) -> tuple[str, dict[str, str]]:
    alignment = "center"
    if fragment.startswith("\\raggedright"):
        alignment = "left"
        fragment = fragment[len("\\raggedright"):]
    elif fragment.startswith("\\raggedleft"):
        alignment = "right"
        fragment = fragment[len("\\raggedleft"):]
    elif fragment.startswith("\\centering"):
        alignment = "center"
        fragment = fragment[len("\\centering"):]
    return alignment, _parse_font_fragment(fragment)


def _parse_font_fragment(fragment: str) -> dict[str, str]:
    family = "sans-serif" if "\\sffamily" in fragment else "serif"
    size = _extract_first_group(r"\\fontsize\{([^}]+)\}\{\\baselineskip\}\\selectfont", fragment, "")
    if not size:
        size = _extract_first_group(r"(\\[A-Za-z]+)", fragment, "\\small")
        if size in {"\\sffamily", "\\rmfamily", "\\bfseries", "\\itshape"}:
            size = "\\small"
    return {
        "family": family,
        "size": size,
        "weight": "bold" if "\\bfseries" in fragment else "normal",
        "style": "italic" if "\\itshape" in fragment else "normal",
    }


def _parse_label_separator(value: str) -> str:
    return {
        "colon": ":",
        "period": ".",
        "endash": " - ",
        "quad": "  ",
    }.get(value, ":")
