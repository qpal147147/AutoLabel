# AutoLabel
 This project is developed using PyQt and is inspired by [SAM](https://github.com/facebookresearch/segment-anything), creating an automatic labeling system based on the concept of [Labelimg](https://github.com/heartexlabs/labelImg).

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

# Reference
[segment-anything](https://github.com/facebookresearch/segment-anything)
