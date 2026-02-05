#!/usr/bin/env python3
"""
Test script to verify blacklist functionality
"""

import json
import os

def is_user_blacklisted(identity):
    """
    Test version of blacklist check - copied from service.py
    """
    # CRITICAL: If identity is None or empty, reject to be safe
    if not identity or not identity.strip():
        return True
    
    blacklist_path = os.path.join(os.path.dirname(__file__), "blacklist.json")
    
    # Normaliser l'identité (remplacer _ par .)
    normalized_identity = identity.lower().replace("_", ".")
    
    try:
        with open(blacklist_path, "r") as f:
            data = json.load(f)
            blocked_users = data.get("blocked_users", [])
            # Normaliser aussi les entrées de la blacklist
            normalized_blocked = [u.lower().replace("_", ".") for u in blocked_users]
            return normalized_identity in normalized_blocked
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def test_blacklist():
    """Test the blacklist function"""
    
    print("Testing blacklist functionality...")
    print("=" * 60)
    
    # Test 1: Blacklisted user (antoine.beltz)
    print("\n1. Testing blacklisted user 'antoine.beltz':")
    result = is_user_blacklisted("antoine.beltz")
    print(f"   Result: {result}")
    assert result == True, "FAILED: antoine.beltz should be blacklisted!"
    print("   ✓ PASSED")
    
    # Test 2: Blacklisted user with underscore (should normalize)
    print("\n2. Testing blacklisted user 'antoine_beltz' (with underscore):")
    result = is_user_blacklisted("antoine_beltz")
    print(f"   Result: {result}")
    assert result == True, "FAILED: antoine_beltz should be normalized and blacklisted!"
    print("   ✓ PASSED")
    
    # Test 3: Another blacklisted user
    print("\n3. Testing another blacklisted user 'eugene.lepan':")
    result = is_user_blacklisted("eugene.lepan")
    print(f"   Result: {result}")
    assert result == True, "FAILED: eugene.lepan should be blacklisted!"
    print("   ✓ PASSED")
    
    # Test 4: Non-blacklisted user
    print("\n4. Testing non-blacklisted user 'jean.dupont':")
    result = is_user_blacklisted("jean.dupont")
    print(f"   Result: {result}")
    assert result == False, "FAILED: jean.dupont should NOT be blacklisted!"
    print("   ✓ PASSED")
    
    # Test 5: None value (should be treated as blacklisted for security)
    print("\n5. Testing None value:")
    result = is_user_blacklisted(None)
    print(f"   Result: {result}")
    assert result == True, "FAILED: None should be treated as blacklisted!"
    print("   ✓ PASSED")
    
    # Test 6: Empty string (should be treated as blacklisted for security)
    print("\n6. Testing empty string:")
    result = is_user_blacklisted("")
    print(f"   Result: {result}")
    assert result == True, "FAILED: Empty string should be treated as blacklisted!"
    print("   ✓ PASSED")
    
    # Test 7: Whitespace only (should be treated as blacklisted for security)
    print("\n7. Testing whitespace-only string:")
    result = is_user_blacklisted("   ")
    print(f"   Result: {result}")
    assert result == True, "FAILED: Whitespace should be treated as blacklisted!"
    print("   ✓ PASSED")
    
    # Test 8: Case sensitivity (blacklist should be case-insensitive)
    print("\n8. Testing case insensitivity 'Antoine.Beltz':")
    result = is_user_blacklisted("Antoine.Beltz")
    print(f"   Result: {result}")
    assert result == True, "FAILED: Should be case-insensitive!"
    print("   ✓ PASSED")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_blacklist()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
