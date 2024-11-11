from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from restapp.services.custom_token import generate_account_verification_token
from django.utils.encoding import force_bytes,force_str,DjangoUnicodeDecodeError
from django.core.mail import EmailMessage
from django.conf import settings

def send_verification_email(user):
    """
    Sends an email with an account verification link to the specified user.

    This function generates a JWT token that expires after a set duration (e.g., 1 minute)
    for account verification purposes. It then composes an email with the verification link,
    using an HTML template for the email content. The email includes the user ID and token as
    part of the link, allowing the user to activate their account by following the link.

    Parameters:
    - user: The user object for which the verification email is being sent.

    Returns:
    - EmailMessage: Configured email object ready for sending with the verification link.

    Usage:
    - Call this function with a user instance to create a verification email, then call 
      `email.send()` to dispatch it.

    Example:
    >>> email = send_verification_email(user)
    >>> email.send()

    Note:
    - Ensure that `generate_account_verification_token` is defined and generates a token
      that expires in a reasonable time.
    """
    # Generate token for sending mail
    email_subject = "Activate Your Account"
    message = render_to_string(
        "activate.html",
        {
            'user': user,
            'company': settings.COMPANY,
            'domain': settings.DOMAIN_URL,
            'uid': urlsafe_base64_encode(force_bytes(user.id)),
            # 'token': generate_token.make_token(user)
            'token': generate_account_verification_token(user)
        }
    )
    # Configure and send the email
    email = EmailMessage(
        email_subject,
        message,
        settings.EMAIL_HOST_USER,
        [user.email]
    )
    
    return email