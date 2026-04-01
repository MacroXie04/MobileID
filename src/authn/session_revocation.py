"""
Shared tolerances for identifying the current session across access and refresh
tokens.
"""

# Access and refresh tokens are minted together, but the persisted refresh-token
# timestamps can differ by a small amount depending on storage timing. Keep all
# "is this the current session?" checks aligned to the same narrow leeway so we
# do not accidentally revoke or reject a nearby session from another device.
CURRENT_SESSION_IAT_LEEWAY_SECONDS = 2

# Authentication should use the same tolerance as device listing/revocation.
SESSION_REVOCATION_MATCH_WINDOW_SECONDS = CURRENT_SESSION_IAT_LEEWAY_SECONDS
