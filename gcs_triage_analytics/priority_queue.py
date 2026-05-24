from severity_score import SeverityScore
from victim import Victim
import csv

class PriorityQueue:
    def __init__(self):
        self.__victims = {}

    def add_victim_to_queue(self, victim: Victim):
        scorer = SeverityScore()
        victim.set_score(round(scorer.compute(victim), 2))

        victim_json = {
            "pose": victim.get_pose(),
            "hr": victim.get_hr(),
            "temp": victim.get_temp(),
            "env": victim.get_env(),
            "score": victim.get_score(),
            "coord_x": victim.get_coord_x(),
            "coord_y": victim.get_coord_y(),
        }

        self.__victims[victim.get_id()] = victim_json
        
    def classify_severity(self, score):
        if score < 3:
            return "NORMAL"
        elif score < 5:
            return "STABLE"
        elif score < 8:
            return "URGENT"
        else:
            return "CRITICAL"

    def get_victims(self):
        return dict(self.__victims.items())
    
    def get_sorted(self):
        return dict(sorted(self.__victims.items(), key=lambda item: item[1]["score"], reverse=True))
    
    def clean_queue(self):
        self.__victims = {}
    
    def export_csv(self, path="C:/"):
         
        sorted_queue = self.get_sorted()

        mapping = {
            "Score": "score",
            "Pose": "pose",
            "Heart rate": "hr",
            "Temperature": "temp",
            "Environment": "env",
        }

        fields = list(mapping.keys())
        fields.insert(0, "ID")
        fields.insert(2, "Severity")

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)

            writer.writeheader()
            for id in sorted_queue.keys():
                row = {
                    column: sorted_queue[id][key] for column, key in mapping.items()
                }
                row["ID"] = id
                row["Severity"] = self.classify_severity(sorted_queue[id]["score"])
                writer.writerow(row)

    def export_txt(self, path="C:/"):
        sorted_queue = self.get_sorted()

        with open(path, "w") as f:
            f.write("=== PRIORITY QUEUE ===\n\n")

            for i, (id, vitals) in enumerate(sorted_queue.items(), start = 1):
                severity_label = self.classify_severity(vitals["score"])
                f.write(f"#{i} - Victim ID: {id}\n")
                f.write(f"   Score: {vitals['score']}\n")
                f.write(f"   Severity: {severity_label}\n")
                f.write(f"   Pose: {vitals['pose']}\n")
                f.write(f"   Heart rate: {vitals['hr']} bpm\n")
                f.write(f"   Temperature: {vitals['temp']}ºC\n")
                f.write(f"   Environment: {vitals['env']}\n")
                f.write("\n")
