# coding=UTF-8
import sys
reload(sys)
'''
Modified in 2016/03/28
@author: xjunior

Modified in 2018/11/18
@author: wufeng & lr
'''

from cma.music.DataQueryClient import DataQueryClient
import numpy as np
if __name__ == "__main__":
       
    # 1. 定义client对象  
    client = DataQueryClient()
    
    # 2. 调用方法的参数定义，并赋值
    # 2.1 用户名&密码 
    userId = "user_nordb" 
    pwd = "user_nordb_pwd1" 
        
    # 2.2  接口ID     
    interfaceId = "getNafpEleGridByTimeAndLevelAndValidtime"    
    
    # 2.3 服务节点ID
    serverId = "NMIC_MUSIC_CMADAAS"
        
    # 2.3  接口参数，多个参数间无顺序     
    # 必选参数    (1)资料:欧洲中心数值预报产品-低分辨率-全球; (2)起报时间;(3)预报时效;(5)预报要素（单个):气温;(4)预报层次(单个):85000pa;
    params = {'dataCode':"NAFP_FOR_FTM_LOW_EC_GLB",\
                                 'time':"20190324000000",\
                                 'validTime':"24",\
                                 'fcstEle':"TEM",'fcstLevel':"850",\
                                 'levelType':"100"}
    
    # 3. 调用接口
    #result = client.callAPI_to_gridArray2D(userId, pwd, interfaceId,params)
    result = client.callAPI_to_gridArray2D(userId, pwd, interfaceId,params,serverId)    
    
    # 4. 输出接口
    print "return code: ",result.request.errorCode
    print "return message: ",result.request.errorMessage
    
    if result.request.errorCode == 0:
        resultData = result.data
        #返回数据行shapes[0]和列shapes[1]
        shapes = np.array(result.data).shape
        #print shapes[0], shapes[1]
        f = open('gridArray2D.txt', 'w')
        for i in range(shapes[0]):
            jointsFrame = resultData[i] #每行
            resultData.append(jointsFrame)
            for j in range(shapes[1]):
                strNum = str(jointsFrame[j])
                f.write(strNum)
                f.write(' ')
            f.write('\n')
        f.close()
    
    
    