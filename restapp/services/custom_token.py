from datetime import datetime,timedelta,timezone
import jwt
from django.conf import settings
# Generate Account Verification Token
def generate_account_verification_token(user):
    """
    Generates a time-limited JWT token for email verification.

    This function creates a JSON Web Token (JWT) that includes the user ID and
    an expiration timestamp, which is set to 24 hours from the time of generation.
    This token can be used for verifying a user's account within the specified timeframe.

    Parameters:
    - user: The user object for which the token is being generated.

    Returns:
    - str: Encoded JWT token as a string, containing the user ID and expiration time.

    Usage:
    - Call this function with a user instance to generate a token, then include the token 
      in the email verification link.
    - The token will expire 24 hours after its creation, enforcing a strict timeframe
      for verification actions.

    Example:
    >>> token = generate_verification_token(user)
    """
    expiration_time = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        'user_id': user.id,
        'exp': expiration_time
    }
    # Generate a token using your secret key
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

