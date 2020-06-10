#include

import datetime 
import time
import math
import picamera
import numpy as np
import cv2
from tkinter import *
import sys
import socket, threading, time
from threading import Thread
from PIL import Image
import RPi.GPIO as GPIO
from termcolor import colored


#own func
import proj_camera_init as cam_init  # Библиотека инициализации камеры
import proj_frame_processing as frame_proc #Библиотека обработки кадра
import proj_load_unload as sys_func #Библиотека сохранения, загрузки и логирования данных
import proj_delay_time as delay_time #Библиотека задержки без подвешивания процессов COLOR SLEEP
import proj_relax_time as relax_time #Библиотека задержки без подвешивания процессов PH RELAX_TIME
import proj_receving as receiving #Библиотека для обработки входных сообщений по TCP/IP
import proj_gpio_module as gpio_module # Библиотека взаимодействия с GPIO
import proj_ph #Библиотека управления насосом дозировки PH
import proj_delay_ph_time as delay_time_ph #Библиотека задержки без подвешивания процессов PH_SLEEP
import proj_uart_module as uart #Библиотека взаимодействия с UARt

#settings

key = 8194
host = "192.168.30.68"
port = 9091
server = ("192.168.30.146",9090) #PC
#server = ("192.168.30.58",9090)  #Asus

#flags
debug_mode = False #РЕЖИМ ОТЛАДКИ
debug_mode_camera = False # debug камеры
error_enable = True #Флаг отображения ошибок
flag_motor_on = False # флаг состояния насоса
flag_save = False # Флаг команды провести сохранене данных
main_debug = True # основные сообщения
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

#define
"""
161 204 (53, 49, 49) (61, 60, 59) 213.1 269.9 2724


film_sum_value - r + g + b для эталона
probe_sum_value - r + g + b для рабочего раствора
film_rgb_value - R:G;B
probe_rgb_value - R:G;B
film_code_value - Концентрация эталона из расчета по формуле
probe_code_value - Концентрация рабочего раствора из расчета по формуле
ph_conv_unit - Условные единицы ph с mk atmega 8L, если 9999 - ошибка
"""
film_sum_value, probe_sum_value, film_rgb_value, probe_rgb_value,film_code_value,probe_code_value,ph_conv_unit  = 0,0,0,0,0,0,0  #Переменные основных параметров

cicle_w, cicle_r = 1,1 #Номер ячейки записи (для усреднения)




#arrays

setting = {"ref":0,"Z":0,"Loop":0,"Sleep":0,"UL":0,"LL":0, "AC":0, "Num":0, "date":"0","SN":0}

ph_array = {"UL":0, "LL":0, "AV":0, "relax_time":0, "Sleep":0}

GPIO_array = {"OUT_COLOR_InLim":1, "OUT_PH_InLim":1, "OUT_ERROR":0, "OUT_PH_MOTOR":0, "OUT_BackLight":0,}
    
ph_calibration = {"a":0,"b":0}

coord = {"x1":0, "y1":0,
         "x2":200, "y2":200,
         "x3":250, "y3":250,
         "x4":450, "y4":450
         }

calibration = {"a":0, "b":0, "c":0}

"""
setting - настройки колориметра ref - данные эталона (калибровка) , z- коэф отсеивания для фильтрации , Loop - число циклов фильтрации , sleep - частота опроса камеры
UL/LL границы раб.раствора, AC - допуски эталона , Num - размер выборки(усреднения). SN - номер лог файла для сохранения

ph_array - настройки ph-метра,UL/LL границы ph метра, AV- текущее значение кислотности в едининцах PH, relax_time - частота вкл/выкл насоса в режиме дозировки,
Sleep - частота опроса датчика / atmega

GPIO_array - массив состояний пинов raspberry. OUT_COLOR_InLim - 1-Цвет рабочего раствора в допусках, 0 - Цвет вне допуска,
OUT_PH_InLim - 1-Кислотность рабочего раствора в допусках, 0 - PH вне допуска,
OUT_ERROR - 1-эталон вне допуска или вход по каналу PH 9999 уе, 0 - ошибок нет,
OUT_PH_MOTOR - 1 - насос дозировки по показаниям PH - вкл
OUT_BackLight - 1- подстветка кюветы включена, 0 - выключена

ph_calibration и calibration - калибровочные коэфициенты ph и цвета

coord - координаты исследуемых областей (есть спец ПО для определения этих областей и калибровки)

"""

# functions

def main_color_cicle(): #функция сбора данных с камеры, фильтрация и определения концентрации по формуле
    global debug_mode,setting,calibration,coord,\
           film_code_value,probe_code_value,\
           film_sum_value,probe_sum_value,\
           film_rgb_value,probe_rgb_value, \
           cicle_w, cicle_r, ph_array,GPIO_array,main_debug,flag_save,status

    if main_debug:
        now = datetime.datetime.now()
        print(colored("Time {0}:{1}:{2} ; Date {3}:{4}:{5}_________Начат колометрический анализ_________".format(now.hour,now.minute,now.second,now.year,now.month,now.day),"yellow"))
        status = 3
        receiving.get_status(status)
    gpio_module.GPIO_backlight_on(GPIO_array,True) # Включение подсветки
        
    with picamera.PiCamera() as camera: # Обращение к камере
        cam_init.init_camera(camera) # Инициализация камеры
        if debug_mode_camera: # вывод диагностического сообщения
                print("---- initialization of camera competed")

        for _ in range(setting["Num"]): # Выполняем измерения Num раз, т.к сбор данных может происходить редко, набор данных для усреденния необходимо производить в рамках одного измерения

            whole_frame = np.empty((480, 640, 3), dtype=np.uint8) # создаем экземляр класса, трехмерный массив с типом данных uint8


            if debug_mode_camera:# вывод диагностического сообщения
                print("---- Start collecting of data")
                
            camera.capture(whole_frame, 'rgb')  # Захват изображения и сохранение в обозначенный ранее экземпляр класса

            im = Image.fromarray(whole_frame) # Конвертируем массив в тип данных типа IMAGE 
            im.save("/home/pi/project/whole_film.jpeg") # Сохраняем весь снимок
                
            film_frame=whole_frame[coord["y1"]:coord["y2"],coord["x1"]:coord["x2"],0:3] # Выделяем первый массив согласно заданным координатам
            probe_frame=whole_frame[coord["y3"]:coord["y4"],coord["x3"]:coord["x4"],0:3] # ВЫделяем второй массив согласно заданным координатам
                
            im = Image.fromarray(film_frame)  # Конвертируем массив в тип данных типа IMAGE 
            im.save("/home/pi/project/film_before_processing.jpeg")  # Сохраняем кадр первой зоны
            im = Image.fromarray(probe_frame) # Конвертируем массив в тип данных типа IMAGE 
            im.save("/home/pi/project/probe_before_processing.jpeg") # Сохраняем кадр второй зоны
                

            film_rgb_value, probe_rgb_value = frame_proc.scan_func(film_frame,probe_frame,setting) #Функция усреднения и фильтрации массивов данных, выходной формат R:G:B 
                
            if debug_mode_camera:# вывод диагностического сообщения
                print("---- film_rgb_value - {0}, probe_rgb_value - {1}".format(film_rgb_value,probe_rgb_value))
                    
            film_sum_value, probe_sum_value, cicle_w, cicle_r = frame_proc.value_to_sum_func(film_rgb_value,probe_rgb_value,setting,cicle_w, cicle_r)  #Функция накопления данных, расчет среднего и приведение к одночисловому представлению цвета 

            if debug_mode_camera:# вывод диагностического сообщения
                print("---- film_sum_value - {0}, probe_sum_value - {1}".format(film_sum_value,probe_sum_value))

            film_code_value = frame_proc.color_code_func(calibration,film_sum_value) # Функция преобразования условнго значения цвета в концентрацию
            probe_code_value = frame_proc.color_code_func(calibration,probe_sum_value) # Функция преобразования условнго значения цвета в концентрацию
                
            if debug_mode_camera:# вывод диагностического сообщения
                print("---- film_code_value - {0}, probe_code_value - {1}".format(film_code_value,probe_code_value))


                
            im = Image.fromarray(film_frame) # Конвертируем массив в тип данных типа IMAGE 
            im.save("/home/pi/project/film_after_processing.jpeg") # Сохраняем кадр первой зоны после фильтрации
            im = Image.fromarray(probe_frame) # Конвертируем массив в тип данных типа IMAGE 
            im.save("/home/pi/project/probe_after_processing.jpeg") # Сохраняем кадр второй зоны после фильтрации

            

        gpio_module.GPIO_backlight_on(GPIO_array,False) # Выключение подсветки

        ###########Вывод отчетности#############
        now = datetime.datetime.now()  #ЗАпрос даты с RTC
        if main_debug: 
            if (probe_code_value>setting["LL"]) & (probe_code_value<setting["UL"]):  # Проверка данных рабочего раствора, определение цвета сообщения
                color = "green"
            else:
                color = "red"
            print(colored("Time {0}:{1}:{2} ; Date {3}:{4}:{5}_________Закончен колометрический анализ_________LL - {6} , CV - {7} , UL - {8}".format(now.hour,now.minute,now.second,now.year,now.month,now.day,setting["LL"],probe_code_value,setting["UL"]),color))
            if (film_code_value<(setting["ref"] + setting["AC"])) & ((probe_code_value>(setting["ref"] - setting["AC"]))):# Проверка данных эталлонной пленки, определение цвета сообщения
                color = "green"
            else:
                color = "red"
            print(colored("Time {0}:{1}:{2} ; Date {3}:{4}:{5}_________Закончен контроль эталона_________CV - {6} , MEM - {7} , AC - {8}".format(now.hour,now.minute,now.second,now.year,now.month,now.day,film_code_value,setting["ref"],setting["AC"]),color))
            status = 4
            receiving.get_status(status)
        flag_save = True #Флаг запуска сохранения
        

# Socket channel

############################


def receving (name, sock):  #функция работы с входным потоком
    global debug_mode,setting,calibration,coord,\
           film_code_value,probe_code_value,\
           film_sum_value,probe_sum_value,\
           film_rgb_value,probe_rgb_value, \
           input_data,num, ph_calibration, \
           cicle_w, cicle_r, ph_array,status
           
    time.sleep(0.1) 
    while True:
        try:
            while True:
                input_data, addr = sock.recvfrom(1024)  # Функция чтения входного сообщения
                num=0
                try:
                    
                    num, setting,calibration,coord,cicle_w,cicle_r,input_data,ph_calibration,ph_array = receiving.recognaize_message(debug_mode,setting,calibration,coord,\
                       film_code_value,probe_code_value, film_sum_value,probe_sum_value, film_rgb_value,probe_rgb_value, num, \
                       cicle_w, cicle_r,input_data,s,server,ph_calibration,GPIO_array,ph_array) # Передача входного потока подпрограмме обработки данных

                
                except Exception as error:          
                    print(error)

  
        except Exception as error:
            if (str(error)[1:9] =="Errno 11"): #Пропуск стандартных ошибок отсутствия связи и тишины
                pass
            elif (str(error)[1:8] =="Errno 9"):
                pass
            else:
                print(str(error)[1:9])

        except BaseException as e:
            s.close()
            rT.join()
            print("---- Прерывание")
            if error_enable == True: 
                raise (e)

now = datetime.datetime.now()  #Запрос даты с RTC

print(colored("Time {0}:{1}:{2} ; Date {3}:{4}:{5}_________Программа запущена и работает корректно_________".format(now.hour,now.minute,now.second,now.year,now.month,now.day),"yellow"))

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)  # Параметры сети TCP/IP
s.bind((host,port)) # Занимаем и открывает порт
s.setblocking(0) #Закрываем доступ к порту другим устройствам

rT = threading.Thread(target = receving, args = ("receving",s)) # Открываем многопоточный режим, передаем второй поток функции receving
rT.start() # Запускаем второй поток
time.sleep(1)
status = 1 
receiving.get_status(status) # Передача нового статуса функции сбора
############################
delay_time.init_time() #Инициализация фукции фонового счета
delay_time_ph.init_time() #Инициализация фукции фонового счета
relax_time.init_time() #Инициализация фукции фонового счета
gpio_module.GPIO_init(GPIO_array) #Инициализация GPIO  пинов
start_flag = False # Сброс загрузочного флага
error_usart = False # Сброс флага ошибки чтения ph с atmega 
setting, coord, calibration, ph_calibration, ph_array=sys_func.load_settings(setting,coord,calibration,ph_calibration,ph_array) # Загрузка настроек и калибровок из txt файлов 

if debug_mode_camera: # вывод диагностического сообщения
    print ("----", coord,"\n","----",setting,"\n","----",calibration, "\n")
    
main_color_cicle() # Вызов функции колориметра  
#ph_conv_unit,ph_array,error_usart,status = uart.dialog_serial(ph_array,ph_calibration,main_debug,error_usart,status) # Вызов функции опроса ph-метра
time.sleep(0.5)
now = datetime.datetime.now() #Запрос даты с RTC
print(colored("Time {0}:{1}:{2} ; Date {3}:{4}:{5}_________Инициализация исполняющей программы завершена___".format(now.hour,now.minute,now.second,now.year,now.month,now.day,setting["LL"],probe_code_value,setting["UL"]),"yellow"))
status = 2
receiving.get_status(status) # Передача нового статуса функции сбора
gpio_module.GPIO_update(GPIO_array, ph_array, setting, film_code_value,probe_code_value,ph_conv_unit) #Обновление состояния пинов GPIO
flag_save = True
try:
    while(1):

##################################################################################################################################        
        if (delay_time.delay_time(setting)): #Проверка Sleep таймера, 
            
            main_color_cicle() # Вызов функции колориметра  
            
################################################################################################################################## 

        #if (GPIO_array["OUT_PH_InLim"]==1): #Проверка статуса PH
            #if (delay_time_ph.delay_time(ph_array)): # Если pH в норме работаем по стандартной задержке
                #flag_save = True #Флаг запуска сохранения
            
                #ph_conv_unit,ph_array,error_usart,status = uart.dialog_serial(ph_array,ph_calibration,main_debug,error_usart,status) # Вызов функции опроса ph-метра
            

        #if (GPIO_array["OUT_PH_InLim"]==0) & (start_flag): #Проверка статуса PH
           # if (delay_time_ph.delay_time({"Sleep":120})): # Если pH не в норме работаем по мануальной задержке
                
                #flag_save = True #Флаг запуска сохранения
                #ph_conv_unit,ph_array,error_usart,status = uart.dialog_serial(ph_array,ph_calibration,main_debug,error_usart,status) # Вызов функции опроса ph-метра

    
################################################################################################################################## 


        if flag_save: #Проверка статуса флага сохранения
            gpio_module.GPIO_update(GPIO_array, ph_array, setting, film_code_value,probe_code_value,ph_conv_unit) #Обновление состояния пинов GPIO

            #GPIO_array, ph_array,flag_motor_on,flag_save,ph_conv_unit,start_flag,error_usart,status = proj_ph.control_motor_ph(GPIO_array, ph_array,flag_motor_on,ph_conv_unit,flag_save,ph_calibration,start_flag, error_usart,status) # Вызов функции управления насосом дозировки PH
        
            gpio_module.GPIO_update(GPIO_array, ph_array, setting, film_code_value,probe_code_value,ph_conv_unit)  #Обновление состояния пинов GPIO
            setting = sys_func.log_func(setting, ph_array,GPIO_array, film_code_value, probe_code_value) #Запуск функции логирования данных
            flag_save = False #Флаг запуска сохранения
            
##################################################################################################################################         
except KeyboardInterrupt as e:
    #rT._stop()
    #rT.join()
    raise(e) 
    s.close() 
    GPIO.cleanup()

    
           
except BaseException as e:    
    print("---- Прерывание")
    raise(e)
    s.close() 
    GPIO.cleanup()
    rT.join()


#Test,y4:255,x3:375,x2:198,y3:220,y1:231,y2:266,x1:163,x4:410,
