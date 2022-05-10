import os
import sys
import re
from shutil import copy
import sqlite3
import logging
from datetime import datetime, timedelta

from history_record import HistoryRecord, HISTORY_RECORD_DELEMITER

from typing import List, Set

logger = logging.getLogger(__name__)

logger.setLevel(level=logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)

logging.basicConfig(filename='log.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

CHROME_BROWSER_TYPE = "chrome"
FIREFOX_BROWSER_TYPE = "firefox"

FIREFOX_DB_FILE_NAME = "places.sqlite"
FIREFOX_DB_COPY_FILE_NAME = "placesCopy.sqlite"

FIREFOX_FOLDER_MASK = ".*\.default-release"
FIREFOX_PROFILES_PATH_POSTFIX = "/AppData/Roaming/Mozilla/Firefox/Profiles/"

CHROME_DB_PATH_POSTFIX = "/AppData/Local/Google//Chrome/User Data/Default/History"
CHROME_DB_COPY_PATH_POSTFIX = "/AppData/Local/Google/Chrome/User Data/Default/HistoryCopy"

FORMAT = '%Y-%m-%d %H:%M:%S'
SIMPLE_FORMAT = '%Y-%m-%d'


def get_sql_request(browser_type: str, date_from: str, date_to: str) -> str:
    query_string = ""

    if browser_type == CHROME_BROWSER_TYPE:
        query_string = "SELECT " \
                       "url, " \
                       "datetime(last_visit_time / 1000000 + (strftime('%s', '1601-01-01')), 'unixepoch', 'localtime') as local_last_visit_time " \
                       "FROM urls " \
                       "WHERE local_last_visit_time >= " + "'" + date_from + "' AND local_last_visit_time < " + "'" + date_to + "' " \
                                                                                                                                "AND url LIKE '%hh.ru%';"
    elif browser_type == FIREFOX_BROWSER_TYPE:
        query_string = "SELECT " \
                       "url, " \
                       "datetime(last_visit_date / 1000000, 'unixepoch','localtime') as local_last_visit_time " \
                       "FROM moz_places " \
                       "WHERE local_last_visit_time >= " + "'" + date_from + "' AND local_last_visit_time < " + "'" + date_to + "' " \
                                                                                                                                "AND url LIKE '%hh.ru%' " \
                                                                                                                                "AND visit_count > 0;"

    return query_string


def get_db_set(browser_type: str, date_from: str, date_to: str) -> Set[HistoryRecord]:
    sql_request = get_sql_request(browser_type, date_from, date_to)
    logger.info(f"sql_request: {sql_request}")

    try:
        con = sqlite3.connect(db_copy_path)
        cursor = con.cursor()

        cursor.execute(sql_request)
        result_db_set = cursor.fetchall()

        db_set = set()
        for s in result_db_set:
            db_set.add(HistoryRecord(s[0], s[1]))

        if con:
            con.close()

        return db_set
    except Exception:
        logger.error("Error while sending request to sqlight db")
        raise


def get_datetime_from_str(date_string: str, date_format: str):
    return datetime.strptime(date_string, date_format)


def get_days_between(date_from: str, date_to: str, format_date: str):
    start_datetime = get_datetime_from_str(date_from, format_date)
    end_datetime = get_datetime_from_str(date_to, format_date)

    return abs((start_datetime - end_datetime).days)


def copy_file(file_path: str, file_copy_path: str):
    copy(file_path, file_copy_path)


def delete_file(file_path):
    os.remove(file_path)


def get_history_record_set_of_txt_file(file_path) -> Set[HistoryRecord]:
    text_file = open(file_path, "a+")
    text_file.seek(0)
    text = text_file.readlines()
    lines = [line.rstrip() for line in text]
    text_file.close()

    res_set = set()
    for line in lines:
        args = line.split(HISTORY_RECORD_DELEMITER)
        if len(args) == 2:
            res_set.add(HistoryRecord(args[0], args[1]))
        else:
            logger.info(f"This line was passed: {line}")

    return res_set


def get_diff_between_sets(first: Set[HistoryRecord], second: Set[HistoryRecord]):
    return first.difference(second)


def create_and_write_file(username: str, path_to_history_folder: str, db_set: Set[HistoryRecord], date: str) -> None:
    file_name = str(username) + "_historyRes_" + str(date) + ".txt"
    file_path = os.path.join(path_to_history_folder, file_name)

    res_hist_set = get_history_record_set_of_txt_file(file_path)

    logger.info(f"db_set: \n {str(db_set)}")
    logger.info(f"res_hist_set: \n {str(res_hist_set)}")

    logger.info(f"Calling get_diff_between_sets()")
    new_lines_set = get_diff_between_sets(db_set, res_hist_set)

    if new_lines_set is not None and len(new_lines_set) > 0:
        history_record_list = [str(s) for s in new_lines_set]
        new_lines_str = "\n".join(history_record_list)

        text_file = open(file_path, "a+")
        logger.info(f"Adding these new_lines_str (as one string) to res hist txt file: \n{new_lines_str}")
        text_file.write(new_lines_str)
        text_file.close()
    else:
        logger.info(f"No new lines: new_lines_set is None or length == 0")


def update_res_hist_files(username: str, path_to_history_folder: str,
                          date_from: str, date_to: str, browser_type: str):
    try:
        start_datetime = get_datetime_from_str(date_from, FORMAT)
        end_datetime = get_datetime_from_str(date_to, FORMAT)

        days = get_days_between(date_from, date_to, FORMAT)
        if days > 0:
            for i in range(0, days):
                logger.info('*' * 30)
                logger.info(f"{i + 1} of {days}")

                start_date_tmp = start_datetime + timedelta(days=i)
                end_date_tmp = start_date_tmp + timedelta(days=1)

                logger.info(f"Calling get_db_set: from: {start_date_tmp}, to: {end_date_tmp}")
                db_set = get_db_set(browser_type, str(start_date_tmp), str(end_date_tmp))

                create_and_write_file(username, path_to_history_folder, db_set,
                                      start_date_tmp.strftime(SIMPLE_FORMAT))
                logger.info('-' * 30)
        elif days == 0:  # < 1 get records inside a day
            logger.info('*' * 30)

            logger.info(f"Calling get_db_set: from: {start_datetime}, to: {end_datetime}")
            db_set = get_db_set(browser_type, str(start_datetime), str(end_datetime))

            create_and_write_file(username, path_to_history_folder, db_set,
                                  start_datetime.strftime(SIMPLE_FORMAT))
            logger.info('-' * 30)
    except Exception as e:
        logger.error(f"Error in updating result history {e}")
        raise


def set_db_paths_by_browser_type(users_folder_path: str, user: str, browser_type: str) -> int:
    global db_path
    global db_copy_path

    user_home = os.path.join(users_folder_path, user)

    if browser_type == FIREFOX_BROWSER_TYPE:
        firefox_user_profiles_path = user_home + FIREFOX_PROFILES_PATH_POSTFIX
        logger.info(f"firefox_user_profiles_path: {firefox_user_profiles_path}")

        reg_compile = re.compile(FIREFOX_FOLDER_MASK)
        folder_names = []
        for dirpath, dirnames, filenames in os.walk(firefox_user_profiles_path):
            folder_names = folder_names + [dirname for dirname in dirnames if reg_compile.match(dirname)]

        if folder_names is None or len(folder_names) == 0:
            logger.error(firefox_user_profiles_path + " doesn't contain folder by mask")
            # raise RuntimeError("No firefox folder was found by mask!")
            return -1

        firefox_db_folder = folder_names[0]
        firefox_db_path = os.path.join(firefox_user_profiles_path, firefox_db_folder)

        db_path = os.path.join(firefox_db_path, FIREFOX_DB_FILE_NAME)
        db_copy_path = os.path.join(firefox_db_path, FIREFOX_DB_COPY_FILE_NAME)
    elif browser_type == CHROME_BROWSER_TYPE:
        db_path = os.path.join(user_home, CHROME_DB_PATH_POSTFIX)
        db_copy_path = os.path.join(user_home, CHROME_DB_COPY_PATH_POSTFIX)

    logger.info(f"db_path: {db_path}, db_copy_path: {db_copy_path}")

    return 0


def get_user_name_list(users_folder_path: str) -> List[str]:
    exclude = ['All Users', 'Default', 'Default User', 'Public', 'Administrator']

    sub_folders = [name for name in os.listdir(users_folder_path)
                   if os.path.isdir(os.path.join(users_folder_path, name))]

    users_list = []
    for user_folder in sub_folders:
        if user_folder not in exclude and not user_folder.startswith("$"):
            users_list.append(user_folder)

    return users_list


def main(users_folder_path: str, browser_type: str, date_from: str, date_to: str, path_to_history_folder: str) -> None:
    logger.info(
        f"path_to_history_folder: {path_to_history_folder}, browser_type: {browser_type}, date_from: {date_from}, date_to: {date_to}")

    users = get_user_name_list(users_folder_path)
    logger.info("users: " + str(users))

    for user in users:
        try:
            logger.info("Current user: " + user)

            logger.info("running get_path_db_by_browser_type(). Processing...")
            if set_db_paths_by_browser_type(users_folder_path, user, browser_type) == 0:
                logger.info(f"Copying db file: {db_path} to {db_copy_path}")
                copy_file(db_path, db_copy_path)

                logger.info(f"Calling updating res hist files. Processing...")
                update_res_hist_files(user, path_to_history_folder, date_from, date_to, browser_type)

                logger.info(f"db_copy_path removing: {db_copy_path}")
                delete_file(db_copy_path)
            else:
                logger.error("set_db_paths_by_browser_type ==-1")
                logger.info(f"User was passed: {user}")
        except Exception as e:
            logger.error(f"Error in main: {e}")
            raise


if __name__ == "__main__":
    logger.info("Start time: " + str(datetime.now()))
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
