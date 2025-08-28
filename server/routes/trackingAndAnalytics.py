from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import get_analytics_model
from ..collections.trackingAndAnalytics import TrackerAndAnalytics

router = APIRouter(prefix="/tracking", tags=["Tracking and Analytics"])

@router.post("/visitors")
def increase_visitor_count(
    analytics: TrackerAndAnalytics = Depends(get_analytics_model)
):
    try:
        return analytics.increase_visitor_count()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/visitors/count")
def get_visitor_count(
    analytics: TrackerAndAnalytics = Depends(get_analytics_model)
):
    try:
        return {
            "count": analytics.get_visitor_count(),
            "nonunique_count": analytics.get_non_unique_visitor_count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visitors/unique")
def get_unique_visitors(
    start_date: Optional[datetime] = Query(None, description="Start date for unique visitors"),
    end_date: Optional[datetime] = Query(None, description="End date for unique visitors"),
    analytics: TrackerAndAnalytics = Depends(get_analytics_model)
):
    try:
        return analytics.get_unique_visitors(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visitors/unique/count")
def get_unique_visitor_count(
    start_date: Optional[datetime] = Query(None, description="Start date for unique visitor count"),
    end_date: Optional[datetime] = Query(None, description="End date for unique visitor count"),
    analytics: TrackerAndAnalytics = Depends(get_analytics_model)
):
    try:
        return {"count": analytics.get_unique_visitor_count(start_date, end_date)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/nu/visitors")
def increase_nu_visitor_count(
    analytics: TrackerAndAnalytics = Depends(get_analytics_model)
):
    try:
        return analytics.increase_non_unique_visitor_count()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/nu/visitors/count")
def get_nu_visitor_count(
    analytics: TrackerAndAnalytics = Depends(get_analytics_model)
):
    try:
        return {"nonunique_count": analytics.get_non_unique_visitor_count()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visitors/count/range")
def get_visitor_count_range(
    start_date: datetime = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: datetime = Query(..., description="End date in YYYY-MM-DD format"),
    analytics: TrackerAndAnalytics = Depends(get_analytics_model)
):
    try:
        # Ensure dates are timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")
        
        return analytics.get_visitor_count_range(start_date, end_date)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
