#IMPORTING LIBRARIES
import json
from os import makedirs
from os.path import exists, dirname

#IMPORTING FILES
from settings import *


#FUNCTION FOR LOADING THE GAME DATA
def load_data(data_path, default_data):

    #CHECKING IF THE DATA EXISTS
    if exists(data_path):
        with open(data_path, 'r') as save_file:
            try:

                #TRYING TO LOAD THE SAVE DATA
                return json.load(save_file)
            
            except json.JSONDecodeError:
                print('Save file is corrupted.\nCreating a new one with default data!')

    #IF THE SAVE FILE DOES NOT EXIST OR IS CORRUPTED, CREATING A NEW SAVE FILE WITH DEFAULT DATA
    save_data(default_data, data_path)
    return default_data



#FUNCTION FOR SAVING DATA FILES
def save_data(data, save_path):

    #ENSURING THE DIRECTORY EXISTS BEFORE WRITTING THE DATA
    makedirs(dirname(save_path), exist_ok = True)

    #CREATING THE SAVE FILE
    with open(save_path, 'w') as save_file:
        json.dump(data, save_file, indent = 4)