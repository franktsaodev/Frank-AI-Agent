from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    tags=[
        "Health",
    ],
)
def health() -> dict[str, str]:
    return {
        "status": "ok",
    }
