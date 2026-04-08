from typing import List, Literal

from atomic_agents import BaseIOSchema
from pydantic import Field


class FontFeature(BaseIOSchema):
    """Detected font characteristics for a specific document element."""

    element_name: str = Field(..., description="Element name such as Title, Body, Section, Caption.")
    font_family: Literal["Serif", "Sans-serif", "Monospace"] = Field(..., description="Detected font family.")
    is_bold: bool = Field(False, description="Whether the text is bold.")
    is_italic: bool = Field(False, description="Whether the text is italic.")
    estimated_size: str = Field(..., description="Estimated font size, e.g. 10pt or 12pt.")
    alignment: Literal["Left", "Center", "Right", "Justified"] = Field(..., description="Detected alignment.")


class PageLayout(BaseIOSchema):
    """Structured page-level layout estimates derived from the screenshots."""

    column_count: int = Field(..., description="Number of text columns.")
    top_margin: str = Field(..., description="Top page margin.")
    bottom_margin: str = Field(..., description="Bottom page margin.")
    left_margin: str = Field(..., description="Left page margin.")
    right_margin: str = Field(..., description="Right page margin.")
    column_sep: str | None = Field(default=None, description="Column gap for two-column layout.")
    head_height: str = Field(default="14pt", description="Header box height.")
    head_sep: str = Field(default="18pt", description="Distance from header to text body.")
    foot_skip: str = Field(default="24pt", description="Distance from text body to footer baseline.")
    first_page_header: str = Field(..., description="First-page header description.")
    standard_header: str = Field(..., description="Running header description.")
    footer_position: str = Field(..., description="Footer or page-number position.")


class SpacingFeature(BaseIOSchema):
    """Structured spacing estimates for body text and major layout blocks."""

    paragraph_indent: str = Field(..., description="First-line paragraph indent.")
    body_line_spacing: str = Field(..., description="Body line spacing.")
    paragraph_spacing: str = Field(..., description="Spacing between paragraphs.")
    section_space_before: str = Field(..., description="Space before section titles.")
    section_space_after: str = Field(..., description="Space after section titles.")
    subsection_space_before: str = Field(..., description="Space before subsection titles.")
    subsection_space_after: str = Field(..., description="Space after subsection titles.")
    title_space_before: str = Field(default="0pt", description="Space before the title block.")
    title_space_after: str = Field(..., description="Space after the title block.")
    author_space_after: str = Field(..., description="Space after the author block.")
    abstract_space_before: str = Field(..., description="Space before the abstract block.")
    abstract_space_after: str = Field(..., description="Space after the abstract block.")
    caption_skip: str = Field(default="6pt", description="Gap between figure/table body and caption.")


class StyleAnalysisReport(BaseIOSchema):
    """Complete structured visual-style analysis used to drive CLS generation."""

    layout: PageLayout = Field(..., description="Structured page layout analysis.")
    fonts: List[FontFeature] = Field(..., description="Key font observations.")
    spacing: SpacingFeature = Field(..., description="Structured spacing analysis.")
    summary: str = Field(..., description="Short natural-language summary of the page style.")
