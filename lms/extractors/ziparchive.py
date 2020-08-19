from typing import Iterator, List, Tuple
from zipfile import BadZipFile, ZipFile

from loguru import logger

from lms.extractors.base import Extractor, File
from lms.models.errors import BadUploadFile


class Ziparchive(Extractor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_zipfile = (
            self.filename is not None
            and self.filename.endswith('.zip')
        )
        if not self.is_zipfile:
            return

        try:
            self.archive = ZipFile(self.to_extract.stream._file)
        except BadZipFile:
            self.is_zipfile = False

    def can_extract(self) -> bool:
        return self.is_zipfile

    def get_exercise(self, file: ZipFile) -> Tuple[int, List[File]]:
        assert self.filename is not None
        exercise_id, _ = self._clean(self.filename.rpartition('.')[0])
        if not exercise_id:
            raise BadUploadFile('Invalid zip name', self.filename)

        files = []
        with file as archive:
            for filename in archive.namelist():
                with archive.open(filename) as current_file:
                    logger.debug(f'Extracting from archive: {filename}')
                    code = current_file.read()
                    decoded = code.decode('utf-8', errors='ignore')
                    files.append(File(path=f'/{filename}', code=decoded))
        return exercise_id, files

    def get_exercises(self) -> Iterator[Tuple[int, List[File]]]:
        exercise_id, files = self.get_exercise(self.archive)
        if files and any(file.code for file in files):
            yield (exercise_id, files)