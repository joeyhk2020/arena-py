from arena import *
import math
from scipy.spatial.transform import Rotation as R
import numpy as np
from threading import Thread
import time



#SCENE COMPATIBLE WITH THIS SERVER: https://arena-dev1.conix.io/dev/joeym2/


# setup library
scene = Scene(host="arena-dev1.conix.io", namespace = "Edward", scene="example1")

left = 0
right = 0

sword = 0
box1 = 0
box2 = 0
master = None
follower = None

left_clicked = False
right_clicked = False

quest_users_toruses = {}


def find_pos_dist(pos1, pos2):
    x1, y1, z1 = pos1['x'], pos1['y'], pos1['z']
    x2, y2, z2 = pos2['x'], pos2['y'], pos2['z']
    return math.dist((x1,y1,z1), (x2,y2,z2))

def on_msg_callback(scene, obj, msg):
    global follow
    global master
    if msg["action"] == "clientEvent":
        name = msg["object_id"]
        if msg["type"] == "triggerdown":

            master = name
            print("TRIGGER")

        elif msg["type"] == "triggerup":
            print("RELEASE")
            if master:
                master = None
            print(name)

def hand_handler(obj):
    global sword
    global master
    global follower

    name = obj["object_id"]
    if follower and master == name:
        pos = obj["data"]["position"]
        rot = obj["data"]["rotation"]
        rot_tuple = (rot.x, rot.y, rot.z, rot.w)

        rot_array = [rot.x, rot.y, rot.z, rot.w]
        rot_quat = R.from_quat(rot_array)
        rot_euler = rot_quat.as_euler("xyz", degrees=True)

        rot_final = (rot_euler[0]+70, rot_euler[1], rot_euler[2])

        scene.update_object(follower,
                            position = (pos.x, pos.y, pos.z),
                            rotation = rot_final)

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
    user = msg['data']['dep']

    if msg['data']['object_type'] == 'handLeft':
        left = scene.get_user_hands(user, "left")
        scene.update_object(left, update_handler=hand_handler)
        print("Left Joined")
    else: #right hand
        right = scene.get_user_hands(user, "right")
        scene.update_object(right, update_handler=hand_handler)
        print("Right Joined")

def hand_left_callback(scene, obj, msg):
    print("hand Disconnected")

@scene.run_async
async def func():
    global sword
    global box1
    global box2
    scene.user_join_callback = user_join_callback
    scene.user_left_callback = user_left_callback
    scene.on_msg_callback = on_msg_callback
    scene.hand_join_callback = hand_join_callback
    scene.hand_left_callback = hand_left_callback

    def obj_handler(scene, evt, msg):
        id = msg["object_id"]
        print("GRABBED", id)
        global follower
        object = scene.all_objects.get
        if evt.type == "mousedown":
            follower = object(id, None)
        if evt.type == "mouseup":
            follower = None

    def box1_handler(scene, evt, msg):
        global box1
        if evt.type == "mousedown":
            scene.update_object(box1, color=Color(100,255,100))
        if evt.type == "mouseup":
            scene.update_object(box1, color=Color(255,100,100))

    def box2_handler(scene, evt, msg):
        global box2
        if evt.type == "mousedown":
            scene.update_object(box2, color=Color(100,255,100))
        if evt.type == "mouseup":
            scene.update_object(box2, color=Color(255,100,100))


    box1 = Box(object_id="box1", position=Position(2,5,-3), scale=Scale(0.3,0.3,0.3),
              click_listener=True, evt_handler=box1_handler, color=Color(255,100,100),
              persist=True)

    box2 = Box(object_id="box2", position=Position(3,4,-2), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=box2_handler, color=Color(255,100,100),
              persist=True)

    box3 = Box(object_id="box3", position=Position(-1,1,-0.5), scale=Scale(0.1,0.1,0.1),
              click_listener=True, evt_handler=obj_handler,
              persist=True)

    xr_logo = GLTF(
        object_id="xr-logo",
        position=(0,0,-10),
        scale=(1.2,1.2,1.2),
        url="https://arena-dev1.conix.io/store/users/wiselab/models/XR-logo.glb",
        persist=True
    )

    sword_box = Box(object_id="sword_box", position=Position(0,3,-2.5), scale=Scale(0.1,0.1,0.1),
              click_listener=True, evt_handler=obj_handler, persist=True,
              visible=False)

    sword = GLTF(
        object_id="sword",
        position=(0,0,0),
        scale=(2,2,2),
        rotation=(0,0,0,0),
        url="https://arena-dev1.conix.io/store/users/joeym/sword.glb",
        persist=True,
        click_listener=True,
        parent="sword_box",
        visible=True

    )
    mini_sword = GLTF(
        object_id="mini_sword",
        position=(-1,3,-2),
        scale=(0.1,0.1,0.1),
        rotation=(0,0,0,0),
        url="https://arena-dev1.conix.io/store/users/joeym/sword.glb",
        persist=True,
        click_listener=True,
        evt_handler=obj_handler
    )

    sword_box.data['remote-render'] = {'enabled': False}
    box1.data['remote-render'] = {'enabled': True}
    box2.data['remote-render'] = {'enabled': True}
    box3.data['remote-render'] = {'enabled': True}
    xr_logo.data['remote-render'] = {'enabled': True}
    sword.data['remote-render'] = {'enabled': False}
    mini_sword.data['remote-render'] = {'enabled': True}

    scene.add_object(sword_box)
    scene.add_object(box1)
    scene.add_object(box2)
    scene.add_object(box3)
    scene.add_object(xr_logo)
    scene.add_object(sword)
    scene.add_object(mini_sword)

# start tasks
scene.run_tasks()
