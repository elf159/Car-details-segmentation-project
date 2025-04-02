from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI()

class ImageProcessRequest(BaseModel):
    download_object_name: str
    job_id: str
    result_name: str

class ResultMetadata(BaseModel):
    damage_level: str
    segment_name: str

class ResultList(BaseModel):
    result: List[Dict[str, ResultMetadata]]

@app.post("/api/v1/process_request", response_model=ResultList)
async def process_request(request: ImageProcessRequest):
    # Заглушка

    if request.job_id == "error_job":
        raise HTTPException(status_code=500, detail="Ошибка обработки изображения")

    if request.job_id == "no_damage":
        results = {
            "result": [
                {
                    "front_bumper": {
                        "damage_level": "NONE",
                        "segment_name": "front_bumper"
                    }
                },
                {
                    "hood": {
                        "damage_level": "NONE",
                        "segment_name": "hood"
                    }
                },
                {
                    "left_door": {
                        "damage_level": "NONE",
                        "segment_name": "left_door"
                    }
                },
            ]
        }
        return results

    if request.job_id == "no_segments":
        results = {
            "result": [
                {
                    "0": {
                        "damage_level": "NONE",
                        "segment_name": "empty"
                    }
                }
            ]
        }
        return results

    # Заглушка 
    results = {
        "result": [
            {
                "front_bumper": {
                    "damage_level": "DENT",
                    "segment_name": "front_bumper"
                }
            },
            {
                "hood": {
                    "damage_level": "SCRATCH",
                    "segment_name": "hood"
                }
            },
            {
                "left_door": {
                    "damage_level": "BROKEN",
                    "segment_name": "left_door"
                }
            },
            {
                "right_door": {
                    "damage_level": "TOTAL_LOSS",
                    "segment_name": "right_door"
                }
            },
            {
                "windshield": {
                    "damage_level": "NONE",
                    "segment_name": "windshield"
                }
            },
        ]
    }
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)