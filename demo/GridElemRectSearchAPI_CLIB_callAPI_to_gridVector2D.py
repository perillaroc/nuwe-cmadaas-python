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
    interfaceId = "getNafpVectorEleGridByTimeAndLevelAndValidtime"    
    
    # 2.3 服务节点ID
    serverId = "NMIC_MUSIC_CMADAAS"
        
    # 2.3  接口参数，多个参数间无顺序     
    # 必选参数    (1)资料:欧洲中心数值预报产品-低分辨率-全球; (2)起报时间;(3)预报时效;(5)预报要素（单个):气温;(4)预报层次(单个):85000pa;
    params = {'dataCode':"NAFP_FOR_FTM_LOW_EC_GLB",\
                                 'time':"20190324000000",\
                                 'validTime':"24",\
                                 'fcstuele':"WIU",'fcstvele':"WIV",\
                                 'fcstLevel':"850",'levelType':"100"}
    
    # 3. 调用接口
    #result = client.callAPI_to_gridVector2D(userId, pwd, interfaceId,params)
    result = client.callAPI_to_gridVector2D(userId, pwd, interfaceId,params,serverId)    
    
    # 4. 输出接口
    print "return code: ",result.request.errorCode
    print "return message: ",result.request.errorMessage
    
    if result.request.errorCode == 0:
        resultDataU = result.u_datas
        resultDataV = result.v_datas
        #返回数据行shapes[0]和列shapes[1]
        shapesU = np.array(resultDataU).shape
        shapesV = np.array(resultDataV).shape
        #print shapes[0], shapes[1]
        fu = open('gridVectorU2D.txt', 'w')
        fv = open('gridVectorV2D.txt', 'w')
        
        for i in range(shapesU[0]):
            jointsFrame = resultDataU[i] #每行
            resultDataU.append(jointsFrame)
            for j in range(shapesU[1]):
                strNum = str(jointsFrame[j])
                fu.write(strNum)
                fu.write(' ')
            fu.write('\n')
        
        for i in range(shapesV[0]):
            jointsFrame = resultDataV[i] #每行
            resultDataV.append(jointsFrame)
            for j in range(shapesV[1]):
                strNum = str(jointsFrame[j])
                fv.write(strNum)
                fv.write(' ')
            fv.write('\n')
            
        fu.close()
        fv.close()
    
    
    