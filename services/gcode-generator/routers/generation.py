from fastapi import APIRouter, HTTPException

from schemas import GenerationRequest, SaveRequest
from services.gcode_service import GCodeService
from services.supabase_service import supabase_service

router = APIRouter(tags=["Generation"])

@router.post("/generate")
async def generate_output(payload: GenerationRequest):
    try:
        output_result = GCodeService.process_generation(payload)
        return {
            "status": "success",
            "file_type": payload.file_type,
            "output": output_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
async def save_output(payload: SaveRequest):
    try:
        supabase_service.save_generation(
            user_id=payload.user_id,
            file_type=payload.file_type,
            output_data=payload.output_data
        )
        return {"status": "success", "message": "Saved to database successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
async def get_generation_history(user_id: str):
    try:
        history = supabase_service.get_user_generations(user_id)
        return {
            "status": "success",
            "data": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))