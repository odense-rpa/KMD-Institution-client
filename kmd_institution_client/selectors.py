class KMDSelectors:
    """Playwright selectors for KMD Institution og kommunens IdP-login."""

    class Login:
        # "Log ind"-knap på Fælleskommunal-siden (vises kun hvis man ikke allerede har en session)
        FAELLESKOMMUNAL_KNAP = "a.btn[role='button']"
        # Dropdown og OK-knap hvor kommunens IdP vælges
        IDP_SELECT = "select#SelectedAuthenticationUrl"
        IDP_OK_BUTTON = "input[type='button'][value='OK']"
        # Microsoft-login hos kommunen
        USERNAME_INPUT = 'input[name="loginfmt"]'
        PASSWORD_INPUT = 'input[name="passwd"]'
        SUBMIT_BUTTON = 'input[type="submit"]'
