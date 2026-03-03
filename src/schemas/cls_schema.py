# schemas/cls_schema.py
from pydantic import Field
from typing import Literal
from atomic_agents import BaseIOSchema


# =============================================================================
# 1. 页面几何设置
# =============================================================================
class GeometrySettings(BaseIOSchema):
    """
    页面几何参数，对应 geometry 宏包的设置。
    所有尺寸单位统一使用 mm 或 cm。
    """

    paper_size: Literal["a4paper", "letterpaper", "a5paper"] = Field(
        default="a4paper",
        description=(
            "纸张尺寸。常见学术期刊使用 'a4paper'(210mm×297mm) 或 'letterpaper'(8.5in×11in)。"
            "IEEE/ACM 美国期刊通常用 letterpaper，欧洲期刊通常用 a4paper。"
        ),
    )
    top_margin: str = Field(
        ...,
        description=(
            "页面顶部边距，包含单位。例如 '25mm', '1in', '2.5cm'。"
            "学术论文通常在 20mm-30mm 之间。首页可能因页眉内容不同而需要特殊处理。"
        ),
    )
    bottom_margin: str = Field(
        ...,
        description=(
            "页面底部边距，包含单位。例如 '25mm', '1in', '2.5cm'。"
            "需要为页脚/页码预留足够空间，通常与顶部边距相近或略大。"
        ),
    )
    left_margin: str = Field(
        ...,
        description=(
            "页面左侧边距，包含单位。例如 '20mm', '0.75in'。"
            "双栏布局时左右边距通常较小(15-20mm)，单栏布局时较大(25-30mm)。"
        ),
    )
    right_margin: str = Field(
        ...,
        description=(
            "页面右侧边距，包含单位。例如 '20mm', '0.75in'。"
            "通常与左边距对称，但某些装订格式可能不对称。"
        ),
    )
    column_sep: str | None = Field(
        default=None,
        description=(
            "双栏布局时的栏间距，包含单位。例如 '5mm', '0.25in'。"
            "仅在 twocolumn 模式下有效。IEEE 格式通常为 4-6mm。"
            "单栏布局时设为 None。"
        ),
    )


# =============================================================================
# 2. 字体设置
# =============================================================================
class FontSettings(BaseIOSchema):
    """
    全局字体配置。
    注意：具体元素（标题、正文等）的字体在各自的 Settings 中单独定义。
    """

    base_font_size: Literal["9pt", "10pt", "11pt", "12pt"] = Field(
        default="10pt",
        description=(
            "文档基础字号，作为其他字号的参考基准。"
            "学术论文常用 10pt 或 11pt。期刊论文多用 9pt 或 10pt 以节省版面。"
            "这个值会传递给 \\LoadClass 命令。"
        ),
    )
    main_font_family: Literal["serif", "sans-serif"] = Field(
        default="serif",
        description=(
            "正文主字体族。'serif' 表示衬线字体(如 Times)，'sans-serif' 表示无衬线字体(如 Helvetica)。"
            "绝大多数学术期刊正文使用 serif，技术文档/报告可能使用 sans-serif。"
        ),
    )
    math_font_package: str = Field(
        default="newtxmath",
        description=(
            "数学字体宏包名称。常用选项："
            "'newtxmath' - 与 Times 正文搭配；"
            "'mathptmx' - 经典 Times 数学字体；"
            "'fourier' - Utopia 风格；"
            "'lmodern' - Latin Modern，与 Computer Modern 兼容。"
        ),
    )
    use_microtype: bool = Field(
        default=True,
        description=(
            "是否启用 microtype 宏包进行微排版优化。"
            "microtype 可改善字间距和断行效果，推荐在最终输出时启用。"
            "某些字体可能不完全支持。"
        ),
    )


# =============================================================================
# 3. 标题样式设置
# =============================================================================
class TitleSettings(BaseIOSchema):
    """
    文档标题（\\title 命令）的样式配置。
    """

    font_size: str = Field(
        ...,
        description=(
            "标题字号。可以是绝对值如 '18pt', '24pt'，"
            "或相对命令如 '\\LARGE', '\\huge'。"
            "期刊论文标题通常在 14pt-24pt 之间，会议论文可能更大。"
        ),
    )
    font_weight: Literal["normal", "bold"] = Field(
        default="bold",
        description="标题字重。几乎所有学术论文标题都使用 'bold'。",
    )
    font_family: Literal["serif", "sans-serif"] = Field(
        default="sans-serif",
        description=(
            "标题字体族。许多现代期刊标题使用 'sans-serif' 以区别于正文，"
            "传统期刊可能使用 'serif'。IEEE 格式标题为 sans-serif。"
        ),
    )
    alignment: Literal["left", "center", "right"] = Field(
        default="center",
        description="标题对齐方式。绝大多数期刊使用 'center'，少数使用 'left'。",
    )
    space_before: str = Field(
        default="0pt",
        description=(
            "标题上方的垂直间距。例如 '12pt', '1em', '\\baselineskip'。"
            "首页标题上方通常有较大留白或由页眉决定。"
        ),
    )
    space_after: str = Field(
        ...,
        description=(
            "标题下方到作者信息的垂直间距。例如 '12pt', '1.5em'。"
            "这个间距影响标题与作者块的视觉分离度。"
        ),
    )


# =============================================================================
# 4. 作者信息样式设置
# =============================================================================
class AuthorSettings(BaseIOSchema):
    """
    作者姓名和单位信息的样式配置。
    """

    name_font_size: str = Field(
        ...,
        description=(
            "作者姓名字号。例如 '12pt', '\\large'。" "通常比正文大一号，比标题小。"
        ),
    )
    name_font_weight: Literal["normal", "bold"] = Field(
        default="normal",
        description="作者姓名字重。多数期刊使用 'normal'，部分使用 'bold'。",
    )
    affiliation_font_size: str = Field(
        ...,
        description=(
            "作者单位/机构字号。例如 '10pt', '\\small'。" "通常与正文相同或略小。"
        ),
    )
    affiliation_font_style: Literal["normal", "italic"] = Field(
        default="italic",
        description="作者单位字体样式。'italic' 较常见，用于与姓名区分。",
    )
    alignment: Literal["left", "center", "right"] = Field(
        default="center",
        description="作者信息块对齐方式。通常与标题保持一致。",
    )
    space_after: str = Field(
        ...,
        description=(
            "作者信息块下方到摘要的垂直间距。例如 '18pt', '2em'。"
            "这个间距分隔元信息区和正文内容区。"
        ),
    )


# =============================================================================
# 5. 摘要样式设置
# =============================================================================
class AbstractSettings(BaseIOSchema):
    """
    摘要（Abstract）部分的样式配置。
    """

    font_size: str = Field(
        ...,
        description=(
            "摘要正文字号。例如 '9pt', '\\small'。" "通常比正文小一号，以视觉区分。"
        ),
    )
    font_style: Literal["normal", "italic"] = Field(
        default="normal",
        description="摘要正文字体样式。部分期刊使用 'italic'。",
    )
    left_indent: str = Field(
        ...,
        description=(
            "摘要左侧缩进量。例如 '10mm', '0.5in', '2em'。"
            "双栏格式通常无缩进或很小，单栏格式缩进较大。"
        ),
    )
    right_indent: str = Field(
        ...,
        description=(
            "摘要右侧缩进量。例如 '10mm', '0.5in', '2em'。" "通常与左侧缩进对称。"
        ),
    )
    heading_text: str = Field(
        default="Abstract",
        description=(
            "摘要标题文字。英文通常为 'Abstract' 或 'ABSTRACT'，"
            "中文为 '摘要'。部分格式使用 'Summary'。"
        ),
    )
    heading_font_weight: Literal["normal", "bold"] = Field(
        default="bold",
        description="摘要标题字重。绝大多数使用 'bold'。",
    )
    space_before: str = Field(
        default="12pt",
        description="摘要区域上方间距。",
    )
    space_after: str = Field(
        ...,
        description=("摘要区域下方到正文/关键词的间距。例如 '12pt', '1em'。"),
    )


# =============================================================================
# 6. 章节标题样式设置
# =============================================================================
class SectionSettings(BaseIOSchema):
    """
    章节标题（\\section, \\subsection 等）的样式配置。
    使用 titlesec 宏包实现。
    """

    # Section (一级标题)
    section_font_size: str = Field(
        ...,
        description=(
            "一级标题(\\section)字号。例如 '12pt', '\\large'。" "通常比正文大 1-2 号。"
        ),
    )
    section_font_weight: Literal["normal", "bold"] = Field(
        default="bold",
        description="一级标题字重。几乎总是 'bold'。",
    )
    section_font_family: Literal["serif", "sans-serif"] = Field(
        default="sans-serif",
        description="一级标题字体族。现代期刊多用 'sans-serif'。",
    )
    section_alignment: Literal["left", "center", "right"] = Field(
        default="left",
        description="一级标题对齐方式。绝大多数使用 'left'。",
    )
    section_numbering_format: str = Field(
        default="arabic",
        description=(
            "一级标题编号格式。"
            "'arabic' - 阿拉伯数字 (1, 2, 3)；"
            "'Roman' - 大写罗马数字 (I, II, III)；"
            "'none' - 无编号。"
            "IEEE 使用大写罗马数字，多数期刊使用阿拉伯数字。"
        ),
    )
    section_space_before: str = Field(
        ...,
        description=(
            "一级标题上方间距。例如 '12pt', '1.5em', '\\baselineskip'。"
            "这个间距创造章节之间的视觉分隔。"
        ),
    )
    section_space_after: str = Field(
        ...,
        description=(
            "一级标题下方到正文的间距。例如 '6pt', '0.5em'。" "通常小于上方间距。"
        ),
    )

    # Subsection (二级标题)
    subsection_font_size: str = Field(
        ...,
        description=(
            "二级标题(\\subsection)字号。例如 '11pt', '\\normalsize'。"
            "通常介于一级标题和正文之间。"
        ),
    )
    subsection_font_weight: Literal["normal", "bold"] = Field(
        default="bold",
        description="二级标题字重。",
    )
    subsection_font_style: Literal["normal", "italic"] = Field(
        default="normal",
        description="二级标题字体样式。部分格式使用 'italic' 以区别于一级标题。",
    )
    subsection_space_before: str = Field(
        ...,
        description="二级标题上方间距。通常小于一级标题的上方间距。",
    )
    subsection_space_after: str = Field(
        ...,
        description="二级标题下方间距。",
    )


# =============================================================================
# 7. 页眉页脚设置
# =============================================================================
class HeaderFooterSettings(BaseIOSchema):
    """
    页眉页脚配置，使用 fancyhdr 宏包实现。
    区分首页和后续页面的不同样式。
    """

    # 首页设置
    first_page_header_left: str = Field(
        default="",
        description=(
            "首页页眉左侧内容。可以是文字如会议名称、期刊名，或留空。"
            "例如 'IEEE Conference 2024', ''。"
        ),
    )
    first_page_header_center: str = Field(
        default="",
        description="首页页眉中间内容。通常留空或放置标题缩写。",
    )
    first_page_header_right: str = Field(
        default="",
        description="首页页眉右侧内容。可能包含页码或留空。",
    )
    first_page_footer_center: str = Field(
        default="",
        description=(
            "首页页脚中间内容。常见内容：页码、版权声明、DOI。"
            "例如 '\\thepage', '© 2024 IEEE'。"
        ),
    )
    first_page_has_rule: bool = Field(
        default=False,
        description=("首页页眉下方是否有横线。" "许多期刊首页无横线或使用特殊样式。"),
    )

    # 后续页面设置
    running_header_left: str = Field(
        default="",
        description=(
            "后续页面页眉左侧内容。"
            "常见内容：作者姓名缩写、文章短标题。"
            "可使用 '\\leftmark' 获取章节名。"
        ),
    )
    running_header_center: str = Field(
        default="",
        description="后续页面页眉中间内容。",
    )
    running_header_right: str = Field(
        default="\\thepage",
        description=(
            "后续页面页眉右侧内容。" "常见内容：页码 '\\thepage'、期刊名缩写。"
        ),
    )
    running_footer_center: str = Field(
        default="",
        description="后续页面页脚中间内容。如果页码在页眉则留空。",
    )
    header_rule_width: str = Field(
        default="0.4pt",
        description=(
            "页眉下方横线粗细。例如 '0.4pt', '0.5pt', '0pt'(无线)。"
            "设为 '0pt' 表示无横线。"
        ),
    )
    footer_rule_width: str = Field(
        default="0pt",
        description="页脚上方横线粗细。大多数格式无此线，设为 '0pt'。",
    )


# =============================================================================
# 8. 段落设置
# =============================================================================
class ParagraphSettings(BaseIOSchema):
    """
    正文段落的排版参数。
    """

    line_spread: str = Field(
        ...,
        description=(
            "行距倍数，传递给 \\linespread 命令。"
            "'1.0' - 单倍行距；"
            "'1.25' - 1.25倍行距；"
            "'1.5' - 1.5倍行距。"
            "学术论文通常使用 1.0-1.15，投稿稿件可能要求 1.5 或 2.0。"
        ),
    )
    paragraph_indent: str = Field(
        ...,
        description=(
            "段落首行缩进量。例如 '2em', '12pt', '0pt'。"
            "'2em' 约等于两个汉字宽度，是中文排版标准。"
            "英文学术论文通常使用 '1em' 到 '1.5em'。"
            "'0pt' 表示无缩进（此时通常需要段间距）。"
        ),
    )
    paragraph_skip: str = Field(
        default="0pt",
        description=(
            "段落之间的额外垂直间距。例如 '0pt', '6pt', '0.5em'。"
            "有首行缩进时通常为 '0pt'；"
            "无缩进的格式（如某些技术文档）使用段间距分隔段落。"
        ),
    )
    text_justification: Literal["justified", "ragged-right"] = Field(
        default="justified",
        description=(
            "正文对齐方式。"
            "'justified' - 两端对齐，学术论文标准；"
            "'ragged-right' - 左对齐右侧不齐，某些风格指南推荐。"
        ),
    )


# =============================================================================
# 9. 图表标题设置
# =============================================================================
class CaptionSettings(BaseIOSchema):
    """
    图表标题（caption）的样式配置，使用 caption 宏包。
    """

    font_size: str = Field(
        default="\\small",
        description=(
            "图表标题字号。例如 '\\small', '\\footnotesize', '9pt'。"
            "通常比正文小一号。"
        ),
    )
    label_font_weight: Literal["normal", "bold"] = Field(
        default="bold",
        description=(
            "标签部分（如 'Figure 1:'）的字重。" "多数格式标签加粗，描述文字不加粗。"
        ),
    )
    label_separator: str = Field(
        default=":",
        description=(
            "标签与描述之间的分隔符。"
            "常见选项：':' (Figure 1: xxx), '.' (Figure 1. xxx), ' - ', '  '(空格)。"
        ),
    )
    figure_position: Literal["above", "below"] = Field(
        default="below",
        description="图片标题位置。几乎所有格式图片标题在下方 'below'。",
    )
    table_position: Literal["above", "below"] = Field(
        default="above",
        description="表格标题位置。几乎所有格式表格标题在上方 'above'。",
    )


# =============================================================================
# 10. 根输出 Schema
# =============================================================================
class CLSGeneratorOutput(BaseIOSchema):
    """
    模板架构师 (CLS Generator) 的完整输出。
    包含所有结构化的样式参数，由代码生成器组装成最终的 .cls 文件。
    """

    class_name: str = Field(
        default="template",
        description=(
            "LaTeX 类名称，用于 \\ProvidesClass{} 和 \\documentclass{}。"
            "应为小写字母，无空格。例如 'ieeeconf', 'acmart', 'template'。"
        ),
    )
    base_class: Literal["article", "report", "book"] = Field(
        default="article",
        description=(
            "基础文档类，通过 \\LoadClass 加载。" "学术论文几乎总是基于 'article'。"
        ),
    )
    is_twocolumn: bool = Field(
        ...,
        description=(
            "是否为双栏布局。"
            "True - 双栏（IEEE、ACM 等会议论文常用）；"
            "False - 单栏（期刊论文、学位论文常用）。"
        ),
    )

    geometry: GeometrySettings = Field(..., description="页面几何参数")
    fonts: FontSettings = Field(..., description="全局字体设置")
    title: TitleSettings = Field(..., description="文档标题样式")
    author: AuthorSettings = Field(..., description="作者信息样式")
    abstract: AbstractSettings = Field(..., description="摘要样式")
    sections: SectionSettings = Field(..., description="章节标题样式")
    header_footer: HeaderFooterSettings = Field(..., description="页眉页脚样式")
    paragraph: ParagraphSettings = Field(..., description="段落排版参数")
    caption: CaptionSettings = Field(..., description="图表标题样式")

    additional_packages: list[str] = Field(
        default_factory=list,
        description=(
            "额外需要加载的宏包列表（不含选项）。"
            "基础宏包（geometry, fancyhdr, titlesec 等）会自动加载，"
            "此处填写特殊需求，如 ['amsmath', 'graphicx', 'hyperref']。"
        ),
    )
    custom_commands: str = Field(
        default="",
        description=(
            "自定义 LaTeX 命令或额外配置代码。"
            "用于处理特殊情况，如自定义 \\maketitle、特殊环境定义等。"
            "直接写 LaTeX 代码，会被插入到 .cls 文件末尾。"
        ),
    )
