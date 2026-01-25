
from src.payments.schemas import CheckoutResponse

def test_checkout_response_validation():
    # This should no longer raise a validation error even if we pass an int, 
    # but the router now passes result["id"] which we fixed to be a string.
    # Let's test if CheckoutResponse handles it or if our fix works.
    
    try:
        # Before fix, result["id"] was 169631 (int)
        # Now it is "169631" (str)
        data = {
            "redirect_url": "https://example.com",
            "checkout_intent_id": "169631"
        }
        res = CheckoutResponse(**data)
        print(f"Validation successful: {res}")
    except Exception as e:
        print(f"Validation failed: {e}")

if __name__ == "__main__":
    test_checkout_response_validation()
