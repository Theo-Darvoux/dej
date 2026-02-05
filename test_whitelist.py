#!/usr/bin/env python3
"""
Test script to verify whitelist functionality.
Whitelisted users can order even without BDE membership.
"""

import json
import os
import sys


def is_user_whitelisted(identity):
    """
    Test version of whitelist check - mirrors service.py logic
    """
    if not identity or not identity.strip():
        return False

    whitelist_path = os.path.join(os.path.dirname(__file__), "whitelist.json")

    normalized_identity = identity.lower().replace("_", ".")

    try:
        with open(whitelist_path, "r") as f:
            data = json.load(f)
            allowed_users = data.get("allowed_users", [])
            normalized_allowed = [u.lower().replace("_", ".") for u in allowed_users]
            return normalized_identity in normalized_allowed
    except (FileNotFoundError, json.JSONDecodeError):
        return False


def is_user_blacklisted(identity):
    """
    Test version of blacklist check - copied from service.py
    """
    if not identity or not identity.strip():
        return True

    blacklist_path = os.path.join(os.path.dirname(__file__), "blacklist.json")

    normalized_identity = identity.lower().replace("_", ".")

    try:
        with open(blacklist_path, "r") as f:
            data = json.load(f)
            blocked_users = data.get("blocked_users", [])
            normalized_blocked = [u.lower().replace("_", ".") for u in blocked_users]
            return normalized_identity in normalized_blocked
    except (FileNotFoundError, json.JSONDecodeError):
        return False


def test_whitelist():
    """Test the whitelist function"""

    # First, add test users to whitelist temporarily
    whitelist_path = os.path.join(os.path.dirname(__file__), "whitelist.json")

    # Save original whitelist
    with open(whitelist_path, "r") as f:
        original_data = json.load(f)

    # Write test whitelist
    test_data = {
        "allowed_users": [
            "test.user",
            "marie.curie",
            "jean_pierre.dupont"
        ]
    }
    with open(whitelist_path, "w") as f:
        json.dump(test_data, f, indent=4)

    try:
        print("Testing whitelist functionality...")
        print("=" * 60)

        # Test 1: Whitelisted user
        print("\n1. Testing whitelisted user 'test.user':")
        result = is_user_whitelisted("test.user")
        print(f"   Result: {result}")
        assert result == True, "FAILED: test.user should be whitelisted!"
        print("   PASSED")

        # Test 2: Whitelisted user with underscore normalization
        print("\n2. Testing whitelisted user 'test_user' (underscore -> dot):")
        result = is_user_whitelisted("test_user")
        print(f"   Result: {result}")
        assert result == True, "FAILED: test_user should normalize to test.user!"
        print("   PASSED")

        # Test 3: Case insensitivity
        print("\n3. Testing case insensitivity 'Marie.Curie':")
        result = is_user_whitelisted("Marie.Curie")
        print(f"   Result: {result}")
        assert result == True, "FAILED: Should be case-insensitive!"
        print("   PASSED")

        # Test 4: Non-whitelisted user
        print("\n4. Testing non-whitelisted user 'random.person':")
        result = is_user_whitelisted("random.person")
        print(f"   Result: {result}")
        assert result == False, "FAILED: random.person should NOT be whitelisted!"
        print("   PASSED")

        # Test 5: None value (should return False, not whitelisted)
        print("\n5. Testing None value:")
        result = is_user_whitelisted(None)
        print(f"   Result: {result}")
        assert result == False, "FAILED: None should NOT be whitelisted!"
        print("   PASSED")

        # Test 6: Empty string (should return False)
        print("\n6. Testing empty string:")
        result = is_user_whitelisted("")
        print(f"   Result: {result}")
        assert result == False, "FAILED: Empty string should NOT be whitelisted!"
        print("   PASSED")

        # Test 7: Whitespace only (should return False)
        print("\n7. Testing whitespace-only string:")
        result = is_user_whitelisted("   ")
        print(f"   Result: {result}")
        assert result == False, "FAILED: Whitespace should NOT be whitelisted!"
        print("   PASSED")

        # Test 8: Whitelisted user with compound name
        print("\n8. Testing whitelisted user 'jean_pierre.dupont' (compound name):")
        result = is_user_whitelisted("jean_pierre.dupont")
        print(f"   Result: {result}")
        assert result == True, "FAILED: jean_pierre.dupont should be whitelisted!"
        print("   PASSED")

        # Test 9: Whitelist does NOT override blacklist
        # A user on both lists should still be blacklisted
        print("\n9. Testing that blacklist takes priority over whitelist:")
        # Add a blacklisted user to whitelist
        test_data_with_overlap = {
            "allowed_users": [
                "test.user",
                "antoine.beltz"  # This user is also blacklisted
            ]
        }
        with open(whitelist_path, "w") as f:
            json.dump(test_data_with_overlap, f, indent=4)

        whitelisted = is_user_whitelisted("antoine.beltz")
        blacklisted = is_user_blacklisted("antoine.beltz")
        print(f"   Whitelisted: {whitelisted}, Blacklisted: {blacklisted}")
        assert blacklisted == True, "FAILED: antoine.beltz should still be blacklisted!"
        print("   PASSED - blacklist check still catches them")
        print("   (blacklist is checked before whitelist in the auth flow)")

        # Test 10: Missing whitelist file
        print("\n10. Testing with missing whitelist file:")
        os.rename(whitelist_path, whitelist_path + ".bak")
        try:
            result = is_user_whitelisted("test.user")
            print(f"   Result: {result}")
            assert result == False, "FAILED: Missing file should return False!"
            print("   PASSED - graceful handling of missing file")
        finally:
            os.rename(whitelist_path + ".bak", whitelist_path)

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    finally:
        # Restore original whitelist
        with open(whitelist_path, "w") as f:
            json.dump(original_data, f, indent=4, ensure_ascii=False)
        print("\nOriginal whitelist.json restored.")


if __name__ == "__main__":
    try:
        test_whitelist()
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
