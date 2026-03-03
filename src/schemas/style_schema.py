from pydantic import Field
from typing import List, Literal
from atomic_agents import BaseIOSchema


# =============================================================================
# 1. 字体特征 Schema
# =============================================================================
class FontFeature(BaseIOSchema):
    """
    描述文档中单一文本元素（如标题、正文、摘要）的详细字体特征。
    """

    element_name: str = Field(
        ..., description="元素名称。如：Title, Abstract, Section, Body, Caption等。"
    )
    font_family: Literal["Serif", "Sans-serif", "Monospace"] = Field(
        ...,
        description="字体族类型：Serif (有衬线), Sans-serif (无衬线), Monospace (等宽)。",
    )
    is_bold: bool = Field(False, description="是否加粗")
    is_italic: bool = Field(False, description="是否斜体")
    estimated_size: str = Field(..., description="估算字号，例如 '12pt', '10.5pt'。")
    alignment: Literal["Left", "Center", "Right", "Justified"] = Field(
        ..., description="对齐方式。"
    )


# =============================================================================
# 2. 页面布局 Schema
# =============================================================================
class PageLayout(BaseIOSchema):
    """
    描述页面的全局几何布局特征，包括分栏和页眉页脚。
    """

    column_count: int = Field(..., description="分栏数量。通常为 1 或 2。")
    margins: str = Field(
        ..., description="页边距的视觉描述。例如：'上下2.5cm，左右2cm'。"
    )

    first_page_header: str = Field(
        ...,
        description="【首页】特有的页眉。若无则填 'None'。请描述是否有横线、版权信息或Logo。",
    )
    standard_header: str = Field(
        ...,
        description="【后续页面】的通用页眉。请描述分隔线粗细、内容（如章节名）及位置。",
    )
    footer_position: str = Field(
        ..., description="页码位置。例如：'页底居中', '页底外侧'。"
    )


# =============================================================================
# 3. 间距特征 Schema
# =============================================================================
class SpacingFeature(BaseIOSchema):
    """
    描述文本的微观排版特征。
    """

    paragraph_indent: str = Field(
        ..., description="段落首行缩进情况。例如：'缩进2字符'。"
    )
    line_spacing: str = Field(
        ..., description="行距密度。例如：'单倍行距', '1.2倍行距'。"
    )
    section_spacing: str = Field(..., description="章节标题前后的留白情况。")


# =============================================================================
# 4. 最终报告 Schema (根对象)
# =============================================================================
class StyleAnalysisReport(BaseIOSchema):
    """
    样式分析师 (Style Analyzer) 的最终产出报告。
    """

    layout: PageLayout = Field(..., description="页面布局与页眉页脚信息")
    fonts: List[FontFeature] = Field(..., description="关键文本元素的字体特征列表")
    spacing: SpacingFeature = Field(..., description="段落间距与缩进细节")
    summary: str = Field(..., description="对整体排版风格的简短自然语言总结。")
