import xgboost as xgb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error


def time_convert(x):
    h, m, s = x.split(':')
    return int(h) * 60 ** 2 + int(m) * 60 + int(s)


class XGBoost:

    @staticmethod
    def train_data():
        print("Preparing data for training...")
        # TODO: Calculate distance in straigth line from long and lat
        # prepare the dataframe
        training_df = pd.read_csv("training_data.csv")
        training_df["duration"] = training_df["duration"].apply(time_convert)
        x = training_df.drop(["duration"], axis=1)
        target = training_df["duration"]

        # split the data into train, test and validation sets
        x_train, x_test, target_train, target_test = train_test_split(x, target, test_size=0.3, random_state=123)
        x_train, x_validate, target_train, target_validate = train_test_split(x_train, target_train, test_size=0.2,
                                                                              random_state=12)

        # convert the split datasets into Dmatrix
        d_train = xgb.DMatrix(x_train, label=target_train)
        d_val = xgb.DMatrix(x_validate, label=target_validate)
        d_test = xgb.DMatrix(x_test)

        # remove from memory
        del x_train, x_test

        evaluate = [(d_train, "train"),(d_val, "validated")]

        # Set up params for XGBoost
        params = {
            'min_child_weight': 0.5,
            'objective': 'reg:linear',
            'eval_metric': 'rmse',
            'silent': 1,
            'eta': 0.05,
            'max_depth': 12,
            'colsample_bylevel': 0.7,
            'subsample': 0.9
        }

        model = xgb.train(params,
                        dtrain=d_train,
                        num_boost_round=500,
                        evals=evaluate,
                        verbose_eval=True
                        )

        predicted_test = model.predict(d_test)
        rmse = pd.np.sqrt(mean_squared_error(target_test, predicted_test))

        # Save the model file
        model.save_model('model.mdl')

        # Predict on the test dataset
        p_test = model.predict(d_test)

        # Create a submission file
        sub = pd.DataFrame()
        sub['target'] = target_test
        sub['trip_duration'] = p_test

        # write the csv
        sub.to_csv('results.csv', index=False)

