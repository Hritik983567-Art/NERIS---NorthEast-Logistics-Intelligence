from fastapi import APIRouter, HTTPException, status
from app.models.routing import OptimizeRouteRequest, OptimizedRouteResponse
from app.services.routing_engine import get_routing_engine

router = APIRouter(tags=["NERIS Deterministic Route Planner Engine"])

@router.post("/routes/compute", response_model=OptimizedRouteResponse, status_code=status.HTTP_200_OK)
@router.post("/api/routes/compute", response_model=OptimizedRouteResponse, status_code=status.HTTP_200_OK)
@router.post("/api/v1/routes/compute", response_model=OptimizedRouteResponse, status_code=status.HTTP_200_OK)
@router.post("/api/routes/plan", response_model=OptimizedRouteResponse, status_code=status.HTTP_200_OK)
@router.post("/api/v1/routes/plan", response_model=OptimizedRouteResponse, status_code=status.HTTP_200_OK)
@router.post("/api/v1/routing/optimize-route", response_model=OptimizedRouteResponse, status_code=status.HTTP_200_OK)
async def compute_disaster_aware_route(request: OptimizeRouteRequest):
    """
    Consumes real active NERIS incidents from DynamoDB, evaluates terrain/weather/weight risks, 
    and computes primary & alternate routes with explicit operational rationale using deterministic Risk Engine.
    """
    engine = get_routing_engine()
    try:
        response = engine.find_optimal_and_alternate_routes(request)
        return response
    except ValueError as val_err:
        err_msg = str(val_err)
        if "No passable route" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Routing Error: {err_msg}"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation Error: {err_msg}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route computation engine error: {str(e)}"
        )
