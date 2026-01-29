
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock

# Force addition of /app to sys.path for Docker
sys.path.append("/app")

from src.auth.service import normalize_email, request_verification_code, ALLOWED_DOMAINS
from src.users.models import User
from src.db.base import Base
from src.core.exceptions import InvalidEmailException

# Setup in-memory DB
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

async def test_normalization():
    print("--- Testing Email Normalization ---")
    
    # Test valid formats
    valid_cases = [
        ("jean.valjean@imt-bs.eu", "jean.valjean@imt-bs.eu", "jean.valjean"),
        ("jean_valjean@it-sudparis.eu", "jean_valjean@it-sudparis.eu", "jean.valjean"),
        ("JEAN.VALJEAN@TELECOM-SUDPARIS.EU", "jean.valjean@telecom-sudparis.eu", "jean.valjean"),
    ]
    
    for email, expected_delivery, expected_identity in valid_cases:
        delivery, identity = normalize_email(email)
        assert delivery == expected_delivery, f"Expected {expected_delivery}, got {delivery}"
        assert identity == expected_identity, f"Expected {expected_identity}, got {identity}"
        print(f"✅ {email} -> {delivery} | {identity}")

    # Test invalid formats
    invalid_cases = [
        "jean.valjean@gmail.com",      # Invalid domain
        "jean.valjean+alias@imt-bs.eu", # Alias blocked
        "valjean@imt-bs.eu",           # No separator
        "jeanvaljean@imt-bs.eu",       # No separator
    ]
    
    for email in invalid_cases:
        try:
            normalize_email(email)
            print(f"❌ {email} should have been invalid")
        except InvalidEmailException as e:
            print(f"✅ {email} correctly blocked: {e}")

async def test_deduplication():
    print("\n--- Testing User Deduplication ---")
    db = SessionLocal()
    
    # Mock settings and send_verification_email
    import src.auth.service as auth_service
    from unittest.mock import AsyncMock
    auth_service.send_verification_email = AsyncMock()
    
    # 1. Register with dot
    await request_verification_code("jean.valjean@imt-bs.eu", db)
    user1 = db.query(User).filter(User.normalized_email == "jean.valjean").first()
    assert user1 is not None
    assert user1.email == "jean.valjean@imt-bs.eu"
    assert user1.normalized_email == "jean.valjean"
    print("✅ Registered jean.valjean@imt-bs.eu")

    # 2. Register same person with underscore and different domain
    await request_verification_code("jean_valjean@it-sudparis.eu", db)
    user2 = db.query(User).filter(User.normalized_email == "jean.valjean").first()
    assert user2.id == user1.id
    assert user2.email == "jean_valjean@it-sudparis.eu" # Should update delivery email
    
    all_users = db.query(User).all()
    assert len(all_users) == 1
    print("✅ Correctly matched jean_valjean@it-sudparis.eu to existing user")

    db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_normalization())
    asyncio.run(test_deduplication())
