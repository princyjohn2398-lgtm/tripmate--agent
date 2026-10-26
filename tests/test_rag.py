from tools.destination_rag import search_destination_guide

def test_empty_query_returns_no_results():
    assert search_destination_guide("") == []

def test_search_finds_bangkok_guide():
    results = search_destination_guide("Bangkok temple clothing and customs")
    assert results
    assert any("bangkok.txt" in result.lower() for result in results)


def test_city_in_query_returns_only_that_city():
    results = search_destination_guide("Bangkok December weather packing", top_k=5)
    assert results
    assert all("bangkok.txt" in r.lower() for r in results)
