from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from minio import Minio
from minio.error import S3Error
import io

from processing import classify_brand, run_segmentation
import pika
import json

def send_rabbitmq_event(job_id: str, message: str):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
        channel = connection.channel()
        channel.queue_declare(queue="minioevents", durable=True)

        event = {
            "job_id": job_id,
            "error": message
        }
        channel.basic_publish(
            exchange="",
            routing_key="minioevents",
            body=json.dumps(event),
            properties=pika.BasicProperties(delivery_mode=2) 
        )
        connection.close()
    except Exception as e:
        print(f"RabbitMQ error: {str(e)}")

app = FastAPI()

class ImageProcessRequest(BaseModel):
    download_object_name: str
    job_id: str
    result_name: str

minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

@app.post("/api/v1/process_request")
async def process_request(request: ImageProcessRequest):
    try:
        image_name = request.download_object_name
        result_name = request.result_name
        job_id = request.job_id
        
        image_data = get_image_from_minio(image_name)
        if not image_data:
            send_rabbitmq_event(job_id, "Image not found in MinIO")
            raise HTTPException(status_code=404, detail="Image not found in MinIO")

        brand = classify_brand(image_data)
        if brand == "none":
            send_rabbitmq_event(job_id, "Car is not found or brand is not recognized")
            return {"message": "Car is not found", "job_id": job_id}

        result_png = run_segmentation(image_data, brand)
        upload_image_to_minio(result_name, result_png)

        return {
            "message": f"Processed brand: {brand}, saved as {result_name}",
            "job_id": job_id
        }

    except Exception as e:
        send_rabbitmq_event(request.job_id, f"Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


def get_image_from_minio(image_name: str) -> bytes:
    try:
        response = minio_client.get_object("cars", image_name)
        return response.read()
    except S3Error as e:
        print(f"MinIO error: {str(e)}")
        return None

def upload_image_to_minio(file_name: str, image_data: bytes):
    try:
        minio_client.put_object(
            "cars",
            file_name,
            io.BytesIO(image_data),
            len(image_data),
            content_type="image/png"
        )
        print(f"Uploaded {file_name} to MinIO")
    except S3Error as e:
        print(f"Upload error: {str(e)}")

# C:\useful\copy\FastAPI
#.\venv\Scripts\activate
# uvicorn main:app --reload