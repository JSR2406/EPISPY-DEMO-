"""Marketplace API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime

from ...database.connection import get_db
from ...database.resource_models import (
    ResourceProvider, ResourceInventory, ResourceRequest, ResourceMatch,
    ResourceTransfer, VolunteerStaff, StaffDeployment,
    ProviderType, ResourceType, UrgencyLevel, MatchStatus, TransferStatus,
    QualityGrade
)
from ...marketplace.matching_engine import ResourceMatchingEngine
from ..schemas.marketplace import (
    ProviderCreate, ProviderResponse, InventoryCreate, InventoryUpdate,
    InventoryResponse, RequestCreate, RequestResponse, MatchResponse,
    TransferResponse, VolunteerCreate, VolunteerResponse, DeploymentCreate,
    MarketplaceOverview, SupplyDemandAnalytics,
    ProviderTypeEnum, ResourceTypeEnum, UrgencyLevelEnum, QualityGradeEnum
)
from ...utils.logger import api_logger

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


def _convert_provider_type(enum_val: ProviderTypeEnum) -> ProviderType:
    """Convert API enum to database enum."""
    return ProviderType[enum_val.value]


def _convert_resource_type(enum_val: ResourceTypeEnum) -> ResourceType:
    """Convert API enum to database enum."""
    return ResourceType[enum_val.value]


def _convert_urgency(enum_val: UrgencyLevelEnum) -> UrgencyLevel:
    """Convert API enum to database enum."""
    return UrgencyLevel[enum_val.value]


# ============================================================================
# Provider Endpoints
# ============================================================================

@router.post("/providers", response_model=ProviderResponse)
async def create_provider(
    provider_data: ProviderCreate,
    db: AsyncSession = Depends(get_db)
) -> ProviderResponse:
    """Register a new resource provider."""
    try:
        provider = ResourceProvider(
            name=provider_data.name,
            provider_type=_convert_provider_type(provider_data.provider_type),
            location_id=UUID(provider_data.location_id) if provider_data.location_id else None,
            contact_info=provider_data.contact_info,
            verified=False,
        )
        
        db.add(provider)
        await db.commit()
        await db.refresh(provider)
        
        return ProviderResponse(
            id=str(provider.id),
            name=provider.name,
            provider_type=provider.provider_type.value,
            location_id=str(provider.location_id) if provider.location_id else None,
            verified=provider.verified,
            rating=provider.rating or 0.0,
            total_transactions=provider.total_transactions,
            created_at=provider.created_at,
        )
    except Exception as e:
        await db.rollback()
        api_logger.error(f"Error creating provider: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db)
) -> ProviderResponse:
    """Get provider details."""
    result = await db.execute(
        select(ResourceProvider).where(ResourceProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return ProviderResponse(
        id=str(provider.id),
        name=provider.name,
        provider_type=provider.provider_type.value,
        location_id=str(provider.location_id) if provider.location_id else None,
        verified=provider.verified,
        rating=provider.rating or 0.0,
        total_transactions=provider.total_transactions,
        created_at=provider.created_at,
    )


# ============================================================================
# Inventory Endpoints
# ============================================================================

@router.post("/inventory", response_model=InventoryResponse)
async def add_inventory(
    provider_id: str,
    inventory_data: InventoryCreate,
    db: AsyncSession = Depends(get_db)
) -> InventoryResponse:
    """Add inventory item to provider."""
    try:
        # Verify provider exists
        result = await db.execute(
            select(ResourceProvider).where(ResourceProvider.id == provider_id)
        )
        provider = result.scalar_one_or_none()
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        inventory = ResourceInventory(
            provider_id=UUID(provider_id),
            resource_type=_convert_resource_type(inventory_data.resource_type),
            quantity_available=inventory_data.quantity_available,
            unit_price=inventory_data.unit_price,
            currency=inventory_data.currency,
            quality_grade=QualityGrade[inventory_data.quality_grade.value] if inventory_data.quality_grade else None,
            expiry_date=inventory_data.expiry_date,
            certification_info=inventory_data.certification_info,
            description=inventory_data.description,
        )
        
        db.add(inventory)
        await db.commit()
        await db.refresh(inventory)
        
        return InventoryResponse(
            id=str(inventory.id),
            provider_id=str(inventory.provider_id),
            resource_type=inventory.resource_type.value,
            quantity_available=inventory.quantity_available,
            quantity_reserved=inventory.quantity_reserved,
            unit_price=float(inventory.unit_price) if inventory.unit_price else None,
            currency=inventory.currency,
            quality_grade=inventory.quality_grade.value if inventory.quality_grade else None,
            expiry_date=inventory.expiry_date,
            is_active=inventory.is_active,
            created_at=inventory.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        api_logger.error(f"Error adding inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/inventory/{inventory_id}", response_model=InventoryResponse)
async def update_inventory(
    inventory_id: str,
    inventory_data: InventoryUpdate,
    db: AsyncSession = Depends(get_db)
) -> InventoryResponse:
    """Update inventory item."""
    try:
        result = await db.execute(
            select(ResourceInventory).where(ResourceInventory.id == inventory_id)
        )
        inventory = result.scalar_one_or_none()
        
        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")
        
        # Update fields
        if inventory_data.quantity_available is not None:
            inventory.quantity_available = inventory_data.quantity_available
        if inventory_data.unit_price is not None:
            inventory.unit_price = inventory_data.unit_price
        if inventory_data.quality_grade is not None:
            inventory.quality_grade = QualityGrade[inventory_data.quality_grade.value]
        if inventory_data.expiry_date is not None:
            inventory.expiry_date = inventory_data.expiry_date
        if inventory_data.is_active is not None:
            inventory.is_active = inventory_data.is_active
        if inventory_data.description is not None:
            inventory.description = inventory_data.description
        
        await db.commit()
        await db.refresh(inventory)
        
        return InventoryResponse(
            id=str(inventory.id),
            provider_id=str(inventory.provider_id),
            resource_type=inventory.resource_type.value,
            quantity_available=inventory.quantity_available,
            quantity_reserved=inventory.quantity_reserved,
            unit_price=float(inventory.unit_price) if inventory.unit_price else None,
            currency=inventory.currency,
            quality_grade=inventory.quality_grade.value if inventory.quality_grade else None,
            expiry_date=inventory.expiry_date,
            is_active=inventory.is_active,
            created_at=inventory.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        api_logger.error(f"Error updating inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/my-listings", response_model=List[InventoryResponse])
async def get_my_listings(
    provider_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[InventoryResponse]:
    """Get all inventory listings for a provider."""
    result = await db.execute(
        select(ResourceInventory)
        .where(ResourceInventory.provider_id == provider_id)
        .order_by(ResourceInventory.created_at.desc())
    )
    inventory_items = result.scalars().all()
    
    return [
        InventoryResponse(
            id=str(item.id),
            provider_id=str(item.provider_id),
            resource_type=item.resource_type.value,
            quantity_available=item.quantity_available,
            quantity_reserved=item.quantity_reserved,
            unit_price=float(item.unit_price) if item.unit_price else None,
            currency=item.currency,
            quality_grade=item.quality_grade.value if item.quality_grade else None,
            expiry_date=item.expiry_date,
            is_active=item.is_active,
            created_at=item.created_at,
        )
        for item in inventory_items
    ]


# ============================================================================
# Request Endpoints
# ============================================================================

@router.post("/requests", response_model=RequestResponse)
async def create_request(
    requester_id: str,
    request_data: RequestCreate,
    db: AsyncSession = Depends(get_db)
) -> RequestResponse:
    """Create a resource request."""
    try:
        # Verify requester exists
        result = await db.execute(
            select(ResourceProvider).where(ResourceProvider.id == requester_id)
        )
        requester = result.scalar_one_or_none()
        if not requester:
            raise HTTPException(status_code=404, detail="Requester not found")
        
        request = ResourceRequest(
            requester_id=UUID(requester_id),
            resource_type=_convert_resource_type(request_data.resource_type),
            quantity_needed=request_data.quantity_needed,
            urgency=_convert_urgency(request_data.urgency),
            location_id=UUID(request_data.location_id) if request_data.location_id else None,
            deadline=request_data.deadline,
            description=request_data.description,
            status="OPEN",
        )
        
        db.add(request)
        await db.commit()
        await db.refresh(request)
        
        # Trigger matching
        matching_engine = ResourceMatchingEngine(db)
        await matching_engine.match_requests_to_inventory(request_id=str(request.id))
        
        return RequestResponse(
            id=str(request.id),
            requester_id=str(request.requester_id),
            resource_type=request.resource_type.value,
            quantity_needed=request.quantity_needed,
            quantity_fulfilled=request.quantity_fulfilled,
            urgency=request.urgency.value,
            location_id=str(request.location_id) if request.location_id else None,
            deadline=request.deadline,
            status=request.status,
            priority_score=request.priority_score,
            created_at=request.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        api_logger.error(f"Error creating request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/{request_id}/matches", response_model=List[MatchResponse])
async def get_request_matches(
    request_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[MatchResponse]:
    """Get matches for a request."""
    result = await db.execute(
        select(ResourceMatch)
        .where(ResourceMatch.request_id == request_id)
        .where(ResourceMatch.status == MatchStatus.PENDING)
        .order_by(ResourceMatch.match_score.desc())
    )
    matches = result.scalars().all()
    
    match_responses = []
    for match in matches:
        # Get provider name
        prov_result = await db.execute(
            select(ResourceProvider).where(ResourceProvider.id == match.provider_id)
        )
        provider = prov_result.scalar_one_or_none()
        
        match_responses.append(
            MatchResponse(
                id=str(match.id),
                request_id=str(match.request_id),
                inventory_id=str(match.inventory_id),
                provider_id=str(match.provider_id),
                quantity_matched=match.quantity_matched,
                match_score=match.match_score,
                status=match.status.value,
                accepted_at=match.accepted_at,
                created_at=match.created_at,
                provider_name=provider.name if provider else None,
                inventory_details=match.metadata_json,
            )
        )
    
    return match_responses


@router.post("/requests/{request_id}/accept-match")
async def accept_match(
    request_id: str,
    match_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Accept a match for a request."""
    try:
        result = await db.execute(
            select(ResourceMatch).where(ResourceMatch.id == match_id)
        )
        match = result.scalar_one_or_none()
        
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        if match.request_id != UUID(request_id):
            raise HTTPException(status_code=400, detail="Match does not belong to request")
        
        if match.status != MatchStatus.PENDING:
            raise HTTPException(status_code=400, detail="Match already processed")
        
        # Update match status
        match.status = MatchStatus.ACCEPTED
        match.accepted_at = datetime.now()
        
        # Reserve inventory
        inv_result = await db.execute(
            select(ResourceInventory).where(ResourceInventory.id == match.inventory_id)
        )
        inventory = inv_result.scalar_one_or_none()
        if inventory:
            inventory.quantity_reserved += match.quantity_matched
        
        # Update request
        req_result = await db.execute(
            select(ResourceRequest).where(ResourceRequest.id == request_id)
        )
        request = req_result.scalar_one_or_none()
        if request:
            request.quantity_fulfilled += match.quantity_matched
            if request.quantity_fulfilled >= request.quantity_needed:
                request.status = "FULFILLED"
        
        # Create transfer
        transfer = ResourceTransfer(
            match_id=match.id,
            from_location_id=inventory.provider.location_id if inventory and inventory.provider else None,
            to_location_id=request.location_id if request else None,
            quantity=match.quantity_matched,
            status=TransferStatus.SCHEDULED,
        )
        db.add(transfer)
        
        await db.commit()
        
        return {"message": "Match accepted", "match_id": match_id, "transfer_id": str(transfer.id)}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        api_logger.error(f"Error accepting match: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Dashboard & Analytics
# ============================================================================

@router.get("/dashboard/overview", response_model=MarketplaceOverview)
async def get_marketplace_overview(
    db: AsyncSession = Depends(get_db)
) -> MarketplaceOverview:
    """Get marketplace overview statistics."""
    from sqlalchemy import func
    
    # Count providers
    prov_result = await db.execute(select(func.count(ResourceProvider.id)))
    total_providers = prov_result.scalar() or 0
    
    # Count inventory
    inv_result = await db.execute(select(func.count(ResourceInventory.id)))
    total_inventory = inv_result.scalar() or 0
    
    # Count requests
    req_result = await db.execute(select(func.count(ResourceRequest.id)))
    total_requests = req_result.scalar() or 0
    
    open_req_result = await db.execute(
        select(func.count(ResourceRequest.id))
        .where(ResourceRequest.status == "OPEN")
    )
    open_requests = open_req_result.scalar() or 0
    
    # Count matches
    match_result = await db.execute(
        select(func.count(ResourceMatch.id))
        .where(ResourceMatch.status == MatchStatus.ACCEPTED)
    )
    active_matches = match_result.scalar() or 0
    
    # Count transfers
    trans_result = await db.execute(
        select(func.count(ResourceTransfer.id))
        .where(ResourceTransfer.status.in_([TransferStatus.SCHEDULED, TransferStatus.IN_TRANSIT]))
    )
    pending_transfers = trans_result.scalar() or 0
    
    # Count volunteers
    vol_result = await db.execute(select(func.count(VolunteerStaff.id)))
    total_volunteers = vol_result.scalar() or 0
    
    # Count deployments
    dep_result = await db.execute(
        select(func.count(StaffDeployment.id))
        .where(StaffDeployment.status == "ACTIVE")
    )
    active_deployments = dep_result.scalar() or 0
    
    return MarketplaceOverview(
        total_providers=total_providers,
        total_inventory_items=total_inventory,
        total_requests=total_requests,
        open_requests=open_requests,
        active_matches=active_matches,
        pending_transfers=pending_transfers,
        total_volunteers=total_volunteers,
        active_deployments=active_deployments,
    )


@router.get("/predictions/resource-needs")
async def get_resource_predictions(
    location_id: str,
    days_ahead: int = Query(14, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get predicted resource needs for a location."""
    matching_engine = ResourceMatchingEngine(db)
    predictions = await matching_engine.predict_future_needs(location_id, days_ahead)
    return predictions


# ============================================================================
# Volunteer Endpoints
# ============================================================================

@router.post("/volunteers", response_model=VolunteerResponse)
async def register_volunteer(
    volunteer_data: VolunteerCreate,
    db: AsyncSession = Depends(get_db)
) -> VolunteerResponse:
    """Register a volunteer."""
    try:
        volunteer = VolunteerStaff(
            name=volunteer_data.name,
            email=volunteer_data.email,
            phone=volunteer_data.phone,
            specialization=volunteer_data.specialization,
            certifications=volunteer_data.certifications,
            availability_dates=volunteer_data.availability_dates,
            location_preferences=volunteer_data.location_preferences,
            max_distance_km=volunteer_data.max_distance_km,
            verified=False,
        )
        
        db.add(volunteer)
        await db.commit()
        await db.refresh(volunteer)
        
        return VolunteerResponse(
            id=str(volunteer.id),
            name=volunteer.name,
            email=volunteer.email,
            specialization=volunteer.specialization,
            verified=volunteer.verified,
            total_hours=volunteer.total_hours,
            rating=volunteer.rating or 0.0,
            is_active=volunteer.is_active,
        )
    except Exception as e:
        await db.rollback()
        api_logger.error(f"Error registering volunteer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

