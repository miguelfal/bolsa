import datetime
import glob
import inspect
import os
import shutil
import time
import sqlite3
import logging
import pandas as pd
from dateutil.relativedelta import relativedelta

from datetime import datetime
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

# global variables
script_name = '(' + os.path.basename(__file__) + ') ' # for logging


def download_company_directory(download_folder: str):
    """
    Download file with list of equities from the Euronext site.

        :param: download_folder: path to dowload the file
        :return: None
    """
    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # url
    url = 'https://live.euronext.com/en/products/equities/list'

    logging.debug(script_name + 'url = ' + url)
    logging.debug(script_name + 'download_folder = ' + download_folder)

    # the interface for turning on headless mode and download preferences
    options = Options()
    options.add_argument('-headless')  # hide browser window
    options.set_preference('browser.download.folderList', 2)  # set downloads to default directory
    options.set_preference('browser.download.dir', download_folder)  # change download default directory
    options.set_preference('browser.download.manager.showWhenStarting', False)  # don't show download manager
    options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/x-gzip')  # don't show diialog
    options.add_argument('--disable-blink-features=AutomationControlled')  # avoid detection

    # aggregate data

    # using Firefox webdriver to secure connection to Firefox
    with webdriver.Firefox(options=options) as driver:
        # remove webdriver property to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # opening the target website in the browser
        driver.implicitly_wait(10)
        driver.get(url)

        # get cookies button
        time.sleep(2)  # to get cookie selection to appear
        save_pref_button = driver.find_elements(By.XPATH, ".//button[@class='eu-cookie-compliance-save-preferences"
                                                          "-button ']")  # find button
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(save_pref_button[0])).click()  # click after wait
        logging.debug(script_name + 'Clicked accepted cookies.')

        # get download button
        download_button = driver.find_elements(By.XPATH, ".//button[@class='btn btn-link']")
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(download_button[0])).click()
        logging.debug(script_name + 'Clicked download button.')

        # get go button
        time.sleep(5)  # to give time to find button
        go_button = driver.find_elements(By.XPATH, ".//input[@value = 'Go']")
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(go_button[0])).click()
        time.sleep(5)  # for new window to open and file to be downloaded
        logging.debug(script_name + 'Clicked Go button.')
        time.sleep(5)  # for file to be downloaded

        # exit
        driver.quit()
        logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')


def download_indice_directory(download_folder: str):
    """
    Download file with list of indices from the Euronext site to the folder.

        :param: download_folder: path to dowload the file
        :return: None
    """
    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # url
    url = 'https://live.euronext.com/en/products/indices/list'

    logging.debug(script_name + 'url = ' + url)
    logging.debug(script_name + 'download_folder = ' + download_folder)

    # the interface for turning on headless mode and download preferences
    options = Options()
    options.add_argument('-headless')  # hide browser window
    options.set_preference('browser.download.folderList', 2)  # set downloads to default directory
    options.set_preference('browser.download.dir', download_folder)  # change download default directory
    options.set_preference('browser.download.manager.showWhenStarting', False)  # don't show download manager
    options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/x-gzip')  # don't show diialog
    options.add_argument('--disable-blink-features=AutomationControlled')  # avoid detection

    # using Firefox webdriver to secure connection to Firefox
    with webdriver.Firefox(options=options) as driver:
        # remove webdriver property to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # opening the target website in the browser
        driver.implicitly_wait(10)
        driver.get(url)

        # get cookies button
        time.sleep(2)  # to get cookie selection to appear
        save_pref_button = driver.find_elements(By.XPATH, ".//button[@class='eu-cookie-compliance-save-preferences"
                                                          "-button ']")  # find button
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(save_pref_button[0])).click()  # click after wait
        logging.debug(script_name + 'Clicked accepted cookies.')

        # get download button
        download_button = driver.find_elements(By.XPATH, ".//button[@class='btn btn-link']")
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(download_button[0])).click()
        logging.debug(script_name + 'Clicked download button.')

        # get go button
        time.sleep(5)  # to give time to find button
        go_button = driver.find_elements(By.XPATH, ".//input[@value = 'Go']")
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(go_button[0])).click()
        logging.debug(script_name + 'Clicked Go button.')
        time.sleep(5)  # for new window to open and file to be downloaded

        # exit
        driver.quit()
        logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')


def scrape_company_information(company_list: list) -> list:
    """
    Scrape company information from the Euronext site for companies in the company list.

        :param company_list: list with the following elements [(name,isin,market)]
        :return: company information in a list of dictionaries
    """
    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # setup lists to receive information
    company_info_list = []

    # main url
    url = 'https://live.euronext.com/en/product/equities/'

    logging.debug(script_name + 'url = ' + url)

    # the interface for turning on headless mode and download preferences
    options = Options()
    options.add_argument('-headless')  # hide browser window
    options.set_preference('browser.download.folderList', 2)  # set downloads to default directory
    # options.set_preference('browser.download.dir', download_path)  # change download default directory
    options.set_preference('browser.download.manager.showWhenStarting', False)  # don't show download manager
    options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/x-gzip')  # don't show diialog
    options.add_argument('--disable-blink-features=AutomationControlled')  # avoid detection

    # using Firefox webdriver to secure connection to Firefox
    with webdriver.Firefox(options=options) as driver:
        # remove webdriver property to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # opening the target website in the browser
        driver.implicitly_wait(10)

        # go to homepage to accept cookies
        driver.get('https://live.euronext.com/en')

        # click cookies button
        time.sleep(2)  # to get cookie selection to appear
        save_pref_button = driver.find_elements(By.XPATH, ".//button[@class='eu-cookie-compliance-save-preferences"
                                                          "-button ']")  # find button
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(save_pref_button[0])).click()  # click after wait
        logging.debug(script_name + 'Clicked accept cookies.')

        # initialize counters
        num_companies = len(company_list)
        num_counter = 1

        # loop all equities in list
        for company in company_list:

            try:
                # setup company_url
                company_url = (company[1] or '') + '-' + (company[2] or '') + '/' + \
                              (company[0] or '').replace(' ', '_') + '/market-information'
                logging.info(script_name + '(' + str(num_counter) + ' of ' + str(num_companies) + ') ' \
                                                                                                  'Opening company page: ' + url + company_url)

                # open page
                driver.get(url + company_url)
                time.sleep(2)  # for new window to open and file to be downloaded

                # create dictionary: add name, isin, market
                company_info = {'name': (company[0] or ''), 'isin': (company[1] or ''), 'market': (company[2] or '')}

                # get general information
                logging.debug(script_name + 'Getting general information table.')
                cards = driver.find_elements(By.ID, 'block-fs-info-block')  # find table
                rows = cards[0].find_elements(By.TAG_NAME, 'tr')  # get table rows
                for r in rows:  # loop rows
                    col0 = r.find_elements(By.TAG_NAME, 'td')[0]  # get 1st column
                    col1 = r.find_elements(By.TAG_NAME, 'td')[1]  # get 2nd column
                    company_info[col0.text] = col1.text  # add to dictionary

                # get trading information
                logging.debug(script_name + 'Getting trading table.')
                cards = driver.find_elements(By.ID, 'block-fs-tradinginfo-block')  # find table
                rows = cards[0].find_elements(By.TAG_NAME, 'tr')  # get table rows
                for r in rows:  # loop rows
                    col0 = r.find_elements(By.TAG_NAME, 'td')[0]  # get 1st column
                    col1 = r.find_elements(By.TAG_NAME, 'td')[1]  # get 2nd column
                    company_info[col0.text] = col1.text  # add to dictionary

                # get sector information
                logging.debug(script_name + 'Getting sector information.')
                cards = driver.find_elements(By.ID, 'block-fs-icb-block')  # find table
                rows = cards[0].find_elements(By.TAG_NAME, 'tr')  # get table rows
                for r in rows:  # loop rows
                    col0 = r.find_elements(By.TAG_NAME, 'td')[0]  # get 1st column
                    col1 = r.find_elements(By.TAG_NAME, 'td')[1]  # get 2nd column
                    company_info[col0.text] = col1.text  # add to dictionary

                company_url = (company[1] or '') + '-' + (company[2] or '') + '/' + \
                              (company[0] or '').replace(' ', '_') + '/company-information'
                driver.get(url + company_url)
                time.sleep(2)  # for new window to open and file to be downloaded

                # get company profile
                logging.debug(script_name + 'Getting company profile information.')
                company_profile = ''
                cards = driver.find_elements(By.ID, 'block-awlcofisempublicblock')  # find table
                rows = cards[0].find_elements(By.CLASS_NAME, 'field-wrapper')  # get table rows
                for r in rows:  # loop rows
                    company_profile += r.text
                company_info['Company profile'] = company_profile  # add to dictionary

                # update counter
                num_counter = num_counter + 1

            except Exception as e:
                logging.exception('Error getting company information from ' + company[0] + ' :', repr(e))

            # add dictionary to list
            company_info_list.append(company_info)  # add to list

        # exit
        driver.quit()
        logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return company_info_list


def scrape_company_quotes(company_list: list) -> list:
    """
    Scrape company daily quote information from the Euronext site for companies in the company list.

        :param company_list: list of companies in form [(name, isin, short_market_name)]
        :return: company information in a list of dictionaries
    """
    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # setup lists to receive information
    company_quote_list = []

    # main url
    url = 'https://live.euronext.com/en/product/equities/'

    logging.debug(script_name + 'url = ' + url)

    # the interface for turning on headless mode and download preferences
    options = Options()
    options.add_argument('-headless')  # hide browser window
    options.set_preference('browser.download.folderList', 2)  # set downloads to default directory
    # options.set_preference('browser.download.dir', download_path)  # change download default directory
    options.set_preference('browser.download.manager.showWhenStarting', False)  # don't show download manager
    options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/x-gzip')  # don't show diialog
    options.add_argument('--disable-blink-features=AutomationControlled')  # avoid detection

    # using Firefox webdriver to secure connection to Firefox
    with webdriver.Firefox(options=options) as driver:
        # remove webdriver property to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # opening the target website in the browser
        driver.implicitly_wait(10)

        # go to homepage to accept cookies
        driver.get('https://live.euronext.com/en')

        # click cookies button
        time.sleep(2)  # to get cookie selection to appear
        save_pref_button = driver.find_elements(By.XPATH, ".//button[@class='eu-cookie-compliance-save-preferences"
                                                          "-button ']")  # find button
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(save_pref_button[0])).click()  # click after wait
        logging.debug(script_name + 'Clicked accept cookies.')

        # initialize counters
        num_companies = len(company_list)
        num_counter = 1

        # loop all equities in list
        for company in company_list:

            # setup company_url
            company_url = (company[1] or '') + '-' + (company[2] or '') + '/' + \
                          (company[0] or '').replace(' ', '_')
            logging.info(script_name + '(' + str(num_counter) + ' of ' + str(num_companies) + ') ' \
                                                                                              'Opening company page: ' + url + company_url)

            # open page
            driver.get(url + company_url)
            time.sleep(2)  # for new window to open and file to be downloaded

            # create quote dictionary: add name, isin, market
            company_quote = {'name': (company[0] or ''), 'isin': (company[1] or ''), 'market': (company[2] or '')}

            # get detailed quote
            logging.debug(script_name + 'Getting detailed quote table.')
            cards = driver.find_elements(By.ID, 'detailed-quote')  # find table
            if len(cards) > 0:
                rows = cards[0].find_elements(By.TAG_NAME, 'tr')  # get table rows
                for r in rows:  # loop rows
                    col0 = r.find_elements(By.TAG_NAME, 'td')[0]  # get 1st column
                    col1 = r.find_elements(By.TAG_NAME, 'td')[1]  # get 2nd column
                    col2 = r.find_elements(By.TAG_NAME, 'td')[0]  # get 1st column
                    col3 = r.find_elements(By.TAG_NAME, 'td')[2]  # get 2nd column
                    company_quote[col0.text] = col1.text  # add to dictionary
                    company_quote[col2.text + '_cont'] = col3.text  # add to dictionary

                company_quote_list.append(company_quote)  # add to list

            num_counter = num_counter + 1
        # exit
        driver.quit()
        logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return company_quote_list


def scrape_company_intraday_quotes(company_list: list) -> list:
    """
    Scrape company intradday information from the Euronext site for companies in the company list.

        :param company_list: list of companies in form [(name, isin, short_market_name)]
        :return: company information in a list of dictionaries
    """
    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # setup lists to receive information
    company_intraday_list = []

    # main url
    url = 'https://live.euronext.com/en/product/equities/'

    logging.debug(script_name + 'url = ' + url)

    # the interface for turning on headless mode and download preferences
    options = Options()
    options.add_argument('-headless')  # hide browser window
    options.set_preference('browser.download.folderList', 2)  # set downloads to default directory
    # options.set_preference('browser.download.dir', download_path)  # change download default directory
    options.set_preference('browser.download.manager.showWhenStarting', False)  # don't show download manager
    options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/x-gzip')  # don't show diialog
    options.add_argument('--disable-blink-features=AutomationControlled')  # avoid detection

    # using Firefox webdriver to secure connection to Firefox
    with webdriver.Firefox(options=options) as driver:
        # remove webdriver property to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # opening the target website in the browser
        driver.implicitly_wait(10)

        # go to homepage to accept cookies
        driver.get('https://live.euronext.com/en')

        # click cookies button
        time.sleep(2)  # to get cookie selection to appear
        save_pref_button = driver.find_elements(By.XPATH, ".//button[@class='eu-cookie-compliance-save-preferences"
                                                          "-button ']")  # find button
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(save_pref_button[0])).click()  # click after wait
        logging.debug(script_name + 'Clicked accept cookies.')

        # initialize counters
        num_companies = len(company_list)
        num_counter = 1

        # loop all equities in list
        for company in company_list:

            # get intraday price
            company_url = (company[1] or '') + '-' + (company[2] or '') + '/' + \
                          (company[0] or '').replace(' ', '_') + '/#intraday-prices'
            driver.get(url + company_url)
            logging.info(script_name + '(' + str(num_counter) + ' of ' + str(num_companies) + ') ' \
                                                                                              'Opening company page: ' + url + company_url)
            time.sleep(2)  # for new window to open and file to be downloaded

            # get date
            date = driver.find_elements(By.ID, 'nav-tab-yesterday')
            if len(date) > 0:
                date_text = date[0].text

            # get trade count
            if len(driver.find_elements(By.ID, 'awlIntradayPrice_totalTransactions')) > 0:
                trade_count_total = int(driver.find_elements(By.ID, 'awlIntradayPrice_totalTransactions')[0].text)
            else:
                trade_count_total = 0
            trade_count = 0
            trade_count_enum = 1

            # load more
            logging.debug(script_name + 'Getting intraday price table.')
            load_more = driver.find_elements(By.ID, 'intraday-price-load-more')
            if len(load_more) > 0:
                while load_more[0].is_displayed():
                    WebDriverWait(driver, 100).until(ec.element_to_be_clickable(load_more[0])).click()
                    time.sleep(1)

            # get intraday table
            while trade_count_total > trade_count:
                intraday_table = driver.find_elements(By.ID, 'AwlIntradayPriceCanvasTable')
                rows = intraday_table[0].find_elements(By.TAG_NAME, 'tr')  # get table rows
                try:
                    for n, r in enumerate(rows[trade_count_enum:]):  # loop rows
                        company_intraday = {'name': (company[0] or ''), 'isin': (company[1] or ''),
                                            'market': (company[2] or ''), 'date': (date_text or '')}
                        col0 = r.find_elements(By.TAG_NAME, 'td')[0]  # get 1st column
                        col1 = r.find_elements(By.TAG_NAME, 'td')[1]  # get 2nd column
                        col2 = r.find_elements(By.TAG_NAME, 'td')[2]  # get 3rd column
                        col3 = r.find_elements(By.TAG_NAME, 'td')[3]  # get 4th column
                        col4 = r.find_elements(By.TAG_NAME, 'td')[4]  # get 5th column
                        company_intraday['TRADE ID'] = col0.text  # add to dictionary
                        company_intraday['TIME'] = col1.text  # add to dictionary
                        company_intraday['PRICE'] = col2.text  # add to dictionary
                        company_intraday['SHARES'] = col3.text  # add to dictionary
                        company_intraday['TYPE'] = col4.text  # add to dictionary
                        company_intraday_list.append(company_intraday)  # add to list
                        trade_count = trade_count + 1
                except Exception as e:
                    trade_count_enum = trade_count
                    logging.warning(script_name + ' Error reading intraday table: ' + repr(e))

            num_counter = num_counter + 1

        # exit
        driver.quit()
        logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return company_intraday_list


def scrape_company_historical_quotes(company_list: list) -> list:
    """
    Scrape company information from the Euronext site for companies in the company list.

        :param company_list: list of companies in form [(name, isin, short_market_name)]
        :return: company information in a list of dictionaries
    """
    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # setup lists to receive information
    company_historical_list = []

    # main url
    url = 'https://live.euronext.com/en/product/equities/'

    logging.debug(script_name + 'url = ' + url)

    # the interface for turning on headless mode and download preferences
    options = Options()
    options.add_argument('-headless')  # hide browser window
    options.set_preference('browser.download.folderList', 2)  # set downloads to default directory
    # options.set_preference('browser.download.dir', download_path)  # change download default directory
    options.set_preference('browser.download.manager.showWhenStarting', False)  # don't show download manager
    options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/x-gzip')  # don't show diialog
    options.add_argument('--disable-blink-features=AutomationControlled')  # avoid detection

    # using Firefox webdriver to secure connection to Firefox
    with webdriver.Firefox(options=options) as driver:
        # remove webdriver property to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # opening the target website in the browser
        driver.implicitly_wait(10)

        # go to homepage to accept cookies
        driver.get('https://live.euronext.com/en')

        # click cookies button
        time.sleep(2)  # to get cookie selection to appear
        save_pref_button = driver.find_elements(By.XPATH, ".//button[@class='eu-cookie-compliance-save-preferences"
                                                          "-button ']")  # find button
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable(save_pref_button[0])).click()  # click after wait
        logging.debug(script_name + 'Clicked accept cookies.')

        # initialize counters
        num_companies = len(company_list)
        num_counter = 1

        # loop all equities in list
        for company in company_list:
            try:
                # get historical quotes
                company_url = (company[1] or '') + '-' + (company[2] or '') + '/' + \
                              (company[0] or '').replace(' ', '_') + '/#historical-price'
                driver.get(url + company_url)
                logging.info(script_name + '(' + str(num_counter) + ' of ' + str(num_companies) + ') ' \
                                                                                                  'Opening company page: ' + url + company_url)

                time.sleep(2)  # for new window to open and file to be downloaded

                # load more
                # set from date
                if company[2] == 'BGEM':  # Milan only 5 days available
                    from_dt = datetime.today() + relativedelta(days=-5)
                else:
                    from_dt = datetime.today() + relativedelta(years=-2)

                logging.debug(script_name + 'Getting historical price table.')
                date_from = driver.find_elements(By.ID, 'datetimepickerFrom')
                WebDriverWait(driver, 10).until(ec.element_to_be_clickable(date_from[0])).click()
                date_from[0].send_keys(Keys.CONTROL, "a")
                date_from[0].send_keys(Keys.BACKSPACE)
                date_from[0].send_keys(from_dt.strftime('%Y-%m-%d'), Keys.RETURN)
                time.sleep(5)

                # get table
                historical_table = driver.find_elements(By.ID, 'AwlHistoricalPriceTable')
                rows = historical_table[1].find_elements(By.TAG_NAME, 'tr')  # get table rows
                for n, r in enumerate(rows):  # loop rows
                    if n > 0:
                        company_historical = {'name': (company[0] or ''), 'isin': (company[1] or ''),
                                              'market': (company[2] or '')}
                        col0 = r.find_elements(By.TAG_NAME, 'td')[0]  # get 1st column
                        col1 = r.find_elements(By.TAG_NAME, 'td')[1]  # get 2nd column
                        col2 = r.find_elements(By.TAG_NAME, 'td')[2]  # get 3rd column
                        col3 = r.find_elements(By.TAG_NAME, 'td')[3]  # get 4th column
                        col4 = r.find_elements(By.TAG_NAME, 'td')[4]  # get 5th column
                        col5 = r.find_elements(By.TAG_NAME, 'td')[5]  # get 6th column
                        col6 = r.find_elements(By.TAG_NAME, 'td')[6]  # get 7th column
                        col7 = r.find_elements(By.TAG_NAME, 'td')[7]  # get 8th column
                        col8 = r.find_elements(By.TAG_NAME, 'td')[8]  # get 9th column
                        company_historical['DATE'] = col0.text  # add to dictionary
                        company_historical['OPEN'] = col1.text  # add to dictionary
                        company_historical['HIGH'] = col2.text  # add to dictionary
                        company_historical['LOW'] = col3.text  # add to dictionary
                        company_historical['LAST'] = col4.text  # add to dictionary
                        company_historical['CLOSE'] = col5.text  # add to dictionary
                        company_historical['NUMBER OF SHARES'] = col6.text  # add to dictionary
                        company_historical['TURNOVER'] = col7.text  # add to dictionary
                        company_historical['VWAP'] = col8.text  # add to dictionary
                        company_historical_list.append(company_historical)  # add to list

                # update counter
                num_counter = num_counter + 1

            except Exception as e:
                logging.exception('Error getting company information from ' + company[0] + ' :', repr(e))

        # exit
        driver.quit()
        logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return company_historical_list


def insert_company_directory_sqlite(database: str, download_file_path: str, error_file_path: str = ''):
    """
    To download and insert into the sqlite database a list of all equities from Euronext.

       :param error_file_path: where the files that raise erros should be moved
       :param download_file_path: where the file to be imported is located
       :param database: full path and name of the sqlite database to be used
       :return: None
    """
    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')
    logging.debug(script_name + 'database = ' + database)
    logging.debug(script_name + 'download_file_path = ' + download_file_path)

    # download file
    download_company_directory(download_file_path)

    # get list of files
    file_mask = 'Euronext_Equities*.xlsx'
    file_list = glob.glob(download_file_path + '/' + file_mask)

    # set default error path
    if error_file_path == '':
        error_file_path = os.path.join(download_file_path, './error')
    logging.debug(script_name + 'error_file_path = ' + error_file_path)

    # loop files
    for file in file_list:
        data_file = os.path.join(download_file_path, file)
        path = os.path.split(data_file)
        data_file_error = os.path.join(error_file_path, path[1])
        logging.debug(script_name + 'Files found: ' + data_file)

        try:
            data = pd.read_excel(data_file, sheet_name=0)
            data_list = data.values.tolist()

            # connect to sqlite database
            conn = sqlite3.connect(database, isolation_level=None)  # isolation_level = none to commit automatically

            # delete existing data
            cur = conn.cursor()
            sql_delete = 'DELETE FROM "euronext_equities"'
            cur.execute(sql_delete)
            logging.debug(script_name + 'Deleted table "euronext_equities"')

            # insert company info into the databse
            sql_insert = 'INSERT INTO "euronext_equities" ("name","isin","symbol", "market","currency","z_updated_on") \
             VALUES (?,?,?,?,?,?) on conflict do nothing;'

            for item in data_list[3:]:
                item[5] = str(datetime.today())
                cur.execute(sql_insert, item[:6])

        except Exception as e:
            logging.error(script_name + 'Could not insert file: ' + data_file + '. Error msg: ' + repr(e))
            shutil.move(data_file, data_file_error)
            pass
        else:
            logging.debug(script_name + 'Inserted company directory into sqlite.')
            os.remove(data_file)

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return None


def insert_indice_directory_sqlite(database: str, download_file_path: str, error_file_path: str = ''):
    """
    To download and insert into the sqlite database a list of all indices from Euronext.

       :param error_file_path: where the files that raise erros should be moved
       :param download_file_path: where the file to be imported is located
       :param database: full path and name of the sqlite database to be used
       :return: None
    """
    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')
    logging.debug(script_name + 'database = ' + database)
    logging.debug(script_name + 'download_file_path = ' + download_file_path)

    # download file
    download_indice_directory(download_file_path)

    # get list of files
    file_mask = 'Euronext_Indices*.xls'
    file_list = glob.glob(download_file_path + '/' + file_mask)

    # set default error path
    if error_file_path == '':
        error_file_path = os.path.join(download_file_path, './error')
    logging.debug(script_name + 'error_file_path = ' + error_file_path)

    # loop files
    for file in file_list:
        data_file = os.path.join(download_file_path, file)
        path = os.path.split(data_file)
        data_file_error = os.path.join(error_file_path, path[1])
        logging.debug(script_name + 'Files found: ' + data_file)

        try:
            data = pd.read_csv(data_file, sep='\t', encoding='ISO-8859-1')
            data_list = data.values.tolist()

            # connect to sqlite database
            conn = sqlite3.connect(database, isolation_level=None)  # isolation_level = none to commit automatically

            # delete existing data
            cur = conn.cursor()
            sql_delete = 'DELETE FROM "euronext_indices"'
            cur.execute(sql_delete)
            logging.debug(script_name + 'Deleted table "euronext_indices"')

            # insert company info into the databse
            sql_insert = 'INSERT INTO "euronext_indices" ("name","isin","symbol","trading_currency","timezone", \
                          "z_updated_on") VALUES (?,?,?,?,?,?) on conflict do nothing;'

            for item in data_list[3:]:
                item[4] = item[9]
                item[5] = str(datetime.today())
                cur.execute(sql_insert, item[:6])

        except Exception as e:
            logging.error(script_name + 'Could not insert file: ' + data_file + '. Error msg: ' + repr(e))
            shutil.move(data_file, data_file_error)
            pass
        else:
            logging.debug(script_name + 'Inserted company directory into sqlite.')
            os.remove(data_file)

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return None


def insert_company_information_sqlite(database: str, company_list: list):
    """
    To scrape and insert into the sqlite database information on the companies in the list.

       :param company_list: list of companies in form [(name, isin, short_market_name)]
       :param database: full path and name of the sqlite database to be used
       :return: None
    """
    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # get list with company information from euronext: isin + name + market is needed
    company_information = scrape_company_information(company_list)

    # connect to sqlite database
    conn = sqlite3.connect(database, isolation_level=None)  # isolation_level = none to commit automatically
    cur = conn.cursor()

    for company in company_information:
        # delete existing data
        sql_delete = 'DELETE FROM "euronext_company_information" WHERE isin in ("' + (company.get('isin', '') or '') \
                     + '")'
        cur.execute(sql_delete)

        logging.debug(script_name + 'Deleted company information from table  "euronext_company_information" : ' +
                      (company.get('name', '') or '') + ' - ' + (company.get('isin', '') or '') + ' - ' +
                      (company.get('market', '') or ''))

        # insert company info into the databse
        sql_insert = 'INSERT INTO "euronext_company_information" ("name","isin","market", \
                                  "type", "sub_type","currency", "price_multiplier","quantity_notation","admitted_shares", \
                                  "nominal_value","trading_group","trading_type","tick_size","industry","supersector", \
                                  "sector","subsector", "company_profile", "z_updated_on") VALUES (?,?,?,?,?,?,?,?,?,? \
                                  ,?,?,?,?,?,?,?,?,?) on conflict do nothing;'

        logging.debug(script_name + 'Inserting company information for: ' + (company.get('name', '') or ''))
        cur.execute(sql_insert, [(company.get('name', '') or ''), (company.get('isin', '') or ''),
                                 (company.get('market', '') or ''), (company.get('Type', '') or ''),
                                 (company.get('Sub type', '') or ''), (company.get('Trading currency', '') or ''),
                                 (company.get('Price multiplier', '') or ''),
                                 (company.get('Quantity notation', '') or ''),
                                 (company.get('Admitted shares', '') or ''),
                                 (company.get('Nominal value', '') or ''), (company.get('Trading group', '') or ''),
                                 (company.get('Trading type', '') or ''), (company.get('Tick size', '') or ''),
                                 (company.get('Industry', '') or ''), (company.get('SuperSector', '') or ''),
                                 (company.get('Sector', '') or ''), (company.get('Subsector', '') or ''),
                                 (company.get('Company profile', '') or ''), datetime.today()])

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return None


def insert_company_quotes_sqlite(database: str, company_list: list):
    """
    To scrape and insert into the sqlite database daily quote data from the last day for companies in the list.

       :param database: full path and name of the sqlite database to be used
       :param company_list: list of companies in form [(name, isin, short_market_name)]
       :return: None
    """

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # connect to sqlite database
    conn = sqlite3.connect(database, isolation_level=None)  # isolation_level = none to commit automatically

    # delete existing data
    cur = conn.cursor()

    # get list with company information from euronext: isin + name + market is needed
    company_quotes_day = scrape_company_quotes(company_list)

    # insert company info into the databse
    sql_insert = 'INSERT INTO "euronext_company_quotes" ("name","isin","market", "date", "open","high","low","last", \
                 "close","volume","turnover","vwap","z_updated_on") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)  \
                 on conflict do nothing;'

    for cmq in company_quotes_day:
        cur.execute(sql_insert,
                    [(cmq.get('name', '') or ''), (cmq.get('isin', '') or ''), (cmq.get('market', '') or ''),
                     (cmq.get('Valuation Close_cont', '')[7:11] + '-' +
                      cmq.get('Valuation Close_cont', '')[4:6] + '-' +
                      cmq.get('Valuation Close_cont', '')[1:3] or ''),
                     (cmq.get('Open', '') or ''), (cmq.get('High', '') or ''),
                     (cmq.get('Low', '') or ''), (cmq.get('Last Traded', '') or ''),
                     (cmq.get('Valuation Close', '') or ''), (cmq.get('Volume', '') or ''),
                     (cmq.get('Turnover', '') or ''), (cmq.get('VWAP', '') or ''), datetime.today()])

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return None


def insert_company_intraday_quotes_sqlite(database: str, company_list: list):
    """
        To scrape and insert into the sqlite database intraday quote data from the last day for companies in the list.

       :param database: full path and name of the sqlite database to be used
       :param company_list: list of companies in form [(name, isin, short_market_name)]
       :return: None
    """
    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # connect to sqlite database
    conn = sqlite3.connect(database, isolation_level=None)  # isolation_level = none to commit automatically

    # delete existing data
    cur = conn.cursor()

    # get list with company information from euronext: isin + name + market is needed
    company_quotes_intraday = scrape_company_intraday_quotes(company_list)

    sql_insert = 'INSERT INTO "euronext_company_intraday_quotes" ("name","isin","market", \
                                      "date", "trade_id", "time", "price","shares", "type","z_updated_on") VALUES \
                                      (?,?,?,?,?,?,?,?,?,?) on conflict do nothing;'

    for cmq in company_quotes_intraday:
        cur.execute(sql_insert, [(cmq.get('name', '') or ''), (cmq.get('isin', '') or ''),
                                 (cmq.get('market', '') or ''), (cmq.get('date', '') or ''),
                                 (cmq.get('TRADE ID', '') or ''), (cmq.get('TIME', '') or ''),
                                 (cmq.get('PRICE', '') or ''), (cmq.get('SHARES', '') or ''),
                                 (cmq.get('TYPE', '') or ''), datetime.today()])

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return None


def insert_company_historical_quotes_sqlite(database: str, company_list: list):
    """
    To scrape and insert into the sqlite database historical quote data from the 2 years for companies in the list.

       :param database: full path and name of the sqlite database to be used
       :param company_list: list of companies in form [(name, isin, short_market_name)]

       :return: None
    """
    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # connect to sqlite database
    conn = sqlite3.connect(database, isolation_level=None)  # isolation_level = none to commit automatically

    # delete existing data
    cur = conn.cursor()

    # get list with company information from euronext: isin + name + market is needed
    company_historical_quotes = scrape_company_historical_quotes(company_list)

    # insert company info into the databse
    sql_insert = 'INSERT INTO "euronext_company_quotes" ("name","isin","market", "date", "open","high","low","last", \
                 "close","volume","turnover","vwap","z_updated_on") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) \
                 on conflict do nothing;'

    for cmq in company_historical_quotes:
        cur.execute(sql_insert, [(cmq.get('name', '') or ''), (cmq.get('isin', '') or ''),
                                 (cmq.get('market', '') or ''), (cmq.get('DATE', '') or ''),
                                 (cmq.get('OPEN', '') or ''), (cmq.get('HIGH', '') or ''),
                                 (cmq.get('LOW', '') or ''), (cmq.get('LAST', '') or ''),
                                 (cmq.get('CLOSE', '') or ''), (cmq.get('NUMBER OF SHARES', '') or ''),
                                 (cmq.get('TURNOVER', '') or ''), (cmq.get('VWAP', '') or ''), datetime.today()])

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return None


def get_company_sqlite(database: str, market: str = '', isin: str = '', name: str = '') -> list:
    """
    To get a list of companies from a particular Euronext market using filters.

       :param database: full path and name of the sqlite database to be used.
       :param market: the short name of the market: {'MTAA', 'XAMS', 'XBRU', 'XLIS', 'XMSM', 'XPAR'}.
                      If empty then get companies from all markets.
       :param name: full or partial name of the company
       :param isin: isin identifier of company

       return: list of companies in form [name, isin ,short_market_name].
    """

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # available markets
    markets = {'MTAA', 'XAMS', 'XBRU', 'XLIS', 'XMSM', 'XPAR', ''}

    # check if market parameter is valid
    if market not in markets:
        raise ValueError("Unavailable market: must be one of %r." % markets)

    # set sql string
    # sql_market
    sql_market = ''
    if len(market) == 0:
        for m in markets:
            if len(sql_market) > 0:
                sql_market = sql_market + ','
            sql_market = sql_market + '"' + m + '"'
    else:
        sql_market = '"' + market + '"'

    # isin full or partial
    if len(isin) > 0:
        sql_isin = ' AND isin like "%' + isin + '%"'
    else:
        sql_isin = ''

    # company full or partial name
    if len(name) > 0:
        sql_name = ' AND name like "%' + name + '%"'
    else:
        sql_name = ''

    logging.debug(script_name + 'Selected markets sql: ' + sql_market)

    # connect to sqlite database
    conn = sqlite3.connect(database, isolation_level=None)  # isolation_level = none to commit automatically
    logging.debug(script_name + 'Connected to database: ' + database)

    # delete existing data
    cur = conn.cursor()

    # get list of equities of market
    sql_select = 'SELECT "name", "isin" ,"main_market_short_name"  \
                      FROM "euronext_equities" as equ INNER JOIN euronext_markets as mkt \
                      ON equ.market = mkt.market_name WHERE \
                      mkt.main_market_short_name in (' + sql_market + ')' + sql_isin + sql_name

    # get list of equities of market
    logging.debug(script_name + 'Getting list of companies: ' + sql_select)

    cur.execute(sql_select)
    company_list = cur.fetchall()

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return company_list


def create_sqlite_tables(database: str):
    """
    To create tables for euronext scraping in a sqlite database.

       :param database: full path and name of the sqlite database to be used.
    """

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    # connect to sqlite database
    conn = sqlite3.connect(database, isolation_level=None)  # isolation_level = none to commit automatically
    cur = conn.cursor()
    logging.debug(script_name + 'Connected to database: ' + database)

    # "euronext_company_information"
    try:
        sql_create = 'CREATE TABLE "euronext_company_information" ("name" TEXT, "isin" TEXT, "market" TEXT, "type" TEXT, \
	              "sub_type" TEXT, "currency" TEXT, "price_multiplier" INT, "quantity_notation" TEXT, \
	              "admitted_shares"	INT, "nominal_value" REAL, "trading_group" TEXT, "trading_type"	TEXT, "tick_size" \
	              TEXT, "industry" TEXT, "supersector" TEXT, "sector" TEXT,	"subsector"	TEXT, "company_profile" TEXT, \
                  "z_updated_on" DATE, UNIQUE("name","isin", "market"));'
        cur.execute(sql_create)
        logging.debug(script_name + 'Created table "euronext_company_information".')
    except Exception as e:
        logging.warning(script_name + 'Error creating table "euronext_company_information".' + repr(e))

    # "euronext_company_intraday_quotes"
    try:
        sql_create = 'CREATE TABLE "euronext_company_intraday_quotes" ("name" TEXT, "isin" TEXT, "market" TEXT, \
                "date" DATE, "trade_id" TEXT, "time" TEXT, "price" REAL, "shares" INT,"type" TEXT, \
	            "z_updated_on" DATE, UNIQUE("name","isin", "market","date","trade_id"));'
        cur.execute(sql_create)
        logging.debug(script_name + 'Created table "euronext_company_intraday_quotes".')
    except Exception as e:
        logging.warning(script_name + 'Error creating table "euronext_company_intraday_quotes".' + repr(e))

    # "euronext_company_quotes"
    try:
        sql_create = 'CREATE TABLE "euronext_company_quotes" ("name" TEXT, "isin" TEXT, "market" TEXT, "date" DATE \
                    ,"open"	REAL, "high" REAL, "low" REAL, "last" REAL, "close" REAL, "volume" INTEGER, "turnover" REAL, \
                    "vwap" REAL, "z_updated_on" DATE, UNIQUE("name","isin", "market","date"));'
        cur.execute(sql_create)
        logging.debug(script_name + 'Created table "euronext_company_quotes".')
    except Exception as e:
        logging.warning(script_name + 'Error creating table "euronext_company_quotes".' + repr(e))

    # "euronext_equities"
    try:
        sql_create = 'CREATE TABLE "euronext_equities" ("name" TEXT, "isin" TEXT, "symbol" TEXT, "market" TEXT, \
                    "currency"	TEXT, z_updated_on DATE);'
        cur.execute(sql_create)
        logging.debug(script_name + 'Created table "euronext_equities".')
    except Exception as e:
        logging.warning(script_name + 'Error creating table "euronext_equities".' + repr(e))

    # "euronext_indices"
    try:
        sql_create = 'CREATE TABLE "euronext_indices" ("name" TEXT,"isin" TEXT,"symbol"	TEXT,"trading_currency"	TEXT, \
                      "timezone"	TEXT,"z_updated_on"	TEXT);'
        cur.execute(sql_create)
        logging.debug(script_name + 'Created table "euronext_indices".')
    except Exception as e:
        logging.warning(script_name + 'Error creating table "euronext_indices".' + repr(e))

    # "euronext_markets"
    try:
        sql_create = 'CREATE TABLE "euronext_markets" ("market_name" TEXT, "market_short_name" TEXT, \
                      "main_market_short_name" TEXT);'
        cur.execute(sql_create)
        logging.debug(script_name + 'Created table "euronext_markets" .')
    except Exception as e:
        logging.warning(script_name + 'Error creating table "euronext_markets".' + repr(e))

    try:
        sql_insert = "INSERT INTO 'euronext_markets' ('market_name', 'market_short_name', 'main_market_short_name') \
                      SELECT 'Borsa Italiana Global Equity Market' as 'market_name', 'BGEM' as  'market_short_name' , \
                      'BGEM' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Access Brussels' as 'market_name', 'MLXB' as  'market_short_name' , \
                      'MLXB' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Access Lisbon' as 'market_name', 'ENXL' as  'market_short_name' , \
                      'ENXL' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Access Paris' as 'market_name', 'XMLI' as  'market_short_name' , \
                      'XMLI' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Amsterdam' as 'market_name', 'XAMS' as  'market_short_name' , \
                      'XAMS' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Amsterdam, Brussels' as 'market_name', 'XAMS, XBRU' as  'market_short_name' ,\
                       'XAMS' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Amsterdam, Brussels, Paris' as 'market_name', 'XAMS, XBRU, XPAR' as  \
                      'market_short_name' , 'XAMS' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Amsterdam, Paris' as 'market_name', 'XAMS, XPAR' as  'market_short_name' ,\
                       'XAMS' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Brussels' as 'market_name', 'XBRU' as  'market_short_name' , \
                      'XBRU' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Brussels, Amsterdam' as 'market_name', 'XBRU, XAMS' as  'market_short_name' ,\
                       'XBRU' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Brussels, Paris' as 'market_name', 'XBRU, XPAR' as  'market_short_name' , \
                      'XBRU' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Dublin' as 'market_name', 'XMSM' as  'market_short_name' , \
                      'XMSM' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Expand Oslo' as 'market_name', 'XOAS' as  'market_short_name' , \
                       'XOAS' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Expert Market' as 'market_name', 'VPXB' as  'market_short_name' , \
                      'VPXB' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Growth Brussels' as 'market_name', 'ALXB' as  'market_short_name' , \
                      'ALXB' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Growth Dublin' as 'market_name', 'XESM' as  'market_short_name' ,\
                       'XESM' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Growth Lisbon' as 'market_name', 'ALXL' as  'market_short_name' , \
                      'ALXL' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Growth Milan' as 'market_name', 'EXGM' as  'market_short_name' , \
                      'EXGM' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Growth Oslo' as 'market_name', 'MERK' as  'market_short_name' , \
                      'MERK' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Growth Paris' as 'market_name', 'ALXP' as  'market_short_name' , \
                      'ALXP' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Growth Paris, Brussels' as 'market_name', 'ALXP. ALXB' as  'market_short_name' ,\
                       'ALXP' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Lisbon' as 'market_name', 'XLIS' as  'market_short_name' , 'XLIS' as  \
                      'main_market_short_name' UNION \
                      SELECT 'Euronext Milan' as 'market_name', 'MTAA' as  'market_short_name' , 'MTAA' as  \
                      'main_market_short_name' UNION \
                      SELECT 'Euronext Paris' as 'market_name', 'XPAR' as  'market_short_name' , 'XPAR' as \
                       'main_market_short_name' UNION \
                      SELECT 'Euronext Paris, Amsterdam' as 'market_name', 'XPAR, XAMS' as  'market_short_name' , \
                      'XPAR' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Paris, Amsterdam, Brussels' as 'market_name', 'XPAR, XAMS, XBRU' as \
                       'market_short_name' , 'XPAR' as  'main_market_short_name' UNION \
                      SELECT 'Euronext Paris, Brussels' as 'market_name', 'XPAR, XBRU' as  'market_short_name' , \
                      'XPAR' as  'main_market_short_name' UNION \
                      SELECT 'Oslo Børs' as 'market_name', 'XOSL' as  'market_short_name' , 'XOSL' as \
                       'main_market_short_name' UNION \
                      SELECT 'Traded not listed Brussels' as 'market_name', 'TNLB' as  'market_short_name' , \
                      'TNLB' as  'main_market_short_name' UNION \
                      SELECT 'Trading After Hours' as 'market_name', 'MTAH' as  'market_short_name' , \
                      'MTAH' as  'main_market_short_name'"
        cur.execute(sql_insert)
        logging.debug(script_name + 'Inserted values into table "euronext_markets".' + repr(e))
    except Exception as e:
        logging.warning(script_name + 'Error inserting values into table "euronext_markets".')

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')

    return None


def main():

    # Variables --------------------------------------------------------------------------------------------------------
    # define variables
    base_dir = os.path.dirname(os.path.abspath(__file__))
    download_path = os.path.join(base_dir, './download')
    db_file = os.path.join(base_dir, 'bolsa.db')

    # Logging Options --------------------------------------------------------------------------------------------------
    # define logging manually, comment to use command line --log=INFO for example
    loglevel = 'INFO'
    logtoconsole = True

    # assuming loglevel is bound to the string value obtained from the command line argument convert case
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    # setup logging options
    if not logtoconsole:
        logging.basicConfig(filename='bolsa.log', encoding='utf-8', level=numeric_level,
                            format='%(asctime)s %(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=numeric_level)

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" started.')

    """ Reference and Historical data ----------------------------------------------------------------------------------
    # get company directory into sqlite database
    # insert_company_directory_sqlite(db_file, download_path)

    # get indice directory into sqlite database
    # insert_indice_directory_sqlite(db_file, download_path)

    # get company information into sqlite database one market at a time
    # insert_company_information_sqlite(db_file, get_company_sqlite(db_file, 'XLIS'))
    
    # Get Historical Quotes
    insert_company_historical_quotes_sqlite(db_file, get_company_sqlite(db_file, market='XLIS'))
    """

    xlis_companies = get_company_sqlite(db_file, market='XLIS')
    insert_company_quotes_sqlite(db_file, xlis_companies)

    for c in xlis_companies:
        insert_company_intraday_quotes_sqlite(db_file, [c])

    logging.info(script_name + '"' + inspect.currentframe().f_code.co_name + '" finished.')


if __name__ == '__main__':
    main()
