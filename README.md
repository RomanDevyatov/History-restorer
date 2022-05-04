# Overview

This program copies history records (url, visit date) from specified browser (chrome or firefox).

# Installation and running

1) Download program file (start_fix_history.py)
   
2) Create bat file:
    ```cmd
    python history_restorer.py <path_to_users_folder> <browser_type> <date_start> <date_end> <path_to_folder>
    ```
    `path_to_users_folder` -  Users folder path (ex. C:/Users/)
    
    `browser_type` -          Browser type (ex. firefox, ex. chrome)
    
    `date_start` -            Start date (ex. 1945-06-22)
    
    `date_end` -              End date (ex. 1945-06-22)
    
    `path_to_folder` -        Path to just created folder. Or you can specify path to folder which contains history records txt files:
                              name format is `<username>_historyRes_<date_format_2022-04-23>.txt`. 
                              This file may contain following content:
                              ```
                              https://hh.ru/, Visited On 2021-08-24 18:01:05
                              ```
                              Nothing will be added if this url is found at the browser history.
   
    ### Batch file example
   ```bat
   python history_restorer.py C:/Users/ chrome 1940-11-10 1941-11-15 C:/Users/Some_Username/ResultHistory
   ```
