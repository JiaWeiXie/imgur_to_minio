from io import BytesIO
from typing import Annotated

import httpx
from environs import Env
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio
from minio.error import S3Error
from pydantic import BaseModel

env = Env()
env.read_env()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hackmd.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

endpoint = env("MINIO_S3_ENDPOINT")
minio_client = Minio(
    endpoint,
    access_key=env("MINIO_ACCESS_KEY_ID"),
    secret_key=env("MINIO_SECRET_ACCESS_KEY"),
    secure=env.bool("MINIO_S3_USE_SSL"),
    region=env("MINIO_S3_REGION_NAME"),
)

bucket_name = env("MINIO_STORAGE_BUCKET_NAME")
APIKEY_LIST = env.list("APIKEY_LIST")


class ImgurImage(BaseModel):
    imgur_url: str


class MinIOImage(BaseModel):
    minio_url: str

async def upload_image_to_minio(image_url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)

    try:
        image_name = image_url.split("/")[-1]
        result = minio_client.put_object(
            bucket_name,
            image_name,
            data=BytesIO(response.content),
            length=len(response.content),
            content_type=response.headers["Content-Type"],
        )
        return f"https://{endpoint}/{bucket_name}/{result.object_name}"
    except S3Error as e:
        raise HTTPException(
            status_code=500, detail=f"Error uploading image to MinIO: {str(e)}"
        )
         

@app.post("/upload-to-minio/")
async def upload_to_minio(
    imgur_image: ImgurImage,
    api_key: Annotated[str, Query(max_length=50)],
) -> MinIOImage:
    if api_key not in APIKEY_LIST:
        raise HTTPException(
            status_code=401,
            detail="401 Unauthorized",
        )
    minio_url = await upload_image_to_minio(imgur_image.imgur_url)
    return MinIOImage(minio_url=minio_url)
