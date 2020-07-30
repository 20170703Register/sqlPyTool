# 获取表名称
def getSQLTableName(sql):
    tableNameIndex1 = sql.find("INSERT INTO")
    tableNameIndex2 = sql.find("(")
    tableName = sql[tableNameIndex1 + 11:tableNameIndex2]
    return tableName.strip()


# 获取创建表sql的表名称
def getCreateSQLTableName(sql):
    tableNameIndex1 = sql.find("CREATE TABLE")
    tableNameIndex2 = sql.find("(")
    tableName = sql[tableNameIndex1 + 12:tableNameIndex2]
    return tableName.strip()


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


# 获取创建列数组
def getCreateSQLColumns(sql):
    columnIndex1 = sql.find("(")
    columnIndex2 = sql.rfind(")")
    columnStr = sql[columnIndex1 + 1:columnIndex2].strip().strip("\n")
    columns = columnStr.split("\n")

    _columns = []
    for column in columns:
        if column.find("PRIMARY ") > 0:
            continue
        if column.find("UNIQUE ") > 0:
            continue
        if column.find("INDEX ") > 0:
            continue

        column = column.strip()

        _column = {}
        columnNameIndex = column.find(" ")
        columnName = column[0:columnNameIndex].strip()

        columnComment = ""
        columnCommentIndex = column.find(" COMMENT", columnNameIndex)
        if columnCommentIndex > 0:
            columnComment = column[columnCommentIndex+8:len(column)]
            columnComment = columnComment.strip()

        columnDefault = ""
        columnDefaultIndex = column.find(" DEFAULT ", columnNameIndex)
        if columnDefaultIndex > 0:
            columnDefault = column[columnDefaultIndex+9:column.find(" ", columnDefaultIndex+9)]
            columnDefault = columnDefault.strip()
            if columnDefault == "CURRENT_TIMESTAMP":
                columnDefault = "NULL"
        
    
        _column["name"] = columnName
        _column["comment"] = columnComment
        _column["default"] = columnDefault
        _columns.append(_column)
    
    return _columns


# 获取值数组，TODO，这里有问题，如何值内容里有","逗号，那么切割字符串时是否会分割这个呢
def _get_SQLValues(sql):
    valueIndex1 = sql.rfind("(")
    valueIndex2 = sql.rfind(")")
    valueStr = sql[valueIndex1 + 1:valueIndex2]
    values = valueStr.split(",")
    return values

def getSQLValues(sql):
    valueIndex1 = re.search('\)\s*values\s*\(', sql, re.I).span()
    valueIndex2 = sql.rfind(")")
    valueStr = sql[valueIndex1[1]:valueIndex2].strip()

    values = []
    _values = shlex.shlex(valueStr)
    for _v in _values:
        # 匹配,或者，
        if re.match('[,，]', _v):
            continue
        values.append(_v.strip())
        
    return values


# 替换sql语句的列，返回新sql语句
def replaceSQLColumn(oldsql, newColumnStr):
    columnIndex1 = oldsql.find("(")
    columnIndex2 = oldsql.find(")")

    prefix = oldsql[0:columnIndex1 + 1]
    suffix = oldsql[columnIndex2:len(oldsql)]
    
    suffix = suffix.strip('\n')

    # 并接字符串
    newsql = [prefix, newColumnStr, suffix];
    return ''.join(newsql)


# 替换sql语句的值，返回新sql语句
def replaceSQLValues(sql, newValues):
    valuesIndex1 = sql.find("VALUES (")
    valuesIndex2 = sql.rfind(")")

    prefix = sql[0:valuesIndex1 + 8]
    suffix = sql[valuesIndex2:len(sql)]

    # 并接字符串
    newsql = [prefix, newValues, suffix];
    return ''.join(newsql)


# 替换sql语句的表名，返回新sql语句
def replaceSQLTableName(sql, newTableName):
    tableNameIndex1 = sql.find("INSERT INTO")
    tableNameIndex2 = sql.find("(")

    prefix = sql[0:tableNameIndex1 + 12]
    suffix = sql[tableNameIndex2:len(sql)]

    newTableName = "`" + newTableName + "` "

    # 并接字符串
    newsql = [prefix, newTableName, suffix];
    return ''.join(newsql)


# 合并列，以column1为主，存在的不替换
def mergeSQLColumn(column1, column2):
    for c2 in column2:
        if c2 not in column1:
            column1.append(c2)
        else:
            continue 
    return column1


# 补充值，只支持null
def supplementSQLValues(sql, qty):
    valueIndex = sql.rfind(")")

    prefix = sql[0:valueIndex]
    suffix = ');'

    newsql = [prefix]
    for i in range(qty):
        newsql.append(", null")
        
    newsql.append(suffix)
    return ''.join(newsql)


def supplementSQLValues2(sql, columns):
    # 判断列数和值数是否相同
    cv = computeSQLColumnValues(sql)
    if cv[0] == cv[1]:
        return sql
    
    valueIndex = sql.rfind(")")

    prefix = sql[0:valueIndex]
    suffix = ');'

    newsql = [prefix]
    for key in columns:
        newsql.append(", " + columns[key])     
    newsql.append(suffix)
    
    return ''.join(newsql)



# 计算sql的多少列和多少值
def computeSQLColumnValues(sql):
    columns = getSQLColumns(sql)
    values = getSQLValues(sql)
    return [len(columns), len(values)]



# 创建新文件
def createNewFile(path, newDir, flag):
    dirPathIndex = path.rfind('\\') + 1
    dirPath = path[0:dirPathIndex]

    # 创建文件夹
    if len(newDir) > 0:
        dirPath = dirPath + newDir + "\\"
        if not os.path.exists(dirPath):
            os.mkdir(dirPath)
    
    fileName = path[dirPathIndex:len(path)]
    fileNameSuffixIndex = fileName.rfind('.')
    fileNameSuffix = fileName[fileNameSuffixIndex:len(fileName)]
    fileNamePrefix = fileName[0:fileNameSuffixIndex]

    newPahs = [dirPath, fileNamePrefix, flag, fileNameSuffix]

    # 新文件路径
    newPah = ''.join(newPahs)
    
    newFile = open(newPah, 'w', encoding = 'utf8')
    return newFile
    

# 执行入口方法
def execute(path, fileName, createSQL, target):

    # 新文件
    tableName = getCreateSQLTableName(createSQL).strip("`")
    tableName = tableName + os.path.splitext(fileName)[-1]
    newFile = createNewFile(path + "\\" + tableName, "new2", '')
    
    # 打开文件：r+ r
    file = open(path + "\\" + fileName, 'r', encoding = 'utf8')
    
    try:
        # 读取每一行
        lines = file.readlines()
        if len(lines) == 0:
            return

        for line in lines:
            
            newSQL = genNewInsertSQL(line, createSQL, target)
            content = [newSQL, '\n']
            newFile.write(''.join(content))
            
    #except Exception as e:
     #   print('%s - 执行异常！' %path)
    #    print(e)
##    else:
##        print('%s - 执行完成！' %path)
    finally:
        print("-")

        # 关闭文件流
        newFile.close()
        file.close()
    print('所有执行完成！')
    


##temp = {
##    'alone_auth_user': {
##        "0": {"index": "0", "ID": '40288b854a329988014a329a12f30002'},
##        "1": {"index": "0", "ID": '40288b854a329988014a329a12f30002'},
##        "2": {"index": "0", "ID": '40288b854a329988014a329a12f30002'},
##        "3": {"index": "0", "ID": '40288b854a329988014a329a12f30002'},
##        }
##    }
# 解释insert sql语句
def analysisInsetSQL(insertSQL):
    columns = getSQLColumns(insertSQL)
    values = getSQLValues(insertSQL)
##    print(insertSQL)
##    print(len(columns))
##    print(len(values))
    tableName = getSQLTableName(insertSQL)

    sqlTemp = InsertSQLTemp(tableName, columns, values, insertSQL)
##    print(sqlTemp.getDicStr())
    return sqlTemp
    

# 解析create sql语句
def analysisCreateSQL(createSQL):
    columns = getCreateSQLColumns(createSQL)
    tableName = getCreateSQLTableName(createSQL)

    sqlTemp = CreateSQLTemp(tableName, columns)
##    print(sqlTemp.getDicStr())
    return sqlTemp


def genNewInsertSQL(insertSQL, createSQL, newIndexs):
    insertTemp = analysisInsetSQL(insertSQL)
    createTemp = analysisCreateSQL(createSQL)

    if len(newIndexs) != len(createTemp.getColumns()):
        print("newIndexs长度不正确！")
        return
    
    insertTemp.updateValue(len(createTemp.getColumns()))
    
    insertTemp.updateIndex(newIndexs)

    newSQL = insertTemp.genSQL(createTemp)
    
##    print(insertTemp.getDicStr())
##    print(newSQL)
    return newSQL


class InsertSQLTemp:
    sql = ""
    tableName = ""
    columns = []
    values = []

    def __init__(self, tableName, columns, values, sql):
      InsertSQLTemp.sql = sql
      InsertSQLTemp.tableName = tableName
      InsertSQLTemp.columns = columns
      InsertSQLTemp.values = values

    def getTableName(self):
        return InsertSQLTemp.tableName

    def getDicTemp(self):
        temp = {}
        temp[InsertSQLTemp.tableName] = []

        columns = InsertSQLTemp.columns
        values = InsertSQLTemp.values

        for index, column in enumerate(columns):
            t = {}
            t["index"] = index
            t["name"] = column.strip()
            t["value"] = values[index].strip()
            temp[InsertSQLTemp.tableName].append(t)
        return temp

    def getDicStr(self):
        strss = [InsertSQLTemp.tableName]
        strss.append(":\n")
        
        temp = InsertSQLTemp.getDicTemp(self)
        arr = temp[InsertSQLTemp.tableName]
        
        for index, a in enumerate(arr): 
            strss.append(index)
            strss.append(":")
            strss.append(a)
            strss.append("\n")
        return ''.join('%s' %s for s in strss)


    def updateValue(self, aSzie):
        values = InsertSQLTemp.values
        if aSzie < len(values):
            return

        for i in range(aSzie - len(values)):
            InsertSQLTemp.columns.append("__none")
            InsertSQLTemp.values.append("__none")

        
    def updateIndex(self, nindexs):
        columns = InsertSQLTemp.columns.copy()
        values = InsertSQLTemp.values.copy()
        
        for index, n in enumerate(nindexs):
            if n == " ":
                columns[index] = "__none"
                values[index] = "__none"
                continue

            column = InsertSQLTemp.columns[n]
            value = InsertSQLTemp.values[n]

            columns[index] = column
            values[index] = value

        InsertSQLTemp.columns = columns
        InsertSQLTemp.values = values


    def genSQL(self, createSQLTemp):
        columns = createSQLTemp.getColumns()
        oldSQL = InsertSQLTemp.sql
        values = InsertSQLTemp.values
        tableName = InsertSQLTemp.tableName

        newSQL = replaceSQLTableName(oldSQL, createSQLTemp.getTableName())
        
        newColumns = []
        for column in columns:
            columnName = column["name"]
            newColumns.append('`')
            newColumns.append(columnName)
            newColumns.append('`')
            newColumns.append(", ")

        newColumns.pop()
        newSQL = replaceSQLColumn(newSQL, ''.join(newColumns))

        newValues = []
        for index, value in enumerate(values):
            if value == "__none":
                column = columns[index]
                default = column["default"]
                if default == "NULL":
                    newValues.append("NULL")
                    newValues.append(", ")
                    continue
                if default == "":
                    newValues.append("\'\'")
                    newValues.append(", ")
                    continue
                newValues.append(default)
                newValues.append(", ")
                continue
            
            newValues.append(value.strip())
            newValues.append(", ")
        newValues.pop()

        newSQL = replaceSQLValues(newSQL, ''.join(newValues))
        return newSQL
        
    

class CreateSQLTemp:
    tableName = ""
    columns = []

    def __init__(self, tableName, columns):
      CreateSQLTemp.tableName = tableName
      CreateSQLTemp.columns = columns

    def getTableName(self):
        return CreateSQLTemp.tableName

    def getDicTemp(self):
        temp = {}
        temp[CreateSQLTemp.tableName] = []

        columns = CreateSQLTemp.columns

        for index, column in enumerate(columns):
            t = {}
            t["index"] = index
            t["name"] = column["name"]
            t["comment"] = column["comment"]
            t["default"] = column["default"]
            temp[CreateSQLTemp.tableName].append(t)
        return temp

    def getDicStr(self):
        strss = [CreateSQLTemp.tableName]
        strss.append(":\n")
        
        temp = CreateSQLTemp.getDicTemp(self)
        arr = temp[CreateSQLTemp.tableName]
        
        for index, a in enumerate(arr): 
            strss.append(index)
            strss.append(":")
            strss.append(a)
            strss.append("\n")
        return ''.join('%s' %s for s in strss)

    def getColumns(self):
        return CreateSQLTemp.columns





# 解释insert sql语句
def _analysisInsetSQL(insertSQL):
    columns = getSQLColumns(insertSQL)
    values = getSQLValues(insertSQL)
    tableName = getSQLTableName(insertSQL)

    sqlTemp = InsertSQLTemp(tableName, columns, values, insertSQL)
    print(sqlTemp.getDicStr())
    return sqlTemp
# 解析create sql语句
def _analysisCreateSQL(createSQL):
    columns = getCreateSQLColumns(createSQL)
    tableName = getCreateSQLTableName(createSQL)

    sqlTemp = CreateSQLTemp(tableName, columns)
    print(sqlTemp.getDicStr())
    return sqlTemp
def _genNewInsertSQL(insertSQL, createSQL, newIndexs):
    insertTemp = _analysisInsetSQL(insertSQL)
    createTemp = _analysisCreateSQL(createSQL)

    if len(newIndexs) != len(createTemp.getColumns()):
        print("newIndexs长度不正确！")
        return
    
    insertTemp.updateValue(len(createTemp.getColumns()))
    
    insertTemp.updateIndex(newIndexs)

    newSQL = insertTemp.genSQL(createTemp)
    
    print(insertTemp.getDicStr())
    print(newSQL)
    return newSQL


    
insertSQL1 = "INSERT INTO `alone_auth_user` (`ID`, `NAME`, `PASSWORD`, `COMMENTS`, `TYPE`, `CTIME`, `UTIME`, `CUSER`, `MUSER`, `STATE`, `LOGINNAME`, `LOGINTIME`, `IMGID`) VALUES ('40288b854a329988014a329a12f30002', '系统管理员', '45A6964B87BEC90B5B6C6414FAF397A7', '', '3', '20141210130925', '20200211155443', 'userId', '40288b854a329988014a329a12f30002', '1', 'sysadmin', '20200723111811', '402880867272d4fa0172886dbf2f0013');"
#analysisInsetSQL(insertSQL)


createSQL1 = '''
CREATE TABLE SYS_USER  (
  ID VARCHAR(32) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NOT NULL COMMENT '主键ID',
  USERNAME VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '登录账号',
  REALNAME VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '真实姓名',
  PASSWORD VARCHAR(255) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '密码',
  SALT VARCHAR(45) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT 'MD5密码盐',
  AVATAR VARCHAR(255) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '头像',
  BIRTHDAY DATETIME(0) NULL DEFAULT NULL COMMENT '生日',
  SEX TINYINT(1) NULL DEFAULT NULL COMMENT '性别(0-默认未知,1-男,2-女)',
  EMAIL VARCHAR(45) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '电子邮件',
  PHONE VARCHAR(45) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '电话',
  ORG_CODE VARCHAR(64) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '机构编码',
  STATUS TINYINT(1) NULL DEFAULT NULL COMMENT '状态(1-正常,2-冻结)',
  ACTIVITI_SYNC TINYINT(1) NULL DEFAULT NULL COMMENT '同步工作流引擎(1-同步,0-不同步)',
  WORK_NO VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '工号，唯一键',
  POST VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '职务，关联职务表',
  TELEPHONE VARCHAR(45) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '座机号',
  IDENTITY TINYINT(1) NULL DEFAULT NULL COMMENT '身份（1普通成员 2上级）',
  DEPART_IDS LONGTEXT CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL COMMENT '负责部门',
  REL_TENANT_IDS VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL COMMENT '多租户标识',
  DEL_FLAG INT(1) NULL DEFAULT 0 COMMENT '删除状态',
  CREATE_DATE          DATE DEFAULT NULL COMMENT '创建日期',
  CREATE_TIME          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UPDATE_DATE          DATE DEFAULT NULL COMMENT '修改日期',
  UPDATE_TIME          DATETIME DEFAULT NULL COMMENT '修改时间',
  CREATE_USER_ID       VARCHAR(64) DEFAULT NULL COMMENT '创建人ID',
  CREATE_USER_NAME     VARCHAR(32) DEFAULT NULL COMMENT '创建人姓名',
  UPDATE_USER_ID       VARCHAR(64) DEFAULT NULL COMMENT '修改人ID',
  UPDATE_USER_NAME     VARCHAR(32) DEFAULT NULL COMMENT '修改人姓名',
  PRIMARY KEY (ID) USING BTREE,
  UNIQUE INDEX INDEX_USER_NAME(USERNAME) USING BTREE,
  UNIQUE INDEX UNIQ_SYS_USER_WORK_NO(WORK_NO) USING BTREE,
  INDEX INDEX_USER_STATUS(STATUS) USING BTREE,
  INDEX INDEX_USER_DEL_FLAG(DEL_FLAG) USING BTREE
) ENGINE = INNODB CHARACTER SET = UTF8 COLLATE = UTF8_GENERAL_CI COMMENT = '用户表' ROW_FORMAT = DYNAMIC;
'''

target1 = [
    0,
    10,
    1,
    2,
    " ",
    12,
    " ",
    " ",
    " ",
    " ",
    " ",
    9,
    " ",
    " ",
    " ",
    " ",
    4,
    " ",
    " ",
    " ",
    5,
    5,
    6,
    6,
    7,
    " ",
    11,
    " ",
    ]



insertSQL2 = "INSERT INTO `alone_auth_organization` (`ID`, `TREECODE`, `COMMENTS`, `NAME`, `CTIME`, `UTIME`, `STATE`, `CUSER`, `MUSER`, `PARENTID`, `SORT`, `TYPE`, `APPID`) VALUES ('402880e8718ff73301718ff846640000', '402880e8718ff73301718ff846640000', '', '测试机构', '20200419090545', '20200620181634', '1', '40288b854a329988014a329a12f30002', '40288b854a329988014a329a12f30002', 'NONE', 3, '1', NULL);"

createSQL2 = '''
CREATE TABLE SYS_DEPART  (
  ID VARCHAR(32) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NOT NULL COMMENT 'ID',
  PARENT_ID VARCHAR(32) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '父机构ID',
  DEPART_NAME VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NOT NULL COMMENT '机构/部门名称',
  DEPART_NAME_EN VARCHAR(500) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '英文名',
  DEPART_NAME_ABBR VARCHAR(500) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '缩写',
  DEPART_ORDER INT(11) NULL DEFAULT 0 COMMENT '排序',
  DESCRIPTION TEXT CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL COMMENT '描述',
  ORG_CATEGORY VARCHAR(10) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NOT NULL DEFAULT '1' COMMENT '机构类别 1组织机构，2岗位',
  ORG_TYPE VARCHAR(10) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '机构类型 1一级部门 2子部门',
  ORG_CODE VARCHAR(64) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NOT NULL COMMENT '机构编码',
  MOBILE VARCHAR(32) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '手机号',
  FAX VARCHAR(32) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '传真',
  ADDRESS VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '地址',
  MEMO VARCHAR(500) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '备注',
  STATUS VARCHAR(1) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '状态（1启用，0不启用）',
  DEL_FLAG INT(1) NULL DEFAULT 0 COMMENT '删除状态',
  CREATE_DATE          DATE DEFAULT NULL COMMENT '创建日期',
  CREATE_TIME          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UPDATE_DATE          DATE DEFAULT NULL COMMENT '修改日期',
  UPDATE_TIME          DATETIME DEFAULT NULL COMMENT '修改时间',
  CREATE_USER_ID       VARCHAR(64) DEFAULT NULL COMMENT '创建人ID',
  CREATE_USER_NAME     VARCHAR(32) DEFAULT NULL COMMENT '创建人姓名',
  UPDATE_USER_ID       VARCHAR(64) DEFAULT NULL COMMENT '修改人ID',
  UPDATE_USER_NAME     VARCHAR(32) DEFAULT NULL COMMENT '修改人姓名',
  PRIMARY KEY (ID) USING BTREE,
  INDEX INDEX_DEPART_PARENT_ID(PARENT_ID) USING BTREE,
  INDEX INDEX_DEPART_DEPART_ORDER(DEPART_ORDER) USING BTREE,
  INDEX INDEX_DEPART_ORG_CODE(ORG_CODE) USING BTREE
) ENGINE = INNODB CHARACTER SET = UTF8 COLLATE = UTF8_GENERAL_CI COMMENT = '组织机构表' ROW_FORMAT = DYNAMIC;

'''


target2 = [
    0,
    9,
    3,
    " ",
    " ",
    10,
    " ",
    " ",
    11,
    " ",
    " ",
    " ",
    " ",
    " ",
    6,
    " ",
    4,
    4,
    5,
    5,
    7,
    " ",
    8,
    " ",
    ]


insertSQL3 = "INSERT INTO `alone_auth_userorg` (`ID`, `USERID`, `ORGANIZATIONID`) VALUES ('0017e97747a74e9c99b14ca97ccfbf06', 'a612488d2a6743dcb66f751d0df3a964', '820da2fbd5e84d118e3dbfaf68d31989');"

createSQL3 = '''
CREATE TABLE SYS_USER_DEPART  (
  ID VARCHAR(32) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NOT NULL COMMENT 'ID',
  USER_ID VARCHAR(32) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '用户ID',
  DEP_ID VARCHAR(32) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '部门ID',
  DEL_FLAG INT(1) NULL DEFAULT 0 COMMENT '删除状态',
  CREATE_DATE          DATE DEFAULT NULL COMMENT '创建日期',
  CREATE_TIME          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UPDATE_DATE          DATE DEFAULT NULL COMMENT '修改日期',
  UPDATE_TIME          DATETIME DEFAULT NULL COMMENT '修改时间',
  CREATE_USER_ID       VARCHAR(64) DEFAULT NULL COMMENT '创建人ID',
  CREATE_USER_NAME     VARCHAR(32) DEFAULT NULL COMMENT '创建人姓名',
  UPDATE_USER_ID       VARCHAR(64) DEFAULT NULL COMMENT '修改人ID',
  UPDATE_USER_NAME     VARCHAR(32) DEFAULT NULL COMMENT '修改人姓名',
  PRIMARY KEY (ID) USING BTREE,
  INDEX INDEX_DEPART_GROUPK_USERID(USER_ID) USING BTREE,
  INDEX INDEX_DEPART_GROUPKORGID(DEP_ID) USING BTREE,
  INDEX INDEX_DEPART_GROUPK_UIDANDDID(USER_ID, DEP_ID) USING BTREE
) ENGINE = INNODB CHARACTER SET = UTF8 COLLATE = UTF8_GENERAL_CI ROW_FORMAT = DYNAMIC;
'''
target3 = [
    0,
    1,
    2,
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    ]


insertSQL4 = "INSERT INTO `view_alone_auth_user` (`ID`, `NAME`, `PASSWORD`, `COMMENTS`, `TYPE`, `CTIME`, `UTIME`, `CUSER`, `MUSER`, `STATE`, `LOGINNAME`, `LOGINTIME`, `IMGID`, `sex`, `email`, `mobile`) VALUES ('f8a10052576743c4812c8a083138b515', '赵勍', '7113AF5F088CB59A270A812E2B502C16', NULL, '1', '20200623095347', '20200623095347', 'f8a10052576743c4812c8a083138b515', 'f8a10052576743c4812c8a083138b515', '1', '360102198307140523', NULL, '50220084f5bc467590803750edf95b17', 0, '2652206770@qq.com', '13970852176');"


createSQL4 = """
CREATE TABLE SYS_USER  (
  ID VARCHAR(32) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NOT NULL COMMENT '主键ID',
  USERNAME VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '登录账号',
  REALNAME VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '真实姓名',
  PASSWORD VARCHAR(255) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '密码',
  SALT VARCHAR(45) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT 'MD5密码盐',
  AVATAR VARCHAR(255) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '头像',
  IDCARD VARCHAR(45) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '身份证号',
  BIRTHDAY DATETIME(0) NULL DEFAULT NULL COMMENT '生日',
  SEX TINYINT(1) NULL DEFAULT NULL COMMENT '性别(0-默认未知,1-男,2-女)',
  EMAIL VARCHAR(45) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '电子邮件',
  PHONE VARCHAR(45) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '电话',
  ORG_CODE VARCHAR(64) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '机构编码',
  STATUS TINYINT(1) NULL DEFAULT NULL COMMENT '状态(1-正常,2-冻结)',
  ACTIVITI_SYNC TINYINT(1) NULL DEFAULT NULL COMMENT '同步工作流引擎(1-同步,0-不同步)',
  WORK_NO VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '工号，唯一键',
  POST VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '职务，关联职务表',
  TELEPHONE VARCHAR(45) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL DEFAULT NULL COMMENT '座机号',
  IDENTITY TINYINT(1) NULL DEFAULT NULL COMMENT '身份（1普通成员 2上级）',
  DEPART_IDS LONGTEXT CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL COMMENT '负责部门',
  REL_TENANT_IDS VARCHAR(100) CHARACTER SET UTF8 COLLATE UTF8_GENERAL_CI NULL COMMENT '多租户标识',
  DEL_FLAG INT(1) NULL DEFAULT 0 COMMENT '删除状态',
  CREATE_DATE          DATE DEFAULT NULL COMMENT '创建日期',
  CREATE_TIME          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UPDATE_DATE          DATE DEFAULT NULL COMMENT '修改日期',
  UPDATE_TIME          DATETIME DEFAULT NULL COMMENT '修改时间',
  CREATE_USER_ID       VARCHAR(64) DEFAULT NULL COMMENT '创建人ID',
  CREATE_USER_NAME     VARCHAR(32) DEFAULT NULL COMMENT '创建人姓名',
  UPDATE_USER_ID       VARCHAR(64) DEFAULT NULL COMMENT '修改人ID',
  UPDATE_USER_NAME     VARCHAR(32) DEFAULT NULL COMMENT '修改人姓名',
  PRIMARY KEY (ID) USING BTREE,
  UNIQUE INDEX INDEX_USER_NAME(USERNAME) USING BTREE,
  UNIQUE INDEX UNIQ_SYS_USER_WORK_NO(WORK_NO) USING BTREE,
  INDEX INDEX_USER_STATUS(STATUS) USING BTREE,
  INDEX INDEX_USER_DEL_FLAG(DEL_FLAG) USING BTREE
) ENGINE = INNODB CHARACTER SET = UTF8 COLLATE = UTF8_GENERAL_CI COMMENT = '用户表' ROW_FORMAT = DYNAMIC;
"""


target4 = [
    0,
    10,
    1,
    2,
    " ",
    12,
    10,
    " ",
    13,
    14,
    15,
    " ",
    9,
    " ",
    " ",
    " ",
    " ",
    4,
    " ",
    " ",
    " ",
    5,
    5,
    6,
    6,
    7,
    " ",
    11,
    " ",
    ]

# 一切从这里开始............

import os
import re
import shlex


# 第一步先分析
#analysisCreateSQL(createSQL3)
_genNewInsertSQL(insertSQL4, createSQL4, target4)


mainPath = r"C:\Users\Administrator\Desktop\106数据库wts迁移至75数据库wts 2020-07-22\用户数据"
fileName1 = "alone_auth_user.sql"
fileName2 = "alone_auth_organization.sql"
fileName3 = "alone_auth_userorg.sql"
fileName4 = "view_alone_auth_user.sql"

##execute(mainPath, fileName1, createSQL1, target1)
##execute(mainPath, fileName2, createSQL2, target2)
##execute(mainPath, fileName3, createSQL3, target3)
##execute(mainPath, fileName4, createSQL4, target4)


#_sql = "INSERT INTO `view_alone_auth_user` (`ID`, `NAME`, `PASSWORD`, `COMMENTS`, `TYPE`, `CTIME`, `UTIME`, `CUSER`, `MUSER`, `STATE`, `LOGINNAME`, `LOGINTIME`, `IMGID`, `sex`, `email`, `mobile`) VALUES ('9115c76d136442a7abf7764bfcb026fe', '吴萍', 'EC7C5FEF0A392BC689E1F09789754E88', NULL, '1', '20200621131905', '20200621131905', '9115c76d136442a7abf7764bfcb026fe', '9115c76d136442a7abf7764bfcb026fe', '1', '360102198109055328', NULL, '96be8bbbdf204b3793d9f036cd2c92f0', 0, '741653792@qq,com', '15807009848');"
#print(getSQLValues(_sql))


temps = input("\n")




        













