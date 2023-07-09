"""
To get the short positions information from stock markets and insert it into and SQLite database.

Available markets:
    belgium, france, germany, italy, portugal, spain, uk

"""


# import packages needed
import urllib.request
import csv
import sqlite3
import os.path
import re
import time
import glob
import pandas as pd
import PyPDF2
import requests
import shutil

from sqlite3 import Error
from bs4 import BeautifulSoup
from numpy.core.defchararray import splitlines
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait


def get_belgium_short_positions(download_path: str):  # should it return a list of files
    """
       :param str download_path: where the files should be downloaded to
       :return: None
    """

    # Spanish short_positions info file link
    url = 'https://www.fsma.be/sites/default/files/media/files/replacement_files/Disclosure%2520net%2520short' \
          '%2520positions%2520-%2520FSMA.xlsx'

    # open link to get file
    response = requests.get(url)
    # set download path and file name
    full_download_path = os.path.join(download_path, 'Disclosure%20net%20short%20positions%20-%20FSMA.xlsx')
    # write to file
    open(full_download_path, 'wb').write(response.content)


def get_croatia_short_positions(download_path: str):
    """
       :param str download_path: where the files should be downloaded to
       :return: None
    """

    # Spanish short_positions info file link
    url = 'http://www.hanfa.hr/getfile/39403/Javna%20objava%20zna%C4%8Dajnih%20neto%20kratkih%20pozicija%20u' \
          '%20dionicama-eng.xlsx'

    # open link to get file
    response = requests.get(url)
    # set download path and file name
    full_download_path = os.path.join(download_path, '0IFhpfzi.xlsx')
    # write to file
    open(full_download_path, 'wb').write(response.content)


def get_france_short_positions(download_path: str, pages: int = 99999):
    """
       :param int pages: number of pages to get since per default it is ordered descenting date, etting top pages is an
                     update
       :param str download_path: where the files shouldbe downloaded to
       :return: None
    """

    # DAX short_positions info home page
    url = 'https://bdif.amf-france.org/en?typesInformation=VAD'

    # the interface for turning on headless mode and download preferences
    options = Options()
    options.add_argument('-headless')  # hide browser window
    options.set_preference('browser.download.folderList', 2)  # set downloads to default directory
    options.set_preference('browser.download.dir', download_path)  # change download default directory
    options.set_preference('browser.download.manager.showWhenStarting', False)  # don't show download manager
    options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/x-gzip')  # don't show diialog
    options.add_argument('--disable-blink-features=AutomationControlled')  # avoid detection

    # aggregate data

    # using Firefox webdriver to secure connection to Firefox
    with webdriver.Firefox(options=options) as driver:
        # remove webdriver property to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # opening the target website in the browser
        driver.implicitly_wait(20)
        driver.get(url)

        # click accept all cookies
        WebDriverWait(driver, 100).until(ec.element_to_be_clickable((By.ID, 'tarteaucitronPersonalize2'))).click()

        # to try and avoid errors that sometimes come up
        time.sleep(5)

        # get result count - Firefox Inspect + Copy XPATH
        result_elements = driver.find_elements(By.XPATH, '/html/body/app-root/div/div/main/app-home-container/section \
                                                        /app-results-container/div[1]/h2')
        result_count_text = result_elements[0].text
        result = re.search(r'(\d+) RESULTS', result_count_text)
        result_count = (int(result.group(1)))
        results_per_page = 20
        num_pages = int((result_count - 20) / results_per_page) + 1

        if pages < num_pages:
            num_pages = pages

        for _ in range(num_pages - 1):
            # get download buttons
            result_elements = driver.find_elements(By.TAG_NAME, 'button')
            for ele in result_elements:
                if ele.text == 'See more':
                    ele.click()
                    time.sleep(5)

        # get download buttons
        result_elements = driver.find_elements(By.TAG_NAME, 'button')

        for ele in result_elements:
            if ele.text == 'downloadDOWNLOAD':
                ele.click()
                time.sleep(5)
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

        # exit
        driver.quit()


def get_germany_short_positions(type_data: str, download_path: str, pages: int = 99999):
    """
       :param int pages: number of pages to get since per default it is ordered descenting date, etting top pages is an
                     update
       :param str type_data: 'latest' for just the curret results, 'history' for everything
       :param str download_path: where the files shouldbe downloaded to
       :return: None
    """

    # DAX short_positions info home page
    url = 'https://www.bundesanzeiger.de/pub/de/nlp?0'

    # the interface for turning on headless mode and download preferences
    options = Options()
    options.add_argument('-headless')  # hide browser window
    options.set_preference('browser.download.folderList', 2)  # set downloads to default directory
    options.set_preference('browser.download.dir', download_path)  # change download default directory
    options.set_preference('browser.download.manager.showWhenStarting', False)  # don't show download manager
    options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/x-gzip')  # don't show diialog
    options.add_argument('--disable-blink-features=AutomationControlled')  # avoid detection

    # aggregate data
    if type_data == 'latest':
        # using Firefox webdriver to secure connection to Firefox
        with webdriver.Firefox(options=options) as driver:
            # remove webdriver property to avoid detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            # opening the target website in the browser
            driver.implicitly_wait(20)
            driver.get(url)

            # click accept all cookies
            WebDriverWait(driver, 100).until(ec.element_to_be_clickable((By.ID, 'cc_all'))).click()

            # to try and avoid errors that sometimes come up
            time.sleep(10)

            # click button to download csv
            WebDriverWait(driver, 1000000).until(ec.element_to_be_clickable((By.ID, 'id13'))).click()

    if type_data == 'history':
        # using Firefox headless webdriver to secure connection to Firefox
        with webdriver.Firefox(options=options) as driver:
            # remove webdriver property to avoid detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            # opening the target website in the browser
            driver.implicitly_wait(10)
            driver.get(url)

            # click accept all cookis
            WebDriverWait(driver, 1000000).until(ec.element_to_be_clickable((By.ID, 'cc_all'))).click()

            # get number of pages
            page_count_elements = driver.find_elements(By.CLASS_NAME, 'page_count')
            page_count_text = page_count_elements[0].text
            result = re.search(r'.+(\b\d+) Seiten', page_count_text)
            page_count = (int(result.group(1)))

            # if pages is defined get n pages
            if pages < page_count:
                page_count = pages

            # loop pages
            for _ in range(page_count):
                # click button to download csv
                historie_elements = driver.find_elements(By.LINK_TEXT, 'Historie')
                for n, ele in enumerate(historie_elements):
                    historie_elements = driver.find_elements(By.LINK_TEXT, 'Historie')
                    WebDriverWait(driver, 1000000).until(ec.element_to_be_clickable(historie_elements[n])).click()
                    csv_elements = driver.find_elements(By.PARTIAL_LINK_TEXT, 'Als CSV')
                    WebDriverWait(driver, 1000000).until(ec.element_to_be_clickable(csv_elements[0])).click()
                    print(csv_elements[0].text)
                    driver.back()
                    time.sleep(10)
                WebDriverWait(driver, 1000000).until(ec.element_to_be_clickable((By.CLASS_NAME, 'next'))).click()

    # exit
    driver.quit()


def get_italy_short_positions(download_path: str):
    """
        :param str download_path: where the files shouldbe downloaded to
       :return: None
    """

    # DAX short_positions info home page
    url = 'https://www.consob.it/web/consob-and-its-activities/short-selling'

    # the interface for turning on headless mode and download preferences
    options = Options()
    options.add_argument('-headless')  # hide browser window
    options.set_preference('browser.download.folderList', 2)  # set downloads to default directory
    options.set_preference('browser.download.dir', download_path)  # change download default directory
    options.set_preference('browser.download.manager.showWhenStarting', False)  # don't show download manager
    options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/x-gzip')  # don't show diialog
    options.add_argument('--disable-blink-features=AutomationControlled')  # avoid detection

    # using Firefox webdriver to secure connection to Firefox
    with webdriver.Firefox(options=options) as driver:
        # remove webdriver property to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # opening the target website in the browser
        driver.implicitly_wait(20)
        driver.get(url)

        # click to cookies
        WebDriverWait(driver, 100).until(ec.element_to_be_clickable((By.ID, 'btnAcceptCookie'))).click()
        # pause 5 seconds
        time.sleep(5)

        # click download file
        WebDriverWait(driver, 20).until(ec.element_to_be_clickable((By.LINK_TEXT, "Download file"))).click()
        time.sleep(5)

    # exit
    driver.quit()


def get_portugal_short_positions(type_data: str) -> list:
    """
    :param str type_data:'comm' : positions communicated or 'agg' : aggregate positions
    :return a list with results of CMVM web scraping
    :rtype: list
    """

    # CMVM short_positions info home page
    main_url = 'https://web3.cmvm.pt/english/sdi/emitentes/shortselling/'  # list of companies

    # get html with list of companies
    client = urllib.request.urlopen(main_url)
    html_page = client.read()
    client.close()

    # get html parsed
    page_soup = BeautifulSoup(html_page, 'html.parser')

    # get list of companies
    company_list = page_soup.find_all('article')
    # company_list = company_list[:1]

    # initialize list to be returned
    data = []

    # aggregate data
    if type_data == 'agg':

        # loop list of companies
        for company in company_list:  # loop list of companies
            company_link = company.a['href']  # get links to the page from each company
            company_name = company.a['title']  # get name of company
            company_page_link = main_url + company_link  # set full link to open
            client = urllib.request.urlopen(company_page_link)  # open link
            html_page = client.read()
            client.close()
            company_soup = BeautifulSoup(html_page, 'html.parser')
            company_file_list = company_soup.select('a[href*=hist_]')

            # find tet of total value for current date
            matched_tags = company_soup.find_all(
                lambda tag: len(tag.find_all()) == 0 and 'Total short positions as at' in tag.text)

            # parse text to get date and agg value
            if len(matched_tags) == 1 and len(matched_tags[0].text) > 28:
                current_text = matched_tags[0].text[28::]
                curr_date = current_text[:10:]
                curr_agg = current_text[12::]
                # add to list
                cols = [company_name] + list(curr_date.split("#")) + list(curr_agg.split("#"))
                data.append([ele for ele in cols])

            # loop links
            for file_link in company_file_list:
                partial_file_link = file_link['href']
                final_file_link = main_url + partial_file_link  # get the link to the actual page
                client = urllib.request.urlopen(final_file_link)
                html_page = client.read()
                client.close()
                file_soup = BeautifulSoup(html_page, 'html.parser')
                table = file_soup.find('table', {'class': 'WTabela'})

                # get each row from the table on the page, some are empty
                try:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        cols = [company_name] + [ele.text.strip() for ele in cols]
                        if len(cols) == 3 and len(
                                cols[1]) == 10:  # only those that have a date and all 3 columns filled out
                            data.append([ele for ele in cols])
                except AttributeError:  # ignore empty tables
                    pass

        # decompose list in columns
        df1 = [item[0] for item in data if item]
        df2 = [item[1] for item in data if item]
        df3 = [item[2] for item in data if item]

        # format date on the 2nd column
        df2 = [sub.replace('/', '-') for sub in df2]
        df2 = [sub[6:11] + sub[2:5] + '-' + sub[0:2] for sub in df2]

        # combine lists back together
        data = tuple(zip(df1, df2, df3))

    if type_data == 'comm':

        # loop list of companies
        for company in company_list:
            company_link = company.a['href']  # get links to the page from each company
            company_name = company.a['title']  # get name of company
            company_page_link = main_url + company_link  # set full link to open
            client = urllib.request.urlopen(company_page_link)
            html_page = client.read()
            client.close()
            company_soup = BeautifulSoup(html_page, 'html.parser')

            # get table on main company page
            table = company_soup.find('table', {'class': 'WTabela'})

            # get each row from the table on the page, some are empty
            try:
                rows = table.find_all('tr')

                for row in rows:
                    cols = row.find_all('td')
                    cols = [company_name] + [ele.text.strip() for ele in cols]

                    if len(cols) == 6 and len(
                            cols[3]) == 10:  # only those that have a date and all 3 columns filled out
                        data.append([ele for ele in cols])
            except AttributeError:  # ignore empty tables
                pass

            # loop links
            company_file_list = company_soup.select('a[href*=historico_]')  # select links for the communications
            for file_link in company_file_list:
                partial_file_link = file_link['href']
                final_file_link = main_url + partial_file_link  # get the link to the actual page
                client = urllib.request.urlopen(final_file_link)
                html_page = client.read()
                client.close()
                file_soup = BeautifulSoup(html_page, 'html.parser')
                table = file_soup.find('table', {'class': 'WTabela'})
                try:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        cols = [company_name] + [ele.text.strip() for ele in cols]
                        if len(cols) == 5 and len(cols[3]) == 10:  # only those that have a date and all 5 columns
                            # filled out
                            data.append([ele for ele in cols])
                except AttributeError:  # ignore empty tables
                    pass

        # decompose list
        df1 = [item[0] for item in data if item]
        df2 = [item[1] for item in data if item]
        df3 = [item[2] for item in data if item]
        df4 = [item[3] for item in data if item]
        df5 = [item[4] for item in data if item]

        # format date on 3rd and 4th columns
        df4 = [sub.replace('/', '-') for sub in df4]
        df4 = [sub[6:11] + sub[2:5] + '-' + sub[0:2] for sub in df4]
        df5 = [sub.replace('/', '-') for sub in df5]
        df5 = [sub[6:11] + sub[2:5] + '-' + sub[0:2] for sub in df5]

        # combine lists back together
        data = tuple(zip(df1, df2, df3, df4, df5))

    return data


def get_spain_short_positions(download_path: str):
    """
       :param str download_path: where the files shouldbe downloaded to
       :return: None
    """

    # Spanish short_positions info file link
    url = 'https://www.cnmv.es/DocPortal/Posiciones-Cortas/NetShortPositions.xls'

    # open link to get file
    response = requests.get(url)
    # set download path and file name
    full_download_path = os.path.join(download_path, 'NetShortPositions.xls')
    # write to file
    open(full_download_path, 'wb').write(response.content)


def get_uk_short_positions(download_path: str):
    """
       :param str download_path: where the files shouldbe downloaded to
       :return: None
    """

    # Spanish short_positions info file link
    url = 'https://www.fca.org.uk/publication/data/short-positions-daily-update.xlsx'

    # open link to get file
    response = requests.get(url)
    # set download path and file name
    full_download_path = os.path.join(download_path, 'short-positions-daily-update.xlsx')
    # write to file
    open(full_download_path, 'wb').write(response.content)


def export_csv_file(data: list, filename: str):
    """
    :param list data: the list generated either with the 'agg' or 'comm'
    :param str filename: to export the results in text format
    :return: None

    """

    with open(filename, 'w') as f:
        write = csv.writer(f)
        write.writerows(data)

    return None


def import_pdf(file_name: str, page_number: int) -> list:
    """
       :param file_name: full file path and file name
       :param page_number

       :return: list
    """

    pdf_file = open(file_name, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    pdf = pdf_reader.getPage(page_number)
    pdf_text = pdf.extractText()
    pdf_file.close()

    pdf_array = splitlines(pdf_text)
    pdf_list = pdf_array.tolist()

    return pdf_list


def insert_sqlite(conn: sqlite3, country: str, data: list, truncate: bool = False, create_table: bool = False) -> int:
    """
    :param bool truncate: truncate existing table
    :param str country: for different set of rules and tables
    :param bool create_table: yes/no
    :param sqlite3 conn: datanase connection
    :param list data: 'comm' data to be exported to database
    :return int : number of rows
    """

    cur = conn.cursor()

    sql_delete = ''
    sql_create = ''
    sql_insert = ''

    match country:
        case 'belgium_archive':
            swap_data = []
            for ele in data:
                swap_data.append((ele[0], ele[1], ele[2], ele[4], ele[3]))
            data = swap_data

            # format data
            data.pop(0)  # delete first list
            del data[len(data) - 2:]  # delete last 2 elements

            sql_delete = 'DELETE FROM "short_positions_belgium_archive"'
            sql_create = 'CREATE TABLE "short_positions_belgium_archive" ("holder_of_position" text,"company" text,\
                         "isin" text, "p_of_capital" REAL, "date" date, UNIQUE("holder_of_position","company","isin" \
                          ,"date","p_of_capital"))'
            sql_insert = 'INSERT INTO "short_positions_belgium_archive" ("holder_of_position","company","isin", \
                                  "p_of_capital", "date") VALUES(?,?,?,?,?) on conflict do nothing;'
        case 'belgium_positions':
            # format data
            data.pop(0)  # delete first list
            del data[len(data) - 2:]  # delete last 2 elements
            data = data[1:]

            sql_delete = 'DELETE FROM "short_positions_belgium_positions"'
            sql_create = 'CREATE TABLE "short_positions_belgium_positions" ("holder_of_position" text,"company" text,\
                         "isin" text, "p_of_capital" REAL, "date" date, UNIQUE("holder_of_position","company","isin" \
                         ,"date","p_of_capital"))'
            sql_insert = 'INSERT INTO "short_positions_belgium_positions" ("holder_of_position","company","isin", \
                          "p_of_capital", "date") VALUES(?,?,?,?,?) on conflict do nothing;'

        case 'belgium_former_positions':  # ----------------------------------------------------------------------------
            # format data
            data.pop(0)  # delete first list
            del data[len(data) - 2:]  # delete last 2 elements
            data = data[1:]

            sql_delete = 'DELETE FROM "short_positions_belgium_former_positions"'
            sql_create = 'CREATE TABLE "short_positions_belgium_former_positions" ("holder_of_position" text,"company"\
             text,"isin" text, "p_of_capital" REAL, "date" date, "close_date" date, UNIQUE("holder_of_position",\
                         "company","isin","p_of_capital","date","close_date"))'
            sql_insert = 'INSERT INTO "short_positions_belgium_former_positions" ("holder_of_position","company","isin"\
            ,"p_of_capital", "date","close_date") VALUES(?,?,?,?,?,?) on conflict do nothing;'

        case 'france':  # ----------------------------------------------------------------------------------------------
            # format data
            # check for different versions of the pdf
            cut = 0
            for n, dt in enumerate(data):
                result = re.search(r'(of the AMF)', data[n])  # get date
                if result is not None:
                    cut = n

            for n, dt in enumerate(data):
                result = re.search(r'(data with the CNIL)', data[n])  # get date
                if result is not None:
                    cut = n

            data = data[cut + 1:]

            match len(data):
                case 5:
                    # check where the decimal value is
                    result = re.search(r'(\d{0,2}\.\d{1,2})?', data[3])  # get decimal value
                    if result.group(1) is not None:
                        data[3] = result.group(1)  # get decimal value

                    result = re.search(r'(\d{0,2}\.\d{1,2})?', data[4])  # get decimal value
                    if result.group(1) is not None:
                        data[4] = result.group(1)  # get decimal value
                        # concatenate first 2 entries that correspond to 2 lines in pdf
                        if len(data[0]) > len(data[2]):
                            data[0] = data[0] + ' ' + data[1]
                            data[1] = data[2]
                            data.pop(1)
                    data.append('')
                case 6:

                    data[0] = data[0] + ' ' + data[1]
                    data[1] = data[2]
                    data.pop(1)

                    result = re.search(r'(\d{0,2}\.\d{1,2})?', data[len(data) - 2])  # get decimal value
                    if result is not None:
                        data[len(data) - 2] = result.group(1)  # get decimal value
                    data.append('')
                case 8:
                    data.pop(6)
                    data.pop(5)
                    result = re.search(r'(\d{0,2}\.\d{1,2})?', data[len(data) - 3])  # get decimal value
                    if result is not None:
                        data[len(data) - 3] = result.group(1)  # get decimal value
                    result = re.search(r'(\d{4}-\d{2}-\d{2})', data[len(data) - 2])  # get date
                    if result is not None:
                        data[len(data) - 2] = result.group(1)  # get decimal value
                    result = re.search(r'(\d{4}-\d{2}-\d{2})', data[len(data) - 1])  # get date
                    if result is not None:
                        data[len(data) - 1] = result.group(1)  # get decimal value
                case 9:
                    data[0] = data[0] + ' ' + data[1]
                    data[1] = data[2]

                    data.pop(1)
                    data.pop(6)
                    data.pop(5)
                    result = re.search(r'(\d{0,2}\.\d{1,2})?', data[len(data) - 3])  # get decimal value
                    if result is not None:
                        data[len(data) - 3] = result.group(1)  # get decimal value
                    result = re.search(r'(\d{4}-\d{2}-\d{2})', data[len(data) - 2])  # get date
                    if result is not None:
                        data[len(data) - 2] = result.group(1)  # get decimal value
                    result = re.search(r'(\d{4}-\d{2}-\d{2})', data[len(data) - 1])  # get date
                    if result is not None:
                        data[len(data) - 1] = result.group(1)  # get decimal value

            new_data = [data]
            data = new_data

            sql_delete = 'DELETE FROM "short_positions_france"'
            sql_create = 'CREATE TABLE CREATE TABLE "short_positions_france" ("holder_of_position" text, "company"\
                         text, "isin" text, "p_of_capital" REAL, "date" date, "cancellation_date" date,\
                         UNIQUE("holder_of_position", "company", "isin" ,"p_of_capital" ,"date" ,"cancellation_date"))'
            sql_insert = 'INSERT INTO "short_positions_france" ("holder_of_position","company","isin",\
                         "p_of_capital","date","cancellation_date") VALUES(?,?,?,?,?,?) on conflict do nothing;'

        case 'germany':  # ---------------------------------------------------------------------------------------------
            sql_delete = 'DELETE FROM "short_positions_germany"'
            sql_create = 'CREATE TABLE "short_positions_germany" ("holder_of_position" text,"company"	text,"isin"\
                         text, "p_of_capital"	REAL,"date"	date,UNIQUE("holder_of_position","company","isin",\
                         "p_of_capital","date")'
            sql_insert = 'INSERT INTO "short_positions_germany" ("holder_of_position","company","isin","p_of_capital",\
                         "date") VALUES(?,?,?,?,?) on conflict do nothing;'

        case 'italy_current':  # ---------------------------------------------------------------------------------------
            data = data[1:]

            sql_delete = 'DELETE FROM "short_positions_italy_current"'
            sql_create = 'CREATE TABLE "short_positions_italy_current" ("holder_of_position" text,"holder_lei" text,\
                         "company" text, "company_lei" text,"isin" text, "p_of_capital" REAL, "date" date,\
                         UNIQUE("holder_of_position","holder_lei","company","company_lei",\
                         "isin","p_of_capital","date"))'
            sql_insert = 'INSERT INTO "short_positions_italy_current" ("holder_of_position","holder_lei",\
                         "company","company_lei","isin","p_of_capital","date") VALUES(?,?,?,?,?,?,?) on conflict\
                         do nothing;'

        case 'italy_history':  # ---------------------------------------------------------------------------------------
            data = data[1:]

            sql_delete = 'DELETE FROM "short_positions_italy_history"'
            sql_create = 'CREATE TABLE "short_positions_italy_history" ("holder_of_position" text,"holder_lei" text,\
                                 "company" text, "company_lei" text,"isin" text, "p_of_capital" REAL, "date" date,\
                                 UNIQUE("holder_of_position","holder_lei","company","company_lei",\
                                 "isin","p_of_capital","date"))'
            sql_insert = 'INSERT INTO "short_positions_italy_history" ("holder_of_position","holder_lei",\
                                 "company","company_lei","isin","p_of_capital","date") VALUES(?,?,?,?,?,?,?) on\
                                 conflict do nothing;'

        case 'portugal_agg':  # ----------------------------------------------------------------------------------------
            sql_delete = 'DELETE FROM "short_positions_portugal_agg"'
            sql_create = 'CREATE TABLE "short_positions_portugal_agg" ("company"	text,"date"	text,"p_of_capital"\
            real,UNIQUE("date","company"))'
            sql_insert = 'INSERT INTO "short_positions_portugal_agg"("company","date","p_of_capital")\
                         VALUES(?,?,?) on conflict do nothing;'

        case 'portugal_comm':  # ---------------------------------------------------------------------------------------
            sql_delete = 'DELETE FROM "short_positions_portugal_comm"'
            sql_create = 'CREATE TABLE "short_positions_portugal_comm" ("company"	text,"holder_of_position"\
                         text,"p_of_capital" REAL, "communication_date"	date,"position_date" date,\
                         UNIQUE("communication_date","company","holder_of_position","position_date"))'
            sql_insert = 'INSERT INTO "short_positions_portugal_comm" ("company","holder_of_position","p_of_capital",\
                         "communication_date","position_date") VALUES(?,?,?,?,?) on conflict do nothing;'

        case 'spain':  # -----------------------------------------------------------------------------------------------
            # format data
            data.pop(0)  # delete first list
            for d in data:  # delete first column in the inner list
                d.pop(0)
            data = data[2:]

            sql_delete = 'DELETE FROM "short_positions_spain"'
            sql_create = 'CREATE TABLE "short_positions_spain" ("lei" text, "company" text, "holder_of_position" text,\
                         "date" date, "p_of_capital" REAL, UNIQUE("lei","company","holder_of_position","date",\
                         "p_of_capital"))'
            sql_insert = 'INSERT INTO "short_positions_spain" ("lei","company","holder_of_position","date",\
                         "p_of_capital") VALUES(?,?,?,?,?) on conflict do nothing;'

        case 'uk':  # --------------------------------------------------------------------------------------------------
            # format data

            # convert timestamp to string
            new_data = []
            for ele in data:
                ele[4] = str(ele[4])
                new_data.append(ele)
            data = new_data

            sql_delete = 'DELETE FROM "short_positions_uk"'
            sql_create = 'CREATE TABLE "short_positions_uk" ("holder_of_position" text, "company" text, "isin" text,\
                          "p_of_capital" REAL, "date" str, UNIQUE("holder_of_position","company", "isin",\
                          "p_of_capital","date"))'
            sql_insert = 'INSERT INTO "short_positions_uk" ("holder_of_position","company", "isin", "p_of_capital",\
                          "date") VALUES(?,?,?,?,?) on conflict do nothing;'

    if truncate:
        cur.execute(sql_delete)

    if create_table:
        cur.execute(sql_create)

    for item in data:
        cur.execute(sql_insert, item)

    cur.close()
    conn.commit()

    return cur.lastrowid


def main():
    # set constants
    base_dir = os.path.dirname(os.path.abspath(__file__))
    download_file_path = os.path.join(base_dir, './download')
    error_file_path = os.path.join(download_file_path, './error')
    db_file = os.path.join(base_dir, 'bolsa.db')
    truncate_db = True

    # error
    error_counter = 0

    # create a database connection
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    # belgium ----------------------------------------------------------------------------------------------------------
    # get files
    get_belgium_short_positions(download_file_path)

    # get list of files
    file_mask = 'Disclosure*FSMA*.xlsx'
    file_list = glob.glob(download_file_path + '/' + file_mask)

    # loop files
    for file in file_list:
        data_file = os.path.join(download_file_path, file)
        path = os.path.split(data_file)
        data_file_error = os.path.join(error_file_path, path[1])

        try:
            data = pd.read_excel(data_file, 'Archives')
            data_list = data.values.tolist()
            insert_sqlite(conn, 'belgium_archive', data_list, truncate_db)

            data = pd.read_excel(data_file, 'Former positions')
            data_list = data.values.tolist()
            insert_sqlite(conn, 'belgium_former_positions', data_list, truncate_db)

            data = pd.read_excel(data_file, 'Current positions')
            data_list = data.values.tolist()
            insert_sqlite(conn, 'belgium_positions', data_list, truncate_db)

        except Exception:
            print("Error inserting file " + file)
            error_counter = error_counter + 1
            shutil.move(data_file, data_file_error)
            pass
        else:
            print('short positions from belgium imported.')
            os.remove(data_file)
      
    # france -----------------------------------------------------------------------------------------------------------
    # get files
    get_france_short_positions(download_file_path, 4)

    # get list of files
    file_mask = 'DPCACT*.pdf'
    file_list = glob.glob(download_file_path + '/' + file_mask)

    # loop files
    for file in file_list:
        data_file = os.path.join(download_file_path, file)
        path = os.path.split(data_file)
        data_file_error = os.path.join(error_file_path, path[1])
        data_list = import_pdf(data_file, 0)

        try:
            insert_sqlite(conn, 'france', data_list)
        except Exception:
            print("Error inserting file " + file)
            error_counter = error_counter + 1
            shutil.move(data_file, data_file_error)
            pass
        else:
            print('short positions from france imported.')
            os.remove(data_file)

    # germany ----------------------------------------------------------------------------------------------------------
    # get files
    get_germany_short_positions('latest', download_file_path)

    # get list of files
    file_mask = 'leerverkaeufe_*.csv'
    file_list = glob.glob(download_file_path + '/' + file_mask)

    # loop files
    for file in file_list:
        data_file = os.path.join(download_file_path, file)
        path = os.path.split(data_file)
        data_file_error = os.path.join(error_file_path, path[1])

        try:
            data = pd.read_csv(data_file)
            data_list = data.values.tolist()
            insert_sqlite(conn, 'germany', data_list, truncate_db)
        except Exception:
            print("Error inserting file " + file)
            error_counter = error_counter + 1
            shutil.move(data_file, data_file_error)
            pass
        else:
            print('short positions from germany imported.')
            os.remove(data_file)
    
    # italy ------------------------------------------------------------------------------------------------------------
    # get files
    get_italy_short_positions(download_file_path)

    # get list of files
    file_mask = 'PncPubbl*.xlsx'
    file_list = glob.glob(download_file_path + '/' + file_mask)

    # loop files
    for file in file_list:
        data_file = os.path.join(download_file_path, file)
        path = os.path.split(data_file)
        data_file_error = os.path.join(error_file_path, path[1])

        try:
            data = pd.read_excel(data_file, ' Correnti - Current ')
            data_list = data.values.tolist()
            insert_sqlite(conn, 'italy_current', data_list, truncate_db)

            data = pd.read_excel(data_file, ' Storiche - Historic ')
            data_list = data.values.tolist()
            insert_sqlite(conn, 'italy_history', data_list, truncate_db)

        except Exception:
            print("Error inserting file " + file)
            error_counter = error_counter + 1
            shutil.move(data_file, data_file_error)
            pass
        else:
            print('short positions from italy imported.')
            os.remove(data_file)

    # portugal ---------------------------------------------------------------------------------------------------------
    try:
        data = get_portugal_short_positions('agg')
        insert_sqlite(conn, 'portugal_agg', data, truncate_db)
        data = get_portugal_short_positions('comm')
        insert_sqlite(conn, 'portugal_comm', data, truncate_db)
    except Exception:
        print("Error inserting portugal.")
        error_counter = error_counter + 1
        pass
    else:
        print('short positions from portugal imported.')
    
    # spain ------------------------------------------------------------------------------------------------------------
    # get files
    get_spain_short_positions(download_file_path)

    # get list of files
    file_mask = 'NetShortPositions*.xls'
    file_list = glob.glob(download_file_path + '/' + file_mask)

    # loop files
    for file in file_list:
        data_file = os.path.join(download_file_path, file)
        path = os.path.split(data_file)
        data_file_error = os.path.join(error_file_path, path[1])

        try:
            data = pd.read_excel(data_file, 'Vivas - Outstanding positions')
            data_list = data.values.tolist()
            insert_sqlite(conn, 'spain', data_list, truncate_db)
        except Exception:
            print("Error inserting file " + file)
            error_counter = error_counter + 1
            shutil.move(data_file, data_file_error)
            pass
        else:
            print('short positions from spain imported.')
            os.remove(data_file)

    # uk ---------------------------------------------------------------------------------------------------------------
    # get files
    get_uk_short_positions(download_file_path)

    # get list of files
    file_mask = 'short-positions-daily-update*.xlsx'
    file_list = glob.glob(download_file_path + '/' + file_mask)

    # loop files
    for file in file_list:
        data_file = os.path.join(download_file_path, file)
        path = os.path.split(data_file)
        data_file_error = os.path.join(error_file_path, path[1])

        try:
            data = pd.read_excel(data_file, sheet_name=0)
            data_list = data.values.tolist()
            insert_sqlite(conn, 'uk', data_list, truncate_db)

            data = pd.read_excel(data_file, sheet_name=1)
            data_list = data.values.tolist()
            insert_sqlite(conn, 'uk', data_list, truncate_db)
        except Exception:
            print("Error inserting file " + file)
            error_counter = error_counter + 1
            shutil.move(data_file, data_file_error)
            pass
        else:
            print('short positions from uk imported.')
            os.remove(data_file)


if __name__ == '__main__':
    main()
