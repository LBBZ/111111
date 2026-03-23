# perception

## Responsibilities
- Own sensor capture and image/depth/seg processing helpers.
- Provide camera data interfaces for online decision making.
- Provide image merge/compress/depth-index utilities.

## Modules
- drone_camera.py: RGB/depth/seg capture and save helpers.
- image_processing.py: merge_images, compress_image_to_size, compute_depth_index.

## Dependency Direction
- Allowed imports: infra only.
- Should not import: core, io, control, test.
- core can consume perception outputs.
