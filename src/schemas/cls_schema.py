from typing import Literal

from atomic_agents import BaseIOSchema
from pydantic import Field


class GeometrySettings(BaseIOSchema):
    """Page geometry parameters used to build the LaTeX class."""

    paper_size: Literal["a4paper", "letterpaper", "a5paper"] = Field(default="a4paper")
    top_margin: str = Field(...)
    bottom_margin: str = Field(...)
    left_margin: str = Field(...)
    right_margin: str = Field(...)
    column_sep: str | None = Field(default=None)
    head_height: str = Field(default="14pt")
    head_sep: str = Field(default="18pt")
    foot_skip: str = Field(default="24pt")


class FontSettings(BaseIOSchema):
    """Global font configuration for the generated class."""

    base_font_size: Literal["9pt", "10pt", "11pt", "12pt"] = Field(default="10pt")
    main_font_family: Literal["serif", "sans-serif"] = Field(default="serif")
    math_font_package: str = Field(default="Cambria Math")
    use_microtype: bool = Field(default=True)


class TitleSettings(BaseIOSchema):
    """Title block typography and spacing settings."""

    font_size: str = Field(...)
    font_weight: Literal["normal", "bold"] = Field(default="bold")
    font_family: Literal["serif", "sans-serif"] = Field(default="sans-serif")
    alignment: Literal["left", "center", "right"] = Field(default="center")
    space_before: str = Field(default="0pt")
    space_after: str = Field(...)


class AuthorSettings(BaseIOSchema):
    """Author block typography and spacing settings."""

    name_font_size: str = Field(...)
    name_font_weight: Literal["normal", "bold"] = Field(default="normal")
    affiliation_font_size: str = Field(...)
    affiliation_font_style: Literal["normal", "italic"] = Field(default="italic")
    alignment: Literal["left", "center", "right"] = Field(default="center")
    space_after: str = Field(...)


class AbstractSettings(BaseIOSchema):
    """Abstract block typography, indentation, and spacing settings."""

    font_size: str = Field(...)
    font_style: Literal["normal", "italic"] = Field(default="normal")
    left_indent: str = Field(...)
    right_indent: str = Field(...)
    heading_text: str = Field(default="Abstract")
    heading_font_weight: Literal["normal", "bold"] = Field(default="bold")
    space_before: str = Field(default="12pt")
    space_after: str = Field(...)


class SectionSettings(BaseIOSchema):
    """Section and subsection typography and spacing settings."""

    section_font_size: str = Field(...)
    section_font_weight: Literal["normal", "bold"] = Field(default="bold")
    section_font_family: Literal["serif", "sans-serif"] = Field(default="sans-serif")
    section_alignment: Literal["left", "center", "right"] = Field(default="left")
    section_numbering_format: str = Field(default="arabic")
    section_space_before: str = Field(...)
    section_space_after: str = Field(...)
    subsection_font_size: str = Field(...)
    subsection_font_weight: Literal["normal", "bold"] = Field(default="bold")
    subsection_font_style: Literal["normal", "italic"] = Field(default="normal")
    subsection_space_before: str = Field(...)
    subsection_space_after: str = Field(...)


class HeaderLineConfig(BaseIOSchema):
    """单行页眉配置，用于支持多行期刊名"""

    text: str = Field(default="", description="该行显示的文字内容")
    font_size: str = Field(default="\\large", description="字体大小，如 \\large, \\Large, \\normalsize")
    font_weight: Literal["normal", "bold"] = Field(default="bold", description="字体粗细")
    font_family: Literal["serif", "sans-serif"] = Field(default="sans-serif", description="字体族")
    space_after: str = Field(default="0pt", description="与下一行的间距")


class FooterLineConfig(BaseIOSchema):
    """单行页脚配置"""

    text: str = Field(default="", description="该行显示的文字内容，支持 \\thepage 等命令")
    font_size: str = Field(default="\\footnotesize", description="字体大小")
    font_weight: Literal["normal", "bold"] = Field(default="normal", description="字体粗细")
    alignment: Literal["left", "center", "right"] = Field(default="center", description="对齐方式")


class HeaderFooterSettings(BaseIOSchema):
    """Header and footer content placement settings for first and running pages."""

    # ===== 首页页眉配置 =====
    # 多行期刊名配置（新增）
    journal_header_lines: list[HeaderLineConfig] = Field(
        default_factory=list,
        description="首页顶部期刊名/杂志名/会议名的多行配置。每行可独立设置字体和间距。适用于多行期刊名的情况。例如中文期刊名、英文期刊名、卷期号等。",
    )

    # 传统单行页眉（向后兼容）
    first_page_header_left: str = Field(default="", description="首页页眉左侧内容")
    first_page_header_center: str = Field(default="", description="首页页眉中间内容")
    first_page_header_right: str = Field(default="", description="首页页眉右侧内容")

    # ===== 内页/普通页页眉配置 =====
    running_header_left: str = Field(default="", description="内页页眉左侧内容，如卷号/期号")
    running_header_center: str = Field(default="", description="内页页眉中间内容，如期刊名")
    running_header_right: str = Field(default="\\thepage", description="内页页眉右侧内容，通常是页码")

    # ===== 首页页脚配置 =====
    first_page_footer_center: str = Field(default="", description="首页页脚中间内容")
    first_page_footer_left: str = Field(default="", description="首页页脚左侧内容")
    first_page_footer_right: str = Field(default="", description="首页页脚右侧内容")

    # ===== 内页/普通页页脚配置 =====
    running_footer_left: str = Field(default="", description="内页页脚左侧内容")
    running_footer_center: str = Field(default="", description="内页页脚中间内容")
    running_footer_right: str = Field(default="", description="内页页脚右侧内容")

    # ===== 分隔线配置 =====
    header_rule_width: str = Field(default="0.4pt", description="页眉与正文之间的分隔线宽度")
    header_rule_skip: str = Field(default="0pt", description="页眉分隔线与页眉的间距")
    footer_rule_width: str = Field(default="0pt", description="页尾与正文之间的分隔线宽度")
    footer_rule_skip: str = Field(default="0pt", description="页尾分隔线与页尾的间距")

    first_page_has_rule: bool = Field(default=True, description="首页是否显示页眉分隔线")


class ParagraphSettings(BaseIOSchema):
    """Body paragraph spacing and justification settings."""

    line_spread: str = Field(...)
    paragraph_indent: str = Field(...)
    paragraph_skip: str = Field(default="0pt")
    text_justification: Literal["justified", "ragged-right"] = Field(default="justified")
    caption_skip: str = Field(default="6pt")


class CaptionSettings(BaseIOSchema):
    """Figure and table caption formatting settings."""

    font_size: str = Field(default="\\small")
    label_font_weight: Literal["normal", "bold"] = Field(default="bold")
    label_separator: str = Field(default=":")
    figure_position: Literal["above", "below"] = Field(default="below")
    table_position: Literal["above", "below"] = Field(default="above")


class FootnoteSettings(BaseIOSchema):
    """脚注/注解配置 - 所有脚注都应放在页面底部，绝对不要放在正文中"""

    # 首页脚注（如基金信息、通讯作者、收稿日期等）
    first_page_footnote: str = Field(
        default="",
        description="首页底部脚注内容（如基金信息、通讯作者、收稿日期等）。支持LaTeX格式代码。注意：脚注必须放在页面底部，绝对不能出现在正文中间。",
    )
    first_page_footnote_font_size: str = Field(default="\\footnotesize", description="首页脚注字体大小")
    first_page_footnote_alignment: Literal["left", "center", "right"] = Field(default="left", description="首页脚注对齐方式")

    # 正文脚注样式
    footnote_font_size: str = Field(default="\\footnotesize", description="正文脚注字体大小")
    footnote_font_style: Literal["normal", "italic"] = Field(default="normal", description="正文脚注字体样式")
    footnote_numbering_format: str = Field(
        default="\\arabic{footnote}",
        description="脚注编号格式，如 \\arabic{footnote}, \\fnsymbol{footnote}",
    )
    footnote_rule_width: str = Field(default="0.4pt", description="脚注分割线宽度")
    footnote_rule_skip: str = Field(default="8pt", description="脚注分割线与正文的间距")
    footnote_indent: str = Field(default="0pt", description="脚注文本的缩进")

    # 符号标记
    use_symbol_marks: bool = Field(
        default=False,
        description="是否使用符号标记（如*†‡）代替数字编号。常用于首页作者单位标注。",
    )


class CLSGeneratorOutput(BaseIOSchema):
    """Complete structured configuration used to render template.cls."""

    class_name: str = Field(default="template")
    base_class: Literal["article", "report", "book"] = Field(default="article")
    is_twocolumn: bool = Field(...)
    geometry: GeometrySettings = Field(...)
    fonts: FontSettings = Field(...)
    title: TitleSettings = Field(...)
    author: AuthorSettings = Field(...)
    abstract: AbstractSettings = Field(...)
    sections: SectionSettings = Field(...)
    header_footer: HeaderFooterSettings = Field(...)
    paragraph: ParagraphSettings = Field(...)
    caption: CaptionSettings = Field(...)
    footnote: FootnoteSettings = Field(default_factory=FootnoteSettings, description="脚注/注解配置")
    additional_packages: list[str] = Field(default_factory=list)
    custom_commands: str = Field(default="")
