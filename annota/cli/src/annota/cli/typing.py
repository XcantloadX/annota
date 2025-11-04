"""
## annota.cli.typing

This module contains pydantic models and typing annotations for annota.
"""

from typing import Annotated, Literal, Any, Optional, Union
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Discriminator, Field, Tag

BuiltInAnnotationType = Literal[
    'slice',
    'box',
    'point',
    'swipe'
]
AnnotationType = Union[BuiltInAnnotationType, str]
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
    type: Literal['slice']
    geometry: Rect


class BoxAnnotationAttributes(BaseModel):
    type: Literal['box']
    geometry: Rect


class PointAnnotationAttributes(BaseModel):
    type: Literal['point']
    geometry: Point


class SwipeAnnotationAttributes(BaseModel):
    type: Literal['swipe']
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

def _attributes_type(data: dict) -> str:
    type = data.get('type', None)
    if type in ['slice', 'box', 'point', 'swipe']:
        return type
    else:
        return 'custom'

class Annotation(BaseModel):
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    """Name of the annotation. This will be used in the generated code."""
    display_name: str
    """Display name of the annotation. This will be used in the UI and code comments."""
    description: Optional[str] = None
    attributes: Union[
        Annotated[SliceAnnotationAttributes, Tag('slice')],
        Annotated[BoxAnnotationAttributes, Tag('box')],
        Annotated[PointAnnotationAttributes, Tag('point')],
        Annotated[SwipeAnnotationAttributes, Tag('swipe')],
        Annotated[dict, Tag('custom')]
    ] = Field(discriminator=Discriminator(_attributes_type))
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