import json
from pathlib import Path


class Calibration:


    def __init__(
        self,
        gopro_model,
        cinema_video,
        gopro_video,
        offset,
        camera
    ):

        self.gopro_model = gopro_model
        self.cinema_video = cinema_video
        self.gopro_video = gopro_video

        self.offset = offset
        self.camera = camera



    def compute(self):

        """
        Ici viendront :
        
        - détection ArUco
        - calibration caméra
        - estimation transformation rigide
        - comparaison mesure physique / estimation
        """


        result = {

            "camera": {

                "gopro_model":
                    self.gopro_model,

                "cinema_camera":
                    self.camera

            },


            "rig_transform": {

                "translation":
                    self.offset,

                "rotation":
                {
                    "x":0,
                    "y":0,
                    "z":0
                }

            }

        }


        output = Path(
            "data/calibration.json"
        )


        output.parent.mkdir(
            exist_ok=True
        )


        with open(
            output,
            "w"
        ) as file:

            json.dump(
                result,
                file,
                indent=4
            )


        return output
