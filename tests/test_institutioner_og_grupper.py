from kmd_institution_client import KMDInstitutionClientManager


def test_hent_institutioner(kmd_institution_manager: KMDInstitutionClientManager):

    result = kmd_institution_manager.institutioner_og_grupper.hent_institutioner()
    
    assert result is not None
    
    # Find institution "test" using lambda in one line
    test_institution = next((inst for inst in result if inst["name"] == "Tilskud til pasning af egne bø"), None)
    
    # Test the results
    assert test_institution is not None
    assert test_institution["name"] == "Tilskud til pasning af egne bø"


def test_hent_institution(kmd_institution_manager: KMDInstitutionClientManager):

    # Test the new hent_institution method
    test_institution = kmd_institution_manager.institutioner_og_grupper.hent_institution("Tilskud til pasning af egne bø")
    
    # Test the results
    assert test_institution is not None
    assert test_institution["name"] == "Tilskud til pasning af egne bø"

