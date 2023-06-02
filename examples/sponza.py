from arena import *
import math
from scipy.spatial.transform import Rotation as R
import numpy as np
import time
from threading import Thread
import json


# setup library
scene = Scene(host="arena-dev1.conix.io", namespace = "Edward", scene="sponzahybrid")
#scene = Scene(host="arena-dev1.conix.io", namespace = "joeym", scene="vr_example1")

class BaseObjectJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for nested BaseObjects.
    """
    def default(self, obj):
        if isinstance(obj, (tuple,list,dict)):
            return obj
        else:
            return vars(obj)
        

remote_mode = True

left = 0
right = 0

hand_obj_dist = 0
original_pos = Position(0,0,0)

interactive_objects = []
master = None
follower = None

def update_controllers(in_remote_mode):
    topic = f"{scene.root_topic}/{scene.mqttc_id}/leftHand"
    d = datetime.utcnow().isoformat()[:-3]+"Z"
    payload = json.dumps({'object_id': "leftHand", 
                            "type": "object", 
                            "action": "update",
                            "timestamp": d,
                            "data": {
                                "object_type": "handLeft",
                                "visible": not in_remote_mode
                                }})
    scene.mqttc.publish(topic, payload, qos=0)
    print(payload)
    print(str(payload))

    topic = f"{scene.root_topic}/{scene.mqttc_id}/rightHand"
    payload = json.dumps({'object_id': "rightHand", 
                            "type": "object", 
                            "action": "update",
                            "timestamp": d,
                            "data": {
                                "object_type": "handRight",
                                "visible": not in_remote_mode
                                }})
    scene.mqttc.publish(topic, payload, qos=0)
    #"remote-render": {'enabled': in_remote_mode}


def command_task():
    global remote_mode
    global interactive_objects
    time.sleep(1)
    while True:
        txt = input("Enter Command: ")
        if txt == "Remote" or txt == "R":
            print("Entered Remote Rendering Mode")
            remote_mode = True

            for name in scene.all_objects:
                obj = scene.all_objects[name]
                if obj["object_id"][0:6] != "camera" and obj["object_id"][0:4] != "hand" and "light" not in obj["object_id"]:
                    obj.data['remote-render'] = {'enabled': True}
                    scene.update_object(obj)

            update_controllers(True)



        elif txt == "Local" or txt == "L":
            print("Local mode currently disabled :(")
            # print("Entered Local Rendering Mode")
            # remote_mode = False

            # for name in scene.all_objects:
            #     obj = scene.all_objects[name]
            #     if obj["object_id"][0:6] != "camera" and obj["object_id"][0:4] != "hand" and "light" not in obj["object_id"]:
            #         obj.data['remote-render'] = {'enabled': False}
            #        scene.update_object(obj)
            # update_controllers(False)

        elif txt == "Hybrid" or txt == "H":
            print("Entered Hybrid Rendering Mode")
            remote_mode = False
            for name in scene.all_objects:
                obj = scene.all_objects[name]
                if obj["object_id"][0:6] != "camera" and obj["object_id"][0:4] != "hand" and "light" not in obj["object_id"]:
                    obj.data['remote-render'] = {'enabled': True}
                    scene.update_object(obj)

            for obj in interactive_objects:
                obj.data['remote-render'] = {'enabled': False}
                scene.update_object(obj)
            
            update_controllers(False)

        time.sleep(0.5)

def get_release_position(pos, rot, dist):
    x, y, z = pos['x'], pos['y'], pos['z']
    
    rot_array = [rot.x, rot.y, rot.z, rot.w]
    rot_quat = R.from_quat(rot_array)
    xrot, yrot, zrot = rot_quat.as_euler("xyz", degrees=False)
    x_new = x + dist * math.cos(zrot) * math.sin(yrot)
    y_new = y + dist * math.sin(zrot)
    z_new = z + dist * math.cos(zrot) * math.cos(yrot)
    return Position(-x_new, y_new, -z_new)

def get_following_position(dist, side):
    if remote_mode:
        return Position(0,0,dist)
    else:
        return Position(0,0,-dist)
       

def find_pos_dist(pos1, pos2):
    x1, y1, z1 = pos1['x'], pos1['y'], pos1['z']
    x2, y2, z2 = pos2['x'], pos2['y'], pos2['z']
    return math.dist((x1,y1,z1), (x2,y2,z2))

# def left_hand_handler(obj):
#     #pass

# def right_hand_handler(obj):
#     pass

# def hand_handler(obj):
#     pass

def on_msg_callback(scene, obj, msg):
    global master
    global follower
    global original_pos
    global remote_mode
    if msg["action"] == "clientEvent":
        name = msg["object_id"]
        if msg["type"] == "triggerdown":
            master = name
            
        elif msg["type"] == "triggerup":
            if obj["object_id"][4] == master[4] and follower:
                follower.data["parent"] = None
                follower.data.position = original_pos
                #scene.add_object(follower)
                if (remote_mode):
                    scene.update_object(follower)

                else:
                    scene.add_object(follower)
                follower = None

def user_join_callback(scene, obj, msg):
    global left
    global right
    #Add user to dictionary
    name = msg['object_id'][7:]
    print("User '%s' Joined" % name)

def user_left_callback(scene, obj, msg):
    #Remove user from dictionary
    name = msg['object_id'][7:]
    print("User '%s' Left" % name)
    
def hand_join_callback(scene, obj, msg):
    global left
    global right
    user = msg['data']['dep']

    if msg['data']['object_type'] == 'handLeft':
        left = scene.get_user_hands(user, "left")
        scene.update_object(left)#, update_handler=hand_handler)
        print("Left Joined")
    else: #right hand
        right = scene.get_user_hands(user, "right")
        scene.update_object(right)#, update_handler=hand_handler)

        print("Right Joined")

    
    print(scene.all_objects.keys())


def hand_left_callback(scene, obj, msg):
    print("hand Disconnected")

@scene.run_async
async def func():
    global sword
    global interactive_objects
    scene.user_join_callback = user_join_callback
    scene.user_left_callback = user_left_callback
    scene.on_msg_callback = on_msg_callback
    scene.hand_join_callback = hand_join_callback
    scene.hand_left_callback = hand_left_callback

    def obj_handler(scene, evt, msg):
        global follower
        global master
        global left
        global right
        global hand_obj_dist
        global original_pos
        id = msg["object_id"]
        object = scene.all_objects.get(id)
        if not follower and object:
            if evt.type == "mousedown":
                if (master[4] == 'R'):
                    if remote_mode:
                        object.update_attributes(parent=right['object_id'])
                    else:
                        object.data["parent"] = 'rightHand'
                    hand_pos = right.data.position
                    side = "right"
                else: 
                    if remote_mode:
                        object.update_attributes(parent=left['object_id'])
                    else:
                        object.data["parent"] = 'leftHand'
                    hand_pos = left.data.position
                    side = "left"

                obj_pos = object.data.position
                original_pos = obj_pos
                dist = find_pos_dist(hand_pos, obj_pos)
                #hand_obj_dist = dist
                object.data.position = get_following_position(dist, side)

                #scene.add_object(object)
                if (remote_mode):
                    scene.update_object(object)

                else:
                    scene.add_object(object)
                follower = object
            elif evt.type == "mouseup":
                pass

    def box1_handler(scene, evt, msg):
        global interactive_objects
        box1 = interactive_objects[0]
        if evt.type == "mousedown":
            scene.update_object(box1, color=Color(100,255,100))
        if evt.type == "mouseup":
            scene.update_object(box1, color=Color(255,100,0))

    box1 = Box(object_id="box1", position=Position(2,0,-3), scale=Scale(0.3,0.3,0.3),
              click_listener=True, evt_handler=box1_handler, color=Color(255,100,0),
              persist=True)
    
    box2 = Box(object_id="box2", position=Position(0,1,-2), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(75,75,75),
              persist=True)
            
    sphere = Sphere(object_id="sphere", position=Position(-1,1,-1.5), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(50,25,0),
              persist=True)
    
    torus = Torus(object_id="torus", position=Position(2,1,-1.5), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(25,5,0),
              persist=True)

    interactive_objects = [box1, box2, sphere, torus]

    for obj in interactive_objects:
        obj.data['remote-render'] = {'enabled': True}

    scene.add_objects([box1, box2, sphere, torus])

    update_controllers(True)


#Start thread and tasks
t2 = Thread(target=command_task)
t2.start()
scene.run_tasks()
