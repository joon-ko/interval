# interval

![](images/alpha_1.png)

### project members
- joon ko (joonhok)
- nisha devasia (ndevasia)

### [proposal document](https://docs.google.com/document/d/1v-Yr0-7mmmqrQtp-VLZKAsVBiACLiTvRRZDyHPhV9q4/edit?usp=sharing)

### setup locally
1. we assume you already have all 21M.385 dependencies installed (esp. Kivy).
2. clone and cd into this repository.
3. `pip install -r requirements.txt`
4. `python client.py`

### sound modules

**interval** is a collaborative music sandbox that works by deploying customizable *sound modules*. currently, you can switch sound modules using the zxc keys. (see the keyboard shortcuts below!)

**PhysicsBubble** (z key) is a physics-based sound bubble that collides with the sandbox edges as well as SoundBlocks. to make a PhysicsBubble, simply click and drag somewhere in the sandbox to 'slingshot' a bubble, and let it go! each PhysicsBubble has a pitch, timbre, and number of bounces associated with it. there is also a gravity toggle.

**SoundBlock** (x key) is a static sound block that makes a sound when either a PhysicsBubble hits it, a user clicks it with a mouse, or a TempoCursor activates it. to make a SoundBlock, click and drag in the sandbox to draw a rectangle. let go to release and deploy. each SoundBlock has a pitch and instrument associated with it.

**TempoCursor** (c key) doesn't make any music on its own, but can be placed *over* static sound modules to activate them exactly the same way a mouse click would. the difference between your mouse and a TempoCursor is that they are configurable to click at a specific rhythm. the GUI for TempoCursor is not fleshed out right now, and there's just a 4x4 white grid -- this represents 16th note subdivisions in a 4-beat measure. to use a TempoCursor, select the rhythm you want using the grid, and then click over a static sound module like SoundBlock to deploy. you'll see a white circle with a rotating black tick, which is the 'current' tick marker, and several static blue ticks which represent the rhythm you chose. when the black tick position lines up with the blue tick position, the TempoCursor activates, 'clicking' the sound module underneath.

we are currently working on more sound modules -- namely, at least one more static module that works with simultaneous or arpeggiated chords, and one module that can play more melodic note sequences, in contrast to SoundBlocks which can only play one instrument and pitch. we're also working to extend SoundBlock to have percussion/drum sounds.

we also are currently working on being able to delete sound modules once you've deployed them -- currently, to refresh your screen, you need to restart the app, which is a bit annoying. :(

### on collaborative playtesting

**interval** was designed to be both a single-player and multiplayer experience -- we encourage playtesting with multiple people! under the hood, when you run `python client.py`, you connect to a server currently hosted on heroku, and the server is responsible for managing all the different clients that connect to it.

currently, the **PhysicsBubble** and **SoundBlock** modules work relatively well in multiplayer. **TempoCursor** doesn't work for multiplayer yet but works well enough in single-player.

#### keyboard shortcuts (be a pro!)

- **z**: PhysicsBubble
- **x**: SoundBlock
- **c**: TempoCursor
- **PhysicsBubble**
  - **qwertyui**: pitch select (white keys)
  - **23567**: pitch select (black keys)
  - **[**, **]**: pitch select octave down, octave up
  - **asdf**: timbre select (sine, square, triangle, sawtooth)
  - **g**: toggle gravity
  - **left**, **right**: # of bounces down, up
- **SoundBlock**
  - **qwertyui**: pitch select (white keys)
  - **23567**: pitch select (black keys)
  - **asdfg**: instrument select