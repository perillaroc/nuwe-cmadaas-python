# coding=utf8
'''
Modified in 2016/03/28
@author: xjunior

Modified in 2018/11/18
@author: wufeng & lr
'''
from cma.music.DataQueryClient import DataQueryClient
import numpy as np
if __name__ == "__main__":
    '''
    格点场要素获取（切块），返回RetGridArray2D对象
    '''
    # 1. 定义client对象  
    client = DataQueryClient()
    
    # 2. 调用方法的参数定义，并赋值
    # 2.1 用户名&密码 
    userId = "NMC_SZYB_TSW"
    pwd = "TSW123456"
        
    # 2.2  接口ID     
    interfaceId = "getSurfEleByTime"
        
    # 2.3 服务节点ID
    serverId = "NMIC_MUSIC_CMADAAS" 
        
    # 2.4  接口参数，多个参数间无顺序     
    # 必选参数    (1)资料:中国地面逐小时资料; (2)检索要素：站号、资料时间、纬度、经度、年、月、日、时; 
    #          (3)检索时间;(4)排序：按照站号从小到大;(5)返回最多记录数：10。
    params = {'dataCode':"SURF_CHN_MUL_HOR",\
                                 'elements':"Station_Id_C,Datetime,Lat,Lon,Year,Mon,Day,Hour",\
                                 'times':"20190331000000",\
                                 'orderby':"Station_ID_C:ASC",\
                                 'limitCnt':"10"}
    
    # 3. 调用接口
    #result = client.callAPI_to_array2D(userId, pwd, interfaceId, params)
    result = client.callAPI_to_array2D(userId, pwd, interfaceId, params,serverId)
    
    # 4. 输出接口
    print("return code: ",result.request.errorCode)
    print("return message: ",result.request.errorMessage)
    
    if result.request.errorCode == 0:
        resultData = result.data
        #返回数据行shapes[0]和列shapes[1]
        shapes = np.array(result.data).shape
        #print shapes[0], shapes[1]
        f = open('outputdata.txt', 'w')
        for i in range(shapes[0]):
            jointsFrame = resultData[i] #每行
            resultData.append(jointsFrame)
            for j in range(shapes[1]):
                strNum = str(jointsFrame[j])
                f.write(strNum)
                f.write(' ')
            f.write('\n')
        f.close()

    
    
    
    
    