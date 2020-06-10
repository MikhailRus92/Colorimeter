import proj_load_unload as sys_func
import proj_frame_processing as frame_proc
import datetime 
import time
import math
import sys
from termcolor import colored
#import clean_project as main_pr
debug_mode_memo = False
debug_mode_save_update = False
status = 0
"""
0 - Ничего не произошло
1 - Программа запущена и работает корректно
2 - Инициализация исполняющей программы завершена
3 - Начат колометрический анализ
4 - Закончен контроль эталона и рабочего раствора 
5 - Ошибка чтения данных по USART насос выкл
6 - Произведен кислотный анализ
7 - PH не в норме, насос вкл
8 - PH не в норме, насос выкл
9 - PH в норме, насос выкл


"""
def recognaize_message(debug_mode,setting,calibration,coord,
                       film_code_value,probe_code_value,\
                       film_sum_value,probe_sum_value,\
                       film_rgb_value,probe_rgb_value, \
                       num, cicle_w, cicle_r,\
                       input_data,s,server,ph_calibration,GPIO_array,ph_array):

    global debug_mode_memo,debug_mode_save_update,status
    if debug_mode: #Вывод диагностичского сообщения
        print(colored(">>>> " + str(input_data), "red"))

    #############################################################################################################################

    if ((str(input_data))[2:12]=="GetSetting"): #Сообщение для запроса настроек колориметра
        msg = "Send;ref:{0};z:{1};loop:{2};sleep:{3};UL:{4};LL:{5};AC:{6};Num:{7};date:{8}"\
            .format(setting["ref"],setting["Z"],setting["Loop"],setting["Sleep"],setting["UL"],setting["LL"],setting["AC"],\
                setting["Num"],setting["date"])

        s.sendto(msg.encode("utf-8"),server) #отправка ответного сообщения
        time.sleep(0.1) #Задержка после отправки
        if debug_mode: #Вывод диагностичского сообщения
            print("<<<< " + str(msg))
    #############################################################################################################################

    if ((str(input_data))[2:12]=="SetSetting"): #Сообщение установки новых параметров колориметра
                    
        s.sendto("Done".encode("utf-8"),server)#отправка ответного сообщения
        if debug_mode:#Вывод диагностичского сообщения
            print("<<<< " + str("Done"))                     
        time.sleep(0.1) #Задержка после отправки

        x=str(input_data) #разбиваем остаток строки на элементы массива настроек
        z=x.split(";")
        for i in range(1,len(z)-1):
            y=z[i].split(":")
            if ("." in y[0]) and (len(y[0])<9):
                setting[y[0]]=float(y[1])
            else:
                try:
                    setting[y[0]]=int(y[1])
                except:
                    setting[y[0]]=(y[1])
        if setting["UL"]<setting["LL"]:
            setting["UL"], setting["LL"]= setting["LL"],setting["UL"]
            if debug_mode:#Вывод диагностичского сообщения
                print("---- Исправлена ошибка границ")
                                    
        sys_func.save_settings(setting) #Сохраняем новые настройки
        if debug_mode:#Вывод диагностичского сообщения
            print ("----", setting)
        cicle_w, cicle_r = 1,1 #Обнуляем все накопленные данные, т.к они могут быть неактуальны
        if debug_mode_save_update:#Вывод диагностичского сообщения
            print("<<<< " + "Setting has been changed")
        setting = sys_func.log_func(setting,ph_array,GPIO_array,film_code_value,probe_code_value) #Логируем все данные

    #############################################################################################################################

    if ((str(input_data))[2:11]=="UpdateRef"):# Сообщение обновления эталона
        now = datetime.datetime.now() #Запрос данных с RC 
        msg = "date - {0}.{1}.{2},time - {3}.{4}.{5}".format(now.year, now.month, now.day, now.hour,now.minute,now.second) #Формирование даты калибровки
        setting["date"]=msg #СОхраняем новую дату в массив колориметра
        setting["ref"]=frame_proc.color_code_func(calibration,film_sum_value) #Запускаем цикл расчета нового эталона 
        msg+=" Ref - {0}".format(str(frame_proc.color_code_func(calibration,film_sum_value))) #Добавляем к ответному сообщению данные об новом эталоне

        sys_func.save_settings(setting) #Сохраняем настройки
        s.sendto(msg.encode("utf-8"),server)#отправка ответного сообщения
        time.sleep(0.1) #Задержка после отправки
                    
        setting = sys_func.log_func(setting,ph_array , GPIO_array,film_code_value,probe_code_value) #Логируем все данные
                                
        if debug_mode:#Вывод диагностичского сообщения
            print ("<<<< " + str(msg))
           
    #############################################################################################################################                       
              
                  
    if ((str(input_data))[2:7]=="Start"): #Сообщение об начале сбора данных
                    
        with open("/home/pi/project/log/LogFile{0}.txt".format(setting["SN"]),"r") as LogFile: #Открываем файл с логами
            num=0
            log_list = []
            for line in LogFile: # Считаем все строки и составляем список из них
                num+=1
                log_list.append(line)
                        
            msg = "Number "+str(num) #Формируем ответное сообщение с числом измерений
            s.sendto(msg.encode("utf-8"),server)#отправка ответного сообщения

            if debug_mode:#Вывод диагностичского сообщения
                print("<<<< " + msg)
            time.sleep(1) #Задержка после отправки
                        
        with open("/home/pi/project/log/LogFile{0}.txt".format(setting["SN"]),"r") as LogFile: #Открываем файл с логами
            for i in range(0,num): # Ещё раз проходимся по всем строкам и отправляем все данные серверу
                s.sendto(log_list[i].encode("utf-8"),server)#отправка ответного сообщения
                if debug_mode_memo:#Вывод диагностичского сообщения
                    print("<<<< " + log_list[i])
                time.sleep(0.01) #Задержка после отправки

    #############################################################################################################################
                
    if ((str(input_data))[2:12]=="DeleteMemo"): # Сообщение об удалении логов
        open("/home/pi/project/log/LogFile{0}.txt".format(setting["SN"]),"w").close() #Открываем файл для перезаписи и закрываем
        s.sendto("Done".encode("utf-8"),server)#отправка ответного сообщения
        if debug_mode:#Вывод диагностичского сообщения
            print("<<<< " + "Done")
        time.sleep(0.01) #Задержка после отправки

    #############################################################################################################################

    if ((str(input_data))[2:15]=="GetRatioColor"): #Сообщение с запросом данных калибровки для колориметра
        msg = "Send;a:{0};b:{1};c:{2};"\
              .format(calibration["a"],calibration["b"],calibration["c"])# Формирование ответного сообющения

        s.sendto(msg.encode("utf-8"),server)#отправка ответного сообщения
        time.sleep(0.1) #Задержка после отправки
        if debug_mode:#Вывод диагностичского сообщения
            print("<<<< " + str(msg))
            
    #############################################################################################################################


    if ((str(input_data))[2:15]=="SetRatioColor"): #Собщение с командой изменения калибровочных коэфицентов колориметра
                    
        s.sendto("Done".encode("utf-8"),server)#отправка ответного сообщения
        if debug_mode:#Вывод диагностичского сообщения
            print("<<<< " + str("Done"))                    
        time.sleep(0.1) #Задержка после отправки

        x=str(input_data) # Разбиваем входную строку на отдельные элементы и обновляем массив калибровочных коэфицентов
        z=x.split(";")
        for i in range(1,len(z)-1): #Все коэфициенты передаются в целочисленном формате, после получения их делим на 1000
            y=z[i].split(":")
            calibration[y[0]]=int(y[1])/1000
                                    
        #sys_func.save_settings(setting)
        sys_func.save_calibration(calibration) #Пересохраняем данные калибровки в txt файл
        if debug_mode:#Вывод диагностичского сообщения
            print ("----", calibration)
            
    #############################################################################################################################

    if ((str(input_data))[2:12]=="GetRatioPh"): #Сообщение с запросом данных калибровки и настроек для ph-метра
        msg = "Send;a:{0};b:{1};sl:{2};rlx:{3};UL:{4};LL:{5}".format(ph_calibration["a"],ph_calibration["b"],ph_array["Sleep"],\
                                                                     ph_array["relax_time"], ph_array["UL"],ph_array["LL"])# Формирование ответного сообющения

        s.sendto(msg.encode("utf-8"),server)#отправка ответного сообщения
        time.sleep(0.1) #Задержка после отправки
        if debug_mode:#Вывод диагностичского сообщения
            print("<<<< " + str(msg))

    #############################################################################################################################

    if ((str(input_data))[2:12]=="SetRatioPh"): #Собщение с командой изменения калибровочных коэфицентов и настроек ph- метра
                    
        s.sendto("Done".encode("utf-8"),server)#отправка ответного сообщения
        if debug_mode:#Вывод диагностичского сообщения
            print("<<<< " + str("Done"))                    
        time.sleep(0.1) #Задержка после отправки

        x=str(input_data) # Разбиваем входную строку на отдельные элементы и обновляем массив калибровочных коэфицентов
        z=x.split(";")
        for i in range(1,len(z)-1):
            y=z[i].split(":")
            if y[0] in ph_calibration:
                ph_calibration[y[0]]=int(y[1])/10000
            if y[0] in ph_array:
                if y[0] in ("relax_time","Sleep"):
                    ph_array[y[0]]=int(y[1])
                if y[0] in ("UL","LL"):
                    ph_array[y[0]]=int(y[1])/10000
                                    
        #sys_func.save_settings(setting)
        sys_func.save_calibration_Ph(ph_calibration)  #Сохранение данных калибровки в txt файл
        sys_func.save_ph_array(ph_array)#Сохранение настроек в txt файл
        if debug_mode:#Вывод диагностичского сообщения
            print ("----", ph_calibration)
            print ("----", ph_array)

    #############################################################################################################################
    if ((str(input_data))[2:10]=="GetValue"): # Сообщенрие с запросом основных параметров + статусы GPIO  
        msg = "Send;Color_Probe:{0};Color_Ref:{1};Actual_Ph:{2};S1:{3};S2:{4};S3:{5};S4:{6};S5:{7};St:{8};"\
            .format(probe_code_value,film_code_value,ph_array["AV"],GPIO_array["OUT_COLOR_InLim"],GPIO_array["OUT_PH_InLim"],GPIO_array["OUT_ERROR"],GPIO_array["OUT_PH_MOTOR"],GPIO_array["OUT_BackLight"],status)#Формирование ответного сообщения
        status = 0
        now = datetime.datetime.now() #Запрос данных с RC 
        msg += "date - {0}.{1}.{2},time - {3}.{4}.{5}".format(now.year, now.month, now.day, now.hour,now.minute,now.second) #Формирование даты запроса
    
        
        s.sendto(msg.encode("utf-8"),server)#отправка ответного сообщения 
        time.sleep(0.001) #Задержка после отправки

   
    return(num,setting,calibration,coord,cicle_w,cicle_r,input_data,ph_calibration,ph_array)
        
def get_status(stat): # функции сбора и хранения статусов
    global status
    status = stat
    
