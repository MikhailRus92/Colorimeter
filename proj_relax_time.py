import datetime

def init_time():
    global prev_hour, prev_minute, prev_second,prev_pause
    now = datetime.datetime.now()#Запрос текущей даты
    prev_hour, prev_minute, prev_second =  now.hour, now.minute, now.second#Приравниваем текущее время и предыдущее
    prev_pause = (prev_hour)*3600 + prev_minute*60 + prev_second#Сколько времени прошло с начала дня в секундах, устанавливаем нулевую точку отсчета

def relax_time(ph_array):
    delay_time = ph_array["relax_time"]# Устанавливаем время задержки
    global prev_hour, prev_minute, prev_second,prev_pause

    now = datetime.datetime.now()#Запрос времени с RTC 
    curr_hour, curr_minute, curr_second =  now.hour, now.minute, now.second#Забираем часы, минуты, секунды из RTC

    if prev_hour > curr_hour:
        pause_time = (curr_hour+24)*3600 + curr_minute*60 + curr_second# Если с прошлого измерения закончился день, добавляем к  времени паузы 24 часа т.к ноль находится в прошлом дне 
    else:
        pause_time = (curr_hour)*3600 + curr_minute*60 + curr_second# Если день тот же, то просто считаем время паузы


    if ((pause_time-prev_pause)>=delay_time):# Если разница текущей паузы и временем начала отсчета больше требуемой задержки
        prev_hour, prev_minute, prev_second = curr_hour, curr_minute, curr_second#Приравниваем текущее время и предыдущее
        curr_hour, curr_minute, curr_second = 0,0,0#Текущее устанавливаем в 0
        prev_pause = (prev_hour)*3600 + prev_minute*60 + prev_second#Сколько времени прошло с начала дня в секундах, устанавливаем нулевую точку отсчета
        
        flag = True# Устанавливаем флаг готовности счетчика в True
            
    else:
        flag = False# Иначе счетчик False

    return flag

