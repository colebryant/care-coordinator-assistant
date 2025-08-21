import pytest

from provider_repository import ProviderRepository


@pytest.fixture(scope="module")
def repo() -> ProviderRepository:
    r = ProviderRepository()
    r.load()
    return r


def test_load_providers(repo: ProviderRepository):
    assert len(repo.providers) >= 5
    names = [p.name for p in repo.providers]
    assert "Grey, Meredith" in names
    assert "House, Gregory" in names


def test_search_by_specialty(repo: ProviderRepository):
    pcs = repo.search_by_specialty("Primary Care")
    assert {p.specialty for p in pcs} == {"Primary Care"}
    assert any(p.name == "Grey, Meredith" for p in pcs)


def test_search_by_name_exact(repo: ProviderRepository):
    p = repo.search_by_name("House, Gregory")
    assert p is not None
    assert p.name == "House, Gregory"
    assert p.specialty == "Orthopedics"


def test_search_by_name_fuzzy(repo: ProviderRepository):
    # Misspelling / different formatting should still resolve to Meredith Grey
    candidate = "Dr. Meridith Gray"
    p = repo.search_by_name(candidate)
    assert p is not None
    assert p.name == "Grey, Meredith"


def test_get_provider_availability(repo: ProviderRepository):
    avail = repo.get_provider_availability("House, Gregory")
    # Expect two locations for House
    locations = {a["location"] for a in avail}
    assert {"PPTH Orthopedics", "Jefferson Hospital"}.issubset(locations)


def test_get_specialty_availability(repo: ProviderRepository):
    avail = repo.get_specialty_availability("Primary Care")
    assert len(avail) >= 2
    # Each entry should have keys
    for a in avail:
        assert {"provider", "location", "days_available", "hours_available"} <= set(a.keys())


def test_get_provider_availability_on_day(repo: ProviderRepository):
    # Brennan is available Tu/We/Th 10am-4pm at Jefferson Hospital
    day = "Tuesday"
    avail = repo.get_provider_availability_on_day("Brennan, Temperance", day)
    assert len(avail) == 1
    assert avail[0]["location"] == "Jefferson Hospital"
    assert avail[0]["hours_available"] == "10am-4pm"


def test_get_specialty_availability_on_day(repo: ProviderRepository):
    day = "Wednesday"
    avail = repo.get_specialty_availability_on_day("Orthopedics", day)
    # Should include House (PPTH Orthopedics) and Brennan (Jefferson Hospital)
    providers = {(a.get("provider"), a.get("location")) for a in avail}
    assert ("House, Gregory", "PPTH Orthopedics") in providers
    assert ("Brennan, Temperance", "Jefferson Hospital") in providers
