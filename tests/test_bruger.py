from kmd_institution_client import KMDInstitutionClientManager


def test_hent_egen_bruger(kmd_institution_manager: KMDInstitutionClientManager):

    result = kmd_institution_manager.bruger.hent_egen_bruger()

    assert result is not None