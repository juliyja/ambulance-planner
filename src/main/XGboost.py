from math import sqrt

import xgboost as xgb
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import mean_squared_error
import joblib


# calculate euclidean distance
def euclidean_dist(x):
    return sqrt((x["lat_origin"] - x["lat_dest"]) ** 2 + (x["lon_origin"] - x["lon_dest"]) ** 2)


class XGBoost:

    @staticmethod
    def train_data(params, d_test, d_train, d_val, target_test):
        evaluate = [(d_train, "train"), (d_val, "validated")]

        # Set up params for XGBoost

        num_boost_rounds = 2000

        model = xgb.train(params,
                          dtrain=d_train,
                          num_boost_round=num_boost_rounds,
                          evals=evaluate,
                          verbose_eval=True,
                          early_stopping_rounds=10
                          )

        predicted_test = model.predict(d_test)
        rmse = pd.np.sqrt(mean_squared_error(target_test, predicted_test))

        print("Best rmse: {:.2f} with {} rounds".format(
            model.best_score,
            model.best_iteration + 1))

        # Save the model file
        joblib.dump(model, "results")

        return rmse

    @staticmethod
    def prepare_data():
        print("Preparing data for training...")
        # prepare the dataframe
        training_df = pd.read_csv("training_data4.csv")
        training_df["distance"] = training_df.apply(euclidean_dist, axis=1)
        x = training_df.drop(["duration"], axis=1)
        target = training_df["duration"]
        # split the data into train, test and validation sets
        x_train, x_test, target_train, target_test = train_test_split(x, target, test_size=0.3, random_state=123)
        x_train, x_validate, target_train, target_validate = train_test_split(x_train, target_train, test_size=0.2,
                                                                              random_state=12)
        print("Converting to Dmatrix")
        # convert the split datasets into Dmatrix
        d_train = xgb.DMatrix(x_train, label=target_train)
        d_val = xgb.DMatrix(x_validate, label=target_validate)
        d_test = xgb.DMatrix(x_test)
        # remove from memory
        del x_train, x_test
        return d_test, d_train, d_val, target_test


def score_check(model):
    print(model.get_score())


def main():
    print("Starting XGBoost...")

    d_test, d_train, d_val, target_test = XGBoost.prepare_data()

    params = {
        'learning_rate': 0.15,
        'objective': 'reg:squarederror',
        'eval_metric': 'rmse',
        'max_depth': 12,
        'colsample_bytree': 0.8,
        'colsample_bylevel': 0.8,
        'subsample': 0.9,
    }
    model = XGBoost.train_data(params, d_test, d_train, d_val, target_test)

    print(model)
    # score_check(model)


if __name__ == "__main__":
    main()
