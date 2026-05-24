class Victim:
    def __init__(self, id, pose, hr, temp, env, coord_x, coord_y):

        self.__pose = pose
        self.__hr = hr
        self.__temp = temp
        self.__env = env
        self.__id = id
        self.__coord_x = coord_x
        self.__coord_y = coord_y
        self.__score = 0

    def get_pose(self):
        return self.__pose

    def get_hr(self):
        return self.__hr
    
    def get_temp(self):
        return self.__temp
    
    def get_env(self):
        return self.__env
    
    def set_id(self, id):
        self.__id = id

    def get_id(self):
        return self.__id
    
    def get_coord_x(self):
        return self.__coord_x

    def get_coord_y(self):
        return self.__coord_y
    
    def set_score(self, score):
        self.__score = score

    def get_score(self):
        return self.__score
