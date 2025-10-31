"""
## annota.cli.typing

This module contains pydantic models and typing annotations for annota.
"""

from typing import Literal, Any, Optional, Union
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

BuiltInAnnotationType = Literal[
    'slice',
    'box',
    'point',
    'swipe'
]
BuiltInDocumentType = Literal['image']


class Rect(BaseModel):
    x: int
    y: int
    width: int
    height: int


class Point(BaseModel):
    x: int
    y: int


class Vec2(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class SliceAnnotationAttributes(BaseModel):
    geometry: Rect


class BoxAnnotationAttributes(BaseModel):
    geometry: Rect


class PointAnnotationAttributes(BaseModel):
    geometry: Point


class SwipeAnnotationAttributes(BaseModel):
    geometry: Vec2


class ImageFile(BaseModel):
    """
    File metadata for image files.

    Available when `root.meta.type` is `image` or `template`.
    """
    width: int
    height: int


class Meta(BaseModel):
    """
    Metadata for the meta document.
    """
    version: int
    tool: str
    tool_version: str
    created_at: datetime
    updated_at: datetime


class Annotation(BaseModel):
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    type: Union[BuiltInAnnotationType, str]
    name: str
    """Name of the annotation. This will be used in the generated code."""
    display_name: str
    """Display name of the annotation. This will be used in the UI and code comments."""
    description: str
    attributes: Union[
        SliceAnnotationAttributes,
        BoxAnnotationAttributes,
        PointAnnotationAttributes,
        SwipeAnnotationAttributes
    ] = Field(discriminator='type')
    """Attributes of the annotation, which contains actual data for the annotation."""
    extra: Optional[dict[str, Any]] = None
    """Custom attributes. You can use this to store any additional data. Must be JSON-serializable."""


class Document(BaseModel):
    """
    Root model for metadata document.
    """
    type: Union[BuiltInDocumentType, str]
    meta: Meta
    file: ImageFile
    annotations: list[Annotation] = Field(default_factory=list)