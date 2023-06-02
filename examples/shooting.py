from arena import *
from threading import Thread
import time
import random

start = False
running = False
score = 0
timer = 0
score = 0
adding = False
remote_mode = False



scene = Scene(host="arena-dev1.conix.io", namespace = "joeym", scene="shoot")
def kill_all_targets():
    to_delete = []
    for key in scene.all_objects.keys():
        if "target" in key:
            to_delete.append(scene.all_objects[key])
    for obj in to_delete:
        scene.delete_object(obj)

def spawn_new_target():
    global remote_mode
    global adding
    name = "target" + str(random.randint(0,999999))
    x_start = random.randint(-15, 15)
    z_start = random.randint(-40, -25)
    y_speed_start = random.uniform(0.3, 0.8)
    x_speed_start = random.uniform(-0.5,0.5)
    target_color = Color(random.randint(0,255),
                  random.randint(0,255),
                  random.randint(0,255))
    target = Cylinder(object_id=name, 
                   position=Position(x_start,2,z_start), 
                   rotation=Rotation(90,0,0),
                   scale=Scale(1,0.5,1), 
                   click_listener=True, 
                   color=target_color,
                   y_speed=y_speed_start,
                   x_speed=x_speed_start,
                   evt_handler=target_handler)
    if remote_mode:
        target.data['remote-render'] = {'enabled': True}
    else:
        target.data['remote-render'] = {'enabled': False}
    while adding:
        pass
    adding = True
    scene.add_object(target)
    adding = False


def target_handler(scene, evt, msg):
    global score
    score_value = scene.all_objects["score_value"]
    target = scene.all_objects[msg["object_id"]]

    if evt.type == "mousedown":
        score += 1
        scene.update_object(score_value,
                            text=str(score))
        scene.delete_object(target)


def start_handler(scene, evt, msg):
    global start
    start_box = scene.all_objects["start_box"]
    start_text = scene.all_objects["start_text"]
    if evt.type == "mousedown":
        scene.update_object(start_box, 
                            position=Position(-5,2,0),
                            color=Color(40,40,40))
        scene.update_object(start_text, 
                            position=Position(-3.8,2.05,0))
    if evt.type == "mouseup":
        scene.update_object(start_box, 
                            position=Position(-4,2,0),
                            color=Color(75,75,75))
        scene.update_object(start_text, 
                            position=Position(-2.8,2.05,0))

        start = True

@scene.run_forever(interval_ms=30)
def gravity():
    global adding
    grav_accel = 0.03
    if running:
        while adding:
            pass
        adding = True
        for key, obj in scene.all_objects.copy().items():
            if "target" in obj["object_id"]:
                
                if "y_speed" in obj["data"] and "position" in obj["data"]:
                    y_cur_speed = obj["data"]["y_speed"]
                    x_cur_speed = obj["data"]["x_speed"]

                    cur_pos = obj["data"]["position"]
                    if cur_pos and cur_pos["y"] > -1:
                        new_pos = Position(cur_pos["x"] + x_cur_speed, 
                                        cur_pos["y"] + y_cur_speed, 
                                        cur_pos["z"])
                        scene.update_object(obj,
                                            y_speed=y_cur_speed-grav_accel,
                                            position=new_pos)
                else:
                    scene.delete_object(obj)
                
        adding = False

    

@scene.run_once
def init():
    start_box = Box(object_id="start_box",
                    position=Position(-4,2,0),
                    scale=Scale(2,1,3),
                    click_listener=True,
                    color=Color(75,75,75),
                    evt_handler=start_handler)
    
    start_text = Text(object_id="start_text", 
                      position=Position(-2.8,2.05,0),
                      scale=Scale(2,2,2),
                      rotation=Rotation(0,90,0), 
                      color=Color(0,0,0), 
                      text = "Press to start")
    
    timer_title = Text(object_id="timer_title", 
                      position=Position(7,13,-17.5),
                      scale=Scale(4,4,4),
                      rotation=Rotation(0,0,0), 
                      color=Color(0,0,0), 
                      text = "Time Left:")

    timer_value = Text(object_id="timer_value", 
                      position=Position(7,12,-17.5),
                      scale=Scale(4,4,4),
                      rotation=Rotation(0,0,0), 
                      color=Color(0,0,0), 
                      text = "0")
    

    score_title = Text(object_id="score_title", 
                      position=Position(-7,13,-17.5),
                      scale=Scale(4,4,4),
                      rotation=Rotation(0,0,0), 
                      color=Color(0,0,0), 
                      text = "Score:")

    score_value = Text(object_id="score_value", 
                      position=Position(-7,12,-17.5),
                      scale=Scale(4,4,4),
                      rotation=Rotation(0,0,0), 
                      color=Color(0,0,0), 
                      text = "0")



    bounding_box_1 = Box(object_id="bb1",
                    position=Position(0,0,-19),
                    scale=Scale(30,4,1),
                    color=Color(75,75,75))
    bounding_box_2 = Box(object_id="bb2",
                position=Position(0,13,-19),
                scale=Scale(30,4,1),
                color=Color(75,75,75))
    bounding_box_3 = Box(object_id="bb3",
                    position=Position(16,6.5,-19),
                    scale=Scale(10,17,1),
                    color=Color(75,75,75))
    bounding_box_4 = Box(object_id="bb4",
                position=Position(-16,6.5,-19),
                scale=Scale(10,17,1),
                color=Color(75,75,75))
    scene.add_objects([start_box, 
                       start_text, 
                       timer_title, 
                       timer_value,
                       score_title,
                       score_value,
                       bounding_box_1,
                       bounding_box_2,
                       bounding_box_3,
                       bounding_box_4])

def run_game():
    global score
    global start
    score_value = scene.all_objects["score_value"]
    score = 0
    scene.update_object(score_value,
                    text=str(score))
    print("Start Game")
    global running
    timer_value = scene.all_objects["timer_value"]
    timer = 15 
    kill_all_targets()
    while True:
        scene.update_object(timer_value, 
                            text=str(timer))
        if timer <= 0:
            print("GAME OVER")
            running = False
            kill_all_targets()
            time.sleep(2)
            print(score)
            start = False
            running = False
            break
        time.sleep(0.5)
        spawn_new_target()
        time.sleep(0.5)
        spawn_new_target()

        timer -= 1


        
        


def timer_task():
    global start
    global running

    
    while True:
        if start and not running:
            running = True
            start = False
            run_game()



def command_task():
    global remote_mode
    time.sleep(1.5)
    while True:
        txt = input("Enter Command: ")
        if txt == "Remote" or txt == "R":
            print("Entered Remote Rendering Mode")
            remote_mode = True

            for name in scene.all_objects:
                obj = scene.all_objects[name]
                if obj["object_id"][0:6] != "camera" \
                and "object_type" in obj["data"] and obj["data"]["object_type"] != "text":
                    obj.data['remote-render'] = {'enabled': True}
                    if obj["object_id"][0:4] != "hand":
                        obj["data"]["object_type"] = "hand"
                        if obj["object_id"][5] == "R":
                            name = "rightHand"
                        else: name = "leftHand"
                        scene.update_object(obj, object_id=name)

        elif txt == "Local" or txt == "L":
            print("Entered Local Rendering Mode")
            remote_mode = False

            for name in scene.all_objects:
                obj = scene.all_objects[name]
                print(obj)
                if obj["object_id"][0:6] != "camera" and obj["data"]["object_type"] != "text":
                    #and obj["object_id"][0:4] != "hand"
                    obj.data['remote-render'] = {'enabled': False}
                    scene.update_object(obj)

        time.sleep(0.5)

t2 = Thread(target=timer_task)
t2.start()
t3 = Thread(target=command_task)
t3.start()
scene.run_tasks()
