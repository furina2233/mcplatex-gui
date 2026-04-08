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


class HeaderFooterSettings(BaseIOSchema):
    """Header and footer content placement settings for first and running pages."""

    first_page_header_left: str = Field(default="")
    first_page_header_center: str = Field(default="")
    first_page_header_right: str = Field(default="")
    first_page_footer_center: str = Field(default="")
    first_page_has_rule: bool = Field(default=False)
    running_header_left: str = Field(default="")
    running_header_center: str = Field(default="")
    running_header_right: str = Field(default="\\thepage")
    running_footer_center: str = Field(default="")
    header_rule_width: str = Field(default="0.4pt")
    footer_rule_width: str = Field(default="0pt")


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
    additional_packages: list[str] = Field(default_factory=list)
    custom_commands: str = Field(default="")
