# coding=UTF-8
'''
Modified in 2016/03/28
@author: xjunior

Modified in 2018/11/18
@author: wufeng & lr
'''
from cma.music.DataQueryClient import DataQueryClient
if __name__ == "__main__":
    
    # 1. 定义client对象  
    client = DataQueryClient()
    
    
    #2. 调用方法的参数定义，并赋值
    # 2.1 用户名&密码 
    userId = "user_nordb" 
    pwd = "user_nordb_pwd1" 
        
    # 2.2  接口ID     
    interfaceId = "getRadaFileByTimeRangeAndStaId"    
    
    # 2.3 服务节点ID
    serverId = "NMIC_MUSIC_CMADAAS"
    
    #  2.4  接口参数，多个参数间无顺序     
    # 必选参数    (1)资料：质控前标准格式单站多普勒雷达基数据;(2)时间点;(3)下载文件数限制。
    params = {'dataCode':"RADA_L2_FMT",\
                                 'elements':"Datetime,DATA_ID,FILE_SIZE,File_URL",\
                                 'timeRange':"[20190323003000,20190323003600)",\
                                 'staIds':"Z9859,Z9852,Z9856,Z9851,Z9855",\
                                 'limitCnt':"10"}
    
    # 可选参数
    #  2.5 文件的本地保持目录     
    #fileDir = "./"   
   
    # 3. 调用接口 
    result = client.callAPI_to_fileList(userId, pwd, interfaceId,params,serverId) 
    
    # 4. 输出结果
    print result.request
    print result.fileInfos
    