from tools.destination_rag import search_destination_guide

def test_empty_query_returns_no_results():
    assert search_destination_guide("") == []

def test_search_finds_bangkok_guide():
    results = search_destination_guide("Bangkok temple clothing and customs")
    assert results
    assert any("bangkok.txt" in result.lower() for result in results)
