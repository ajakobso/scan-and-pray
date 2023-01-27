from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.garden.xcamera import XCamera
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from roboflow import Roboflow
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.app import App
from split_image import split_image
import os

__version__ = '1.0.0'

# minimum confidence for a prediction to be shown
MIN_CONFIDENCE = 0.7
# api key of the roboflow model
API_KEY = "0micJPzji8QmYEzKluri"  # "Oaqu2oIbVpT7bCyf1klh"
# name of the roboflow model
MODEL_ENDPOINT = "group-b-jct/scanpray2"  # "food-hfbxu/scanpray"
# roboflow model version number
VERSION = 2  # 3

# number of rows the image will be split into in order to get more predictions
ROW_NUM_OF_SPLIT = 3

# number of columns the image will be split into in order to get more predictions
COL_NUM_OF_SPLIT = 3


class ChangeCameraButton(Button):
    def __init__(self, **kwargs):
        super(ChangeCameraButton, self).__init__(**kwargs)
        self.size_hint = (0.15, 0.15)
        self.pos_hint = {"x": 0.857, "center_y": 0.38}
        self.background_normal = "switch_camera.png"


class PredictPrayButton(Button):
    def __init__(self, **kwargs):
        super(PredictPrayButton, self).__init__(**kwargs)
        self.size_hint = (0.135, 0.11)
        self.pos_hint = {"x": 0.87, "center_y": 0.65}
        self.background_normal = "raising_hands.png"


def pray(predictions):
    if predictions is None:
        return "לא נמצאו ברכות מתאימות, אנא נסו לצלם שנית"
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
        if last_pray_dict[l_pray] not in pray_text:
            pray_text += "\n" + last_pray_dict[l_pray]

    pray_text += "\n"

    pray_text += "ברכה אחרונה: "

    pray_text += "\n"

    for f_pray in predictions:
        pray_text += "\n" + first_pray_dict[f_pray]

    pray_text += "\n"

    pray_text += "ברכה ראשונה: "

    pray_text += "\n\n"

    return pray_text


def filter_prays(predictions):
    if "המוציא" in predictions:
        return ["המוציא"]
    pray_list = []
    if "שהכל" in predictions:
        pray_list.append("שהכל")
    if "האדמה" in predictions:
        pray_list.append("האדמה")
    if "העץ" in predictions:
        pray_list.append("העץ")
    if "הגפן" in predictions:
        pray_list.append("הגפן")
    if "מזונות" in predictions:
        pray_list.append("מזונות")
    return pray_list


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.orientation = "vertical"
        try:
            self.xcamera = XCamera(index=0, play=True)
            self.add_widget(self.xcamera)
        except:
            popup = Popup(title='Error',
                          content=Label(text='The camera is unavailable', font_size=25, color=(1, 0, 0, 1)),
                          pos_hint={'center_x': 0.5, 'center_y': 0.5},
                          size=(300, 300))
            popup.open()
        self.change_camera_button = ChangeCameraButton()
        self.change_camera_button.bind(on_press=self.change_camera)
        self.add_widget(self.change_camera_button)
        self.predict_pray_button = PredictPrayButton()
        self.predict_pray_button.bind(on_press=self.predict)
        self.add_widget(self.predict_pray_button)

        try:
            # set the roboflow model values in the initial function in order to save time when predicting an image
            self.rf = Roboflow(api_key=API_KEY)
            self.project = self.rf.workspace().project(MODEL_ENDPOINT)
            self.model = self.project.version(VERSION).model
        except:
            popup = Popup(title='Error',
                          content=Label(text='The model is unavailable, please try again later', font_size=25,
                                        color=(1, 0, 0, 1)),
                          pos_hint={'center_x': 0.5, 'center_y': 0.5},
                          size=(300, 300))
            popup.open()

    def change_camera(self, instance):
        try:
            xcamera = self.ids.xcamera
            xcamera.index = (xcamera.index + 1) % 2  # toggle between 0 and 1
            xcamera.play = True

        except:
            popup = Popup(title='Error',
                          content=Label(text='No second camera found', font_size=20, color=(1, 1, 1, 1)),
                          pos_hint={'center_x': 0.5, 'center_y': 0.5},
                          size_hint=(None, None),
                          size=(300, 100))
            popup.open()

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

        try:
            # Get the latest image
            first_image = sorted_date_files[0]
        except:
            popup = Popup(title='Error',
                          content=Label(text='No images found', font_size=20, color=(1, 0, 0, 1)),
                          pos_hint={'center_x': 0.5, 'center_y': 0.5},
                          size_hint=(None, None),
                          size=(300, 100))
            popup.open()
            return

        # e.g. split_image("bridge.jpg", 2, 2, True, False)
        # split_image(image_path, rows, cols, should_square, should_cleanup, [output_dir])

        try:
            # infer on a local image
            output = self.model.predict(first_image).json()

            # create a dictionary from the json object
            predictions_dict = dict(output['predictions'][0]['predictions'])

            # create a dictionary with the pray as key
            pray_dict = {key: value['confidence']
                         for key, value in predictions_dict.items()
                         if value['confidence'] >= MIN_CONFIDENCE}  # only if the prediction is above MIN_CONFIDENCE
        except Exception as e:
            popup = Popup(title='Connection Error',
                          content=Label(text="Please check your internet connection"
                                             "and try again", font_size=25, color=(1, 0, 0, 1)),
                          pos_hint={'center_x': 0.5, 'center_y': 0.5},
                          size_hint=(None, None),
                          size=(200, 200))
            popup.open()
        # split the images into tiles in order to get more predictions
        split_image(first_image, ROW_NUM_OF_SPLIT, COL_NUM_OF_SPLIT, False, False)

        # Iterate through all the split images created from the original image in order to receive more predictions
        for num in range(0, ROW_NUM_OF_SPLIT * COL_NUM_OF_SPLIT):
            # get the path of the split image
            image_path = f"{first_image[:-4]}_{num}.jpg"

            # infer only on images from the center of the image
            if num % COL_NUM_OF_SPLIT != 0 and num % COL_NUM_OF_SPLIT != COL_NUM_OF_SPLIT - 1:

                try:
                    # infer on part of the image
                    output = self.model.predict(image_path).json()

                    # create a dictionary from the json object
                    predictions_dict = dict(output['predictions'][0]['predictions'])

                    # add the additional prediction to the dictionary
                    pray_dict.update({key: value['confidence']
                                      for key, value in predictions_dict.items()
                                      if value['confidence'] >= MIN_CONFIDENCE})

                    print("sub image prediction: ", pray_dict.keys())
                except:
                    popup = Popup(title='Connection Error',
                                  content=Label(text="Please check your internet connection"
                                                     "and try again", font_size=25, color=(1, 0, 0, 1)),
                                  pos_hint={'center_x': 0.5, 'center_y': 0.5},
                                  size_hint=(None, None),
                                  size=(200, 200))
                    popup.open()
            # remove the split image since we no longer need it
            # os.remove(image_path)

        print(pray_dict.keys())
        print("filter = ", filter_prays(pray_dict.keys()))
        # filter the prays to get only the relevant ones and in order, and then create the text to be displayed
        pray_text = pray(filter_prays(pray_dict.keys()))

        print(pray_text)

        # switch to the pray screen
        pray_screen = self.screen_manager.get_screen('pray_screen')
        pray_screen.pray.text = "[color=000000]" + pray_text[::-1] + "[/color]"
        pray_screen.pray.markup = True
        pray_screen.pray.base_direction = 'rtl'
        self.screen_manager.switch_to(pray_screen)

        return_text = "יש ללחוץ על אייקון המצלמה " \
                      "על מנת לחזור אחורה ולצלם תמונה נוספת"
        reversed_return_text = return_text[::-1]
        return_popup = Popup(title='ATTENTION',
                             content=Label(text=reversed_return_text, font_name='arial', base_direction='rtl',
                                           font_size=20,
                                           color=(1, 1, 1, 1)),
                             pos_hint={'center_x': 0.5, 'center_y': 0.5},
                             size_hint=(None, None),
                             size=(600, 100))
        return_popup.open()


class BackToCameraButton(Button):
    def __init__(self, **kwargs):
        super(BackToCameraButton, self).__init__(**kwargs)
        self.size_hint = (0.12, 0.14)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.75}
        self.background_normal = 'return_icon.png'


class PrayScreen(Screen):
    def __init__(self, **kwargs):
        super(PrayScreen, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.icon = "raising_hands.png"

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
        self.title = "Scan&Pray"
        self.icon = "welcome.png"
        screen_manager = ScreenManager(transition=FadeTransition())
        screen_manager.add_widget(MainScreen(name='main_screen'))
        screen_manager.add_widget(PrayScreen(name='pray_screen'))
        MainScreen.screen_manager = screen_manager
        PrayScreen.screen_manager = screen_manager

        welocme_text = """
                בהצלחה, ושיהיה בתיאבון!
לאחר צילום התמונה, לחצו על אייקון הידיים לקבלת הברכות המתאימות
לשינוי המצלמה לחצו על האייקון התחתון בפינה הימנית של המסך    
לצילום תמונה לחצו על אייקון המצלמה שבפינה הימנית של המסך
ברוכים הבאים לאפליקציית סרוק וברך):
        """
        reversed_welcome_text = welocme_text[-1::-1]

        self.popup = Popup(title='WELCOME!',
                           content=Label(text=reversed_welcome_text, font_name='arial', base_direction='rtl',
                                         font_size=20, color=(1, 1, 1, 1)),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5},
                           size_hint=(None, None),
                           size=(600, 200))
        Clock.schedule_once(self.show_popup, 5)
        return screen_manager

    def show_popup(self, dt):
        self.popup.open()


if __name__ == '__main__':
    TestApp().run()
