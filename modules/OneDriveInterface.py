import pandas as pd
from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient
import pickle as pkl
import datetime


class OneDriveInterface(object):
    CLIENT_ID = "5c56f180-6e82-499a-92ae-1047cb1d7d91"
    SECRET_ID = "a624c295-49b3-4f53-b251-585d979576dc"
    CLIENT_SECRET = "z~U8Q~0qTtmvRsH3fVksUt_L2pancVYJ6XN8KbRl"
    TENANT_ID = "aefd17ef-4982-43d7-903d-c12748e15807"
    AUTH_TENANT = TENANT_ID

    def __init__(self, drive_name='OSD Shared Drive'):
        client_credential = ClientSecretCredential(self.TENANT_ID, self.CLIENT_ID, self.CLIENT_SECRET)
        self.client = GraphClient(credential=client_credential)

        drives_request = self.client.get(url='/drives')

        if drives_request.raise_for_status():
            raise Exception

        drives = drives_request.json()['value']

        for drive in drives:
            if drive['name'] == drive_name:
                self.drive_id = drive['id']

        self.current_directory_id = None
        self.directory_id_sequence = []

    def cd_to_child_folder_by_name(self, folder_name):
        if self.current_directory_id:
            children_folders_request = self.client.get(url=f'/drives/{self.drive_id}/items/{self.current_directory_id}/children')
            folder_id = [folder['id'] for folder in children_folders_request.json()['value'] if folder['name'] == folder_name][0]

        else:
            drive_folders_request = self.client.get(url=f'/drives/{self.drive_id}/root/children')
            folder_id = [folder['id'] for folder in drive_folders_request.json()['value'] if folder['name'] == folder_name][0]

        self.current_directory_id = folder_id
        self.directory_id_sequence.append(folder_id)

        return folder_id

    def cd_parent_folder(self):
        self.directory_id_sequence.pop(-1)
        self.current_directory_id = self.directory_id_sequence[-1]

    def create_folder(self, name):
        json = {
            "name": name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail"
        }

        self.client.post(f'/drives/{self.drive_id}/items/{self.current_directory_id}/children', json=json, headers={'Content-Type': 'application/json'})

    def write_file(self, file_path, filename):
        content = open(file_path + filename, "rb").read()

        self.client.put(f'/drives/{self.drive_id}/items/{self.current_directory_id}:/{filename}:/content', data=content, headers={"Content-Type": "text/plain"})

class DataSnapClass(OneDriveInterface):
    def __init__(self, data_name, drive_name='OSD Shared Drive'):
        super().__init__(drive_name=drive_name)

        self.cd_to_child_folder_by_name("Data Snapping")

        if data_name == 'Debank':
            self.cd_to_child_folder_by_name("Debank")
            self.filename = 'user_protocol.pkl'
        elif data_name == 'CIF':
            self.cd_to_child_folder_by_name("CIF Snap")
            self.filename = 'CIF_debank.pkl'

    def snap_file_and_upload(self, object_to_pkl, file_path, filename):
        pkl.dump(object_to_pkl, open(rf"{file_path}{filename}", "wb"))

        self.create_folder(str(datetime.date.today()))

        self.cd_to_child_folder_by_name(str(datetime.date.today()))

        self.write_file(file_path, filename)

    def read_time_series_snaps(self, start_date='2022-09-01'):
        date_folders_request = self.client.get(url=f'/drives/{self.drive_id}/items/{self.current_directory_id}/children')
        date_folders = date_folders_request.json()['value']

        pkl_dict = dict()

        for date_folder in date_folders:
            if date_folder['name'] > start_date:
                specific_date_request = self.client.get(url=f"/drives/{self.drive_id}/items/{date_folder['id']}/children")
                specific_date_folder = specific_date_request.json()['value']

                for file in specific_date_folder:
                    if file['name'] == self.filename:
                        #pkl_dict[date_folder['name']] = pd.read_pickle(file['@microsoft.graph.downloadUrl'])
                        file_request = self.client.get(f'/drives/{self.drive_id}/items/{file["id"]}/content')
                        pkl_dict[date_folder['name']] = pkl.loads(file_request.content)

        return pkl_dict

class ReadStaticFiles(OneDriveInterface):
    def __init__(self, drive_name='OSD Shared Drive'):
        super().__init__(drive_name)

        self.cd_to_child_folder_by_name("Static Data")

    def get_static_data_file(self, filename):
        if len(filename.split('.')) == 1:
            filename += '.xlsx'

        files_request = self.client.get(url=f'/drives/{self.drive_id}/items/{self.current_directory_id}/children')
        files = files_request.json()

        file_id = [file['id'] for file in files['value'] if file['name'] == filename][0]

        graph_file_request = self.client.get(f'/drives/{self.drive_id}/items/{file_id}')
        graph_file_data = graph_file_request.json()

        excel_file = pd.ExcelFile(graph_file_data['@microsoft.graph.downloadUrl'])

        return excel_file











