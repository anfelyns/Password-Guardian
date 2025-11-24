"""
Backend authentication helper functions
"""


def verify_2fa(email, entered_code, sent_code):
    """
    Verify 2FA code
    
    Args:
        email: User email
        entered_code: Code entered by user
        sent_code: Code that was sent to user
        
    Returns:
        bool: True if codes match
    """

    return entered_code == sent_code
