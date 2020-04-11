import csv

from main.Planner import euclidean_dist, get_time_between_points


def test_xgb():
    summed = 0
    number = 0
    with open('xgboost_test_set.csv', mode='r') as csv_file:
        with open("evaluate_xgb.csv", mode='w') as file:
            training = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_reader = csv.DictReader(csv_file)
            rows = list(csv_reader)
            for row in rows:
                distance = euclidean_dist(float(row["lat_origin"]), float(row["lon_origin"]), float(row["lat_dest"]),
                                          float(row["lon_dest"]))
                duration = int(row["duration"])
                duration_found = get_time_between_points(float(row["lat_origin"]), float(row["lon_origin"]),
                                                         float(row["lat_dest"]), float(row["lon_dest"]), distance)
                error = abs((duration_found/duration * 100)-100)
                training.writerow([int(duration_found), duration, row["lat_origin"], row["lon_origin"], row["lat_dest"],
                                   row["lon_dest"], error])

                summed += error
                number += 1
                print(error)

        accuracy = 100 - summed/number
        print(accuracy)


def main():
    print("Test XGBoost")
    distance = euclidean_dist(51.467222, -0.256472, 51.46475248096194, -0.18228788505268062)
    print(get_time_between_points(51.467222, -0.256472, 51.46475248096194, -0.18228788505268062, distance))
    test_xgb()


if __name__ == "__main__":
    main()
