from kmd_institution_client import KMDInstitutionClientManager


def test_find_indmeldelser(kmd_institution_manager: KMDInstitutionClientManager):

    # First get an institution to use in the search
    institution = kmd_institution_manager.institutioner_og_grupper.hent_institution("Tilskud til pasning af egne bø")
    
    assert institution is not None

    fra_dato = "2025-09-01T00:00:00" 
    
    # Test find_indmeldelser method
    result = kmd_institution_manager.indmeldelser.find_indmeldelser(institution, udmeldelsesdato_fra=fra_dato)
    
    assert result is not None
    assert result[0]["endDate"] 
    assert result[0]["startDate"]

    # Assert at fra_dato er mellem endDate and startDate
    assert result[0]["endDate"] >= fra_dato >= result[0]["startDate"] 