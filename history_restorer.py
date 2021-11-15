import os, sys
from shutil import copy
import sqlite3
import logging
from datetime import datetime, timedelta

HISTORY_FILE_PATH_SUFIX = "AppData/Local/Google/Chrome/User Data/Default/History"
COPY_HISTORY_FILE_PATH_SUFIX = "AppData/Local/Google/Chrome/User Data/Default/History2"
HHRU_BASE_URL = "https://hh.ru"
FORMAT = '%Y-%m-%d %H:%M:%S'


def is_hhru_url(url):
    if HHRU_BASE_URL in str(url):
        return True
    return False

def get_history_list(username: str, USERS_FOLDER_PATH : str, date_from: str, date_to: str):  
    SQL = "SELECT URL, datetime(last_visit_time / 1000000 + (strftime('%s', '1601-01-01')), 'unixepoch', 'localtime') as local_last_visit_time FROM urls WHERE local_last_visit_time > '" + date_from + "' AND local_last_visit_time < '" + date_to + "';"
    

    try:
        con = sqlite3.connect(USERS_FOLDER_PATH + "/" + username + "/" + COPY_HISTORY_FILE_PATH_SUFIX)
        cursor = con.cursor()
        cursor.execute(SQL)
        urls = cursor.fetchall()        
        res_hist = ""
        for i in urls:
            row = i[0] + ', Visited On ' + i[1] + '\n'
            if is_hhru_url(row):
                res_hist += row   
        if con:
            con.close()
        return res_hist
    except Exception:
        logging.error("Error while sending request to sqlight db")
        raise

def get_datetime_from_str(date_string: str, string_format: str):
    return datetime.strptime(date_string, string_format)

def get_days_between(date_from: str, date_to: str):
    date_from_datetime = get_datetime_from_str(date_from, FORMAT)
    date_to_datetime = get_datetime_from_str(date_to, FORMAT)
    return abs((date_from_datetime - date_to_datetime).days)

def copy_file(username: str, USERS_FOLDER_PATH : str):
    src = USERS_FOLDER_PATH + "/" + username + "/" + HISTORY_FILE_PATH_SUFIX
    dst = USERS_FOLDER_PATH + "/" + username + "/" + COPY_HISTORY_FILE_PATH_SUFIX
    copy(src, dst)

def delete_file(username: str, USERS_FOLDER_PATH : str):
    os.remove(USERS_FOLDER_PATH + "/" + username + "/" + COPY_HISTORY_FILE_PATH_SUFIX)

def create_and_wrote_file(username: str, path_to_history_folder: str, text: str, date_str: str):
    text_file = open(path_to_history_folder + "/" + username + "_historyRes_" + str(date_str) + ".txt", "w")
    text_file.write(text)
    text_file.close()


def copy_history_content_to_res_gist_folder(username: str, USERS_FOLDER_PATH : str, path_to_history_folder: str, date_from: str, date_to: str):
    try:        
        copy_file(username, USERS_FOLDER_PATH)
        days = get_days_between(date_from, date_to)

        date_from_datetime = get_datetime_from_str(date_from, FORMAT)
        date_to_datetime = get_datetime_from_str(date_to, FORMAT)
     
        date_to_tmp=date_to_datetime 

        if days > 0:
            for i in range(0, days - 1):
                date_from_tmp = date_from_datetime + timedelta(days=i)
                date_to_tmp = date_from_tmp + timedelta(days=1)
            
                res_hist_string = get_history_list(username, USERS_FOLDER_PATH, str(date_from_tmp), str(date_to_tmp))
                create_and_wrote_file(username, path_to_history_folder, res_hist_string, date_from_tmp.strftime("%Y-%m-%d"))
            date_from_tmp = date_from_tmp + timedelta(days=1)
            res_hist_string = get_history_list(username, USERS_FOLDER_PATH, str(date_from_tmp), str(date_to_datetime))
            create_and_wrote_file(username, path_to_history_folder, res_hist_string,  date_from_tmp.strftime("%Y-%m-%d"))
        elif days == 0:
            res_hist_string = get_history_list(username, USERS_FOLDER_PATH, str(date_from_datetime), str(date_to_datetime))
            create_and_wrote_file(username, path_to_history_folder, res_hist_string, date_from_datetime.strftime("%Y-%m-%d"))

        delete_file(username, USERS_FOLDER_PATH)
    except Exception:
        logging.error("Error in while copying folder")
        raise

def get_user_name_list(USERS_FOLDER_PATH) -> list:
    exclude = ['All Users', 'Default', 'Default User', 'Public', 'Administrator', 'roman']

    sub_folders = [name for name in os.listdir(USERS_FOLDER_PATH) if os.path.isdir(os.path.join(USERS_FOLDER_PATH, name))]
    users_list = [elem for elem in sub_folders if elem not in exclude]

    return users_list

def main(USERS_FOLDER_PATH: str, path_to_history_folder: str, date_from: str, date_to: str):
    users = get_user_name_list(USERS_FOLDER_PATH)
    for user in users:
        copy_history_content_to_res_gist_folder(user, USERS_FOLDER_PATH, path_to_history_folder, date_from, date_to)


if __name__ == "__main__":
    if len(sys.argv) > 6:
        logging.basicConfig(level=logging.INFO)
        main(USERS_FOLDER_PATH=str(sys.argv[1]), path_to_history_folder=str(sys.argv[2]), date_from=str(sys.argv[3]) + ' ' + str(sys.argv[4]), date_to=str(sys.argv[5]) + ' ' + str(sys.argv[6]))
    else:
        print("""
            Specify the parameters:
                1. Path to users folder
                2. Start date(ex. 10-09-2021)
                3. Finish date(ex. 10-09-2021)""")

