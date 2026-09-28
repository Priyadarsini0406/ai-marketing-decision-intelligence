import sqlite3
c = sqlite3.connect(r'E:\mini  project\backend\marketing_ai.db')
for r in c.execute("select name from sqlite_master where type='table' order by name"):
    print(r[0])