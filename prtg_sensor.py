import requests
from constants import prtg_id, prtg_pass

def get_prtg_data(sensor_id):
        
    for i in ['','2','3','4']: ## Check for all RIMS 
        url = f"https://rims{i}.allieddigital.net/api/getsensordetails.json?id={sensor_id}&username={prtg_id}&password={prtg_pass}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['sensordata']['name'] != ''and data['sensordata']['name']!='Access Denied': ## Do not return null data
                return data, f'rims{i}'
    
    print("Failed:", response.status_code)
    return "More details not available, work with the data you currently have access to"

def get_all_sensors_for_device(sensor_id):
    data, rims_system = get_prtg_data(sensor_id)
    #print(sensor_id)
    #print(data)
    
    parent_id = data['sensordata']['parentdeviceid']
    url = f'''https://{rims_system}.allieddigital.net/api/table.json?id={parent_id}&columns=objid,probe,device,sensor,status,message,lastvalue,priority&username={prtg_id}&password={prtg_pass}&output=json&count=30&filter_status.not=3'''
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data
    else:
        return "Sensors for the same parent device not available, work with the data you currently have access to"

def get_all_downstream_sensors(sensor_id):
    data, rims_system = get_prtg_data(sensor_id)
    #print(sensor_id)
    #print(data)
    parent_id = sensor_id
    url = f'''https://{rims_system}.allieddigital.net/api/table.json?id={parent_id}&columns=objid,probe,device,sensor,status,message,lastvalue,priority&username={prtg_id}&password={prtg_pass}&output=json&count=30&filter_status.not=3'''
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data
    else:
        return "Downstream sensors not available, work with the data you currently have access to"