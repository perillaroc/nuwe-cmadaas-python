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
    interfaceId = "deleteStationData"    
    
    # 2.3 服务节点ID
    serverId = "NMIC_MUSIC_CMADAAS"   
    
    # 2.4  接口参数，多个参数间无顺序     
    # 必选参数    (1)资料代码：城镇天气预报产品要素资料(测试);(2)要素字段代码（键值）)。
    params = {'dataCode':"SEVP_WEFC_ACPP_STORE",\
                                 'KeyEles':"Datetime,Station_Id_C"}
    
    # 2.5 要素值信息，删除20150114060000的,54323的记录
    inString = "20170114070000,54325;20171014070000,54326"

    # 3. 调用接口 
    result = client.callAPI_to_storeSerializedStr(userId, pwd, interfaceId, params, inString,serverId)
    # 4. 输出结果
    if result.errorCode == 0:
        print "Delete SerializedStr Data Succeed"
    else:    
        print "return code: ",result.errorCode
        print "return message: ",result.errorMessage