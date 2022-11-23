from time import sleep

from percy import percySnapshot

from tests.constants import PERCY_TIME_TO_WAIT, TIME_TO_WAIT, USERS
from tests.utils import create_user_context

PERCY_SCREENSHOT_HEIGHT = 1152
PERCY_SCREENSHOT_WIDTH = 2000


def take_screenshot(
    browser,
    screenshot_name,
    wait_time=PERCY_TIME_TO_WAIT,
    percy_css="",
    disable_maps=True,
    selector_to_replace_link_with_image: str = "",
):
    if wait_time:
        sleep(wait_time)
    if disable_maps:
        # Leaflet
        mapbox_snippet = """
            const map = document.querySelector(
                "#map > div.leaflet-pane.leaflet-map-pane > div.leaflet-pane.leaflet-tile-pane"
            );
            if(map) map.style.visibility = "hidden";
        """
        browser.execute_script(mapbox_snippet)
    if selector_to_replace_link_with_image:
        replace_api_image_with_base64_src(
            browser=browser, selector=selector_to_replace_link_with_image
        )

    # Mock expected values by percy
    browser.current_url = browser.url
    browser.capabilities = {
        "browserName": "MOCKED_NAME",
        "browserVersion": "MOCKED_TEST",
    }
    percySnapshot(
        browser=browser,
        name=screenshot_name,
        minHeight=PERCY_SCREENSHOT_HEIGHT,
        widths=[PERCY_SCREENSHOT_WIDTH],
        percyCSS=percy_css,
    )
    return True


def dashboard_login(browser, client_db, dashboard_url, user_role, expected_css):
    context = create_user_context(USERS[user_role])["user"]

    browser.visit(dashboard_url + "/login")
    browser.fill("user", context["login"])
    browser.fill("password", context["password"])
    browser.find_by_text("Sign in").first.click()
    assert browser.is_element_visible_by_css(f"{expected_css}", wait_time=TIME_TO_WAIT)


def replace_api_image_with_base64_src(browser, selector: str):
    browser.execute_script(
        r"""
        function getBase64Image(img) {
        var canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        var dataURL = canvas.toDataURL('image/jpeg');
        return dataURL.replace(/^data:image\/(png|jpg);base64,/, '');
        }
        var element = document.querySelector("%s");
        element.src = getBase64Image(element);
        """
        % selector
    )
