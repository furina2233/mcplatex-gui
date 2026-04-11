from schemas.cls_schema import CLSGeneratorOutput


def sanitize_custom_commands(custom_commands: str) -> str:
    normalized = custom_commands.strip()
    if not normalized:
        return ""

    full_cls_markers = ("\\NeedsTeXFormat", "\\ProvidesClass", "\\LoadClass")
    if any(marker in normalized for marker in full_cls_markers):
        return ""

    return normalized


def build_cls_code(config: CLSGeneratorOutput) -> str:
    lines: list[str] = []

    lines.append("\\NeedsTeXFormat{LaTeX2e}")
    lines.append(f"\\ProvidesClass{{{config.class_name}}}[2024/01/01 Custom Template Class]")
    lines.append("")

    class_options = [config.fonts.base_font_size]
    if config.is_twocolumn:
        class_options.append("twocolumn")
    lines.append(f"\\LoadClass[{','.join(class_options)}]{{{config.base_class}}}")
    lines.append("")

    geo = config.geometry
    geo_options = [
        geo.paper_size,
        f"top={geo.top_margin}",
        f"bottom={geo.bottom_margin}",
        f"left={geo.left_margin}",
        f"right={geo.right_margin}",
        f"headheight={geo.head_height}",
        f"headsep={geo.head_sep}",
        f"footskip={geo.foot_skip}",
    ]
    if geo.column_sep and config.is_twocolumn:
        geo_options.append(f"columnsep={geo.column_sep}")

    lines.append("% Packages")
    lines.append(f"\\RequirePackage[{', '.join(geo_options)}]{{geometry}}")
    lines.append("\\RequirePackage{fontspec}")
    lines.append("\\RequirePackage{xeCJK}")
    lines.append("\\RequirePackage{unicode-math}")
    if config.fonts.main_font_family == "serif":
        lines.append("\\setmainfont{Times New Roman}")
    else:
        lines.append("\\setmainfont{Arial}")
    lines.append("\\setsansfont{Arial}")
    lines.append("\\setmonofont{Consolas}")
    lines.append("\\setCJKmainfont{SimSun}")
    lines.append("\\setCJKsansfont{Microsoft YaHei}")
    lines.append("\\setCJKmonofont{SimSun}")
    lines.append("\\setmathfont{Cambria Math}")
    if config.fonts.use_microtype:
        lines.append("\\RequirePackage{microtype}")
    lines.append("\\RequirePackage{fancyhdr}")
    lines.append("\\RequirePackage{titlesec}")
    lines.append("\\RequirePackage{caption}")
    lines.append("\\RequirePackage{xcolor}")
    lines.append("\\RequirePackage{graphicx}")

    core_packages = {
        "geometry",
        "fontspec",
        "xeCJK",
        "unicode-math",
        "microtype",
        "fancyhdr",
        "titlesec",
        "caption",
        "xcolor",
        "graphicx",
    }
    for pkg in config.additional_packages:
        if pkg not in core_packages:
            lines.append(f"\\RequirePackage{{{pkg}}}")
    lines.append("")

    para = config.paragraph
    lines.append("% Paragraph")
    lines.append(f"\\linespread{{{para.line_spread}}}")
    lines.append(f"\\setlength{{\\parindent}}{{{para.paragraph_indent}}}")
    lines.append(f"\\setlength{{\\parskip}}{{{para.paragraph_skip}}}")
    if para.text_justification == "ragged-right":
        lines.append("\\raggedright")
    lines.append("")

    hf = config.header_footer
    lines.append("% Header / footer")
    lines.append("\\pagestyle{fancy}")
    lines.append("\\fancyhf{}")
    
    # 多行期刊名处理（新增）
    if hf.journal_header_lines:
        # 如果有新的多行配置，优先使用
        for i, line_config in enumerate(hf.journal_header_lines):
            font_cmd = _build_font_command(
                line_config.font_size,
                line_config.font_weight,
                "normal",
                line_config.font_family,
            )
            # 首页页眉
            lines.append(f"\\fancyhead[C]{{{font_cmd}{line_config.text}}}")
            if line_config.space_after and line_config.space_after != "0pt":
                lines.append(f"\\fancyhead[C]{{\\vspace{{{line_config.space_after}}}}}")
    else:
        # 兼容旧的单行配置
        if hf.first_page_header_left:
            lines.append(f"\\fancyhead[L]{{{hf.first_page_header_left}}}")
        if hf.first_page_header_center:
            lines.append(f"\\fancyhead[C]{{{hf.first_page_header_center}}}")
        if hf.first_page_header_right:
            lines.append(f"\\fancyhead[R]{{{hf.first_page_header_right}}}")
    
    if hf.running_header_left:
        lines.append(f"\\fancyhead[L]{{{hf.running_header_left}}}")
    if hf.running_header_center:
        lines.append(f"\\fancyhead[C]{{{hf.running_header_center}}}")
    if hf.running_header_right:
        lines.append(f"\\fancyhead[R]{{{hf.running_header_right}}}")
    if hf.first_page_footer_center:
        lines.append(f"\\fancyfoot[C]{{{hf.first_page_footer_center}}}")
    if hf.running_footer_center:
        lines.append(f"\\fancyfoot[C]{{{hf.running_footer_center}}}")
    
    # 页眉分隔线
    lines.append(f"\\renewcommand{{\\headrulewidth}}{{{hf.header_rule_width if hf.first_page_has_rule else '0pt'}}}")
    if hf.header_rule_skip != "0pt":
        lines.append(f"\\setlength{{\\headsep}}{{{hf.header_rule_skip}}}")
    
    # 页尾分隔线
    lines.append(f"\\renewcommand{{\\footrulewidth}}{{{hf.footer_rule_width}}}")
    if hf.footer_rule_skip != "0pt":
        lines.append(f"\\setlength{{\\footskip}}{{{hf.footer_rule_skip}}}")
    
    lines.append("\\fancypagestyle{firstpage}{%")
    lines.append("  \\fancyhf{}")
    
    # 首页多行期刊名（新增）
    if hf.journal_header_lines:
        for i, line_config in enumerate(hf.journal_header_lines):
            font_cmd = _build_font_command(
                line_config.font_size,
                line_config.font_weight,
                "normal",
                line_config.font_family,
            )
            lines.append(f"  \\fancyhead[C]{{{font_cmd}{line_config.text}}}")
            if line_config.space_after and line_config.space_after != "0pt":
                lines.append(f"  \\fancyhead[C]{{\\vspace{{{line_config.space_after}}}}}")
    else:
        # 兼容旧的单行配置
        if hf.first_page_header_left:
            lines.append(f"  \\fancyhead[L]{{{hf.first_page_header_left}}}")
        if hf.first_page_header_center:
            lines.append(f"  \\fancyhead[C]{{{hf.first_page_header_center}}}")
        if hf.first_page_header_right:
            lines.append(f"  \\fancyhead[R]{{{hf.first_page_header_right}}}")
    
    # 首页脚注（新增）
    fn = config.footnote
    if fn.first_page_footnote:
        align_cmd = _get_alignment_cmd(fn.first_page_footnote_alignment)
        lines.append(f"  \\fancyfoot[L]{{{align_cmd}{fn.first_page_footnote_font_size}{fn.first_page_footnote}}}")
    
    # 首页分隔线
    first_page_rule = hf.header_rule_width if hf.first_page_has_rule else "0pt"
    lines.append(f"  \\renewcommand{{\\headrulewidth}}{{{first_page_rule}}}")
    lines.append("}")
    lines.append("")
    
    # 脚注配置（新增）
    lines.append("% Footnotes")
    if fn.use_symbol_marks:
        lines.append("\\renewcommand{\\thefootnote}{\\fnsymbol{footnote}}")
    else:
        lines.append(f"\\renewcommand{{\\thefootnote}}{{{fn.footnote_numbering_format}}}")
    lines.append(f"\\renewcommand{{\\footnoterule}}{{\\vspace{{{fn.footnote_rule_skip}}}\\hrule width \\columnwidth height {fn.footnote_rule_width}\\vspace{{2pt}}}}")
    if fn.footnote_indent != "0pt":
        lines.append(f"\\setlength{{\\footnotemargin}}{{{fn.footnote_indent}}}")
    lines.append("")
    lines.append("")

    sec = config.sections
    section_font = _build_font_command(
        sec.section_font_size,
        sec.section_font_weight,
        "normal",
        sec.section_font_family,
    )
    subsection_font = _build_font_command(
        sec.subsection_font_size,
        sec.subsection_font_weight,
        sec.subsection_font_style,
        sec.section_font_family,
    )
    section_align = _get_alignment_cmd(sec.section_alignment)
    lines.append("% Section styles")
    lines.append("\\titleformat{\\section}")
    lines.append(f"  {{{section_align}{section_font}}}")
    lines.append("  {\\thesection.}")
    lines.append("  {0.5em}")
    lines.append("  {}")
    lines.append("\\titlespacing*{\\section}")
    lines.append(f"  {{0pt}}{{{sec.section_space_before}}}{{{sec.section_space_after}}}")
    lines.append("\\titleformat{\\subsection}")
    lines.append(f"  {{{subsection_font}}}")
    lines.append("  {\\thesubsection.}")
    lines.append("  {0.5em}")
    lines.append("  {}")
    lines.append("\\titlespacing*{\\subsection}")
    lines.append(f"  {{0pt}}{{{sec.subsection_space_before}}}{{{sec.subsection_space_after}}}")
    lines.append("")

    cap = config.caption
    label_format = "bf" if cap.label_font_weight == "bold" else "normal"
    lines.append("% Captions")
    lines.append("\\captionsetup{")
    lines.append(f"  font={{{cap.font_size.replace(chr(92), '')}}},")
    lines.append(f"  labelfont={{{label_format}}},")
    lines.append(f"  labelsep={{{_get_labelsep_name(cap.label_separator)}}},")
    lines.append(f"  skip={para.caption_skip},")
    lines.append("}")
    lines.append("")

    title = config.title
    author = config.author
    abstract_cfg = config.abstract
    title_font = _build_font_command(title.font_size, title.font_weight, "normal", title.font_family)
    author_font = _build_font_command(author.name_font_size, author.name_font_weight, "normal", "serif")
    lines.append("% Title")
    lines.append("\\renewcommand{\\maketitle}{%")
    lines.append("  \\thispagestyle{firstpage}%")
    lines.append(f"  \\vspace*{{{title.space_before}}}%")
    lines.append(f"  {{{_get_alignment_cmd(title.alignment)}{title_font}\\@title\\par}}%")
    lines.append(f"  \\vspace{{{title.space_after}}}%")
    lines.append(f"  {{{_get_alignment_cmd(author.alignment)}{author_font}\\@author\\par}}%")
    lines.append(f"  \\vspace{{{author.space_after}}}%")
    lines.append("}")
    lines.append("")

    abstract_font = _build_font_command(abstract_cfg.font_size, "normal", abstract_cfg.font_style, "serif")
    heading_font = "\\bfseries " if abstract_cfg.heading_font_weight == "bold" else ""
    lines.append("% Abstract")
    lines.append("\\renewenvironment{abstract}{%")
    lines.append(f"  \\vspace{{{abstract_cfg.space_before}}}%")
    lines.append("  \\begin{list}{}{%" )
    lines.append(f"    \\setlength{{\\leftmargin}}{{{abstract_cfg.left_indent}}}%")
    lines.append(f"    \\setlength{{\\rightmargin}}{{{abstract_cfg.right_indent}}}%")
    lines.append("  }%")
    lines.append(f"  \\item[]{{\\noindent{heading_font}{abstract_cfg.heading_text}}}\\par\\noindent{abstract_font}")
    lines.append("}{%")
    lines.append("  \\end{list}%")
    lines.append(f"  \\vspace{{{abstract_cfg.space_after}}}%")
    lines.append("}")
    lines.append("")

    custom_commands = sanitize_custom_commands(config.custom_commands)
    if custom_commands:
        lines.append("% Custom commands")
        lines.append(custom_commands)
        lines.append("")

    lines.append("\\endinput")
    return "\n".join(lines)


def _build_font_command(size: str, weight: str, style: str, family: str) -> str:
    parts: list[str] = []
    if family == "sans-serif":
        parts.append("\\sffamily")
    else:
        parts.append("\\rmfamily")

    if size.startswith("\\"):
        parts.append(size)
    else:
        parts.append(f"\\fontsize{{{size}}}{{\\baselineskip}}\\selectfont")

    if weight == "bold":
        parts.append("\\bfseries")
    if style == "italic":
        parts.append("\\itshape")
    return "".join(parts)


def _get_alignment_cmd(alignment: str) -> str:
    return {
        "left": "\\raggedright",
        "center": "\\centering",
        "right": "\\raggedleft",
    }.get(alignment, "\\centering")


def _get_labelsep_name(separator: str) -> str:
    return {
        ":": "colon",
        ".": "period",
        " - ": "endash",
        "  ": "quad",
    }.get(separator, "colon")
