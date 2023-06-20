import numpy as np
import cv2
import torch
import numpy as np
from typing import Tuple
from segment_anything import SamPredictor, sam_model_registry

class SA():
    def __init__(self, model_name="vit_b", model_path=None, gpu=True):
        assert model_path is not None, "Missing \"model_path\" parameter!"
        self.model_name = model_name
        self.model_path = model_path
        self.gpu = gpu

        self.sam = self.load_model(self.model_name, self.model_path)

    def device(self) -> None:
        return "cuda" if torch.cuda.is_available() and self.gpu else "cpu"

    def load_model(self, model_name: str, model_path: str):
        sam = sam_model_registry[model_name](checkpoint=model_path)
        sam.to(device=self.device())

        return sam

    def get_bbox(self, mask: np.ndarray) -> Tuple[int, int, int, int]:
        # flip the array vertically and convert to uint8 datatype
        mask = np.uint8(mask * 255)
        
        # find the largest contour and its bounding rectangle
        thresh = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)[1]
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        max_contour = max(contours, key=cv2.contourArea)
        x,y,w,h = cv2.boundingRect(max_contour)

        return (x, y ,w ,h)

    def predict_box(self, img_path: str, input_point_list: list, input_label_list: list) -> Tuple[int, int, int, int]:
        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # set foreground point position
        input_point = np.array(input_point_list)    # [[x1, y1], [x2, y2], ... ,[x3, y3]] 
        input_label = np.array(input_label_list)    # [1, 1, ... ,0]

        # run model
        predictor = SamPredictor(self.sam)
        predictor.set_image(image)
        masks, scores, logits = predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=False,
        )
        
        bbox = self.get_bbox(masks[0])
        return bbox



