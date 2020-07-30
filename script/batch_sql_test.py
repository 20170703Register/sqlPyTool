# 判断文件
def isFile(path):
    isfile = os.path.isfile(path)
    return isfile


# 判断文件夹
def isDir(path):
    isdir = os.path.isdir(path)
    return isdir


# 获取列数组
def getSQLColumns(sql):
    columnIndex1 = sql.find("(")
    columnIndex2 = sql.find(")")
    columnStr = sql[columnIndex1 + 1:columnIndex2].strip()
    columns = columnStr.split(",")

    _columns = []
    for column in columns:
        _columns.append(column.strip())
    
    return _columns


# 获取值数组，TODO，这里有问题，如何值内容里有","逗号，那么切割字符串时是否会分割这个呢
def getSQLValues(sql):
    
    valueIndex1 = re.search('\)\s*values\s*\(', sql, re.I).span()
    valueIndex2 = sql.rfind(")")
    valueStr = sql[valueIndex1[1]:valueIndex2].strip()
    
    values = []
    _values = shlex.shlex(valueStr)
   
    for _v in _values:
        print(_v)

        # 匹配,或者，
        if re.match('[,，]', _v):
            continue

        if re.match('[null]', _v.lower()):
            values.append(None)
            continue

        if re.match('[\'\"].*[\'\"]', _v):
            values.append(eval(_v.strip()))
        else:
            values.append(_v.strip())       
        
    return values


# 清空脚本对应的数据库表
def clearDataSQLScript(mainPath):
    conn = pymysql.connect(
        host = MySQL_HOST,
        port = MySQL_PORT,
        user = MySQL_USERNAME,
        password = MySQL_PASSWORD,
        db = MySQL_DBNAME)
    cursor = conn.cursor()
    
    files = os.listdir(mainPath)

    # 关闭外键约束
    cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')
    for file in files:
        
        filePath = "".join([mainPath, '\\', file])
        if isFile(filePath) == False:
            continue
        
        suffix = os.path.splitext(file)[-1]
        if suffix != ".sql":
            continue

        fileName = file[0:file.rfind(".")]
        sql = ["TRUNCATE TABLE ", fileName]

        try:
            cursor.execute("".join(sql))
            conn.commit()
            print("%s表执行清理完成！\n" %fileName)  
        except Exception as e:
            conn.rollback()
            print("执行异常！\n %s \n" %e)

    # 开启外键约束   
    cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')
    conn.commit()

    cursor.close()      
    conn.close()


def buildInsertTemp(sql):
    values = getSQLValues(sql)

    valuesIndex = sql.find(")")
    prefix = sql[0:valuesIndex + 1]
    suffix = []
    suffix.append("(")
    
    for value in values:
        #print(value)
        #print(type(value) is int)
        if isinstance(value, int):
            suffix.append("%d")
        else:
            suffix.append("%s")
        suffix.append(", ")
    suffix.pop()     
    suffix.append(");")

    temp = [prefix, " VALUES ", ''.join(suffix)]
    return ''.join(temp)
    

def buildInsertValues(sqls):
    values = []
    for sql in sqls:
        _values = getSQLValues(sql)
        values.append(tuple(_values))  
    return values

    

# 执行sql脚本
def executeSQLScript(conn, filePath):
    cursor = conn.cursor()

    try:
        start = time.time()
        
        # 关闭外键约束
        cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')

        enu = 10000
        rnu = 0
        sqlScripts = []
        
        file = open(filePath, 'r', encoding = 'utf8')
        lines = file.readlines()
        for line in lines:
            
            rnu += 1
            sqlScripts.append(line)
            if (rnu % enu) != 0 and rnu != len(lines):
                continue


            firstSQL = sqlScripts[0]
            firstSQL = buildInsertTemp(firstSQL)
            values = buildInsertValues(sqlScripts)
            print(firstSQL)
            print(values)
            # 执行sql
            #cursor.execute(line)
            # 批量执行sql，不能执行sql脚本
            cursor.executemany(firstSQL, values)
            conn.commit()
            
            print("执行 %s 条数据" %len(sqlScripts))
            sqlScripts = []

        end = time.time()
        print("共执行 %s 条数据" %len(lines))     
        print("执行完成！耗时: %f秒 \n\n" %(end - start))    
##    except Exception as e:
##        conn.rollback()
##        print("执行异常！\n %s \n\n" %e)
    finally:
        # 开启外键约束   
        cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')
        conn.commit()
        cursor.close()


# 执行
def execute(mainPath):
    conn = pymysql.connect(
        host = MySQL_HOST,
        port = MySQL_PORT,
        user = MySQL_USERNAME,
        password = MySQL_PASSWORD,
        db = MySQL_DBNAME)
    
    files = os.listdir(mainPath)
    for file in files:
        
        filePath = "".join([mainPath, '\\', file])
        if isFile(filePath) == False:
            continue
        
        suffix = os.path.splitext(file)[-1]
        if suffix != ".sql":
            continue 

        print("执行脚本：%s " %filePath)
        executeSQLScript(conn, filePath)

    print("关闭数据库连接！")
    conn.close()  


# 一切从这里开始............

import os
import re
import time
import shlex
import pymysql


# mysql信息
MySQL_HOST = "39.105.230.75"          # MySQL IP
MySQL_PORT = 3306                 # MySQL 端口
MySQL_USERNAME = "bboot"           # MySQL 用户名
MySQL_PASSWORD = "NDAmAm2RGJdRTiny"         # MySQL 密码
MySQL_DBNAME = "bboot"   # MySQL 数据库名


# 主路径
mainPath = r"C:\Users\Administrator\Desktop\106数据库wts迁移至75数据库wts 2020-07-22\new_ok\one_execute"

start = time.time()

#clearDataSQLScript(mainPath)
#execute(mainPath)

sql = "INSERT INTO `wts_paper_userown` (`ID`,  `CTIME`,  `CUSER`,  `CUSERNAME`,  `PSTATE`,  `PCONTENT`,  `MODEL_TYPE`,  `PAPER_ID`,  `ROOM_ID`,  `PAPER_NAME`,  `ROOM_NAME`,  `SCORE`,  `RPCENT`,  `CARD_ID`, `DEL_FLAG`, `CREATE_DATE`, `CREATE_TIME`, `UPDATE_DATE`, `UPDATE_TIME`, `CREATE_USER_ID`, `CREATE_USER_NAME`, `UPDATE_USER_ID`, `UPDATE_USER_NAME`) VALUES ('4028808372fa43470172ff41316963dd', '20200629164602', '122de2aaffcd49dd8a227b1f030486e6', '周日新', '1', NULL, '1', '4028808672dbf0a70172e113e85601ce', '4028808672dbf0a70172e12b25e406b4', '2020年工行反假理论考试', '2020年工行反假理论考试', -1000, -1000, '4028808372fa43470172ff41315663dc', 0, null, null, null, null, null, null, null, null);"
print(getSQLValues(sql))

#print(buildInsertTemp(sql))



end = time.time()
print("所有执行完成！总耗时：%f秒" %(end - start))
temps = input("\n")





















        













