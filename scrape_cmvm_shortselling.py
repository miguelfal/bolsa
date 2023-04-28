"""
To get the information from CMVM on short positions in Lisbon Stock Market and input into SQLite
database

There are 2 types of information:

1) the short selling aggregate numbers
2) the short selling communications

"""

# import packages needed
import urllib.request
import csv
import sqlite3

from sqlite3 import Error
from bs4 import BeautifulSoup


def get_cmvm_shortselling(type_data: str, output_file_name: str = '') -> list:
    """
    Get with the information on short positions by company from the CMVM website

    :args:
    type:
        'comm' : positions communicated
        'agg' : aggregate positions
    output_file_name:
        name of csv file to export

    :return:
    list with the information on new communications short positions by company
    """

    # set urls
    main_url = 'https://web3.cmvm.pt/english/sdi/emitentes/shortselling/'  # list of companies

    # get html with list of companies
    client = urllib.request.urlopen(main_url)
    html_page = client.read()
    client.close()

    # get html parsed
    page_soup = BeautifulSoup(html_page, 'html.parser')

    # get list of companies
    company_list = page_soup.find_all('article')

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

    if len(output_file_name) > 0:
        if type_data == 'agg':
            column_names = ['company', 'date', '% of capital']
        else:
            column_names = ['company', 'holder of position', '% of capital', 'communication date', 'position date']

        with open(output_file_name, 'w') as f:
            write = csv.writer(f)
            write.writerow(column_names)
            write.writerows(data)

    return data


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def insert_short_agg(conn: sqlite3, data: list) -> int:
    """
    Create a new project into the projects table
    :param conn:
    :param data:
    :return: project id
    """
    cur = conn.cursor()
    sql = 'DELETE FROM short_selling_agg'
    cur.execute(sql)

    sql = 'INSERT INTO short_selling_agg(company,date,p_of_capital) VALUES(?,?,?)'

    for item in data:
        cur.execute(sql, item)
    cur.close()
    conn.commit()
    return cur.lastrowid


def insert_short_comm(conn: sqlite3, data: list) -> int:
    """
    Create a new task
    :param conn:
    :param data:
    :return:
    """

    cur = conn.cursor()
    sql = 'DELETE FROM short_selling_comm'
    cur.execute(sql)
    sql = 'INSERT INTO short_selling_comm(company,holder_of_position,p_of_capital,communication_date,position_date) ' \
          'VALUES(?,?,?,?,?)'

    for item in data:
        cur.execute(sql, item)
    cur.close()
    conn.commit()

    return cur.lastrowid


def main():

    # set database name
    database = r'bolsa.db'

    # create a database connection
    conn = create_connection(database)

    # write to tables
    with conn:
        project_id = insert_short_agg(conn, get_cmvm_shortselling('agg'))
        project_id = insert_short_comm(conn, get_cmvm_shortselling('comm'))


if __name__ == '__main__':
    main()
