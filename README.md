<h1 align="center"><img src="img/logo.png" alt="PyDeskMates" style="width: 50%; min-width: 256px;
display: block; margin: auto;"></h1>

[![code license](https://img.shields.io/badge/code%20license-MIT-green)](https://github.com/DimaLeon2000/PyDeskMates/blob/main/LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/release/python-3100/)
![work in progress](https://img.shields.io/badge/status-work_in_progress-red)

An incomplete remake of Oska Software's DeskMates in Python. Contributions are welcome.

## What are DeskMates?</h2>
DeskMates are animated characters that live their own lives right on your desktop. You can launch the selected
character and just watch their various sequences, or you can take an active part in them. Clicking on different parts of
the character's body will cause them to have different reactions. There are also very small secret touch reactions
(up to 4 pixels).

## Setup
To install dependencies if you haven't already, run the following command: `pip install -r requirements.txt`

Copy a directory with the name of a DeskMate of your choices, containing the `Data` folder, into the `characters`
directory if it exists.

In the `main.py` file, change the value of the `characters` variable to the same name as the copied directory's.

To start, run the following command: `python main.py`

## Things to be added
<ul>
<li>Touch reaction with hotspots (DONE)</li>
<li>Recursive sequence parsing
<ul>
<li>Frame range (DONE): a numeric string range of frames. It could be either forwards or backwards.

Example:

    0881-0895
</li>
<li>Frame group (DONE): parts enclosed in parentheses.</li>
<li>Repeats (DONE): a frame/group followed by an asterisk and a number.

Examples:

    0000*5
    (0192-0201)*10
</li>
<li>Playing the sound effect (DONE): a name of the sound effect is preceded by a space and an exclamation point, or a
double dagger (" !"/"‡", or 0x2021 in hex). Must be contained in the frame group. (Not necessary: If the previous sound
is currently playing, the animation has to pause till the former ends before playing the next one.)

Example (from the `DESKMATE.FAS` file of Oska DeskMate v2.06):

    ( !FLAP,1218,1220,1218,1219)
</li>
<li>Weighted random choices (DONE): parts followed by a percentage symbol and a number,
separated with '|' delimiters and enclosed in curly brackets.

Example (from the `common_demo.FAS` file of the Kahli DeskMate):
        
    {pause_chair%4|pause_ice|pause_metalsuit_a|pause_metalsuit_b%4|pause_orb%3|pause_treadmill%4}
It will randomly pick either "pause_chair", "pause_ice", "pause_metalsuit_a", "pause_metalsuit_b", "pause_orb", or
"pause_treadmill" with probabilities of [4, 1, 1, 4, 3, 4].
</li>
<li>Relative position (DONE): numbers representing coordinates in a Cartesian coordinate system, enclosed in square
brackets.

Example:

    [15,8]
</li>
<li>Fencing region (ALMOST DONE): numbers representing coordinates of the region (where a character will be
repositioned) in a Cartesian coordinate system, enclosed with copyright symbols (&#169;, 0xA9 in hex). A digit before
the letter can be set to:
<ul><li>0 &mdash; align to the screen</li>
<li>1 &mdash; align the top-left corner to the last saved position</li>
<li>2 &mdash; unknown functionality</li>
<li>3 &mdash; align to the parent sprite</li>
</ul>

It is formatted like: &#169;[x1,y1]0h0v,[x2,y2]0h0v&#169;.

Example:

    ©[-100,100]0c0m,[100,-100]0c0m©
...will set the first point of the region to the center (center-middle) of the screen with the offset of (-100,-100)
and the second one to the center (center-middle) of the screen with the offset of (100,100), and re-position the
character to be in the set region.
</li>
<li>Flipping (DONE): The following frames can be flipped either horizontally or vertically by adding either the "less-
than" symbol (&lt;, 0x3C in hex) or the caret (^, 0x5E in hex), respectively. Introduced in the Maeka DeskMate.</li>
<li>Random floating (DONE): This part will make the character float around at random in the region with set maximum
horizontal and vertical speeds. It's useful if you don't feel like adding relative positioning to every frame. It is
preceded by the section sign (&sect;, 0xA7) and values are separated by the forward slash (/), and the result would be like
this: &sect;h/v. Introduced in the Johlee DeskMate.
<li>Extra sprite (DONE): The parts are preceded by a single number sign (#) followed by symbols representing the
parameters (# for attaching to the parent sprite, - for adding to the back of the current sprite).
Introduced in Sugar-n-Spice.</li>
<li>Loading external FAS file (DONE): the specific FAS file is loaded. The part (filename) is preceded by the underscore
(_). Introduced in Sugar-n-Spice.

Example:

    _SnS_t_both_bondage (loads "SnS_t_both_bondage.fas")
</li>
<li>Timer (DONE): The sequence will be looped for a set number of frames or more. The part is followed by the "at"
symbol (@) and a number of frames. Introduced in Dancing Girls.

Example (taken from the `dance_cheerleader.FAS` file of the Dancing Girls DeskMate):

    float_loop_cheerleader@1000
</li>
<li>Masking (DONE): The sequence is preceded by the symbol &#189; (0xBD in hex) for masking the parent sprite.
Introduced in Screen Sirens.

Example (taken from the `sfx_iris.FAS` file of the Kahli 3D DeskMate):

    ½9198,9100,9102,9104,9106,9108,9110,9112,9199
</li>
</ul>
</li>
</ul>
<h2>Things to be improved</h2>
<ul><li>Faster file loading (NOT YET)</li></ul>
