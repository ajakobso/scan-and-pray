from kivy.uix.button import Button
from kivy.garden.xcamera import XCamera
from kivy.uix.floatlayout import FloatLayout
from roboflow import Roboflow
from kivy.base import runTouchApp
import glob

MIN_CONFIDENCE = 0.5
API_KEY = "Oaqu2oIbVpT7bCyf1klh"
MODEL_ENDPOINT = "food-hfbxu/scanpray"
VERSION = 1


class ChangeCameraButton(Button):
    def __init__(self, **kwargs):
        super(ChangeCameraButton, self).__init__(**kwargs)
        self.size_hint = (0.17, 0.19)
        self.pos_hint = {"x": 0.855, "center_y": 0.38}
        self.background_normal = "change_camera.png"


class PredictPrayButton(Button):
    def __init__(self, **kwargs):
        super(PredictPrayButton, self).__init__(**kwargs)
        self.size_hint = (0.2, 0.2)
        self.pos_hint = {"x": 0.845, "center_y": 0.65}
        self.background_normal = "pray_icon.png"


class MainScreen(FloatLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.xcamera = XCamera(index=0, play=True)
        self.add_widget(self.xcamera)
        self.change_camera_button = ChangeCameraButton()
        self.change_camera_button.bind(on_press=self.change_camera)
        self.add_widget(self.change_camera_button)
        self.predict_pray_button = PredictPrayButton()
        self.predict_pray_button.bind(on_press=self.predict)
        self.add_widget(self.predict_pray_button)

        # set the roboflow model values in the initial function in order to save time when predicting an image
        self.rf = Roboflow(api_key=API_KEY)
        self.project = self.rf.workspace().project(MODEL_ENDPOINT)
        self.model = self.project.version(VERSION).model

    def change_camera(self, instance):
        xcamera = self.root.ids.xcamera
        xcamera.index = (xcamera.index + 1) % 2  # toggle between 0 and 1

    def predict(self, instance):
        # TODO
        # figure out how to get the images in the current directory using globbing, the below might help
        # import glob
        # source_path = "my_path"
        # image_files = [source_path + '/' + f for f in glob.glob('*.png')]
        # images_path = glob.glob('r\\d{4}-\\d{2}-\\d{2}*.jpg')
        # first_image = next(iter(images_path), None)

        first_image = "food.jpg"
        # infer on a local image
        output = self.model.predict(first_image).json()

        # create a dictionary from the json object
        predictions_dict = dict(output['predictions'][0]['predictions'])

        # create a dictionary with the pray as key, and prediction as the value o
        new_dict = {key: value['confidence']
                    for key, value in predictions_dict.items()
                    if value['confidence'] >= MIN_CONFIDENCE}  # only if the prediction is above MIN_CONFIDENCE

        # print the values of the dictionary
        for key, value in new_dict.items():
            print(key, '    ', value)

        # TODO
        # 1. create a dictionary with the name of the pray as the key and the text as the value
        # for example 'שהכל' : 'ברוך את ... שהכל נהיה בדברו'
        # 2. create the whole text to pray using the dictionary and the keys of new_dict
        # 3. create a GUI to display it (maybe use the background of the first presentation) and write above the text


if __name__ == '__main__':
    runTouchApp(MainScreen())