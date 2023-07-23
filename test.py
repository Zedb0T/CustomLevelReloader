bl_info = {
    "name": "Cube Position Logger",
    "blender": (3, 2, 0),
    "category": "Object",
}

import bpy
import os
import socket
import struct
import subprocess
import time
import mathutils
import winsound
import threading

# Paths Ideally set this from a GUI in Blender later
application_path = "C:\\Users\\NinjaPC\\Documents\\Github\\flutflut-legacy\\"
PATHTOGOALC = os.path.join(application_path, "goalc.exe")
PATHTOGK = os.path.join(application_path, "gk.exe -boot -fakeiso -debug -v")
customLevelGLB_path = os.path.join(application_path, "data\\custom_levels\\test-zone\\test-zone2.glb")
serverAddress = ("127.0.0.1", 8181) # will need to adjust port when/if Jak2 custom levels exist

def sendForm(form, clientSocket):
    header = struct.pack('<II', len(form), 10)
    clientSocket.sendall(header + form.encode())
    print("Sent: " + form)

def is_goalc_running():
    try:
        subprocess.check_output('tasklist /FI "IMAGENAME eq goalc.exe"', shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def on_object_move(scene):
    for obj in bpy.data.objects:
        # Check if the object has a 'prev_location' attribute, if not, initialize it
        if not hasattr(obj.data, "prev_location"):
            obj.data.prev_location = obj.location.copy()

        # Check if the object has moved (compare with the previous location)
        if obj.location != obj.data.prev_location:
            # Update the previous location
            obj.data.prev_location = obj.location

            # Run export_file in a new thread
            thread = threading.Thread(target=export_file_in_thread, args=(scene,))
            thread.start()

def on_file_save_pre(scene):
    # Call export_file function with the current frame when the file is saved
    export_file(scene, bpy.context.scene.frame_current)

def export_file(scene, current_frame, x, y ,z):
    global clientSocket

    # Reset the socket

    if 'clientSocket' in globals():
        clientSocket.close()
        del clientSocket

    # Initialize the socket
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    path = customLevelGLB_path
    #bpy.ops.export_scene.gltf(filepath=path, export_apply=True)

    #time.sleep(3)  # Delay for 3 seconds - untested but this is just to hopefully give the glb enough time to export

    # Check if goalc.exe is already running
    if not is_goalc_running():
        # Open a fresh goalc.exe then wait a bit before trying to connect via socket
        print("Opening " + PATHTOGOALC)
        try:
            subprocess.Popen([PATHTOGOALC], creationflags=subprocess.CREATE_NEW_CONSOLE)
            print("goalc.exe started successfully.")
        except subprocess.CalledProcessError:
            print("Failed to start goalc.exe.")
    else:
        print("goalc.exe is already running.")

    time.sleep(2)

    # Check if the socket is already connected
    is_connected = False
    try:
        clientSocket.connect_ex(serverAddress) == 0
        is_connected = True
    except ConnectionRefusedError:
        pass

    if is_connected:
        print("Socket is already connected")
    else:
        # Attempt to establish the connection
        try:
            clientSocket.connect(serverAddress)
            print("Socket connected successfully")
        except ConnectionRefusedError:
            print("Failed to connect to the socket.")

    data = clientSocket.recv(1024)

    # Int block these commands are sent on startup they won't run on the client until the lt and mi finish.
    sendForm("(lt)", clientSocket)
    sendForm("(mi)", clientSocket)
    sendForm("(move-actor \"money-2692\" {} {} {})".format(x, z,(y * -1 )), clientSocket)

   # time.sleep(20) # this is here to be safe; can probably be removed.

    # Close the socket
    clientSocket.close()

last_cube_position = None

def export_file_in_thread(scene):
    # Perform your custom level reload process here for the moved object
    export_file(scene)

def log_cube_position(scene):
    global last_cube_position

    cube = bpy.data.objects.get("Cube")
    if cube:
        position = cube.location

        if last_cube_position != position:
            print(f"Cube Position: X: {position.x}, Y: {position.y}, Z: {position.z}")
            export_file(scene, bpy.context.scene.frame_current, position.x, position.y, position.z)

        last_cube_position = position.copy()

def register():
    bpy.app.handlers.depsgraph_update_post.append(log_cube_position)

def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(log_cube_position)

if __name__ == "__main__":
    register()
