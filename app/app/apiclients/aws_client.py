import io

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from app.core.config import global_config


class AWSClientHelper:

    @staticmethod
    def _build_boto3_session(aws_access_key_id: str, aws_access_secret: str, aws_region: str) -> boto3.Session:
        logger.bind().info("Building boto3 session...")
        return boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_access_secret,
            region_name=aws_region
        )

    @staticmethod
    async def save_to_s3(session: boto3.Session, file_obj: io.BytesIO, bucket_name: str, object_name: str) -> bool:
        s3_client = session.client('s3')
        try:
            s3_client.upload_fileobj(file_obj, bucket_name, object_name)
        except ClientError as e:
            logger.bind(error=e).error("Error while save_to_s3")
            raise e
        return await AWSClientHelper.check_in_s3(session, bucket_name, object_name)

    @staticmethod
    async def check_in_s3(session: boto3.Session, bucket_name: str, object_name: str) -> bool:
        s3_client = session.client('s3')
        try:
            s3_client.head_object(Bucket=bucket_name, Key=object_name)
        except ClientError as e:
            logger.bind(error=e).error("Error while check_in_s3")
            raise e
        return True

    @staticmethod
    async def delete_from_s3(session: boto3.Session, bucket_name: str, object_name: str) -> bool:
        try:
            s3_resource = session.resource('s3')
            s3_resource.Object(bucket_name, object_name).delete()
        except ClientError as e:
            logger.bind(error=e).error("Error while delete_from_s3")
            raise e
        return True


# TODO: move var
boto3_session = AWSClientHelper._build_boto3_session(
    global_config.aws_access_key_id,
    global_config.aws_access_secret,
    global_config.aws_region
)
