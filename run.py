import traci
import math
import csv
import os

def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

# 啟動 SUMO
traci.start(["sumo-gui", "-c", "simpleMap.sumocfg", "--step-length", "0.1"]) # 時間單位為0.1秒

# 繞圈路徑
circle_route = ["J15toJ16", "J16toJ17", "J17toJ12", "J12toJ7", "J7toJ6", "J6toJ5", "J5toJ10", "J10toJ15", "J15toJ16"]

bus_ids = ["bus1", "bus2", "bus3"]
comm_range = 100  # 公車通訊範圍半徑 (公尺)
vehicle_records = {} # 車輛紀錄

simulation_time = 0
end_time = 300

while traci.simulation.getMinExpectedNumber() > 0 and simulation_time <= end_time:
    traci.simulationStep()

    # 設置繞圈公車的路徑
    current_edge = traci.vehicle.getRoadID("bus3")
    if current_edge == "J15toJ16":
        traci.vehicle.setRoute("bus3", circle_route)

    vehicle_ids = traci.vehicle.getIDList()
    bus_ids = [vid for vid in vehicle_ids if vid.startswith("bus")] 
    car_ids = [car for car in vehicle_ids if not car.startswith("bus")]  # 包含路網中所以公車以外的車輛

    # 更新車輛紀錄
    for vehicle_id in car_ids:

        if vehicle_id not in vehicle_records:
            vehicle_records[vehicle_id] = {}

        # 處理轎車進入或離開每輛公車的通訊範圍
        for bus_id in bus_ids:
            # 獲取轎車與公車的位置
            vehicle_position = traci.vehicle.getPosition(vehicle_id)
            bus_position = traci.vehicle.getPosition(bus_id)

            # 計算距離
            distance = calculate_distance(bus_position[0], bus_position[1], vehicle_position[0], vehicle_position[1])

            # 初始化該轎車與公車的紀錄列表
            if bus_id not in vehicle_records[vehicle_id]:
                vehicle_records[vehicle_id][bus_id] = []

            # 最新的紀錄
            records = vehicle_records[vehicle_id][bus_id]
            last_record = records[-1] if records else None

            if distance <= comm_range:
                # 轎車進入公車的通訊範圍
                if not last_record or "exit_time" in last_record:
                    records.append({"enter_time": simulation_time})
            else:
                # 轎車離開公車的通訊範圍
                if last_record and "exit_time" not in last_record:
                    last_record["exit_time"] = simulation_time
                    last_record["stay_time"] = simulation_time - last_record["enter_time"]

    # 檢查離開路網的車輛
    for vehicle_id in list(vehicle_records.keys()):  # 使用 list() 防止字典大小變化
        if vehicle_id not in vehicle_ids:  # 該車輛已經離開路網
            for bus_id, records in vehicle_records[vehicle_id].items():
                last_record = records[-1] if records else None
                if last_record and "exit_time" not in last_record:
                    last_record["exit_time"] = simulation_time
                    last_record["stay_time"] = simulation_time - last_record["enter_time"]

    for bus_id in bus_ids:  # 檢查是否有公車離開
        if bus_id not in vehicle_ids:  # 該公車已經離開路網
            for vehicle_id, buses in vehicle_records.items():
                if bus_id in buses:
                    records = buses[bus_id]
                    last_record = records[-1] if records else None
                    if last_record and "exit_time" not in last_record:
                        last_record["exit_time"] = simulation_time
                        last_record["stay_time"] = simulation_time - last_record["enter_time"]


    simulation_time += 0.1

traci.close()


# 獲取當前程式所在路徑
current_path = os.path.dirname(os.path.abspath(__file__))

# 定義輸出檔案名稱並放在當前路徑
output_file = os.path.join(current_path, "vehicle_records.csv")

# 將結果輸出到 CSV 檔案
with open(output_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Vehicle ID", "Bus ID", "Enter Time", "Exit Time", "Stay Time"])
    for vehicle_id, buses in vehicle_records.items():
        for bus_id, records in buses.items():
            for record in records:
                writer.writerow([
                    vehicle_id, bus_id,
                    record["enter_time"],
                    record.get("exit_time", "N/A"),
                    record.get("stay_time", "N/A")
                ])