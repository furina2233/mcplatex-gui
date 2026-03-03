# schemas/__init__.py
from .style_schema import StyleAnalysisReport, FontFeature, PageLayout, SpacingFeature
from .cls_schema import (
    CLSGeneratorOutput,
    GeometrySettings,
    FontSettings,
    TitleSettings,
    AuthorSettings,
    AbstractSettings,
    SectionSettings,
    HeaderFooterSettings,
    ParagraphSettings,
    CaptionSettings,
)

__all__ = [
    "StyleAnalysisReport",
    "FontFeature",
    "PageLayout",
    "SpacingFeature",
    "CLSGeneratorOutput",
    "GeometrySettings",
    "FontSettings",
    "TitleSettings",
    "AuthorSettings",
    "AbstractSettings",
    "SectionSettings",
    "HeaderFooterSettings",
    "ParagraphSettings",
    "CaptionSettings",
]
