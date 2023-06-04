from arena import *
import math
import numpy as np
import time
from threading import Thread
import json


# setup library
scene = Scene(host='arena-dev1.conix.io', namespace='Edward', scene='sponzahybrid')

remote_mode = True

left = 0
right = 0

original_pos = Position(0,1.6,0)

interactive_objects = []
master = None
follower = None

oleander1 = {
    "lowpoly": "/store/users/Edward/models/Oleander/Oleander1_22k.glb",
    "highpoly": "/store/users/Edward/models/Oleander/Oleander1_200k.glb"
}

oleander2 = {
    "lowpoly": "/store/users/Edward/models/Oleander/Oleander2_15k.glb",
    "highpoly": "/store/users/Edward/models/Oleander/Oleander2_200k.glb"
}

gold_dragon = {
    "lowpoly": "/store/users/Edward/models/gold_dragon/gold_dragon_28k.glb",
    "highpoly": "/store/users/Edward/models/gold_dragon/gold_dragon_240k.glb"
}

knight1 = {
    "lowpoly": "/store/users/Edward/models/golden_knight/golden_knight_9k.glb",
    "highpoly": "/store/users/Edward/models/golden_knight/golden_knight.glb"
}

helmet = {
    "lowpoly": "/store/users/Edward/models/early_medieval_nasal_helmet/early_medieval_nasal_helmet_13k.glb",
    "highpoly": "/store/users/Edward/models/early_medieval_nasal_helmet/early_medieval_nasal_helmet.glb"
}

sponza = {
    "lowpoly": "/store/users/Edward/models/sponza/sponza_100k.glb",
    "highpoly": "/store/users/Edward/models/sponza/sponza.glb"
}

models = {
    "Oleander1": oleander1,
    "Oleander2": oleander2,
    "gold_dragon": gold_dragon,
    "knight1": knight1,
    "helmet": helmet,
    "sponza": sponza
}

def remote_render_controllers(remote_render_enabled):
    topic = f'{scene.root_topic}/{scene.mqttc_id}/leftHand'
    d = datetime.utcnow().isoformat()[:-3]+'Z'
    payload = json.dumps({'object_id': 'leftHand',
                            'type': 'object',
                            'action': 'update',
                            'timestamp': d,
                            'data': {
                                'object_type': 'handLeft',
                                'remote-render': {'enabled': remote_render_enabled}
                            }
                        })
    scene.mqttc.publish(topic, payload, qos=0)

    topic = f'{scene.root_topic}/{scene.mqttc_id}/rightHand'
    payload = json.dumps({'object_id': 'rightHand',
                            'type': 'object',
                            'action': 'update',
                            'timestamp': d,
                            'data': {
                                'object_type': 'handRight',
                                'remote-render': {'enabled': remote_render_enabled}
                            }
                        })
    scene.mqttc.publish(topic, payload, qos=0)

def command_thread():
    global remote_mode
    global interactive_objects

    time.sleep(1)

    interactive_local = False

    while True:
        txt = input('Enter Command: ')
        if txt == 'remote' or txt == 'r':
            print('Entered Remote Rendering Mode')
            remote_mode = True
            interactive_local = False

        elif txt == 'local' or txt == 'l':
            print('Entered Local Rendering Mode')
            remote_mode = False
            interactive_local = True

        elif txt == 'hybrid' or txt == 'h':
            print('Entered Hybrid Rendering Mode')
            remote_mode = True
            interactive_local = True

        else:
            continue

        for name in scene.all_objects:
            obj = scene.all_objects[name]
            if obj in interactive_objects:
                continue

            if obj['object_id'][0:6] != 'camera' and obj['object_id'][0:4] != 'hand' and 'light' not in obj['object_id']:
                if obj['object_id'] in models:
                    resolution = 'highpoly' if remote_mode else 'lowpoly'
                    model_url = models[obj['object_id']][resolution]
                    obj.data.url = model_url
                obj.data['remote-render'] = {'enabled': remote_mode}
                scene.update_object(obj)

        for obj in interactive_objects:
            obj.data['remote-render'] = {'enabled': not interactive_local}
            scene.update_object(obj)

        remote_render_controllers(not interactive_local)

        time.sleep(0.5)

def get_following_position(dist, side):
    if remote_mode:
        return Position(0,0,dist)
    else:
        return Position(0,0,-dist)

def find_pos_dist(pos1, pos2):
    x1, y1, z1 = pos1['x'], pos1['y'], pos1['z']
    x2, y2, z2 = pos2['x'], pos2['y'], pos2['z']
    return math.dist((x1,y1,z1), (x2,y2,z2))

def on_msg_callback(scene, obj, msg):
    global master
    global follower
    global original_pos
    global remote_mode

    if msg['action'] == 'clientEvent':
        name = msg['object_id']
        if msg['type'] == 'triggerdown':
            master = name

        elif msg['type'] == 'triggerup':
            if obj['object_id'][4] == master[4] and follower:
                follower.data['parent'] = None
                follower.data.position = original_pos
                #scene.add_object(follower)
                if (remote_mode):
                    scene.update_object(follower)

                else:
                    scene.add_object(follower)
                follower = None

def user_join_callback(scene, obj, msg):
    # Add user to dictionary
    name = msg['object_id']
    print(f'User {name} Joined')

def user_left_callback(scene, obj, msg):
    #R emove user from dictionary
    name = msg['object_id']
    print(f'User {name} Left')

def hand_join_callback(scene, obj, msg):
    global left
    global right
    user = msg['data']['dep']

    if msg['data']['object_type'] == 'handLeft':
        left = scene.get_user_hands(user, 'left')
        scene.update_object(left)
        print('Left Hand Joined')
    else: # right hand
        right = scene.get_user_hands(user, 'right')
        scene.update_object(right)
        print('Right Hand Joined')

def box1_handler(scene, evt, msg):
    global interactive_objects
    box1 = interactive_objects[0]

    if evt.type == 'mousedown':
        scene.update_object(box1, color=Color(100,255,100))
    if evt.type == 'mouseup':
        scene.update_object(box1, color=Color(255,100,0))

def obj_handler(scene, evt, msg):
    global follower
    global master
    global left
    global right
    global original_pos

    object_id = msg['object_id']
    obj = scene.all_objects.get(object_id, None)
    if obj is not None and follower is not None:
        if evt.type == 'mousedown':
            if master[4] == 'R':
                if remote_mode:
                    obj.update_attributes(parent=right['object_id'])
                else:
                    obj.data['parent'] = 'rightHand'
                hand_pos = right.data.position
                side = 'right'
            else:
                if remote_mode:
                    obj.update_attributes(parent=left['object_id'])
                else:
                    obj.data['parent'] = 'leftHand'
                hand_pos = left.data.position
                side = 'left'

            obj_pos = obj.data.position
            original_pos = obj_pos
            dist = find_pos_dist(hand_pos, obj_pos)
            obj.data.position = get_following_position(dist, side)

            if remote_mode:
                scene.update_object(obj)
            else:
                scene.add_object(obj)

            follower = obj

        elif evt.type == 'mouseup':
            pass

@scene.run_once
def func():
    global sword
    global interactive_objects

    box1 = Box(object_id='box1', position=Position(2,1.6,-3), scale=Scale(0.3,0.3,0.3),
              click_listener=True, evt_handler=box1_handler, color=Color(255,100,0),
              persist=True)

    box2 = Box(object_id='box2', position=Position(0,1.6,-2), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(75,75,75),
              persist=True)

    sphere = Sphere(object_id='sphere', position=Position(-1,1.6,-1.5), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(50,25,0),
              persist=True)

    torus = Torus(object_id='torus', position=Position(2,1.6,-1.5), scale=Scale(0.2,0.2,0.2),
              click_listener=True, evt_handler=obj_handler, color=Color(25,5,0),
              persist=True)

    interactive_objects = [box1, box2, sphere, torus]

    for obj in interactive_objects:
        obj.data['remote-render'] = {'enabled': True}

    scene.add_objects(interactive_objects)
    remote_render_controllers(True)

scene.user_join_callback = user_join_callback
scene.user_left_callback = user_left_callback
scene.on_msg_callback = on_msg_callback
scene.hand_join_callback = hand_join_callback

# start thread and tasks
t2 = Thread(target=command_thread)
t2.daemon = True
t2.start()

scene.run_tasks()
