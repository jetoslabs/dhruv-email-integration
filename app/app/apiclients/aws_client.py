import io

import boto3
from botocore.exceptions import ClientError
from loguru import logger

# from app.core.config import global_config
from app.core.config import configuration


class AWSClientHelper:

    @staticmethod
    def _build_boto3_session(aws_access_key_id: str, aws_access_secret: str, aws_region: str) -> boto3.Session:
        logger.bind().info("Building boto3 session")
        return boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_access_secret,
            region_name=aws_region
        )

    @staticmethod
    async def save_to_s3(session: boto3.Session, file_obj: io.BytesIO, bucket_name: str, object_name: str) -> str:
        s3_client = session.client('s3')
        try:
            s3_client.upload_fileobj(file_obj, bucket_name, object_name)
            # upload_fileobj succeds even in cases like permission issue or bucket not present
            if await AWSClientHelper.check_in_s3(session, bucket_name, object_name):
                logger.bind(bucket_name=bucket_name, object_name=object_name).debug("Saved in s3")
                return f"{bucket_name}/{object_name}"
        except ClientError as e:
            logger.bind(error=e).error("Error while save_to_s3")
            raise e

    @staticmethod
    async def check_in_s3(session: boto3.Session, bucket_name: str, object_name: str) -> bool:
        s3_client = session.client('s3')
        try:
            s3_client.head_object(Bucket=bucket_name, Key=object_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.bind(bucket_name=bucket_name, object_name=object_name).debug("Not Found in s3")
            else:
                raise e
            return False

    @staticmethod
    async def get_or_save_get_in_s3(session: boto3.Session, file_obj: io.BytesIO, bucket_name: str, object_name: str) -> str:
        exist = await AWSClientHelper.check_in_s3(session, bucket_name, object_name)
        if exist:
            return f"{bucket_name}/{object_name}"
        else:
            save = await AWSClientHelper.save_to_s3(session, file_obj, bucket_name, object_name)
            return save

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
# boto3_session = AWSClientHelper._build_boto3_session(
#     global_config.aws_access_key_id,
#     global_config.aws_access_secret,
#     global_config.aws_region
# )


def get_tenant_boto3_session(tenant: str) -> boto3.Session:
    aws_config = configuration.tenant_configurations.get(tenant).aws
    boto3_session = AWSClientHelper._build_boto3_session(
        aws_config.aws_access_key_id,
        aws_config.aws_access_secret,
        aws_config.aws_region
    )
    return boto3_session
