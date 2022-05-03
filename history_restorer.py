import os, sys
import re
from shutil import copy
import sqlite3
import logging
from datetime import datetime, timedelta

from typing import List, Set

logger = logging.getLogger(__name__)


logger.setLevel(level=logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s'
    )
ch.setFormatter(formatter)
logger.addHandler(ch)

CHROME_BROWSER_TYPE = "chrome"
FIREFOX_BROWSER_TYPE = "firefox"

FIREFOX_DB_FILE_NAME = "places.sqlite"
FIREFOX_DB_COPY_FILE_NAME = "placesCopy.sqlite"

FIREFOX_FOLDER_MASK = ".*\.default-release"
FIREFOX_PROFILES_PATH_POSTFIX = "\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\"

CHROME_DB_PATH_POSTFIX = "\\AppData\\Local\\Google\Chrome\\User Data\\Default\\History"
CHROME_DB_COPY_PATH_POSTFIX = "\\AppData\\Local\\Google\Chrome\\User Data\\Default\\HistoryCopy"

HHRU_BASE_URL = "https://hh.ru"
FORMAT = '%Y-%m-%d %H:%M:%S'


def get_sql_request(browser_type: str, dateFrom: str, dateTo: str) -> str:
    queryString = ""

    if browser_type == CHROME_BROWSER_TYPE:
        queryString = "SELECT url, datetime(last_visit_time / 1000000 + (strftime('%s', '1601-01-01')), 'unixepoch', 'localtime') as local_last_visit_time " \
                      "FROM urls " \
                      "WHERE local_last_visit_time >= " + "'" + dateFrom + "' AND local_last_visit_time < " + "'" + dateTo + "' "\
                      "AND url LIKE '%hh.ru%'" + ";"
    elif browser_type == FIREFOX_BROWSER_TYPE:
        queryString = "SELECT url, datetime(last_visit_date / 1000000, 'unixepoch','localtime') as local_last_visit_time " \
                      "FROM moz_places " \
                      "WHERE local_last_visit_time >= " + "'" + dateFrom + "' AND local_last_visit_time < " + "'" + dateTo + "' "\
                      "AND url LIKE '%hh.ru%' " \
                      "AND visit_count > 0" + ";"

    return queryString


def get_history_set(browser_type: str, date_from: str, date_to: str) -> Set[str]:
    sql_request = get_sql_request(browser_type, date_from, date_to)
    logger.info(f"sql_request: {sql_request}")

    try:
        con = sqlite3.connect(db_copy_path_str)
        cursor = con.cursor()
        cursor.execute(sql_request)
        result_db_set = cursor.fetchall()

        record_set = set()
        for i in result_db_set:
            row = i[0] + ', Visited On ' + i[1] + '\n'
            record_set.add(row)

        if con:
            con.close()

        return record_set
    except Exception:
        logger.error("Error while sending request to sqlight db")
        raise


def get_datetime_from_str(date_string: str, string_format: str):
    return datetime.strptime(date_string, string_format)


def get_days_between(date_from: str, date_to: str):
    date_from_datetime = get_datetime_from_str(date_from, FORMAT)
    date_to_datetime = get_datetime_from_str(date_to, FORMAT)

    return abs((date_from_datetime - date_to_datetime).days)


def copy_file(file_path: str, file_copy_path: str):
    copy(file_path, file_copy_path)


def delete_file(file_path):
    os.remove(file_path)


def get_set_of_txt_file(text_file) -> Set[str]:
    return set(line.strip() for line in text_file)


def get_diff_between_sets(first: Set[str], second: Set[str]):
    return first.difference(second)


def create_and_wrote_file(username: str, path_to_history_folder: str, output_from_db: Set[str], date_str: str) -> None:
    file_name = str(username) + "_historyRes_" + str(date_str) + ".txt"
    file_path = os.path.join(path_to_history_folder, file_name)

    text_file = open(file_path, "a+")

    from_txt_set = get_set_of_txt_file(text_file)

    logger.info(f"output_from_db set: \n {str(output_from_db)}")
    logger.info(f"from_txt_set set: \n {str(from_txt_set)}")

    logger.info(f"get_diff_between_sets(). Processing...")
    new_lines_set = get_diff_between_sets(output_from_db, from_txt_set)

    if new_lines_set is not None and len(new_lines_set) > 0:
        new_lines_str = '\n'.join(new_lines_set)
        logger.info(f"Adding these lines to res hist txt file: \n {new_lines_str}")
        text_file.write(new_lines_str)
    else:
        logger.info(f"No new lines: new_lines_set is None or length == 0")
    text_file.close()


def get_user_name_list(users_folder_path) -> List[str]:
    exclude = ['All Users', 'Default', 'Default User', 'Public', 'Administrator']

    sub_folders = [name for name in os.listdir(users_folder_path)
                   if os.path.isdir(os.path.join(users_folder_path, name))]

    users_list = [elem for elem in sub_folders if elem not in exclude]
    users_list = [elem for elem in users_list if "$" not in elem]

    return users_list


def copy_history_content_to_res_gist_folder(username: str, path_to_history_folder: str,
                                            date_from: str, date_to: str, browser_type: str):
    try:
        days = get_days_between(date_from, date_to)

        date_from_datetime = get_datetime_from_str(date_from, FORMAT)
        date_to_datetime = get_datetime_from_str(date_to, FORMAT)

        date_to_tmp = date_to_datetime

        if days > 0:
            for i in range(0, days):
                logger.info(f"************************")
                logger.info(f"{i + 1} of {days}")
                date_from_tmp = date_from_datetime + timedelta(days=i)
                date_to_tmp = date_from_tmp + timedelta(days=1)

                logger.info(f"get_history_set: from: {date_from_tmp}, to: {date_to_tmp}")
                res_hist_set = get_history_set(browser_type, str(date_from_tmp), str(date_to_tmp))

                create_and_wrote_file(username, path_to_history_folder, res_hist_set, date_from_tmp.strftime("%Y-%m-%d"))
                logger.info(f"----------------------")
        elif days == 0:  # < 1 get records inside a day
            logger.info(f"************************")
            res_hist_set = get_history_set(browser_type, str(date_from_datetime), str(date_to_datetime))
            create_and_wrote_file(username, path_to_history_folder, res_hist_set,
                                  date_from_datetime.strftime("%Y-%m-%d"))
            logger.info(f"----------------------")
    except Exception:
        logger.error("Error in while copying folder")
        raise


def get_path_to_history_db_by_browser_type(browser_type: str, users_folder_path: str, user: str) -> None:
    global db_path_str
    global db_copy_path_str

    if browser_type == FIREFOX_BROWSER_TYPE:
        full_path_to_firefox_profiles_str = users_folder_path + user + FIREFOX_PROFILES_PATH_POSTFIX
        logger.info(full_path_to_firefox_profiles_str)

        folder_names = []
        reg_compile = re.compile(FIREFOX_FOLDER_MASK)
        for dirpath, dirnames, filenames in os.walk(full_path_to_firefox_profiles_str):
            folder_names = folder_names + [dirname for dirname in dirnames if reg_compile.match(dirname)]

        if folder_names is None or len(folder_names) == 0:
            logger.error(full_path_to_firefox_profiles_str + " doesn't contain folder by mask")
            raise RuntimeError("No firefox folder was found by mask!")

        firefox_db_folder = folder_names[0]

        db_path_str = os.path.join(full_path_to_firefox_profiles_str, firefox_db_folder, FIREFOX_DB_FILE_NAME)
        db_copy_path_str = os.path.join(full_path_to_firefox_profiles_str, firefox_db_folder, FIREFOX_DB_COPY_FILE_NAME)
    elif browser_type == CHROME_BROWSER_TYPE:
        db_path_str = users_folder_path + user + CHROME_DB_PATH_POSTFIX
        db_copy_path_str = users_folder_path + user + CHROME_DB_COPY_PATH_POSTFIX

    logger.info(f"db_path_str: {db_path_str}, db_copy_path_str: {db_copy_path_str}")


def main(users_folder_path: str, browser_type: str, date_from: str, date_to: str, path_to_history_folder: str) -> None:
    logger.info(f"path_to_history_folder: {path_to_history_folder}, browser_type: {browser_type}, date_from: {date_from}, date_to: {date_to}")

    users = get_user_name_list(users_folder_path)
    logger.info("users: " + str(users))

    for user in users:
        logger.info("Current user: " + user)
        # set paths to db
        logger.info("running get_path_to_history_db_by_browser_type(). Processing...")
        get_path_to_history_db_by_browser_type(browser_type, users_folder_path, user)

        logger.info(f"copy_file(). {db_path_str} to {db_copy_path_str}")
        copy_file(db_path_str, db_copy_path_str)

        logger.info(f"copy_history_content_to_res_gist_folder(). Processing...")
        copy_history_content_to_res_gist_folder(user, path_to_history_folder, date_from, date_to, browser_type)
        logger.info(f"copy_history_content_to_res_gist_folder(). Done.")

        logger.info(f"Deleting. db_copy_path_str: {db_copy_path_str}")
        delete_file(db_copy_path_str)


if __name__ == "__main__":
    logger.info("Args: " + str(sys.argv))
    if len(sys.argv) > 5:
        main(users_folder_path=str(sys.argv[1]),
             browser_type=str(sys.argv[2]),
             date_from=str(sys.argv[3] + " 00:00:00"),
             date_to=str(sys.argv[4] + " 00:00:00"),
             path_to_history_folder=str(sys.argv[5]))
    else:
        print("""Specify the parameters:
                1. Path to users folder (ex. )
                2. browser type (ex. firefox, ex. chrome)
                3. Start date(ex. 10-09-2021)
                4. Finish date(ex. 11-09-2021)
                5. Path to history folder""")
