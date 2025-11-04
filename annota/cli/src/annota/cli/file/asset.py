import json
from pathlib import Path
from typing import Optional, Union
from datetime import datetime, timezone

from annota.cli.error import InvalidFileError
from pydantic import ValidationError

from annota.cli.typing import Document, Annotation, ImageFile, Meta

class ImageAsset:
    """
    API class for reading, modifying and writing image asset files.

    This object represents an image asset and all of its annotations.
    """

    @classmethod
    def load(cls, image_path: Union[str, Path]) -> 'ImageAsset':
        """
        Load the associated .meta file for a given image path and return an Asset.

        :param image_path: Path to the image file (for example ``'main_menu.png'``).
        :raises FileNotFoundError: If the .meta file does not exist.
        :raises ValidationError: If the .meta file content fails validation.
        :return: An :class:`Asset` instance.
        """
        image_path = Path(image_path)
        meta_path = image_path.with_suffix('.meta')

        if not meta_path.exists():
            raise FileNotFoundError(f'Meta file not found: {meta_path}')

        try:
            doc = Document.model_validate_json(meta_path.read_text(encoding='utf-8'))
            return cls(document=doc, source_path=meta_path)
        except (ValidationError, json.JSONDecodeError) as e:
            print(f'Failed to parse {meta_path}!')
            raise e

    @classmethod
    def loads(cls, json_str: str, source_path: Optional[Union[str, Path]] = None) -> 'ImageAsset':
        """
        Create an :class:`ImageAsset` from a JSON string. If ``source_path`` is
        provided it will be used as the asset's ``path`` (for later ``dump`` calls).

        :param json_str: JSON string representing a Document (the contents of a .meta file).
        :param source_path: Optional path to associate with the created asset.
        :raises InvalidFileError: If the string is not valid JSON or the JSON fails model validation.
        :return: An :class:`ImageAsset` instance.
        """
        try:
            doc = Document.model_validate_json(json_str)
            src = Path(source_path) if source_path is not None else None
            return cls(document=doc, source_path=src)
        except (ValidationError, json.JSONDecodeError) as e:
            raise InvalidFileError from e

    @classmethod
    def create(
        cls,
        file_path: Union[str, Path],
        image_width: int,
        image_height: int
    ) -> 'ImageAsset':
        """
        Create a new, empty Asset for a new image file.

        :param image_path: Path to the new image file.
        :param image_width: Width of the image in pixels.
        :param image_height: Height of the image in pixels.
        :return: A new, unsaved :class:`Asset` instance.
        """
        from annota.cli.file import FORMAT_VERSION
        from annota.cli import CLI_VERSION, CLI_NAME

        file_path = Path(file_path)
        meta_path = file_path.with_suffix('.meta')

        return cls(
            document=Document(
                type='image',
                meta=Meta(
                    version=FORMAT_VERSION,
                    tool=CLI_NAME,
                    tool_version=CLI_VERSION,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ),
                file=ImageFile(width=image_width, height=image_height),
                
            ),
            source_path=meta_path
        )

    ############### Instance Methods ###############
    
    def __init__(self, document: Document, source_path: Optional[Path] = None):
        """
        Initialize an Asset instance.

        .. note::
           Direct construction is discouraged. Use :meth:`load` or :meth:`create`.

        :param document: The validated Document model representing the .meta contents.
        :param source_path: Optional Path to the source .meta file.
        """
        self._doc = document
        self.path = source_path
        self._name_map = { ann.name: ann for ann in self._doc.annotations }

    def save(self, path: Union[str, Path, None] = None):
        """
        Dump the current annotations and metadata to a .meta file.

        :param path: Optional target path to save to. If ``None``, the original
                     load path will be used. If the instance was not loaded
                     from a file and no path is provided, a :class:`ValueError`
                     is raised.
        """
        target_path = Path(path) if path else self.path
        if target_path is None:
            raise ValueError('Cannot dump: no target path provided and instance was not loaded from a file.')

        json_str = self.dumps()
        target_path.write_text(json_str, encoding='utf-8')

    def dumps(self, *, update_timestamp: bool = True, indent: int = 2) -> str:
        """
        Return the JSON representation of this asset as a string.

        The asset's ``meta.updated_at`` timestamp will be refreshed before
        serialization.

        :param update_timestamp: If ``True``, update the ``meta.updated_at`` timestamp
                                to the current time before serialization.
        :param indent: Number of spaces to use for JSON indentation. Default is 2.
        :return: The JSON string representing this asset.
        """
        if update_timestamp:
            self._doc.meta.updated_at = datetime.now(timezone.utc)
        return self._doc.model_dump_json(indent=indent)

    @property
    def annotations(self) -> list[Annotation]:
        """Return the list of annotations."""
        return self._doc.annotations
    
    @property
    def image_size(self) -> tuple[int, int]:
        """Return the associated image size as a ``(width, height)`` tuple."""
        return (self._doc.file.width, self._doc.file.height)

    def get_annotation(self, name: str) -> Optional[Annotation]:
        """
        Get an annotation by its name.

        :param name: The unique annotation name.
        :return: The found :class:`Annotation` or ``None`` if not found.
        """
        return self._name_map.get(name)

    def __getitem__(self, name: str) -> Annotation:
        """Allow dict-style access ``asset['annotation_name']`` to get an annotation."""
        ann = self.get_annotation(name)
        if ann is None:
            raise KeyError(f"Annotation with name '{name}' does not exist.")
        return ann

    def __contains__(self, name: str) -> bool:
        """Support the ``in`` operator to check for annotation existence.

        Example: ``if 'ann_name' in asset:``
        """
        return name in self._name_map

    def __len__(self) -> int:
        """Return number of annotations (``len(asset)``)."""
        return len(self._doc.annotations)

    def __iter__(self):
        """Iterate over all annotations: ``for ann in asset:``."""
        return iter(self._doc.annotations)

    def add_annotation(self, annotation: Annotation, overwrite: bool = False):
        """
        Add a new annotation to the asset.

        :param annotation: The :class:`Annotation` to add.
        :param overwrite: If ``True`` and an annotation with the same name exists,
                          the existing one will be replaced.
        :raises ValueError: If an annotation with the same name exists and
                            ``overwrite`` is ``False``.
        """
        if annotation.name in self._name_map:
            if overwrite:
                self.remove_annotation(annotation.name)
            else:
                raise ValueError(f"Annotation with name '{annotation.name}' already exists.")
        
        self._doc.annotations.append(annotation)
        self._name_map[annotation.name] = annotation

    def remove_annotation(self, name: str) -> Optional[Annotation]:
        """
        Remove an annotation by name.

        :param name: The name of the annotation to remove.
        :return: The removed :class:`Annotation`, or ``None`` if not found.
        """
        if name not in self._name_map:
            return None
        
        ann_to_remove = self._name_map.pop(name)
        self._doc.annotations.remove(ann_to_remove)
        return ann_to_remove
