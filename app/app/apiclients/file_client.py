import io
import os
from pathlib import Path

from loguru import logger


class FileHelper:

    @staticmethod
    async def save_to_disk(file_obj: io.BytesIO, base_path: str, relative_path: str, filename: str) -> str:
        try:
            dir_path = f"{base_path}/{relative_path}"
            full_path = f"{dir_path}/{filename}"
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            with open(full_path, 'wb') as file:
                file.write(file_obj.read())

            if FileHelper.check_in_disk(base_path, relative_path, filename):
                logger.bind(full_path=full_path).debug("Saved to disk")
                return full_path

        except Exception as e:
            logger.bind(error=e).error("Error while save_to_disk")
            raise e

    @staticmethod
    async def check_in_disk(base_path: str, relative_path: str, filename: str) -> bool:
        full_path = f"{base_path}/{relative_path}/{filename}"
        file_path = Path(full_path)
        is_file = file_path.is_file()
        return is_file

    @staticmethod
    async def get_or_save_get_in_disk(file_obj: io.BytesIO, base_path: str, relative_path: str, filename: str) -> str:
        exist = await FileHelper.check_in_disk(base_path, relative_path, filename)
        if exist:
            return f"{base_path}/{relative_path}"
        else:
            save = await FileHelper.save_to_disk(file_obj, base_path, relative_path, filename)
            return save
