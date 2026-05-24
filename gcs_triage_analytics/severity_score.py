from victim import Victim

class SeverityScore:
    def __init__(self, w_pose=0.35, w_hr=0.35, w_temp=0.10, w_env=0.20):
        '''
        Weights of each parameter (0-1)
        '''

        self.__w_pose = w_pose
        self.__w_hr = w_hr
        self.__w_temp = w_temp
        self.__w_env = w_env

    def normalize_pose(self, pose):
        if pose == "laying":
            return 1
        elif pose == "sitting":
            return 0.5
        else:
            return 0
    def normalize_hr(self, hr):
        if 55 < hr < 70:
            return 0
        elif 70 <= hr < 100:
            return 0.25
        elif 100 <= hr < 120:
            return 0.50
        elif 120 <= hr < 130:
            return 0.75
        else:
            return 1    # hr <= 55 or hr >= 130

    def normalize_temp(self, temp):
        if temp <= 35.5 or temp >= 38.5:
            return 1
        elif 36 < temp < 37:
            return 0.0
        else:
            return 0.5  # 35.5 < temp <= 36 or 37 <= temp < 38.5

    def normalize_env(self, env):
        if env == "debris" or env == "smoke":
            return 0.5
        elif env == "fire" or env == "snow":
            return 1
        else:
            return 0
    
    def compute(self, victim: Victim):
        return 10*(
            self.__w_pose * self.normalize_pose(victim.get_pose()) +
            self.__w_hr * self.normalize_hr(victim.get_hr()) +
            self.__w_temp * self.normalize_temp(victim.get_temp()) +
            self.__w_env * self.normalize_env(victim.get_env())
        )
