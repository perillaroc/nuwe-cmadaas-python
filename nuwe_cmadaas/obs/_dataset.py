

STATION_DATASETS = {
    "SURF_CHN_MUL_HOR": {
        "long_name": "中国地面逐小时资料",
        "elements": "Station_Id_d,Lat,Lon,Alti,Year,Mon,Day,Hour,PRS_Sea,TEM,DPT,WIN_D_INST,WIN_S_INST,PRE_1h,PRE_6h,PRE_24h,PRS"
    },
    "SURF_CHN_MUL_DAY": {
        "long_name": "中国地面日值数据",
        "elements": "Station_Id_d,Lat,Lon,Alti,Year,Mon,Day,PRS_Sea_Avg,TEM_Avg,TEM_Max,TEM_Min"
    },
    "SURF_CHN_MUL_MON": {
        "long_name": "中国地面月值数据（区域站）",
        "elements": "Station_Id_d,Lat,Lon,Alti,Year,Mon,PRS_Sea_Avg,TEM_Avg,TEM_Max_Avg,TEM_Min_Avg"
    }
}


UPPER_AIR_DATASETS = {
    "UPAR_GLB_MUL_FTM": {
        "long_name": "全球高空定时值资料",
        "elements": "Station_Id_d,Lat,Lon,Alti,Day,Hour,Min,PRS_HWC,EVSS,GPH,TEM,DPT,WIN_D,WIN_S,Time_Dev_WQ,Lat_Dev,Lon_Dev,Q_PRS_HWC,Q_GPH,Q_TEM,Q_DPT,Q_WIN_D,Q_WIN_S",
        "order_by": "Station_Id_d:asc"
    },
    "UPAR_CHN_MUL_FTM": {
        "long_name": "中国高空定时值资料",
        "elements": "Station_Id_d,Lat,Lon,Alti,Day,Hour,Min,PRS_HWC,EVSS,GPH,TEM,DPT,WIN_D,WIN_S,Time_Dev_WQ,Lat_Dev,Lon_Dev,Q_PRS_HWC,Q_GPH,Q_TEM,Q_DPT,Q_WIN_D,Q_WIN_S",
        "order_by": "Station_Id_d:asc"
    },
    "UPAR_ARD_G_MUT_AMD": {
        "long_name": "全球飞机高空探测资料",
        "elements": "Lat,Lon,Day,Hour,Min,Flight_Stat,Flight_Heigh,TEM,WIN_D,WIN_S,Q_Flight_Heigh,Q_TEM,Q_WIN_D,Q_WIN_S,Station_Id_C"
    },
    "UPAR_ARD_GLB_MUT_AMD_BUFR": {
        "long_name": "全球飞机高空探测资料 (BUFR格式)",
        "elements": "Lat,Lon,Day,Hour,Min,Flight_Stat,Flight_Heigh,TEM,WIN_D,WIN_S,Q_Flight_Heigh,Q_TEM,Q_WIN_D,Q_WIN_S,Station_Id_C"
    },
    "UPAR_GLB_MUL_MON": {
        "long_name": "全球高空月值数据",
        "elements": "Station_Id_d,Lat,Lon,Alti,Year,Mon,PRS_HWC,EVSS,GPH,TEM_Avg",
        "order_by": "Station_Id_d:asc"
    },
    "UPAR_GLB_MUL_TEN": {
        "long_name": "全球高空旬值数据",
        "elements": "Station_Id_d,Lat,Lon,Alti,Year,Mon,PRS_HWC,EVSS,GPH,TEM_Avg",
        "order_by": "Station_Id_d:asc"
    }
}
