# utils/cls_builder.py
"""
将结构化的 CLSGeneratorOutput 转换为实际的 .cls 文件代码
"""
from schemas.cls_schema import CLSGeneratorOutput


def build_cls_code(config: CLSGeneratorOutput) -> str:
    """
    根据结构化配置生成完整的 .cls 文件代码

    Args:
        config: CLSGeneratorOutput 结构化配置

    Returns:
        str: 完整的 .cls 文件内容
    """

    lines = []

    # ==========================================================================
    # 1. 文件头
    # ==========================================================================
    lines.append(f"\\NeedsTeXFormat{{LaTeX2e}}")
    lines.append(
        f"\\ProvidesClass{{{config.class_name}}}[2024/01/01 Custom Template Class]"
    )
    lines.append("")

    # ==========================================================================
    # 2. 加载基础类
    # ==========================================================================
    class_options = [config.fonts.base_font_size]
    if config.is_twocolumn:
        class_options.append("twocolumn")

    lines.append(f"\\LoadClass[{','.join(class_options)}]{{{config.base_class}}}")
    lines.append("")

    # ==========================================================================
    # 3. 加载宏包
    # ==========================================================================
    lines.append("% ============ 宏包加载 ============")

    # 几何设置
    geo = config.geometry
    geo_options = [
        geo.paper_size,
        f"top={geo.top_margin}",
        f"bottom={geo.bottom_margin}",
        f"left={geo.left_margin}",
        f"right={geo.right_margin}",
    ]
    if geo.column_sep and config.is_twocolumn:
        geo_options.append(f"columnsep={geo.column_sep}")

    lines.append(f"\\RequirePackage[{', '.join(geo_options)}]{{geometry}}")

    # 字体包
    if config.fonts.main_font_family == "serif":
        lines.append("\\RequirePackage{newtxtext}  % Times-like serif font")
    else:
        lines.append("\\RequirePackage{helvet}  % Helvetica sans-serif")
        lines.append("\\renewcommand{\\familydefault}{\\sfdefault}")

    lines.append(f"\\RequirePackage{{{config.fonts.math_font_package}}}  % Math font")

    if config.fonts.use_microtype:
        lines.append("\\RequirePackage{microtype}  % Microtypography")

    # 其他核心宏包
    lines.append("\\RequirePackage{fancyhdr}  % Header/footer")
    lines.append("\\RequirePackage{titlesec}  % Section formatting")
    lines.append("\\RequirePackage{caption}   % Caption formatting")
    lines.append("\\RequirePackage{xcolor}    % Colors")
    lines.append("\\RequirePackage{graphicx}  % Graphics")

    # 额外宏包
    for pkg in config.additional_packages:
        if pkg not in [
            "geometry",
            "fancyhdr",
            "titlesec",
            "caption",
            "xcolor",
            "graphicx",
        ]:
            lines.append(f"\\RequirePackage{{{pkg}}}")

    lines.append("")

    # ==========================================================================
    # 4. 段落设置
    # ==========================================================================
    lines.append("% ============ 段落设置 ============")
    para = config.paragraph
    lines.append(f"\\linespread{{{para.line_spread}}}")
    lines.append(f"\\setlength{{\\parindent}}{{{para.paragraph_indent}}}")
    lines.append(f"\\setlength{{\\parskip}}{{{para.paragraph_skip}}}")

    if para.text_justification == "ragged-right":
        lines.append("\\raggedright")

    lines.append("")

    # ==========================================================================
    # 5. 页眉页脚设置
    # ==========================================================================
    lines.append("% ============ 页眉页脚 ============")
    lines.append("\\pagestyle{fancy}")
    lines.append("\\fancyhf{}  % Clear all")

    hf = config.header_footer

    # 后续页面设置
    if hf.running_header_left:
        lines.append(f"\\fancyhead[L]{{{hf.running_header_left}}}")
    if hf.running_header_center:
        lines.append(f"\\fancyhead[C]{{{hf.running_header_center}}}")
    if hf.running_header_right:
        lines.append(f"\\fancyhead[R]{{{hf.running_header_right}}}")
    if hf.running_footer_center:
        lines.append(f"\\fancyfoot[C]{{{hf.running_footer_center}}}")

    lines.append(f"\\renewcommand{{\\headrulewidth}}{{{hf.header_rule_width}}}")
    lines.append(f"\\renewcommand{{\\footrulewidth}}{{{hf.footer_rule_width}}}")

    # 首页特殊样式
    lines.append("")
    lines.append("% 首页样式")
    lines.append("\\fancypagestyle{firstpage}{%")
    lines.append("  \\fancyhf{}")
    if hf.first_page_header_left:
        lines.append(f"  \\fancyhead[L]{{{hf.first_page_header_left}}}")
    if hf.first_page_header_center:
        lines.append(f"  \\fancyhead[C]{{{hf.first_page_header_center}}}")
    if hf.first_page_header_right:
        lines.append(f"  \\fancyhead[R]{{{hf.first_page_header_right}}}")
    if hf.first_page_footer_center:
        lines.append(f"  \\fancyfoot[C]{{{hf.first_page_footer_center}}}")

    rule_width = hf.header_rule_width if hf.first_page_has_rule else "0pt"
    lines.append(f"  \\renewcommand{{\\headrulewidth}}{{{rule_width}}}")
    lines.append("}")
    lines.append("")

    # ==========================================================================
    # 6. 标题样式 (titlesec)
    # ==========================================================================
    lines.append("% ============ 章节标题样式 ============")
    sec = config.sections

    # Section 格式
    sec_font_cmd = _build_font_command(
        sec.section_font_size,
        sec.section_font_weight,
        "normal",
        sec.section_font_family,
    )
    sec_align = "\\filcenter" if sec.section_alignment == "center" else ""

    lines.append(f"\\titleformat{{\\section}}")
    lines.append(f"  {{{sec_font_cmd}{sec_align}}}  % format")
    lines.append(f"  {{\\thesection.}}  % label")
    lines.append(f"  {{0.5em}}  % sep")
    lines.append(f"  {{}}  % before-code")
    lines.append(f"\\titlespacing*{{\\section}}")
    lines.append(
        f"  {{0pt}}{{{sec.section_space_before}}}{{{sec.section_space_after}}}"
    )
    lines.append("")

    # Subsection 格式
    subsec_font_cmd = _build_font_command(
        sec.subsection_font_size,
        sec.subsection_font_weight,
        sec.subsection_font_style,
        sec.section_font_family,
    )

    lines.append(f"\\titleformat{{\\subsection}}")
    lines.append(f"  {{{subsec_font_cmd}}}  % format")
    lines.append(f"  {{\\thesubsection.}}  % label")
    lines.append(f"  {{0.5em}}  % sep")
    lines.append(f"  {{}}  % before-code")
    lines.append(f"\\titlespacing*{{\\subsection}}")
    lines.append(
        f"  {{0pt}}{{{sec.subsection_space_before}}}{{{sec.subsection_space_after}}}"
    )
    lines.append("")

    # ==========================================================================
    # 7. 图表标题样式 (caption)
    # ==========================================================================
    lines.append("% ============ 图表标题样式 ============")
    cap = config.caption

    label_format = "bf" if cap.label_font_weight == "bold" else "default"
    lines.append(f"\\captionsetup{{")
    lines.append(f"  font={{{cap.font_size.replace(chr(92), '')}}},")
    lines.append(f"  labelfont={{{label_format}}},")
    lines.append(f"  labelsep={{{_get_labelsep_name(cap.label_separator)}}},")
    lines.append(f"}}")
    lines.append("")

    # ==========================================================================
    # 8. 重定义 \maketitle
    # ==========================================================================
    lines.append("% ============ 标题页样式 ============")
    title = config.title
    author = config.author
    abstract_cfg = config.abstract

    title_font = _build_font_command(
        title.font_size,
        title.font_weight,
        "normal",
        title.font_family,
    )
    title_align = _get_alignment_cmd(title.alignment)

    author_name_font = _build_font_command(
        author.name_font_size,
        author.name_font_weight,
        "normal",
        "serif",
    )

    lines.append("\\renewcommand{\\maketitle}{%")
    lines.append("  \\thispagestyle{firstpage}%")
    lines.append(f"  \\vspace*{{{title.space_before}}}%")
    lines.append(f"  {{{title_align}{title_font}\\@title\\par}}%")
    lines.append(f"  \\vspace{{{title.space_after}}}%")
    lines.append(
        f"  {{{_get_alignment_cmd(author.alignment)}{author_name_font}\\@author\\par}}%"
    )
    lines.append(f"  \\vspace{{{author.space_after}}}%")
    lines.append("}")
    lines.append("")

    # ==========================================================================
    # 9. 重定义 abstract 环境
    # ==========================================================================
    lines.append("% ============ 摘要环境 ============")
    abs_font = _build_font_command(
        abstract_cfg.font_size,
        "normal",
        abstract_cfg.font_style,
        "serif",
    )
    heading_font = "\\bfseries " if abstract_cfg.heading_font_weight == "bold" else ""

    lines.append("\\renewenvironment{abstract}{%")
    lines.append(f"  \\vspace{{{abstract_cfg.space_before}}}%")
    lines.append(f"  \\begin{{list}}{{}}{{%")
    lines.append(f"    \\setlength{{\\leftmargin}}{{{abstract_cfg.left_indent}}}%")
    lines.append(f"    \\setlength{{\\rightmargin}}{{{abstract_cfg.right_indent}}}%")
    lines.append(f"  }}%")
    lines.append(
        f"  \\item[]{{\\noindent{heading_font}{abstract_cfg.heading_text}}}\\par\\noindent{abs_font}"
    )
    lines.append("}{%")
    lines.append("  \\end{list}%")
    lines.append(f"  \\vspace{{{abstract_cfg.space_after}}}%")
    lines.append("}")
    lines.append("")

    # ==========================================================================
    # 10. 自定义命令
    # ==========================================================================
    if config.custom_commands.strip():
        lines.append("% ============ 自定义命令 ============")
        lines.append(config.custom_commands)
        lines.append("")

    # ==========================================================================
    # 11. 结束
    # ==========================================================================
    lines.append("\\endinput")

    return "\n".join(lines)


def _build_font_command(size: str, weight: str, style: str, family: str) -> str:
    """构建字体命令组合"""
    cmds = []

    # 字体族
    if family == "sans-serif":
        cmds.append("\\sffamily")
    elif family == "serif":
        cmds.append("\\rmfamily")

    # 字号
    if size.startswith("\\"):
        cmds.append(size)
    else:
        # 将 pt 值转换为 LaTeX 命令（近似）
        cmds.append(f"\\fontsize{{{size}}}{{\\baselineskip}}\\selectfont")

    # 字重
    if weight == "bold":
        cmds.append("\\bfseries")

    # 字体样式
    if style == "italic":
        cmds.append("\\itshape")

    return "".join(cmds)


def _get_alignment_cmd(alignment: str) -> str:
    """获取对齐命令"""
    mapping = {
        "left": "\\raggedright",
        "center": "\\centering",
        "right": "\\raggedleft",
    }
    return mapping.get(alignment, "\\centering")


def _get_labelsep_name(sep: str) -> str:
    """获取 caption labelsep 名称"""
    mapping = {
        ":": "colon",
        ".": "period",
        " - ": "endash",
        "  ": "quad",
    }
    return mapping.get(sep, "colon")
