# olive_garden_lights
Power and control the string of lights across the garden wall, using a Pi Pico W in micropython

# Installation notes
In the interest of privacy, I have provided `make_config.py`. This is written in standard python.

This needs to be run on a parent computer prior to loading into the pico. It will ask for relevant details and generate the corresponding JSON.

Please ensure the JSON is copied across. `make_config.py` does _not_ need to be on the pico