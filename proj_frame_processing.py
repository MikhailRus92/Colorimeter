import numpy as np
import math

collector = {"w1":0, "r2":0,
             "w2":0, "r2":0,
             "w3":0, "r3":0,
             "rw":False, "rr":False # готовность коллекций
             }


def scan_func (film_frame,probe_frame,setting): #Функция усреднения RGB массива  + вызов функции фильтрации
    
    film_frame_size = film_frame.shape[0]*film_frame.shape[1] #Узнаем размерность массива 1
    probe_frame_size = probe_frame.shape[0]*probe_frame.shape[1]#Узнаем размерность массива 2
    
    film_r_color , film_g_color, film_b_color= SCO_func(film_frame,setting) #Передаем массив 1 и настройки в функцию фильтрации
    probe_r_color , probe_g_color, probe_b_color= SCO_func(probe_frame,setting)#Передаем массив 2 и настройки в функцию фильтрации

    film_r_color=int(np.sum(film_frame[:,:,0])/film_frame_size) #В оставшихся массивах усредняем каждый цвет
    film_g_color=int(np.sum(film_frame[:,:,1])/film_frame_size)
    film_b_color=int(np.sum(film_frame[:,:,2])/film_frame_size)

    probe_r_color=int(np.sum(probe_frame[:,:,0])/probe_frame_size)
    probe_g_color=int(np.sum(probe_frame[:,:,1])/probe_frame_size)
    probe_b_color=int(np.sum(probe_frame[:,:,2])/probe_frame_size)

    film_rgb_value = (film_r_color , film_g_color, film_b_color) # Формируем список из R;G;B для обоих образцов
    probe_rgb_value = (probe_r_color , probe_g_color, probe_b_color)
    return (film_rgb_value,probe_rgb_value) # Возвращаем эти списки в основную функцию
    


def SCO_func(in_array,setting): # Функция расчета SCO фильтрация и удалению промахов
    col=[]
    for l in range(setting["Loop"]): #Повторяем цикл LOOP раз
            
        for k in [0,1,2]: # Повторяем действие для каждого цвета
            dev=in_array.shape[0]*in_array.shape[1] # Считаем количество пикселей
            out_array=in_array[:,:,k] #Выделяем из входного массива только один цвет и формируем новый массив
            sr=np.sum(out_array)/dev # Усредняем все данные этого массива
            dx=out_array-sr # Вычитаем из каждого члена массива среднее значение
            dx2=dx**2 # Считаем квадрат отклонения
            s=math.sqrt(np.sum(dx2)/(dev-1)) # Считаем СКО
            f=s*setting["Z"]/10 #Выоводим из настроек коэф СТ /10
            x=np.argsort(out_array) # Сортируем массив
            dev1=dev # Дублируем число пикселей
            for j in range(dx.shape[0]):  # Проверяем на промахи, удаляем ошибки.
                for i in range(dx.shape[1]-1,1,-1):
                    if ((math.fabs(dx[j][x[j][i]]))>f):
                        dev1-=1
                        out_array[j][x[j][i]]=sr
                        
                    else:
                        break
            if l==setting["Loop"]-1:
                col.append(int(np.sum(out_array[:,:])/dev)) # Считаем размерной массива по фильтрации
    return col



def value_to_sum_func(color1,color2,setting,cicle_w, cicle_r): #Функция накопления значений и усреднения
    global collector#Цикл работы
    if (cicle_w==setting["Num"]): 
        
        collector["rw"]=True
        p1 = color1[0]+color1[1]+color1[2]
        # напиши фильтр на кривое значение
        collector.update({"w{0}".format(cicle_w):p1})
        cicle_w = 1
        
    else:
        p1 = color1[0]+color1[1]+color1[2]
        # напиши фильтр на кривое значение
        collector.update({"w{0}".format(cicle_w):p1})
        cicle_w+=1

    if (cicle_r==setting["Num"]):
        
        collector["rr"]=True
        p2 = color2[0]+color2[1]+color2[2]
        # напиши фильтр на кривое значение
        collector.update({"r{0}".format(cicle_r):p2})
        cicle_r = 1
    else:
        p2 = color2[0]+color2[1]+color2[2]
        # напиши фильтр на кривое значение
        collector.update({"r{0}".format(cicle_r):p2})
        cicle_r+=1

        
    pw,pr=0,0

    
    if (collector["rw"]==True):
        for i in range(setting["Num"]):
            pw+=collector["w{0}".format(i+1)]
        pw = int(pw/(setting["Num"]))
    else:
        pw = p1

    if (collector["rr"]==True):
        for i in range(setting["Num"]):
            pr+=collector["r{0}".format(i+1)]
        pr = int(pr/(setting["Num"]))
    else:
        pr = p2

    return (pw,pr,cicle_w, cicle_r)


def color_code_func(calibration,input_data=0,task="get_color"): #Функция применения калибровочных коэфициентов
    if task=="get_color":
        output_data = calibration["a"]*input_data*input_data+calibration["b"]*input_data + calibration["c"]
    else:
        pass
    return(round(output_data,1))


