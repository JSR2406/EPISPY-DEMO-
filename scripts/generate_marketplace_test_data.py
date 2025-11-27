"""
Generate test data for marketplace and personalized risk systems.
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from src.database.connection import get_async_session
from src.database.models import Location
from src.database.resource_models import (
    ResourceProvider, ResourceInventory, ResourceRequest,
    ProviderType, ResourceType, UrgencyLevel,
    UserProfile, NotificationPreferences
)


async def generate_test_data():
    """Generate test data for development and testing."""
    async with get_async_session() as session:
        print("Generating test data...")
        
        # Create locations
        locations = []
        location_data = [
            {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "country": "India", "pop": 12442373},
            {"name": "Delhi", "lat": 28.6139, "lon": 77.2090, "country": "India", "pop": 11007835},
            {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946, "country": "India", "pop": 8443675},
        ]
        
        for loc_data in location_data:
            location = Location(
                name=loc_data["name"],
                latitude=loc_data["lat"],
                longitude=loc_data["lon"],
                country=loc_data["country"],
                population=loc_data["pop"],
            )
            session.add(location)
            locations.append(location)
        
        await session.commit()
        print(f"Created {len(locations)} locations")
        
        # Create providers
        providers = []
        for i, location in enumerate(locations):
            provider = ResourceProvider(
                name=f"{location.name} Hospital",
                provider_type=ProviderType.HOSPITAL,
                location_id=location.id,
                verified=True,
                contact_info={"email": f"contact@{location.name.lower()}.com"},
                rating=4.0 + (i * 0.2),
                total_transactions=10 + i * 5,
            )
            session.add(provider)
            providers.append(provider)
        
        # Add suppliers
        supplier = ResourceProvider(
            name="Medical Supply Co.",
            provider_type=ProviderType.SUPPLIER,
            location_id=locations[0].id,
            verified=True,
            rating=4.5,
            total_transactions=50,
        )
        session.add(supplier)
        providers.append(supplier)
        
        await session.commit()
        print(f"Created {len(providers)} providers")
        
        # Create inventory
        inventory_items = []
        resource_types = [
            ResourceType.VENTILATOR,
            ResourceType.ICU_BED,
            ResourceType.OXYGEN_CYLINDER,
            ResourceType.N95_MASK,
        ]
        
        for provider in providers[:3]:  # First 3 providers
            for resource_type in resource_types:
                inventory = ResourceInventory(
                    provider_id=provider.id,
                    resource_type=resource_type,
                    quantity_available=20 + hash(str(provider.id) + str(resource_type)) % 30,
                    unit_price=50000.0 if resource_type == ResourceType.VENTILATOR else 1000.0,
                    currency="USD",
                    is_active=True,
                )
                session.add(inventory)
                inventory_items.append(inventory)
        
        await session.commit()
        print(f"Created {len(inventory_items)} inventory items")
        
        # Create requests
        requests = []
        for i, location in enumerate(locations):
            requester = providers[i] if i < len(providers) else providers[0]
            request = ResourceRequest(
                requester_id=requester.id,
                resource_type=ResourceType.VENTILATOR,
                quantity_needed=5 + i,
                urgency=UrgencyLevel.CRITICAL if i == 0 else UrgencyLevel.URGENT,
                location_id=location.id,
                deadline=datetime.now() + timedelta(days=7 - i),
                status="OPEN",
            )
            session.add(request)
            requests.append(request)
        
        await session.commit()
        print(f"Created {len(requests)} requests")
        
        # Create user profiles
        users = []
        for i in range(5):
            user = UserProfile(
                user_id=f"test_user_{i+1}",
                age_group=["18-30", "31-50", "51-65", "65+"][i % 4],
                comorbidities=[] if i < 2 else ["diabetes", "hypertension"][:i-1],
                vaccination_status={"doses": 2 if i < 3 else 1, "last_dose": "2023-06-01"},
                occupation=["HEALTHCARE", "ESSENTIAL", "REMOTE", "EDUCATION", "RETIRED"][i],
                household_size=1 + (i % 3),
            )
            session.add(user)
            
            # Create notification preferences
            prefs = NotificationPreferences(
                user_id=user.user_id,
                push_enabled=True,
                email_enabled=True,
                sms_enabled=(i % 2 == 0),
            )
            session.add(prefs)
            users.append(user)
        
        await session.commit()
        print(f"Created {len(users)} user profiles")
        
        print("\n✅ Test data generation complete!")
        print(f"   - {len(locations)} locations")
        print(f"   - {len(providers)} providers")
        print(f"   - {len(inventory_items)} inventory items")
        print(f"   - {len(requests)} requests")
        print(f"   - {len(users)} user profiles")


if __name__ == "__main__":
    asyncio.run(generate_test_data())

