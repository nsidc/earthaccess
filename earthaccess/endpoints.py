"""
Crawls NASA CMR API and maps bucket/prefix keys to S3 credentials endpoints.

Warns about bucket/prefix keys with conflicting endpoints.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Set, Tuple
from collections import defaultdict

# Set up logger for this module
logger = logging.getLogger(__name__)


async def fetch_page(
    session: aiohttp.ClientSession,
    base_url: str,
    page_num: int,
    page_size: int,
    cloud_hosted: bool = True
) -> Tuple[int, list, int]:
    """Fetch a single page from CMR API.

    Parameters:
        session: Active aiohttp client session for making HTTP requests.
        base_url: CMR API endpoint URL.
        page_num: Page number to fetch (1-indexed).
        page_size: Number of results per page.
        cloud_hosted: Filter for cloud-hosted collections only. Defaults to True.

    Returns:
        Tuple of (page_num, items, total_hits) where items is a list of collection
        records and total_hits is the total number of results available.
    """
    params = {
        "page_size": page_size,
        "page_num": page_num
    }

    if cloud_hosted:
        params["cloud_hosted"] = True
    
    try:
        async with session.get(base_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
            response.raise_for_status()
            data = await response.json()
            items = data.get("items", [])
            total_hits = int(response.headers.get("CMR-Hits", 0))

            logger.debug(f"Successfully fetched page {page_num}: {len(items)} items")
            return page_num, items, total_hits

    except Exception as e:
        logger.error(f"Error fetching page {page_num}: {e}")
        return page_num, [], 0


async def query_cmr_async(
    base_url: str = "https://cmr.earthdata.nasa.gov/search/collections.umm_json",
    cloud_hosted: bool = True,
    page_size: int = 100,
    concurrent_requests: int = 10,
    max_results: int | None = None
) -> Dict[str, Dict]:
    """Asynchronously query CMR API and collect DirectDistributionInformation.

    The function automatically queries the API to determine total available results,
    then fetches all pages concurrently (or up to max_results if specified).

    Parameters:
        base_url: CMR API endpoint. Defaults to the NASA CMR collections endpoint.
        cloud_hosted: Filter for cloud-hosted collections. Defaults to True.
        page_size: Results per page (default: 100, max: 2000).
        concurrent_requests: Number of concurrent API requests. Defaults to 10.
        max_results: Optional limit on total results to fetch. If None, fetches all
            available results.

    Returns:
        Dictionary mapping concept_id to DirectDistributionInformation.
    """

    logger.info(f"Starting CMR query: {page_size=}, {concurrent_requests=}")

    results = {}

    async with aiohttp.ClientSession() as session:
        # First, fetch page 1 to get total hits and start collecting data
        _, items, total_hits = await fetch_page(session, base_url, 1, page_size, cloud_hosted)

        if items:
            for item in items:
                concept_id = item.get("meta", {}).get("concept-id")
                if concept_id:
                    direct_dist_info = item.get("umm", {}).get("DirectDistributionInformation")
                    if direct_dist_info:
                        results[concept_id] = direct_dist_info

        # Calculate how many results to actually fetch
        results_to_fetch = min(total_hits, max_results) if max_results else total_hits
        total_pages = (results_to_fetch + page_size - 1) // page_size

        logger.info(f"Total collections available: {total_hits}, fetching {results_to_fetch} results across {total_pages} page(s)")

        if total_pages <= 1:
            logger.info(f"Collected {len(results)} collections with DirectDistributionInformation")
            return results

        # Fetch remaining pages concurrently
        tasks = []
        for page_num in range(2, total_pages + 1):
            task = fetch_page(session, base_url, page_num, page_size, cloud_hosted)
            tasks.append(task)

            # Process in batches to limit concurrency
            if len(tasks) >= concurrent_requests:
                batch_results = await asyncio.gather(*tasks)

                for page_num, items, _ in batch_results:
                    if items:
                        logger.debug(f"Fetched page {page_num}: {len(items)} collections")
                        for item in items:
                            concept_id = item.get("meta", {}).get("concept-id")
                            if concept_id:
                                direct_dist_info = item.get("umm", {}).get("DirectDistributionInformation")
                                if direct_dist_info:
                                    results[concept_id] = direct_dist_info

                tasks = []

        # Process remaining tasks
        if tasks:
            batch_results = await asyncio.gather(*tasks)

            for page_num, items, _ in batch_results:
                if items:
                    logger.debug(f"Fetched page {page_num}: {len(items)} collections")
                    for item in items:
                        concept_id = item.get("meta", {}).get("concept-id")
                        if concept_id:
                            direct_dist_info = item.get("umm", {}).get("DirectDistributionInformation")
                            if direct_dist_info:
                                results[concept_id] = direct_dist_info

    logger.info(f"Collected {len(results)} collections with DirectDistributionInformation")
    return results


def extract_bucket_prefix_key(s3_path: str, prefix_depth: int = 0) -> str:
    """Extract bucket and prefix up to specified depth from S3 path.

    Parameters:
        s3_path: S3 path like 's3://bucket/prefix/component1/component2'.
        prefix_depth: How many prefix components to include after the bucket.
            Defaults to 0 (bucket only).

    Returns:
        String like 'bucket' (depth=0) or 'bucket/prefix/component1' (depth=2).

    Examples:
        ```python
        extract_bucket_prefix_key('s3://my-bucket/data/2024/file.txt', 0)
        # Returns: 'my-bucket'

        extract_bucket_prefix_key('s3://my-bucket/data/2024/file.txt', 1)
        # Returns: 'my-bucket/data'

        extract_bucket_prefix_key('s3://my-bucket/data/2024/file.txt', 2)
        # Returns: 'my-bucket/data/2024'
        ```
    """
    if s3_path.startswith('s3://'):
        s3_path = s3_path[5:]
    
    parts = s3_path.split('/')
    bucket = parts[0]
    
    if prefix_depth == 0:
        return bucket
    
    # Include bucket + prefix_depth components
    # Handle case where path doesn't have enough components
    end_idx = min(1 + prefix_depth, len(parts))
    key = '/'.join(parts[:end_idx])
    
    return key


def create_bucket_key_mapping_recursive(
    results: Dict[str, Dict],
    max_depth: int = 5
) -> Dict[str, str]:
    """Create mapping from bucket/prefix key to endpoint.

    Recursively increases depth only for keys that have conflicts.

    Strategy:
        1. Start at depth 0 (bucket only)
        2. For any key with multiple endpoints, increase depth by 1
        3. Repeat until no conflicts or max_depth reached
        4. If conflicts remain at max_depth, raise ValueError

    Parameters:
        results: Dictionary mapping concept IDs to DirectDistributionInformation
            records from the CMR API.
        max_depth: Maximum prefix depth to try for conflict resolution.
            Defaults to 5.

    Returns:
        Dictionary mapping bucket/prefix keys to S3 credentials API endpoints.

    Raises:
        ValueError: If conflicts cannot be resolved at max_depth.
    """

    logger.info(f"Building bucket/prefix mapping {max_depth=}")

    # First, collect all S3 paths and their endpoints
    path_endpoints = []  # List of (s3_path, endpoint)

    for _concept_id, info in results.items():
        endpoint = info.get('S3CredentialsAPIEndpoint')
        if not endpoint:
            continue

        s3_paths = info.get('S3BucketAndObjectPrefixNames', [])
        for s3_path in s3_paths:
            path_endpoints.append((s3_path, endpoint))

    logger.info(f"Processing {len(path_endpoints)} S3 paths")

    # Track final mapping and paths that still need processing
    final_mapping = {}
    paths_to_process = path_endpoints  # Start with all paths at depth 0

    for depth in range(max_depth + 1):
        if not paths_to_process:
            break

        logger.debug(f"Processing depth {depth} with {len(paths_to_process)} paths")

        # Build mapping at current depth for paths still being processed
        key_endpoints = defaultdict(set)
        key_original_paths = defaultdict(list)  # Track which original paths map to each key

        for s3_path, endpoint in paths_to_process:
            key = extract_bucket_prefix_key(s3_path, depth)
            key_endpoints[key].add(endpoint)
            key_original_paths[key].append((s3_path, endpoint))

        # Separate unique keys from conflicting keys
        paths_still_conflicting = []
        resolved_count = 0
        conflict_count = 0

        for key, endpoints in key_endpoints.items():
            if len(endpoints) == 1:
                # No conflict at this depth - add to final mapping
                final_mapping[key] = next(iter(endpoints))
                resolved_count += 1
            else:
                # Still conflicting - need to go deeper
                if depth < max_depth:
                    # Add these paths back for processing at next depth
                    paths_still_conflicting.extend(key_original_paths[key])
                    conflict_count += 1
                else:
                    # Max depth reached and still have conflicts - raise error
                    conflict_details = "\n".join(
                        f"  {key}: {sorted(endpoints)}"
                        for key in [key]  # Just this key
                    )
                    raise ValueError(
                        f"Cannot resolve conflicts at max_depth={max_depth}. "
                        f"Found {len(endpoints)} endpoints for key '{key}':\n{conflict_details}\n"
                        f"Consider increasing max_depth or fixing data inconsistencies."
                    )

        logger.debug(f"Depth {depth}: resolved {resolved_count} keys, {conflict_count} conflicts")

        paths_to_process = paths_still_conflicting

    logger.info(f"Successfully created mapping with {len(final_mapping)} unique bucket/prefix keys")

    return final_mapping


async def crawl_cmr_endpoints(
    max_depth: int = 5,
    page_size: int = 20,
    concurrent_requests: int = 10,
    max_results: int | None = None
) -> Dict[str, str]:
    """Crawl NASA CMR API and create a unique mapping from S3 bucket/prefix keys to auth endpoints.

    This function queries the CMR API for all cloud-hosted collections (or up to max_results)
    and builds a mapping from S3 bucket/prefix combinations to their S3 credentials API endpoints.
    It uses recursive conflict resolution to find the appropriate prefix depth for each bucket.

    Parameters:
        max_depth: Maximum prefix depth to try for conflict resolution. Defaults to 5.
        page_size: Results per page (default: 100, max: 2000).
        concurrent_requests: Number of concurrent API requests. Defaults to 10.
        max_results: Optional limit on total results to fetch. If None, fetches all
            available results.

    Returns:
        Dictionary uniquely mapping bucket/prefix keys to S3 credentials API endpoints.

    Raises:
        ValueError: If conflicts remain after reaching max_depth (non-unique mapping).
        RuntimeError: If no results are collected from CMR API.

    Examples:
        ```python
        # Fetch all results
        mapping = await crawl_cmr_endpoints(max_depth=5)
        print(mapping['my-bucket/data'])
        # Output: 'https://data.nasa.gov/s3credentials'

        # Limit to first 500 results for testing
        mapping = await crawl_cmr_endpoints(max_depth=5, max_results=500)
        ```
    """
    # Step 1: Query CMR asynchronously
    results = await query_cmr_async(
        page_size=page_size,
        concurrent_requests=concurrent_requests,
        max_results=max_results
    )

    if not results:
        raise RuntimeError("No results collected from CMR API")

    # Step 2: Create bucket/prefix mapping with recursive conflict resolution
    # Will raise ValueError if conflicts cannot be resolved at max_depth
    mapping = create_bucket_key_mapping_recursive(results, max_depth=max_depth)

    return mapping