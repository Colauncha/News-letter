from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from ..schemas import PaginatedResponse
from ..schemas.subcribers_schema import SubscriberCreate, SubscriberRead, SubscriberUpdate
from ..dependencies import get_subscriber_model
from ..collections.subscribers import Subscriber

router = APIRouter(prefix="/subscribers", tags=["Subscribers"])


@router.post("/", response_model=dict[str, SubscriberRead | str], status_code=status.HTTP_201_CREATED)
async def create_subscriber(
    payload: SubscriberCreate,
    subscriber_model: Subscriber = Depends(get_subscriber_model)
):
    if subscriber_model.exists({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Subscriber already exists")
    new = subscriber_model.create(payload)
    return {
        "message": "Subscribed successfully",
        "data": new
    }


@router.get("/{subscriber_id}", response_model=SubscriberRead)
async def get_subscriber(
    subscriber_id: str,
    subscriber_model: Subscriber = Depends(get_subscriber_model)
):
    subscriber = subscriber_model.get_by_id(subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return subscriber


@router.get("/", response_model=PaginatedResponse[SubscriberRead])
async def list_subscribers(
    skip: int = 0,
    limit: int = 50,
    subscriber_model: Subscriber = Depends(get_subscriber_model)
):
    return subscriber_model.list(skip=skip, limit=limit)


@router.put("/{subscriber_id}", response_model=bool)
async def update_subscriber(
    subscriber_id: str,
    payload: SubscriberUpdate,
    subscriber_model: Subscriber = Depends(get_subscriber_model)
):
    payload.updated_at = payload.updated_at or datetime.now(timezone.utc)
    updated = subscriber_model.update(subscriber_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Subscriber not found or no changes made")
    return updated


@router.delete("/{subscriber_id}", response_model=bool)
async def delete_subscriber(
    subscriber_id: str,
    subscriber_model: Subscriber = Depends(get_subscriber_model)
):
    deleted = subscriber_model.delete(subscriber_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return deleted

# Campain retrieval and export endpoints
@router.get("/campaigns/export/csv")
async def export_campaigns_csv(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Maximum records to export (max 10,000)"),
    email_filter: Optional[str] = Query(None, description="Filter by email pattern (e.g., '@gmail.com')"),
    active_only: bool = Query(False, description="Export only users with active campaigns"),
    service=Depends(get_subscriber_model)  # Your service dependency
):
    """
    Export campaign data as CSV file
    
    Query Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records (max 10,000)
    - email_filter: Filter emails containing this string
    - active_only: Only export users with at least one active campaign
    """
    try:
        # Build query filter
        query_filter = {}
        
        if email_filter:
            query_filter["email"] = {"$regex": email_filter, "$options": "i"}
        
        if active_only:
            query_filter["$or"] = [
                {"campaigns.updates": True},
                {"campaigns.marketing": True},
                {"campaigns.announcements": True},
                {"campaigns.newsletters": True},
                {"campaigns.seasonal": True}
            ]
        
        # Get data from database using existing list method
        paginated_response = service.list(
            filters=query_filter, 
            skip=skip, 
            limit=limit or 10000  # Default limit if none provided
        )
        
        if not paginated_response.items:
            raise HTTPException(status_code=404, detail="No records found matching the criteria")
        
        # Generate CSV content from paginated response items
        csv_content = service._create_csv_content(paginated_response.items)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"campaigns_export_{timestamp}.csv"
        
        # Return streaming response
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/campaigns/export/csv/stream")
async def export_campaigns_csv_stream(
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1, le=50000),
    email_filter: Optional[str] = Query(None),
    active_only: bool = Query(False),
    batch_size: int = Query(1000, ge=100, le=5000, description="Batch size for streaming"),
    service=Depends(get_subscriber_model)
):
    """
    Stream large CSV exports in batches for better memory efficiency
    """
    try:
        # Build query filter
        query_filter = {}
        
        if email_filter:
            query_filter["email"] = {"$regex": email_filter, "$options": "i"}
        
        if active_only:
            query_filter["$or"] = [
                {"campaigns.updates": True},
                {"campaigns.marketing": True},
                {"campaigns.announcements": True},
                {"campaigns.newsletters": True},
                {"campaigns.seasonal": True}
            ]
        
        async def generate_csv():
            """Generator function to stream CSV data in batches"""
            # Write CSV headers first
            headers = ['id', 'email', 'updates', 'marketing', 'announcements', 'newsletters', 'seasonal']
            yield ','.join(headers) + '\n'
            
            current_skip = skip
            total_processed = 0
            
            while True:
                # Fetch batch using existing list method
                paginated_response = service.list(
                    filters=query_filter,
                    skip=current_skip,
                    limit=min(batch_size, (limit - total_processed) if limit else batch_size)
                )
                
                if not paginated_response.items:
                    break
                
                # Convert batch to CSV rows
                for item in paginated_response.items:
                    campaigns = item.campaigns
                    
                    row_data = [
                        str(item.id),
                        item.email,
                        str(campaigns.updates if campaigns else False),
                        str(campaigns.marketing if campaigns else False),
                        str(campaigns.announcements if campaigns else False),
                        str(campaigns.newsletters if campaigns else False),
                        str(campaigns.seasonal if campaigns else False)
                    ]
                    
                    # Escape CSV values and join
                    escaped_row = []
                    for value in row_data:
                        if ',' in value or '"' in value or '\n' in value:
                            escaped_row.append(f"""\"{value.replace('"', '""')}\"""")
                        else:
                            escaped_row.append(value)
                    
                    yield ','.join(escaped_row) + '\n'
                
                total_processed += len(paginated_response.items)
                current_skip += len(paginated_response.items)
                
                # Check if we've reached the limit
                if limit and total_processed >= limit:
                    break
                
                # Check if we got fewer items than requested (end of data)
                if len(paginated_response.items) < batch_size:
                    break
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"campaigns_export_stream_{timestamp}.csv"
        
        return StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming export failed: {str(e)}")

# Specialized export endpoints

@router.get("/campaigns/export/csv/active")
async def export_active_campaigns_csv(
    service=Depends(get_subscriber_model)
):
    """Export only users with active campaigns"""
    
    query_filter = {
        "$or": [
            {"campaigns.updates": True},
            {"campaigns.marketing": True},
            {"campaigns.announcements": True},
            {"campaigns.newsletters": True},
            {"campaigns.seasonal": True}
        ]
    }
    
    try:
        paginated_response = service.list(filters=query_filter)
        
        if not paginated_response.items:
            raise HTTPException(status_code=404, detail="No active campaigns found")
        
        csv_content = service._create_csv_content(paginated_response.items)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"active_campaigns_{timestamp}.csv"
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/campaigns/export/csv/by-campaign/{campaign_type}")
async def export_by_campaign_type(
    campaign_type: str,
    enabled: bool = Query(True, description="Filter by enabled/disabled campaigns"),
    service=Depends(get_subscriber_model)
):
    """
    Export users filtered by specific campaign type
    
    Path Parameters:
    - campaign_type: updates, marketing, announcements, newsletters, or seasonal
    """
    
    valid_campaigns = ['updates', 'marketing', 'announcements', 'newsletters', 'seasonal']
    if campaign_type not in valid_campaigns:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid campaign type. Must be one of: {', '.join(valid_campaigns)}"
        )
    
    query_filter = {f"campaigns.{campaign_type}": enabled}
    
    try:
        paginated_response = service.list(filters=query_filter)
        
        if not paginated_response.items:
            status = "enabled" if enabled else "disabled"
            raise HTTPException(
                status_code=404, 
                detail=f"No users found with {campaign_type} campaigns {status}"
            )
        
        csv_content = service._create_csv_content(paginated_response.items)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        status_suffix = "enabled" if enabled else "disabled"
        filename = f"{campaign_type}_campaigns_{status_suffix}_{timestamp}.csv"
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")