# AutoLabel
 This project is developed using PyQt and is inspired by [SAM](https://github.com/facebookresearch/segment-anything), creating an automatic annotation system based on the concept of [LabelImg](https://github.com/heartexlabs/labelImg).

## Features
Similar functionalities to LabelImg (although very basic).

### Annotate the rect box
<img src="https://github.com/qpal147147/AutoLabel/blob/main/samples/annotate.gif" alt="Annotate" width="600" height="402">

### Automated annotations with SAM
1. Right mouse on the object you're interested in.
  <img src="https://github.com/qpal147147/AutoLabel/blob/main/samples/sam_1.gif" alt="Automated annotations" width="600" height="402">  
  <img src="https://github.com/qpal147147/AutoLabel/blob/main/samples/sam_2.gif" alt="Automated annotations" width="600" height="402">
  
2. Left mouse to exclude the objects you're not interested in.
  <img src="https://github.com/qpal147147/AutoLabel/blob/main/samples/sam_3.gif" alt="Automated annotations" width="600" height="402">
   
### Saving
You can choose from three formats: `YOLO`, `Pascal VOC` and `COCO`, the default is YOLO.  
***Notice:***
- If you choose the `COCO` format, it must be consistent from the beginning, otherwise, you will only obtain annotations for a single image.

### Visualization
You can place the annotations in the same directory as the images, and the labels file name must be same with image file name.  
If it is in `COCO` format, put `annotations.json` in the directory.
<img src="https://github.com/qpal147147/AutoLabel/blob/main/samples/visualization.gif" alt="Visualization" width="600" height="402">

### Hotkeys
| Hotkey | Description |
| :--: | :--: |
| D | Next image |
| A | Previous image |
| Space | Automatically predict rectangle box |
| del | Delete the selected rectangle box |
| Ctrl + S | Save annotations |
| ↑→↓←  | Move the selected rectangle box |

## Environment
- PyQt5
- lxml
- [Segment Anything](https://github.com/facebookresearch/segment-anything#installation)

## Model
| Name | Checkpoint |
| :--: | :--: |
| vit_h | [ViT-H SAM model](https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth) |
| vit_l | [ViT-L SAM model](https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth) |
| vit_b | [ViT-B SAM model](https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth) |

Then modify the `name` and `path` [here](https://github.com/qpal147147/AutoLabel/blob/main/autoLabel.py#L24):
```python
self.sam = SA(model_name="vit_b", model_path="sam_vit_b_01ec64.pth")
```

## Usage
1. Your directory must include 'classes.txt' and you can edit the classes on your own.
   ```txt
   dog
   person
   cat
   ...
   ```
2. Run
   ```python
   python autoLabel.py
   ```

## Reference
- [segment-anything](https://github.com/facebookresearch/segment-anything)
- [labelImg](https://github.com/heartexlabs/labelImg)
