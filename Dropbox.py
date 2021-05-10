import json
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM

import requests
from pip._vendor.distlib.compat import raw_input

import helper

server_addr = "localhost"
server_port = 8090
redirect_uri = "http://" + server_addr + ":" + str(server_port)

class Dropbox:
    _access_token = ""
    _path = "/"
    _files = []
    _root = None
    _msg_listbox = None

    def __init__(self, root):
        self._root = root

    def local_server(self):
        # 8090. portuan entzuten dagoen zerbitzaria sortu
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((server_addr, server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port " + str(server_port))

        # nabitzailetik 302 eskaera jaso
        client_connection, client_address = server_socket.accept()
        eskaera = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        print (eskaera)

        # eskaeran "auth_code"-a bilatu
        lehenengo_lerroa = eskaera.decode("utf8").split('\n')[0]
        aux_auth_code = lehenengo_lerroa.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]
        print ("\tauth_code: " + auth_code)

        # erabiltzaileari erantzun bat bueltatu
        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                        "<html>" \
                        "<head><title>Proba</title></head>" \
                        "<body>The authentication flow has completed. Close this window.</body>" \
                        "</html>"
        client_connection.sendall(http_response.encode(encoding="utf8"))
        client_connection.close()
        server_socket.close()

        return auth_code

    def do_oauth(self):
        auth_uri = "https://www.dropbox.com/oauth2/authorize"
        datos = {'client_id': app_key,
                 'response_type': "code",
                 'redirect_uri': redirect_uri}

        datos_encoded = urllib.parse.urlencode(datos)
        webbrowser.open_new(auth_uri+"?"+datos_encoded)

        print("# Step 4: Handle the OAuth 2.0 server response")
        auth_code = self.local_server()
        #auth_code = raw_input('Enter code')
        print("# Step 5: Exchange authorization code for refresh and access tokens")
        token_uri="https://api.dropboxapi.com/oauth2/token"
        datos = {'code': auth_code,
                 'grant_type': 'authorization_code',
                 'client_id': app_key,
                 'client_secret': app_secret,
                 'redirect_uri': redirect_uri}
        respuesta = requests.post(token_uri, data=datos, allow_redirects=False)
        status = respuesta.status_code
        print("\tStatus: " + str(status))

        # Google responds to this request by returning a JSON object
        # that contains a short-lived access token and a refresh token.
        contenido = respuesta.text
        print("\tCotenido:")
        print(contenido)
        contenido_json = json.loads(contenido)
        access_token = contenido_json['access_token']
        print("\taccess_token: " + access_token)
        self._access_token = access_token

        self._root.destroy()

    def list_folder(self, msg_listbox):
        print("/list_folder")
        if self._path == "/":
            self._path = ""
        list_uri = 'https://api.dropboxapi.com/2/files/list_folder'
        cabeceras = {'Authorization': 'Bearer ' + self._access_token,
                     'Content-Type': 'application/json'}
        datos = {
            "path": self._path,
            "recursive": False,
            "include_media_info": False,
            "include_deleted": False,
            "include_has_explicit_shared_members": False,
            "include_mounted_folders": True,
            "include_non_downloadable_files": True}
        datos_encoded = json.dumps(datos)
        respuesta = requests.post(list_uri, headers=cabeceras, data=datos_encoded, allow_redirects=False)
        status = respuesta.status_code
        print("\tStatus: " + str(status))
        contenido = respuesta.text
        print("\tContenido:")
        print(contenido)
        edukia_json_dict = json.loads(contenido)

        self._files = helper.update_listbox2(msg_listbox, self._path, edukia_json_dict)

    def transfer_file(self, file_path, file_data):
        print("/upload " + file_path)

        upload_uri = 'https://content.dropboxapi.com/2/files/upload'
        jsonupload = {
            "path": file_path,
            "mode": "add",
            "autorename": True,
            "mute": False,
            "strict_conflict": False
            }
        cabeceras = {'Authorization': 'Bearer ' + self._access_token,
                     'Content-Type': 'application/octet-stream',
                     'Dropbox-API-Arg': json.dumps(jsonupload)}
        datos = {'data-binary': file_data}
        respuesta = requests.post(upload_uri, headers=cabeceras, data=datos, allow_redirects=False)
        status = respuesta.status_code
        print("\tStatus: " + str(status))
        contenido = respuesta.text
        print("\tContenido:")
        print(contenido)

    def delete_file(self, file_path):
        print("/delete_file " + file_path)

        delete_uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        cabeceras = {'Authorization': 'Bearer ' + self._access_token,
                     'Content-Type': 'application/json'}
        datos = {'path': file_path}
        datos_encoded = json.dumps(datos)
        respuesta = requests.post(delete_uri, headers=cabeceras, data=datos_encoded, allow_redirects=False)
        status = respuesta.status_code
        print("\tStatus: " + str(status))
        contenido = respuesta.text
        print("\tContenido:")
        print(contenido)

    def create_folder(self, path):
        print("/create_folder " + path)

        create_uri = 'https://api.dropboxapi.com/2/files/create_folder_v2'
        cabeceras = {'Authorization': 'Bearer ' + self._access_token,
                     'Content-Type': 'application/json'}
        datos = {'path': path,
                 'autorename': False}
        datos_encoded = json.dumps(datos)
        respuesta = requests.post(create_uri, headers=cabeceras, data=datos_encoded, allow_redirects=False)
        status = respuesta.status_code
        print("\tStatus: " + str(status))
        contenido = respuesta.text
        print("\tContenido:")
        print(contenido)

    def download_links(self, file_path):
        print("/download_links " + file_path)

        download_uri = 'https://api.dropboxapi.com/2/files/get_temporary_link'
        cabeceras = {'Authorization': 'Bearer ' + self._access_token,
                     'Content-Type': 'application/json'}
        datos = {"path": file_path}
        datos_encoded = json.dumps(datos)
        respuesta = requests.post(download_uri, headers=cabeceras, data=datos_encoded, allow_redirects=False)
        r = json.loads(respuesta.content)
        status = respuesta.status_code
        print("\tStatus: " + str(status))
        contenido = respuesta.text
        print("\tContenido:")
        print(contenido)
        url = r["link"]
        print(url)
        webbrowser.open(url)

