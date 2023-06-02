from arena import *
import math
from scipy.spatial.transform import Rotation as R
import numpy as np
import time
from threading import Thread
import random


# setup library
scene = Scene(host="arena-dev1.conix.io", namespace = "Edward", scene="example1")
#scene = Scene(host="arena-dev1.conix.io", namespace = "joeym", scene="vr_example1")

remote_mode = True
is_magicleap = False

left = 0
right = 0
box = None

hand_obj_dist = 0
original_pos = Position(0,0,0)

interactive_objects = []
master = None
follower = None

def command_task():
    global remote_mode
    global interactive_objects
    time.sleep(1)
    while True:
        txt = input("Enter Command: ")
        if txt == "Remote":
            print("Entered Remote Rendering Mode")
            remote_mode = True

            for name in scene.all_objects:
                obj = scene.all_objects[name]
                if obj["object_id"][0:6] != "camera" and obj["object_id"][0:4] != "hand":
                    obj.data['remote-render'] = {'enabled': True}
                    scene.update_object(obj)

        elif txt == "Local":
            print("Entered Local Rendering Mode")
            remote_mode = False

            for name in scene.all_objects:
                obj = scene.all_objects[name]
                if obj["object_id"][0:6] != "camera" and obj["object_id"][0:4] != "hand":
                    obj.data['remote-render'] = {'enabled': False}
                    scene.update_object(obj)

        elif txt == "Hybrid":
            print("Entered Hybrid Rendering Mode")
            remote_mode = False
            for name in scene.all_objects:
                obj = scene.all_objects[name]
                if obj["object_id"][0:6] != "camera" and obj["object_id"][0:4] != "hand":
                    obj.data['remote-render'] = {'enabled': True}
                    scene.update_object(obj)

            for obj in interactive_objects:
                obj.data['remote-render'] = {'enabled': False}
                scene.update_object(obj)

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
    global is_magicleap
    global remote_mode
    if is_magicleap:
        print("IS ML")
        if remote_mode:
            return Position(0, 0, dist)
        else:
            if (side == "left"):
                x = 0.25 * dist/2
            else: x = -0.25 * dist/2
            angle = math.pi/5
            y = dist * math.sin(angle)
            z = dist * math.cos(angle)
            return Position(x, -y, -z)

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

def obj_handler(scene, evt, msg):
    global follower
    global master
    global left
    global right
    global hand_obj_dist
    global original_pos
    global is_magicleap
    id = msg["object_id"]
    obj = scene.all_objects.get(id)
    if not follower:
        if evt.type == "mousedown":
            if (master[4] == 'R'):
                if remote_mode:
                    obj.update_attributes(parent=right['object_id'])
                else:
                    obj.data["parent"]='rightHand'
                hand_pos = right.data.position
                side = "right"
            else: 
                if remote_mode:
                    obj.update_attributes(parent=left['object_id'])
                else:
                    obj.data["parent"]='leftHand'
                hand_pos = left.data.position
                side = "left"

            obj_pos = obj.data.position
            original_pos = obj_pos
            dist = find_pos_dist(hand_pos, obj_pos)
            #hand_obj_dist = dist
            
            follow_pos = get_following_position(dist, side)

            obj.data.position = follow_pos
            # if is_magicleap and remote_mode: #if magic leap
            #     obj.data.position = Position(follow_pos["x"] * 100,
            #                           follow_pos["y"] * 100,
            #                           follow_pos["z"] * 100)
            # else:
            #     obj.data.position = follow_pos


            if (remote_mode):
                scene.update_object(obj)

            else:
                scene.add_object(obj)

            follower = obj
        elif evt.type == "mouseup":
            pass


def on_msg_callback(scene, obj, msg):
    global master
    global follower
    global original_pos
    global interactive_objects
    if msg["action"] == "clientEvent":
        name = msg["object_id"]
        if msg["type"] == "triggerdown":
            master = name
            
        elif msg["type"] == "triggerup":
            if follower:
                if obj["object_id"][4] == master[4]:
                    
                    follower.data['remote-render'] = {'enabled': False}

                    follower.update_attributes(parent=None)
                    follower.data.position = original_pos
                    scene.update_object(follower)
                    if remote_mode:
                        follower.data['remote-render'] = {'enabled': True}
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
    global is_magicleap
    user = msg['data']['dep']

    if msg['data']['object_type'] == 'handLeft':
        left = scene.get_user_hands(user, "left")
        scene.update_object(left)#, update_handler=hand_handler)
        print("Left Joined")
    else: #right hand
        right = scene.get_user_hands(user, "right")
        scene.update_object(right)#, update_handler=hand_handler)

        print("Right Joined")

    if "magicleap" in obj["data"]["url"]:
        is_magicleap = True
    
    print(scene.all_objects.keys())


def hand_left_callback(scene, obj, msg):
    print("hand Disconnected")
    is_magicleap = False

def box1_handler(scene, evt, msg):
    global interactive_objects
    box1 = interactive_objects[0]
    if evt.type == "mousedown":
        scene.update_object(box1, color=Color(100,255,100))
    if evt.type == "mouseup":
        scene.update_object(box1, color=Color(255,100,0))
        pass

@scene.run_once
def init():
    global sword
    global interactive_objects
    scene.user_join_callback = user_join_callback
    scene.user_left_callback = user_left_callback
    scene.on_msg_callback = on_msg_callback
    scene.hand_join_callback = hand_join_callback
    scene.hand_left_callback = hand_left_callback

    box1 = Box(object_id="box1", position=Position(2,0,-3), scale=Scale(0.3,0.3,0.3),
              click_listener=True, evt_handler=box1_handler, color=Color(255,100,0),
              persist=True)
    scene.update_object(box1, color=Color(255,100,0))
    
    box2 = Box(object_id="box2", position=Position(0,1,-2), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(75,75,75),
              persist=True)
            
    sphere = Sphere(object_id="sphere", position=Position(-1,1,-1.5), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(50,25,0))
    
    torus = Torus(object_id="torus", position=Position(2,1,-1.5), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(25,5,0),
              persist=True)

    interactive_objects = [box1, box2, sphere, torus]

    for obj in interactive_objects:
        obj.data['remote-render'] = {'enabled': True}
        #scene.update_object(obj)

    scene.add_objects([box1, box2, sphere, torus])


#Start thread and tasks
t2 = Thread(target=command_task)
t2.start()
scene.run_tasks()
