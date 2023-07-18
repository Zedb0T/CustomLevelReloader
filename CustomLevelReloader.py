import bpy
import os
import socket
import struct
import subprocess
import time


bl_info = {
    'name': 'openGOAL custom level reload on save',
    'blender': (2, 80, 0),
    'category': 'Import-Export'
}

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

def export_file(scene):
    # Reset the socket
    if 'clientSocket' in globals():
        clientSocket.close()
        del clientSocket

    # Initialize the socket
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    path = customLevelGLB_path
    bpy.ops.export_scene.gltf(filepath=path, export_apply=True)

    time.sleep(3)  # Delay for 3 seconds - untested but this is just to hopefully give the glb enough time to export

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

    # Int block these commands are sent on startup they wont run on the client until the lt and mi finish.
    sendForm("(lt)", clientSocket)
    sendForm("(mi)", clientSocket)
    sendForm("(send-event *target* 'get-pickup (pickup-type eco-red) 5.0)", clientSocket)
    sendForm("(dotimes (i 1) (sound-play-by-name (static-sound-name \"cell-prize\") (new-sound-id) 1024 0 0 (sound-group sfx) #t))", clientSocket)
    
    sendForm(" ((method-of-type target unload-level) 'test-zone)")

    time.sleep(20) #this is here to be safe can probably be removed.

    # Close the socket
    clientSocket.close()


def register():
    unregister()  # Unregister the handlers first
    bpy.app.handlers.save_post.append(export_file)

def unregister():
    try:
        bpy.app.handlers.save_post.remove(export_file)
    except ValueError:
        pass

if __name__ == "__main__":
    register()
