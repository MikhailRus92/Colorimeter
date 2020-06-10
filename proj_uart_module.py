#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime 
import serial
import time
from termcolor import colored
import proj_receving as receiving #Библиотека для обработки входных сообщений по TCP/IP
import RPi.GPIO as GPIO
OUT_USART = 18

def dialog_serial(ph_array,ph_calibration,main_debug,error_usart,status): #Функция чтения данных по USART
    ser = serial.Serial("/dev/ttyS0",9600) # Инициализация порта
    ph_conv_unit = 9999 #Определения стандартного статуса в случае ошибкки 
    time.sleep(0.1)
    GPIO.output(OUT_USART, True)
    time.sleep(0.1)
    ser.write(b"GetValue") #Исходящий запрос
    time.sleep(0.1)
    GPIO.output(OUT_USART, False)
    time.sleep(1) #Ожидание ответа
    
    if (ser.inWaiting()>0): #Если входящий буфер не 0
        received_data = ser.read() #читаем пурвый байт
        time.sleep(0.03) 
        data_left = ser.inWaiting() #Считаем число и содержание оставшихся байтов 
        received_data += ser.read(data_left)#добавляем их к первому байту
        
        data = str(received_data)#Переводим из байта в строку
        start_bit = data.find("<")+1
        stop_bit = data.find(">")
        try:
            ph_conv_unit = int(data[start_bit:stop_bit])-1000 # ПРобуем перевести в целочисленный тип 
            
        except:
            pass   
    ser.close()#Закрываем соединение

    
    if (ph_conv_unit == 9999): #Если прочтеннное сообщение 9999
        error_usart = True # устанавливаем флаг ошибки
        print(colored("_________Ошибка чтения данных по USART насос выкл_________LL - {0} , CV - {1} , UL - {2}".format(ph_array["LL"],ph_array["AV"],ph_array["UL"]),"red"))
        status = 5 
        receiving.get_status(status)# Передача нового статуса функции сбора 
    else:
        error_usart = False # Иначе снимаем флаг ошибки
        ph_array["AV"] = (round((ph_calibration["a"]*ph_conv_unit + ph_calibration["b"])*1000))/1000#преобразуем входное число в PH

    if main_debug:
        now = datetime.datetime.now()#запрос времени с RTC
        if (ph_array["LL"]<ph_array["AV"])&(ph_array["AV"]<ph_array["UL"]):#Определяем цвет сообщения
            color = "green" 
        else:
            color = "red"
        if (not error_usart): # Если нет ошибки, то выводим результат анализа
            print(colored("Time {0}:{1}:{2} ; Date {3}:{4}:{5}_________Произведен кислотный анализ_________LL - {6} , CV - {7} , UL - {8}".format(now.hour,now.minute,now.second,now.year,now.month,now.day,ph_array["LL"],ph_array["AV"],ph_array["UL"]),color))
            status = 6
            receiving.get_status(status)# Передача нового статуса функции сбора

    return(ph_conv_unit,ph_array,error_usart,status)

