import ibm_db
# import ibm_db_dbi
import configparser
from operator import itemgetter
from itertools import groupby
import os
# class Test:
#     def __init__(self, name):
#         self.name = name
#     def sendTest (self):
#         return self.name

class DbConnection:
    def getConfigDatas():
        # p = Test("Evan")
        # print(p.sendTest())
        base_dir = str(os.path.dirname(os.path.dirname(__file__)))
        base_dir = base_dir.replace('\\', '/')
        file_path = base_dir + "/config.ini" # config的路径应该在最根目录
        markName = "DB2-Database"
        cf = configparser.ConfigParser()
        cf.read(file_path)
        # secs = cf.sections()
        # options = cf.options(markName)
        # items = cf.items(markName)
        # secs = cf.sections() 查看所有ini的section
        dataBaseName = cf.get(markName, "dataBaseName")
        hostname = cf.get(markName, "hostname")
        port = cf.get(markName, "port")
        protocol = cf.get(markName, "protocol")
        uid = cf.get(markName, "uid")
        pwd = cf.get(markName, "pwd")
        confData = { "dataBaseName": dataBaseName,
                     "hostname": hostname,
                     "port": port,
                     "protocol": protocol,
                     "uid": uid,
                     "pwd": pwd
                    }
        
        return confData

    def openDbConnection ():
        configData = DbConnection.getConfigDatas()
        conn_str = "database=" + configData.get("dataBaseName") + \
                   ";hostname=" + configData.get("hostname") + \
                   ";port=" + configData.get("port") + \
                   ";protocol=" + configData.get("protocol") +\
                   ";uid=" + configData.get("uid") + \
                   ";pwd=" +configData.get("pwd")
        ibm_db_conn = ibm_db.connect(conn_str,'','')
        # conn = ibm_db_dbi.Connection(ibm_db_conn)
    # check if the database connection success.
        if (ibm_db_conn != False):
            return ibm_db_conn
        else:
            return False

    def getRequestId(nodeId, lineItemId):
        conn = DbConnection.openDbConnection()
        if (conn != False):
            sql = "SELECT CLIENT_REQUEST_ID FROM DATAOPS.RULECHK_REQUESTS WHERE " \
                  " NODE_ID = '"+ nodeId +"' AND LINEITEM_ID = '"+ lineItemId +"' AND STATUS = 2";
            stmt = ibm_db.exec_immediate(conn, sql)
            row = ibm_db.fetch_tuple(stmt)
            requId = 0
            while (row):
                for i in row:
                    requId = i
                row = ibm_db.fetch_tuple(stmt)
                if (row == False):
                    ibm_db.close(conn)
            return requId

    # return value: 1, 2,3,4
    # 1: data in crm
    # 2: data in team
    # 3: data in lineItem team
    # 4: data in LineItem
    # 5: data no match
    def checkInWitchDomain (domainId) :
        cmrAttributes = ("BASECOVID", "BRANCH", "BRANCHGRP", "CLNTSUBTYP", "CLNTTYP", "COUNTRY", "CURRCOVID",
                         "DOMBUYGRP", "DOMCLTID", "GBS1L1", "GBS1L2", "GBS1L3", "GBSSECTOR", "GLBBUYGRP", "IMT",
                         "INDCLASS", "INDSECTOR", "INDUSTRY")
        teamAttributes = ("PRODUCTS", "CLIENTS")
        rliTeamAttributes = ("NODEID")
        lineAttributes = ("CHANNEL", "SIZE", "PRODUCT_TYPE", "CONTRACT_TYPE", "GBT10", "GBT15", "GBT17", "GBT20",
                          "GBT30")
        if (domainId in cmrAttributes):
            return 1
        elif (domainId in teamAttributes):
            return 2
        elif (domainId in rliTeamAttributes):
            return 3
        elif (domainId in lineAttributes):
            return 4
        else:
            return 5


    def getMatchDatas (reqId):
        conn= DbConnection.openDbConnection()
        if (conn != False):
            # reqId = DbConnection.getRequestId(nodeId, ItemId)
            if (reqId) :
                status = DbConnection.getRunStatus(reqId, conn)
                isAccessState = DbConnection.switchStatue(status)
                if (isAccessState):
                    sql = "SELECT DISTINCT req.NODE_ID, req.LINEITEM_ID, req.STATUS, ret.TYPE, ret.RESULT, rrd.ATTR, RRD.EXPECTED, nu.ASSIGNED_USER_ID AS expected_user, rrd.ACTUAL " \
                          "FROM DATAOPS.RULECHK_REQUESTS req LEFT JOIN DATAOPS.RULECHK_RESULTS ret ON req.id = ret.request_id " \
                          "LEFT JOIN (SELECT SUBSTRING(RRD.EXPECTED, 2, LENGTH(RRD.EXPECTED)) AS EXPECTED, RRD.ATTR, RRD.ACTUAL, RRD.RESULT_ID "\
                          "FROM DATAOPS.RULECHK_RESULTS_DETAILS RRD ) RRD ON RRD.result_id = ret.id LEFT JOIN FCST.IBM_NODE_USERS NU ON " \
                          "NU.DELETED = 0 AND UPPER(NU.NODE_ID)= RRD.EXPECTED AND rrd.ATTR = 'NODEID' AND NU.user_type = 'OWNER' " \
                          "WHERE req.client_request_id IN ('"+reqId+"') ORDER BY ret.TYPE, RRD.ATTR"
                    # print(sql)
                    conn = DbConnection.openDbConnection()
                    stmt = ibm_db.prepare(conn, sql, )
                    result = ibm_db.execute(stmt)
                    row = ibm_db.fetch_both(stmt)
                    returnArry = []
                    while (row):
                        if (row == False):
                            # there is a result but is type is none
                            ibm_db.close(conn)
                            return "No Data Match"
                        elif (row['TYPE'] == "None"):
                            ibm_db.close(conn)
                            return "No data query by List"
                        else:
                            returnArry.append(row)
                            row = ibm_db.fetch_assoc(stmt)
                    ibm_db.close(conn)
                    return DbConnection.groupResultDatas(returnArry)
                else:
                    return status
            else:
                return "Counld't connection DB2, please contact Admin ."

    def groupResultDatas(resultDatas):
        groupDomain = []
        resultDatas = sorted(resultDatas, key=itemgetter('ATTR'))
        for date, items in groupby(resultDatas, key=itemgetter('ATTR')):
            currentItem = sorted(list(items), key=itemgetter('ATTR'))
            tempExpected = []
            tempActual = []
            proResult = ""
            for i in range(len(currentItem)):
                tempExpected.append(currentItem[i]['EXPECTED'])
                tempActual.append(currentItem[i]['ACTUAL'])
                proState = currentItem[i]['STATUS']
                proResult = currentItem[i]['RESULT']
            resultVal = {
                "platFrom":  DbConnection.checkInWitchDomain(resultDatas[i]["ATTR"]),
                "attrVal": date,
                "expectedVal": tempExpected,
                "actualVal":  tempActual,
                "result": proResult
            }
            groupDomain.append(resultVal)
        # print(groupDomain)
        return groupDomain
    def getRunStatus (reqId, conn):
        if (conn):
            sql = "SELECT STATUS FROM DATAOPS.RULECHK_REQUESTS WHERE CLIENT_REQUEST_ID='"+reqId+"'"
            stmt = ibm_db.exec_immediate(conn, sql)
            row = ibm_db.fetch_tuple(stmt)
            status = 0
            while (row):
                for i in row:
                    status = i
                row = ibm_db.fetch_tuple(stmt)
                if (row == False):
                    ibm_db.close(conn)
            return status

    def switchStatue (status):
        if (status == 0) :
            return False
        elif (status == 1):
            return False
        elif (status == 2):
            return True
        elif (status == 3):
            return False