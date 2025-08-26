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
            "non-unique-count": analytics.get_non_unique_visitor_count()
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
        return {"non-unique-count": analytics.get_non_unique_visitor_count()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
