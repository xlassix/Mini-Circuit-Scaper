from selenium import webdriver
from os import listdir, path, makedirs
import pandas as pd
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import date, datetime
from time import sleep

options = webdriver.ChromeOptions()

# basic input folders
_dir = "input"
_output_dir = "output"
makedirs(_output_dir, exist_ok=True)


def getTextById(browser: webdriver, _id: str) -> str:
    """This Function Gets Text from the WebDriver Instance that matches the HTML AttributeId

    Args:
        browser (webdriver): Selenium.WebDriver,
        _id(str): id HTMLAttribute

    Returns:
        str: String that matches the query
    """
    return browser.find_element(by=By.ID, value=_id).text.replace(",", "")


def getTextByXPath(browser: webdriver, xpath: str) -> str:
    """This Function Gets Text from the WebDriver Instance that matches the Xpath

    Args:
        browser (webdriver): Selenium.WebDriver,
        _id(str): id HTMLAttribute

    Returns:
        str: String that matches the query
    """
    return browser.find_element(by=By.XPATH, value=xpath).text.replace(",", "")


def parseDate(_date: str) -> date:
    """This function takes a date string in the format m/d/y and returns a datetime object

    Args:
        _date (str): date string Example 5/30/22
    Returns:
        date: datetime.date
    """
    return datetime.strptime(_date.strip(), "%m/%d/%Y").date()


def parseFloat(_number: str) -> float:
    """This function takes in a string strips unwanted symbols like $ and + and parses it to a float

    Args:
        _number (str): for example $5.0 or 10000+

    Returns:
        float: 
    """
    return float(_number.strip().strip("+").strip("$"))


def getPriceList(browser: webdriver) -> dict:
    """This function get the Price list(dict) For ElectoricMaster.com on a product page

    Args:
        browser (webdriver): Selenium.WebDriver

    Returns:
        dict
    """
    data = list(map(lambda x: list(map(lambda y: y.split(" ")[0], x.split(" $"))), getTextByXPath(
        browser, '//*[@id="model_price_section"]/table').split("\n")[1:]))
    results = []
    list(results.extend([("PB{} Qty".format(index+1), parseFloat(i[0])),
         ("PB{} $".format(index+1), parseFloat(i[1]))]) for index, i in enumerate(data[:20]))
    return dict(results)


def getExcels(path: str) -> [str]:
    """This function returns the list of excel in path

    Args:
        path (str)

    Returns:
        [str]: list of excel(.xlsx) in path
    """
    return (list(filter(lambda elem: elem.endswith(".csv") or elem.endswith(".xlsx"), listdir(path))))


def getItem(browser: webdriver, item: str) -> bool:
    """This Function Checks if an item query as any results on the current page
        it returns true to indicate if on the right page and false if the search item returns no results

    Args:
        browser (webdriver):Selenium.WebDriver
        item (str): Query

    Returns:
        bool
    """
    url = (
        "https://www.minicircuits.com/WebStore/modelSearch.html?model={0}".format(item))
    browser.get(url)
    if len(browser.find_elements(by=By.XPATH, value='//*[@id="wrapper"]/header/a/img')) == 0:
        sleep(8)  # bypass access denial
        getItem(browser, item)
    elif len(browser.find_elements(by=By.XPATH, value='//*[@id="wrapper"]/section/div[1]/label[1]')) > 0:
        return False
    if len(browser.find_elements(by=By.XPATH, value='//*[@id="wrapper"]/section/div[1]/div[1]')) > 0:
        search_result_elem = browser.find_element(by=By.XPATH,
                                                  value='//*[@id="wrapper"]/section/div[1]/div[1]/a')
        if(browser.current_url == url):
            search_result_elem.click()
    return True




def main():

    # initialise Browser
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    _columns = ['Internal Part Number', 'Description', 'Manufacturer', 'Query',
                'Qty', 'Run Datetime', "Stock", "Mfr PN", "Mfr", "Mfr Stock", "Mfr Stock Date", 'On-Order', 'On-Order Date', "Lead-Time", "Min Order",
                "PB1 Qty", "PB2 Qty", "PB3 Qty", "PB4 Qty", "PB5 Qty", "PB6 Qty", "PB7 Qty", "PB8 Qty",	"PB9 Qty", "PB10 Qty", "PB1 $",	"PB2 $", "PB3 $",	"PB4 $",	"PB5 $",	"PB6 $",	"PB7 $",	"PB8 $",	"PB9 $", "PB10 $",	"URL", "Source"]

    for excel in (getExcels(_dir)):
        print('\n\n\n')
        result_df = pd.DataFrame(columns=_columns)
        timestamp = datetime.now()
        raw_data = pd.read_excel(path.join(_dir, excel)) if excel.endswith(
            '.xlsx') else pd.read_csv(path.join(_dir, excel))
        present_columns = set(raw_data.columns).intersection(
            ['Internal Part Number', 'Description', 'Manufacturer', 'Query', 'Qty'])
        if ("Query" in present_columns):
            for index, row in enumerate(raw_data.to_dict(orient='records')):
                print("currently at index: {} \nData\t:{}".format(index, row))
                if getItem(browser, row["Query"]):
                    row['Run Datetime'] = timestamp
                    row['Mfr'] = "Mini-Circuits"
                    try:
                        row["Mfr PN"] = getTextByXPath(
                            browser, '//*[@id="content_area_home"]/section/section[1]/label[1]')
                    except:
                        break
                    if len(browser.find_elements(by=By.XPATH, value='//*[@id="model_price_section"]/div/p/span')) != 0:
                        mfr_date_text = getTextByXPath(
                            browser, '//*[@id="model_price_section"]/div/p/span').split(":")
                        row["On-Order Date"] = null if len(
                            mfr_date_text) < 2 else parseDate(mfr_date_text[1].strip("*"))
                    if len(browser.find_elements(by=By.XPATH, value='//*[@id="model_price_section"]/div/div[2]/span')) != 0:
                        stock = getTextByXPath(
                            browser, '//*[@id="model_price_section"]/div/div[2]/span').split(" ")
                        row["Stock"] = ">" + \
                            stock[-1] if len(stock) > 1 else stock[-1]
                    if len(browser.find_elements(by=By.XPATH, value='//*[@id="model_price_section"]/table/thead/tr/th[1]')) != 0:
                        row.update(getPriceList(browser))
                else:
                    row['Run Datetime'] = timestamp
                    row['Mfr'] = "No Result"
                    row["Mfr PN"] = "No Result"
                row["Source"] = "Mini-Circuits.com"
                row["URL"] = browser.current_url
                result_df = result_df.append(
                    row, ignore_index=True, sort=False)
        else:
            print("could not find `Query` in {}".format(excel))
        result_df[_columns].to_excel(
            path.join(_output_dir, str(timestamp)+"_"+(excel if excel.endswith(".xlsx") else excel+".xlsx")), index=False)
    browser.close()


if __name__ == "__main__":
    main()
