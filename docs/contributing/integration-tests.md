# Integration tests

## Testing most popular datasets

Some integration tests operate on the most popular collections for each provider in CMR.
Those collection IDs are cached as static data in `tests/integration/popular_collections/`
to give our test suite more stability. The list of most popular collections can be
updated by running a script in the same directory.

Sometimes, we find collections with unexpected conditions, like 0 granules, and
therefore "comment" those collections from the list by prefixing the line with a `#`.

!!! note

    Let's consider a CSV format for this data; we may want to, for example, allow
    skipping collections with a EULA by representing that as a column.
