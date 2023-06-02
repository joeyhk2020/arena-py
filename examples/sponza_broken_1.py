from arena import *
import math
from scipy.spatial.transform import Rotation as R
import numpy as np
import time
import random
from threading import Thread


# setup library
scene = Scene(host="arena-dev1.conix.io", namespace = "Edward", scene="example1")
#scene = Scene(host="arena-dev1.conix.io", namespace = "joeym", scene="vr_example1")

remote_mode = False


left = 0
right = 0
box1 = 0
box3 = 0

hand_obj_dist = 0
original_pos = Position(0,0,0)

interactive_objects = []
master = None
follower = None
def obj_handler(scene, evt, msg):
    global follower
    global master
    global left
    global right
    global hand_obj_dist
    global original_pos
    print("Handler")
    id = msg["object_id"]
    obj = scene.all_objects.get(id)
    if not follower:
        if evt.type == "mousedown":
            print("Trigger click:", id)
            if (master[4] == 'R'):
                if remote_mode:
                    obj.data["parent"] = right['object_id']
                else:
                    obj.data["parent"] = 'rightHand'
                    
                hand_pos = right.data.position
                side = "right"
            else: 
                if remote_mode:
                    obj.data["parent"] = left['object_id']
                else:
                    obj.data["parent"] = 'leftHand'
                hand_pos = left.data.position
                side = "left"

            obj_pos = obj.data.position
            original_pos = obj_pos
            dist = find_pos_dist(hand_pos, obj_pos)
            hand_obj_dist = dist
            obj.data.position = get_following_position(dist, side)

            scene.add_object(obj)
            follower = obj
        elif evt.type == "mouseup":
            pass

def command_task():
    # for name in scene.all_objects:
    #             obj = scene.all_objects[name]
    #             if obj["object_id"][0:6] != "camera" and obj["object_id"][0:4] != "hand":
    #                 obj.data['remote-render'] = {'enabled': False}
    #                 scene.update_object(obj)

    global remote_mode
    global interactive_objects

    # global box1
    # time.sleep(5)
    # scene.delete_object(box1)
    # print("Add box 1 again")
    # box1.update_attributes(color=Color(50, 50, 200), parent="plane1")
    # scene.add_object(box1)

    # time.sleep(5)
    # scene.delete_object(box1)
    # print("Add box 1 again")
    # box1.update_attributes(color=Color(200, 50, 50), parent=None, position=Position(2,0,-3))
    # scene.add_object(box1)

    
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
    if (side == "left"):
        x = 0.25 * dist/2
    else: x = -0.25 * dist/2
    # if remote_mode:
    #     return Position(3, 0, 0)
    # else:
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
            if follower is None:
                return
            if obj["object_id"][4] == master[4]:
                #follower.data["parent"] = None
                #follower.data.position = original_pos
                #scene.delete_object(follower)
                print("Released!!")
                scene.delete_object(follower)

                new_id = "sphere" + str(random.randint(0, 9999999999))

                new_obj = Sphere(object_id=new_id, position=Position(-1,1,-1.5), scale=Scale(0.2,0.2,0.2),
                    click_listener=True, evt_handler=obj_handler, color=Color(50,25,0))
                #new_obj.data['remote-render'] = {'enabled': True}

                #follower.update_attributes(object_id)
                print(new_id)

                scene.add_object(new_obj)
                # interactive_objects[0] = new_obj
                #follower.update_attributes(position=original_pos, parent=None)

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
    
# interactive_objects = [box1, box2, sphere, torus]
def box1_handler(scene, evt, msg):
    global interactive_objects
    global box1
    #box1 = interactive_objects[0]
    if evt.type == "mousedown":
        scene.update_object(box1, color=Color(100,255,100))
    if evt.type == "mouseup":
        scene.update_object(box1, color=Color(255,100,0))

@scene.run_once
def func():
    global sword
    global box1
    global box3
    global interactive_object_index
    scene.user_join_callback = user_join_callback
    scene.user_left_callback = user_left_callback
    scene.on_msg_callback = on_msg_callback
    scene.hand_join_callback = hand_join_callback
    scene.hand_left_callback = hand_left_callback

    box1 = Box(object_id="box1", position=Position(2,0,-3), scale=Scale(0.3,0.3,0.3),
              click_listener=True, evt_handler=box1_handler, color=Color(255,100,0),
              persist=True)
    
    box1.data['remote-render'] = {'enabled': True}
    
    box2 = Box(object_id="box2", position=Position(0,1,-2), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(75,75,75),
              persist=True)

    sphere = Sphere(object_id="sphere", position=Position(-1,1,-1.5), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(50,25,0))

    sphere.data['remote-render'] = {'enabled': True}

    print(sphere)

    
    torus = Torus(object_id="torus", position=Position(2,1,-1.5), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(25,5,0),
              persist=True)

    #scene.add_objects([box1, box2, sphere, torus])
    scene.add_object(sphere)
    interactive_objects = [sphere]


#Start thread and tasks
t2 = Thread(target=command_task)
t2.start()
scene.run_tasks()
