# coding=utf8
'''
Modified in 2016/03/28
@author: xjunior

Modified in 2018/11/18
@author: wufeng & lr
'''
from cma.music.DataStoreClient import DataStoreClient
if __name__ == "__main__":
    
    # 1. 定义client对象  
    client = DataStoreClient()
    
    #2. 调用方法的参数定义，并赋值
    # 2.1 用户名&密码 
    userId = "user_nordb"
    pwd = "user_nordb_pwd1"
        
    # 2.2  接口ID(删除站点、指数等数据)  
    interfaceId = "saveFiles" 
    
    # 2.3 服务节点ID
    serverId = "NMIC_MUSIC_CMADAAS"   
        
    # 2.4  接口参数，多个参数间无顺序     
    # 必选参数    (1)资料代码  (2)要素字段代码（键值）)。
    params = {'dataCode':"SEVP_CIPAS_TEM_ANOM",
              'Elements':"Datetime,PUBLISH_TIME,FILE_NAME,DATA_CONTENT,DATA_ID,FORMAT,AREA,PRODUCER,DATA_SOURCE,FILE_SIZE"}
    
    # 2.5 要素值信息
    inArray2D = [["20151214000000", "20151114060000","demo1.png","-", "TEM", "PNG", "NHE", "NCC", "CIPAS", "1222"],\
                 ["20151215000000", "20151114060000","demo2.png","-", "TEM", "PNG", "NHE", "NCC", "CIPAS", "1222"]]
    
    ftpfiles =["D:\demo1.png",\
               "D:\demo2.png"];
    # 3. 调用接口 
    result = client.callAPI_to_storeFile(userId, pwd, interfaceId,params,inArray2D,ftpfiles,serverId)

    # 4. 输出结果   
    if result.errorCode == 0:
        print "Upload Files Succeed"
    else:    
        print "return code: ",result.errorCode
        print "return message: ",result.errorMessage
