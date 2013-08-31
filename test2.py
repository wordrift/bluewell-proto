import mysql.connector
cnx = mysql.connector.connect(user='biren', password='cArrion69',
                              host='birenshah.ciic9oqhvrvk.us-east-1.rds.amazonaws.com',
                              port='3306',
                              database='scribblevault')
cnx.close()