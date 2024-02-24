#!/usr/bin/env python
# coding: utf-8

# In[1]:


# get_ipython().system('pip install -r requirements.txt')


# In[2]:


# Google Sheet API
from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
import json
import time

start_time = time.time()  # Record the start time


# def get_dynamic_range(service, spreadsheet_id, sheet_name, starting_cell='A2'):
#     # Get the last row with data in the specified sheet
#     request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=f'{sheet_name}!A:A')
#     response = request.execute()
#     values = response.get('values', [])

#     if not values:
#         print('No data found.')
#         return None

#     # Filter rows with at least one non-empty cell
#     filtered_values = [row for row in values if any(cell.strip() for cell in row)]

#     if not filtered_values:
#         print('No non-empty rows found.')
#         return None

#     # Find the last row with data
#     last_row = len(filtered_values)

#     # Construct the dynamic range
#     dynamic_range = f"{sheet_name}!{starting_cell}:E{last_row}"

#     return dynamic_range

# def get_all_researchers_data():
#     SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
#     SAMPLE_SPREADSHEET_ID = '1PqIcpTPeb7_CuvTtQhb0p1OySDGArqF6auQVmz_jF8c'
#     SHEET_NAME = 'Sheet1'

#     creds = None
#     if os.path.exists('token.json'):
#         creds = Credentials.from_authorized_user_file('token.json', SCOPES)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             print(f'Token expires at: {creds.expiry}')
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 'credentials.json', SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json())

#     try:
#         service = build('sheets', 'v4', credentials=creds)

#         # Get the dynamic range based on the last row with data
#         dynamic_range = get_dynamic_range(service, SAMPLE_SPREADSHEET_ID, SHEET_NAME)

#         # Call the Sheets API with the dynamic range
#         result = service.spreadsheets().values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
#                                                     range=dynamic_range).execute()
#         values = result.get('values', [])

#         if not values:
#             print('No data found.')
#             return

#         all_researcher_data = []
#         for row in values:
#             if row:
#                 data_records = {
#                     "nama": row[0] if len(row) > 0 else '',
#                     "link_scholar": row[1] if len(row) > 1 else '',
#                     "jabatan": row[2] if len(row) > 2 else '',
#                     "profile_url": row[3] if len(row) > 3 else ''
#                 }
#                 all_researcher_data.append(data_records)
#         list_peneliti = pd.DataFrame(all_researcher_data)
#         print("get data finish")
#         return list_peneliti
#     except HttpError as err:
#         print(err)

# print(get_all_researchers_data())


# In[3]:


# Scrapping

from selenium import webdriver
import chromedriver_autoinstaller_fix
from selenium.webdriver.common.keys import Keys
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver import ChromeOptions  # for suppressing the browser


csv_file = pd.read_csv("https://raw.githubusercontent.com/pkr-br/scholar-scraping/main/list_peneliti.csv")
list_peneliti = csv_file
list_peneliti = list_peneliti[list_peneliti['link_scholar'].notna()]
added_link = "&view_op=list_works&sortby=pubdate"
list_peneliti["updated_link_scholar"] = [i+added_link for i in list_peneliti['link_scholar']]
chromedriver_autoinstaller_fix.install()
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
driver = webdriver.Chrome()

all_publications = {}
for index, row in list_peneliti.iterrows():
    start_scrap_one = time.time()
    nama_peneliti = row["nama"]
    URL = row["updated_link_scholar"]
    driver.get(URL)
    driver.implicitly_wait(2)

    for i in range(5):
        btn = driver.find_elements(By.XPATH , '//button[@id="gsc_bpf_more"]')[0]
        disabled = btn.get_attribute("disabled")
        if not disabled:
            btn.click()
            time.sleep(3)
            print("click " + str(i + 1))
        elif disabled:
            break
    print("click finish " + nama_peneliti)

#     Extract h-index
    index_table = driver.find_element(By.ID, "gsc_rsb_st")
    h_index_row = index_table.find_elements(By.TAG_NAME, "tr")[2]
    h_index = h_index_row.find_element(By.CLASS_NAME, "gsc_rsb_std").text
    
#     Extract specialities
    specialities = driver.find_elements(By.CLASS_NAME, "gsc_prf_inta.gs_ibl")
    # Check if specialities exist
    if specialities:
        # If specialities exist, extract text from each element and store it in a list
        speciality_list = [element.text for element in specialities]
    else:
        speciality_list = []
    

    publications = driver.find_elements(By.CLASS_NAME, "gsc_a_tr")
    publications_list = []
    for publication in publications:
        data_list = {}
        title = publication.find_element(By.CLASS_NAME, "gsc_a_at").text
        data_list["title"] = str(title)
        link = publication.find_element(By.CLASS_NAME, "gsc_a_at").get_attribute("href")
        data_list['link'] = str(link)
        year = publication.find_element(By.CLASS_NAME, "gsc_a_y").text
        if(year != ""):
            data_list["year"] = int(year)
        citate = publication.find_element(By.CLASS_NAME, "gsc_a_c").text
        if "\n*" in citate:
            citate = citate.replace("\n*", "")
        if(citate != ""):
            data_list["cited by"] = int(citate)
        else :
            data_list["cited by"] = 0
        authors = publication.find_element(By.CLASS_NAME, "gs_gray").text
        journal = publication.find_elements(By.CLASS_NAME, "gs_gray")[1].text
        if(journal == ""):
            journal = "-"
        data_list["journal"] = str(journal)
        data_list["authors"] = str(authors)

        publications_list.append(data_list)
    all_publications[nama_peneliti] = {
        "name": nama_peneliti,
        "publications": publications_list,
        "specialities": speciality_list,
        "h_index": h_index
    }
    print("peneliti " + str(index + 1)+" "+ nama_peneliti + " selesai")
    end_scrap_one = time.time()
    scrap_time = end_scrap_one - start_scrap_one
    print("waktu scraping " + nama_peneliti + " adalah " + str(scrap_time) + " detik")

# Specify the file path where you want to save the JSON file
file_path = 'data_publications.json'

# Write the dictionary data to a JSON file
with open(file_path, 'w', encoding='utf-8') as json_file:
    json.dump(all_publications, json_file, indent=2, ensure_ascii=False)

driver.close()


# In[4]:


total_publications = sum(len(author_data["publications"]) for author_data in all_publications.values())
print(total_publications)
print(list_peneliti)


# In[5]:


# Github
username = 'pkr-br'
repository = 'scholar-scraping'
file_path = 'data_publications.json'

access_token = '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'

from github import Github

# Authentication is defined via github.Auth
from github import Auth

# using an access token
auth = Auth.Token(access_token)


# Public Web Github
g = Github(auth=auth)

repo = g.get_repo(f'{username}/{repository}')

from datetime import datetime

# Get the current date
current_date = datetime.now()

# Format the date as "dd-mm-yyyy"
formatted_date = current_date.strftime("%d-%m-%Y %H:%M")

updated_file_path = 'data_publications.json'

with open(updated_file_path, 'r', encoding='utf-8') as file:
    updated_json_data = file.read()

# Update the file in the repository
commit_message = f'Updated data at {formatted_date}'
file = repo.get_contents(file_path)
updated_file = repo.update_file(file_path, commit_message, updated_json_data, file.sha)

if updated_file:
    print('File updated successfully.')
else:
    print('Failed to update the file.')


# In[6]:


end_time = time.time()  # Record the end time
elapsed_time = end_time - start_time  # Calculate the elapsed time
print(elapsed_time)


# In[ ]:




