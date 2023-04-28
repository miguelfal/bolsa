# importar  libs
import urllib.request
import math
import csv
import sys

from bs4 import BeautifulSoup

# set default output file name
output_file_name = 'short_selling_lisboa.csv'
output_file_name_coms = 'short_selling_lisboa_coms.csv'

# set file name to first argument if exists
if len(sys.argv)>1:
    output_file_name = sys.argv[1]

# url inicial para começar
main_url="https://web3.cmvm.pt/english/sdi/emitentes/shortselling/index.cfm"
shortselling_url="https://web3.cmvm.pt/english/sdi/emitentes/shortselling/"

# obter página inicial
client = urllib.request.urlopen(main_url)
html_page = client.read()
client.close()

# obter html
page_soup = BeautifulSoup(html_page, "html.parser")

company_list = page_soup.find_all('article')

#company_list = company_list[0:2]
#print(len(company_list))
#print(company_list)

data = [] #aggregate positions
data_coms = [] #communications per entitie


for company in company_list:
     company_link = company.a['href']
     company_name = company.a['title']
     #print(company_name)
     company_page_link = shortselling_url + company_link
     client = urllib.request.urlopen(company_page_link)
     html_page = client.read()
     client.close()
     company_soup =  BeautifulSoup(html_page, "html.parser")
     company_file_list = company_soup.select("a[href*=hist_]")
     for file_link in company_file_list:
         partial_file_link= file_link['href']
         final_file_link = shortselling_url + partial_file_link
         client = urllib.request.urlopen(final_file_link)
         html_page = client.read()
         client.close()
         file_soup = BeautifulSoup(html_page, "html.parser")
         table = file_soup.find('table', {"class": "WTabela"})
         try:
             rows = table.find_all('tr')
             for row in rows:
                 cols = row.find_all('td')
                 cols = [company_name] + [ele.text.strip() for ele in cols]
                 if len(cols)==3 and len(cols[1])==10: # Get rid of empty values
                        data.append([ele for ele in cols])
         except AttributeError: #ignore empty tables>
             pass

     company_file_list = company_soup.select("a[href*=historico_]")
     for file_link in company_file_list:
         partial_file_link = file_link['href']
         final_file_link = shortselling_url + partial_file_link
         client = urllib.request.urlopen(final_file_link)
         html_page = client.read()
         client.close()
         file_soup = BeautifulSoup(html_page, "html.parser")
         table = file_soup.find('table', {"class": "WTabela"})
         try:
             rows = table.find_all('tr')
             for row in rows:
                 cols = row.find_all('td')
                 cols = [company_name] + [ele.text.strip() for ele in cols]
                 if len(cols) == 5 and len(cols[3])==10:  # Get rid of empty values
                     data_coms.append([ele for ele in cols])
         except AttributeError:  # ignore empty tables>
             pass

# decompose list
df1 = [item[0] for item in data if item]
df2 = [item[1] for item in data if item]
df3 = [item[2] for item in data if item]

# format date
df2 = [sub.replace('/', '-') for sub in df2]
df2 = [sub[6:11]+sub[2:5]+'-'+sub[0:2] for sub in df2]

# combine lists
data = tuple(zip(df1, df2, df3))

column_names = ['company', 'date', '% of capital']
with open(output_file_name, 'w') as f:
    write = csv.writer(f)
    write.writerow(column_names)
    write.writerows(data)

# decompose list
df1 = [item[0] for item in data_coms if item]
df2 = [item[1] for item in data_coms if item]
df3 = [item[2] for item in data_coms if item]
df4 = [item[3] for item in data_coms if item]
df5 = [item[4] for item in data_coms if item]

# format date
df4 = [sub.replace('/', '-') for sub in df4]
df4 = [sub[6:11]+sub[2:5]+'-'+sub[0:2] for sub in df4]

df5 = [sub.replace('/', '-') for sub in df5]
df5 = [sub[6:11]+sub[2:5]+'-'+sub[0:2] for sub in df5]

# combine lists
data_coms = tuple(zip(df1, df2, df3, df4, df5))

column_names = ['company', 'holder of position', '% of capital', 'communication date', 'position date']
with open(output_file_name_coms, 'w') as f:
    write = csv.writer(f)
    write.writerow(column_names)
    write.writerows(data_coms)

# decompose list
df1 = [item[0] for item in data_coms if item]
df2 = [item[1] for item in data_coms if item]
df3 = [item[2] for item in data_coms if item]
df4 = [item[3] for item in data_coms if item]
df5 = [item[4] for item in data_coms if item]