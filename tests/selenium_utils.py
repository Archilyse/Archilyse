from pathlib import Path


def jquery():
    jquery_path = Path().cwd().joinpath("tests/fixtures/selenium/jquery-3.4.1.min.js")
    with jquery_path.open() as input_stream:
        jquery_script = input_stream.read()
        return jquery_script


def dnd_script():
    dnd_script_path = Path().cwd().joinpath("tests/fixtures/selenium/dnd.js")
    with dnd_script_path.open() as input_stream:
        dnd_script_content = input_stream.read()
        return dnd_script_content


def expand_competition_category_upper_tab(browser, category: str):
    browser.find_by_xpath(
        f"//div[text()='{category}']/following-sibling::div//button"
    ).first.click()


def expand_competition_category_clicking_arrow(browser, category: str):
    browser.find_by_xpath(
        f"//div[@class = 'expandable-field' and text() = '{category}']"
    ).find_by_css("[aria-label='expand']").click()
