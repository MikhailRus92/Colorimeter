import sys
import datetime 
import time
import math

debug_mode_unload =False
debug_mode =True
debug_mode_save_update = False

def log_func(setting,ph_array,GPIO_array,film_code_value,probe_code_value,mode = "ok"): #Функция логирования данных
    global debug_mode,debug_mode_unload, debug_mode_save_update 
    with open("/home/pi/project/log/LogFile{0}.txt".format(setting["SN"]),"a") as LogFile: #  Отрываем файл с функцией изменения
        now = datetime.datetime.now() # Запрос времени с RTC
        if mode == "ok": 
            log_msg = "Reference - {0} ; Sample - {1} ; REF - {2} ; UL - {3} ; LL - {4} ; AC - {5} ; AV_PH - 0.0 ; UL_PH - 0.0 ; LL_PH - 0.0 ; S1 - {6} ; S2 - {7} ; S3 - {8} ; S4 - {9} ; S5 - {10} ; Time {11}:{12}:{13} ; Date {14}:{15}:{16}\n".format(\
                film_code_value,probe_code_value,setting["ref"],setting["UL"],setting["LL"],setting["AC"],GPIO_array["OUT_COLOR_InLim"],GPIO_array["OUT_PH_InLim"],GPIO_array["OUT_ERROR"],\
                GPIO_array["OUT_PH_MOTOR"],GPIO_array["OUT_BackLight"], now.hour,now.minute,now.second,now.year,now.month,now.day) # формируем сохраняемую строку
            LogFile.write(log_msg) # добавляем строку
            if debug_mode_save_update: #отображение отладочной информации
                print("---- data has been saved")
        else:
            pass

    with open("/home/pi/project/log/LogFile{0}.txt".format(setting["SN"]),"r") as LogFile: #открывае log Только для чтения  и считаем число строк, если больше 3000, меняем имя файла SN
            num=0
            log_list = []
            for line in LogFile:
                num+=1
                log_list.append(line)

            if num>3000:
                setting["SN"] +=1
                save_settings(setting)
                print ("Началось сохранение логов в другой файл №{0}".format(setting["SN"])) 

    return setting

    

def load_settings(setting,coord,calibration,ph_calibration,ph_array): # Загрузить настройки из файлов
    global debug_mode,debug_mode_save_update

########################################################################
    with open("/home/pi/project/Setting.txt","r") as SettingFile: # Открыть файл для чтения разделить текст на ключи и слова и обновить массивы
        for line in SettingFile:  
            line = line.replace("\n","")
            temp=line.split(":")
            if ("." in temp[1]) & (len(temp[1])<9):
                setting[temp[0]]=float(temp[1])
            else:
                try:
                    setting[temp[0]]=int(temp[1])
                except ValueError as e:
                    setting[temp[0]]=temp[1]
    if setting["UL"]<setting["LL"]:
        setting["UL"], setting["LL"]= setting["LL"],setting["UL"]
        save_settings()
        if debug_mode:
            print("---- Исправлена ошибка границ")

    if debug_mode_unload:
        print("---- setting_array has been unloaded")
        
########################################################################
    with open("/home/pi/project/PH-array.txt","r") as ph_arrayFile: # Открыть файл для чтения разделить текст на ключи и слова и обновить массивы
        for line in ph_arrayFile:
            line = line.replace("\n","")
            temp=line.split(":")
            if ("." in temp[1]) & (len(temp[1])<9):
                ph_array[temp[0]]=float(temp[1])
            else:
                try:
                    ph_array[temp[0]]=int(temp[1])
                except ValueError as e:
                    ph_array[temp[0]]=temp[1]
    if ph_array["UL"]<ph_array["LL"]:
        ph_array["UL"], ph_array["LL"]= ph_array["LL"],ph_array["UL"]
        save_settings()
        if debug_mode:
            print("---- Исправлена ошибка границ Ph")

    if debug_mode_unload:
        print("---- ph_array has been unloaded")
        
########################################################################
        
    with open("/home/pi/project/CoordFile.txt","r") as CoordFile: # Открыть файл для чтения разделить текст на ключи и слова и обновить массивы
            for line in CoordFile:
                line = line.replace("\n","")
                if len(line) >10:
                    temp=line.split(",")
                    coord_name=temp[0]
                    temp.remove(temp[0])
                    try:
                        temp.remove("")
                    except ValueError as err:
                        pass
                    for i in temp:
                        temp1=i.split(":")
                        coord[temp1[0]]=int(temp1[1])

            if debug_mode_unload:
                print("---- coord_array has been unloaded")
                
########################################################################
                
    with open("/home/pi/project/CalibrationFile.txt","r") as CalibrationFile: # Открыть файл для чтения разделить текст на ключи и слова и обновить массивы
        for line in CalibrationFile:
            line = line.replace("\n","")
            temp=line.split(":")
            if ("." in temp[1]) & (len(temp[1])<9):
                calibration[temp[0]]=float(temp[1])
            else:
                try:
                    calibration[temp[0]]=int(temp[1])
                except ValueError as e:
                    calibration[temp[0]]=temp[1]
        if debug_mode_unload:
             print("---- calibration_array has been unloaded")

########################################################################

    with open("/home/pi/project/CalibrationFilePh.txt","r") as CalibrationFilePh: # Открыть файл для чтения разделить текст на ключи и слова и обновить массивы
        for line in CalibrationFilePh:
            line = line.replace("\n","")
            temp=line.split(":")
            if ("." in temp[1]) & (len(temp[1])<9):
                ph_calibration[temp[0]]=float(temp[1])
            else:
                try:
                    ph_calibration[temp[0]]=int(temp[1])
                except ValueError as e:
                    ph_calibration[temp[0]]=temp[1]
        if debug_mode_unload:
             print("---- ph_calibration has been unloaded")
             
########################################################################
             
    return (setting,coord,calibration,ph_calibration,ph_array)

    
def save_settings(setting): # Функция сохранения обновленных настроек
    global debug_mode,debug_mode_save_update
    with open("/home/pi/project/Setting.txt","w") as SettingFile:# Открыть файл для записи формируем строчку из ключа и слова и добавляем в файл
        for i in setting:
            SettingFile.write("{0}:{1}\n".format(i,setting[i]))
    if debug_mode_save_update:
        print("---- setting_array has been saved")

def save_ph_array(ph_array):# Открыть файл для записи формируем строчку из ключа и слова и добавляем в файл
    global debug_mode,debug_mode_save_update
    with open("/home/pi/project/PH-array.txt","w") as PH_arrayFile:
        for i in ph_array:
            PH_arrayFile.write("{0}:{1}\n".format(i,ph_array[i]))
    if debug_mode_save_update:
        print("---- ph_array has been saved")


def save_calibration(calibration):# Открыть файл для записи формируем строчку из ключа и слова и добавляем в файл
    global debug_mode,debug_mode_save_update
    with open("/home/pi/project/CalibrationFile.txt","w") as CalibrationFile:
        for i in calibration:
            CalibrationFile.write("{0}:{1}\n".format(i,calibration[i]))
    if debug_mode_save_update:
        print("---- calibration_array has been saved")
    
def save_calibration_Ph(ph_calibration):# Открыть файл для записи формируем строчку из ключа и слова и добавляем в файл
    global debug_mode,debug_mode_save_update
    with open("/home/pi/project/CalibrationFilePh.txt","w") as CalibrationFilePh:
        for i in ph_calibration:
            CalibrationFilePh.write("{0}:{1}\n".format(i,ph_calibration[i]))
    if debug_mode_save_update:
        print("---- ph_calibration has been saved")

