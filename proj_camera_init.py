#import picamera
debug_mode_camera = False
import time

def init_camera (camera):
#Словарь с актуальными параметрами
    params = {"sharpness" : 0, # Резкость 
          "contrast" : 0, # Контрастность
          "brightness" : 50, # Яркость
          "saturation" : 0, # Насыщенность  
          "ISO" : 800, # Чувствительность
          "rotation" : 0, # Поворот
          "awb_mode" : 'off', # Баланс белого
          "exposure_comp" : 0,
          "exposure_mode" : 'backlight',
          "image_effect" : 'none'
         }

    camera.resolution = (640, 480)
    camera.framerate = 30
    camera.sharpness = params["sharpness"]                # Резкость     
    camera.contrast = params["contrast"]                   # Контрастность
    camera.brightness = params["brightness"]                # Яркость
    camera.saturation = params["saturation"]                 # Насыщенность  
    camera.ISO = params["ISO"]                        # Чувствительность
    camera.rotation = params["rotation"]                   # Поворот

    camera.exposure_compensation = params["exposure_comp"]   # Компенсация экспозиции
    camera.exposure_mode = params["exposure_mode"]  # Режим экспозиции
    camera.image_effect = params["image_effect"] # Эффект

    camera.awb_mode = params["awb_mode"]         # Баланс белого

    camera.shutter_speed = 10000

    if params["awb_mode"] == "off" :
        camera.awb_gains = 2.0 #2.0
    return("done")

#with picamera.PiCamera() as camera:
#    init_camera(camera)
#    camera.start_preview()
#    time.sleep(2)
#    camera.stop_preview()
