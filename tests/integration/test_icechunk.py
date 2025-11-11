import earthaccess

def test_mur():
    url = "s3://nasa-eodc-public/icechunk/MUR-JPL-L4-GLOB-v4.1-virtual-v2-p2"
    store = earthaccess.icechunk._open_icechunk_from_url(url)
    print(store)
    assert 1 ==0 
