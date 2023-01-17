from kivy.graphics import Rectangle
from kivy.uix.button import Button
from kivy.garden.xcamera import XCamera
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from roboflow import Roboflow
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.app import App

import os

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


def pray(predictions):
    first_pray_dict = {'המוציא': "בָּרוּךְ אַתָּה יהֵוָהֵ אֱלהֵינוּ מֶלֶךְ הָעולָם הַמּוֹצִיא לֶחֶם מִן הָאָרֶץ",
                       'שהכל': "בָּרוּךְ אַתָּה יהֵוָהֵ אֱלהֵינוּ מֶלֶךְ הָעולָם שֶׁהַכֹּל ניהיה בִּדְבָרו",
                       'מזונות': "בָּרוּךְ אַתָּה יהֵוָהֵ אֱלהֵינוּ מֶלֶךְ הָעולָם בּוֹרֵא מִינֵי מְזוֹנוֹת",
                       'הגפן': "בָּרוּךְ אַתָּה יהֵוָהֵ אֱלהֵינוּ מֶלֶךְ הָעולָם בּוֹרֵא פְּרִי הַגָּפֶן",
                       'העץ': "בָּרוּךְ אַתָּה יהֵוָהֵ אֱלהֵינוּ מֶלֶךְ הָעולָם בּוֹרֵא פְּרִי הָעֵץ",
                       'האדמה': "בָּרוּךְ אַתָּה יהֵוָהֵ אֱלהֵינוּ מֶלֶךְ הָעולָם בּוֹרֵא פְּרִי הָאֲדָמָה"}

    create_souls_pray = "עַל כָּל מַה שֶׁבָּרָאתָ לְהַחֲיוֹת בָּהֶם נֶפֶשׁ כָּל חָי. בָּרוּךְ חֵי הָעוֹלָמִים"
    create_souls_pray += "\n"
    create_souls_pray += "בָּרוּךְ אַתָּה יי אֱלהֵינוּ מֶלֶךְ הָעוֹלָם בּוֹרֵא נְפָשׁוֹת רַבּוֹת וְחֶסְרוֹנָן"

    last_pray_dict = {'המוציא': "ברכת המזון",
                      'שהכל': create_souls_pray,
                      'מזונות': "מעין שלוש",
                      'הגפן': "מעין שלוש",
                      'העץ': create_souls_pray,
                      'האדמה': create_souls_pray}

    pray_text = ""

    for l_pray in predictions:
        pray_text += "\n" + last_pray_dict[l_pray]

    pray_text += "\n"

    pray_text += "ברכה אחרונה: "

    pray_text += "\n"

    for f_pray in predictions:
        pray_text += "\n" + first_pray_dict[f_pray]

    pray_text += "\n"

    pray_text += "ברכה ראשונה: "

    pray_text += "\n\n"

    pray_text += "סדר הברכות: המוציא, מזונות, הגפן, עץ, אדמה, שהכל "

    return pray_text


class MainScreen(Screen):
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
        # Get the current working directory
        cwd = os.getcwd()

        # Initialize an empty list to store the files
        date_files = []

        # Iterate through all the subdirectories and files in the current directory
        for root, dirs, files in os.walk(cwd):
            for file in files:
                # Check if the file name matches the specified format
                if file.endswith(".jpg") and file.split(".")[0].replace("_", " ").replace("-", " ").split():
                    # Append the file to the list
                    date_files.append(os.path.join(root, file))

        # Sort the list of files by date
        sorted_date_files = sorted(date_files, key=lambda x: os.path.getmtime(x), reverse=True)

        # print(sorted_date_files)

        # TODO
        # if there is no file available - print an error, and ask to take a picture first
        first_image = sorted_date_files[0]

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

        pray_text = pray(new_dict.keys())

        print(pray_text)

        # switch to the pray screen
        pray_screen = self.screen_manager.get_screen('pray_screen')
        pray_screen.pray.text = "[color=000000]" + pray_text[::-1] + "[/color]"
        pray_screen.pray.markup = True
        pray_screen.pray.base_direction = 'rtl'
        self.screen_manager.switch_to(pray_screen)

        # TODO
        # 1. create a dictionary with the name of the pray as the key and the text as the value check
        # for example 'שהכל' : 'ברוך את ... שהכל נהיה בדברו'
        # 2. create the whole text to pray using the dictionary and the keys of new_dict check
        # 3. create a GUI to display it (maybe use the background of the first presentation) and write above the text
        # 4. create a button to go back to the camera screen


class BackToCameraButton(Button):
    def __init__(self, **kwargs):
        super(BackToCameraButton, self).__init__(**kwargs)
        self.size_hint = (0.16, 0.16)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.8}
        self.background_normal = 'return_icon.png'


class PrayScreen(Screen):
    def __init__(self, **kwargs):
        super(PrayScreen, self).__init__(**kwargs)
        self.orientation = "vertical"

        # add background image to the screen
        self.background = Image(pos=self.pos, size=self.size, source='pray_background.jpeg')
        self.add_widget(self.background)

        # add a return to camera button
        self.back_to_camera_button = BackToCameraButton()
        self.back_to_camera_button.bind(on_press=self.back_to_camera)
        self.add_widget(self.back_to_camera_button)

        # add a label for the pray text
        self.pray = Label(text="", pos_hint={'center_x': 0.5, 'center_y': 0.5}, font_size=20, font_name='arial')
        self.add_widget(self.pray)

    def back_to_camera(self, instance):
        self.screen_manager.switch_to(self.screen_manager.get_screen('main_screen'))


class TestApp(App):
    def build(self):
        screen_manager = ScreenManager(transition=FadeTransition())
        screen_manager.add_widget(MainScreen(name='main_screen'))
        screen_manager.add_widget(PrayScreen(name='pray_screen'))
        MainScreen.screen_manager = screen_manager
        PrayScreen.screen_manager = screen_manager
        return screen_manager


if __name__ == '__main__':
    TestApp().run()
