from logs.logger import LoggerCacheSingleton

lc = LoggerCacheSingleton()  # unified Logger + Cache

def run_query(query: str):
    """
    Check memory + disk cache first. If missing, run DB/Pinecone/Neo4j call,
    then store result in cache.
    """
    # First check cache
    cached_result = lc.get_persistent_query(query)
    if cached_result is not None:
        return cached_result

    # Simulate DB / Neo4j / Pinecone call
    lc.info(f"Running DB call for query: {query}")
    result = f"Result for {query}"  # Replace with actual DB query

    # Store result in memory + disk
    lc.put_persistent_query(query, result)
    return result
