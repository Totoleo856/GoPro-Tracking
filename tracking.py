import json


class Tracker:


    def __init__(
        self,
        video,
        calibration_file
    ):

        self.video = video

        with open(
            calibration_file,
            "r"
        ) as f:

            self.calibration = json.load(f)



    def run(self):

        """
        Futur pipeline :

        1 - charger vidéo GoPro

        2 - appliquer calibration optique

        3 - lancer COLMAP

        4 - récupérer poses GoPro

        5 - aligner COLMAP -> ArUco

        6 - appliquer GoPro -> caméra cinéma

        7 - exporter trajectoire

        """


        print(
            "Tracking démarré"
        )
