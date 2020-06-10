import time
import proj_uart_module as uart
import RPi.GPIO as GPIO
import proj_gpio_module as gpio_module
import proj_relax_time as relax_time
from termcolor import colored
import datetime
import proj_receving as receiving #Библиотека для обработки входных сообщений по TCP/IP
temp_pump = False

def control_motor_ph(GPIO_array, ph_array,flag_motor_on,ph_conv_unit,flag_save,ph_calibration,start_flag,error_usart,status): # Функция управления насосом дозировки по PH
    global temp_pump
    now = datetime.datetime.now() # Запрос времени с RTC
    if ((GPIO_array["OUT_PH_InLim"]==0)&(not error_usart)): # Если вне допусков и при этом нет ошибки связи  Ph-метром
        temp_pump = True # Устанавливаем флаг того, что насос находится в режиме дозировки
        relax_flag = relax_time.relax_time(ph_array) # Принимаем флаг готовности к смене сотояния насоса по времени
        if (relax_flag & (not flag_motor_on)) or (not start_flag): # Если пора менять состояние, при этом насос выключен или это просто первый запуск программы  
            
            gpio_module.GPIO_motor_on(GPIO_array,ph_array,True) #Включаем насос передачей соответствующей команды в функции GPIO
            flag_motor_on = True # Устанавливаем флаг, что насос работает
            print(colored("Time {0}:{1}:{2} ; Date {3}:{4}:{5}_________PH не в норме, насос вкл_________LL - {6} , CV - {7} , UL - {8}".format(now.hour,now.minute,now.second,now.year,now.month,now.day,ph_array["LL"],ph_array["AV"],ph_array["UL"]),"red"))
            status = 7
            receiving.get_status(status)
            

        elif (relax_flag & (flag_motor_on)): #Если пора менять состояние, при этом насос выключен
            gpio_module.GPIO_motor_on(GPIO_array,ph_array,False) #Временно выключаем насос передачей соответствующей команды в функции GPIO
            flag_motor_on = False #Устанавливаем флаг выключенного насоса
            print(colored("Time {0}:{1}:{2} ; Date {3}:{4}:{5}_________PH не в норме, насос выкл_________LL - {6} , CV - {7} , UL - {8}".format(now.hour,now.minute,now.second,now.year,now.month,now.day,ph_array["LL"],ph_array["AV"],ph_array["UL"]),"red"))
            status = 8
            receiving.get_status(status)
    else: #Если ph в допусках
        
        gpio_module.GPIO_motor_on(GPIO_array,ph_array,False) # вВыключаем насос передачей соответствующей команды в функции GPIO
        flag_motor_on = False #Устанавливаем флаг того, что насос выключен
        if (temp_pump) & (error_usart): # Проверяем находится ли насос в режиме дозировки и есть ли ошибка?
            print(colored("Time {0}:{1}:{2} ; Date {3}:{4}:{5}_________Ошибка чтения данных по USART насос выкл_________LL - {6} , CV - {7} , UL - {8}".format(now.hour,now.minute,now.second,now.year,now.month,now.day,ph_array["LL"],ph_array["AV"],ph_array["UL"]),"yellow"))
            temp_pump = False #Устанавливаем флаг того, что режим дозировка выкл
            status = 5
            receiving.get_status(status)
        elif temp_pump: #Если тоже самое только без ошибки
            print(colored("Time {0}:{1}:{2} ; Date {3}:{4}:{5}_________PH в норме, насос выкл_________LL - {6} , CV - {7} , UL - {8}".format(now.hour,now.minute,now.second,now.year,now.month,now.day,ph_array["LL"],ph_array["AV"],ph_array["UL"]),"yellow"))
            temp_pump = False #Устанавливаем флаг того, что режим дозировка выкл
            status = 9
            receiving.get_status(status)
       
    start_flag = True #Устанавливаем флаг того, что программа прошла стартовый цикл
    
    return GPIO_array, ph_array, flag_motor_on,flag_save, ph_conv_unit,start_flag,error_usart,status

