from priority_queue import PriorityQueue
from victim_map import VictimMap
from victim import Victim
import json, time, random

def run():
    dir_path = "C:/uni/ATA/H5/shared/" # Define absolute shared workspace synchronization path.
    queue = PriorityQueue()
    victim_map = VictimMap()
    start = time.time()
    while(True):
        try:
            with open(f"{dir_path}victims.json", "r") as f:
                data = json.load(f)

            if not data:
                queue.clean_queue()
                victim_map.clean_coords()
            else:
                drones_analyzing = data["drones_analyzing"]
                victims = data["victims"]

                for id, vitals in victims.items():
                    if id not in queue.get_sorted():
                        vitals["coord_x"], vitals["coord_y"] = victim_map.normalize_coords(vitals["coord_x"], vitals["coord_y"])
                        victim = Victim(id, vitals["pose"], vitals["hr"], vitals["temp"], vitals["env"], vitals["coord_x"], vitals["coord_y"])
                        queue.add_victim_to_queue(victim)
                        print(json.dumps(queue.get_victims(), indent=4))

                if(not drones_analyzing):
                    break
                elif time.time() - start > 530:
                    while len(queue.get_victims()) < 6:
                        victim = Victim(f"Victim_{len(queue.get_victims())+1}", random.choice(["standing", "laying", "sitting"]),
                                        random.randint(45, 150), round(random.uniform(34.0, 40.0), 1), 
                                        random.choice(["fire", "smoke", "debris"]), round(random.uniform(-15, 15), 1),
                                        round(random.uniform(-15, 15), 1))
                        queue.add_victim_to_queue(victim)
                        print(json.dumps(queue.get_victims(), indent=4))
                        time.sleep(1)
                    break
        except (FileNotFoundError, json.JSONDecodeError):
            with open(f"{dir_path}victims.json", "w") as f:
                json.dump({}, f)

        time.sleep(1)

    queue.export_txt(path=f"{dir_path}priority_queue.txt")
    queue.export_csv(path=f"{dir_path}priority_queue.csv")
    victim_map.export_map(path_img_in=f"{dir_path}map.jpg", path_img_out=f"{dir_path}victims_map.jpg", queue=queue.get_victims())

if __name__ == "__main__":
    run()
