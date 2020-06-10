
#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Подключаем необходимые библиотеки (для задержки по времени и GPIO)

import time
import RPi.GPIO as GPIO

# Установим номера пинов GPIO, с которыми будем работать
# RESERVED 14/15 GPIO
debug_mode_unload = False 
warm_up_time = 0.5  # Время разогрева светодиодов
OUT_COLOR_InLim = 23 
OUT_PH_InLim = 25
OUT_REFER_InLim = 24
OUT_PH_MOTOR = 2
OUT_BackLight = 3
OUT_USART = 18
LIST_GPIO = (OUT_COLOR_InLim, OUT_PH_InLim, OUT_REFER_InLim, OUT_PH_MOTOR, OUT_BackLight,OUT_USART)# Формируем спикок выходов

def GPIO_init(GPIO_array): # Функция инициализации GPIO выходов
    global debug_mode_unload,LIST_GPIO
     
    GPIO.setwarnings(False) #Отключаем предупреждения GPIO 
    GPIO.cleanup() #Сбрасываем настройки GPIO
     
    
    GPIO.setmode(GPIO.BCM) #Конфигурируем название пинов согласно схеме BCM
    GPIO.setup(LIST_GPIO, GPIO.OUT) # Конфигурируем пины из списка на выход
    GPIO.output(LIST_GPIO, GPIO.LOW) # Устанавливаем 0 на всех пинах
    
    if debug_mode_unload: #отображение отладочного сообщения
            print("---- initialization of GPIO competed")
    

def GPIO_update(GPIO_array, ph_array, setting, film_code_value,probe_code_value,ph_conv_unit): # функция обновления состояния ножек GPIO

############################
    global OUT_COLOR_InLim, OUT_PH_InLim, OUT_REFER_InLim, OUT_PH_MOTOR, OUT_BackLight,OUT_USART
    if  ((setting["UL"] > probe_code_value) & (probe_code_value > setting["LL"])): # Если цвет рабочего раствора вышел за допустимые рамки
        GPIO_array["OUT_COLOR_InLim"]=1 # Прописываем 1 в массив со списком состояний ножек GPIO
        GPIO.output(OUT_COLOR_InLim, True) # Устанавливаем 1 на выход соответствующего пина
    else:
        GPIO_array["OUT_COLOR_InLim"]=0 # Прописываем 0 в массив со списком состояний ножек GPIO
        GPIO.output(OUT_COLOR_InLim, False) # Устанавливаем 0 на выход соответствующего пина

############################

    if  ((((setting["AC"]+setting["ref"]) < film_code_value) or (film_code_value < (setting["ref"])-setting["AC"])) or (ph_conv_unit == 9999)): #Если калибровочный канал вышел за допуски или ошибка связи с atmega/ph-метром
        GPIO_array["OUT_ERROR"]=1 # Прописываем 1 в массив со списком состояний ножек GPIO
        GPIO.output(OUT_REFER_InLim, False)# Устанавливаем 1 на выход соответствующего пина
            
    else:
        GPIO_array["OUT_ERROR"]=0# Прописываем 0 в массив со списком состояний ножек GPIO
        GPIO.output(OUT_REFER_InLim, True)# Устанавливаем 0 на выход соответствующего пина
                                                              
############################
    
    #if  ((ph_array["UL"] > ph_array["AV"]) & (ph_array["AV"] > ph_array["LL"])): # Ph за пределами допусков
    #    GPIO_array["OUT_PH_InLim"]=1 # Прописываем 1 в массив со списком состояний ножек GPIO
    #    GPIO.output(OUT_PH_InLim, True)# Устанавливаем 1 на выход соответствующего пина
    #else:
    #    GPIO_array["OUT_PH_InLim"]=0# Прописываем 0 в массив со списком состояний ножек GPIO
    #    GPIO.output(OUT_PH_InLim, False)# Устанавливаем 0 на выход соответствующего пина

############################


def GPIO_motor_on(GPIO_array,ph_array,flag_relax_time): # Функция включеемя насоса
    global OUT_COLOR_InLim, OUT_PH_InLim, OUT_REFER_InLim, OUT_PH_MOTOR, OUT_BackLight,OUT_USART
############################
    if  (GPIO_array["OUT_PH_InLim"]==0) & (flag_relax_time): #Если ph не в допусках и есть флаг relax_time 
                                                              
        GPIO_array["OUT_PH_MOTOR"]=1 # Прописываем 1 в массив со списком состояний ножек GPIO
        GPIO.output(OUT_PH_MOTOR, True)# Устанавливаем 1 на выход соответствующего пина
    else:
        GPIO_array["OUT_PH_MOTOR"]=0# Прописываем 0 в массив со списком состояний ножек GPIO
        GPIO.output(OUT_PH_MOTOR, False)    # Устанавливаем 0 на выход соответствующего пина    
############################


def GPIO_backlight_on(GPIO_array,command=False): # Функция включения подсветки
    global OUT_COLOR_InLim, OUT_PH_InLim, OUT_REFER_InLim, OUT_PH_MOTOR, OUT_BackLight,OUT_USART
############################
    global warm_up_time
    if  command: 
        GPIO_array["OUT_BackLight"]=1# Прописываем 1 в массив со списком состояний ножек GPIO
        GPIO.output(OUT_BackLight, True)# Устанавливаем 1 на выход соответствующего пина
        time.sleep(warm_up_time)
    else:
        GPIO_array["OUT_BackLight"]=0# Прописываем 0 в массив со списком состояний ножек GPIO
        GPIO.output(OUT_BackLight, False)  # Устанавливаем 0 на выход соответствующего пина         
############################

        



