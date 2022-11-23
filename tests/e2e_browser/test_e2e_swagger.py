def test_swagger(browser, base_url):
    browser.visit(f"{base_url}/api/docs/swagger")
    assert browser.find_by_text("potential_api")
