# smart-squat-rack-kit

Yep — this is a very real, sellable B2B wedge.
Retrofits computer vision for dumb gym equipment.

Gyms already spent money on racks. They do not want to replace them with $8k smart racks.

BUT they will buy a $500–$1,500 bolt-on kit that turns their existing rack into:
- a coach for squats (and any other barbell exercise)
- a rep/set counter
- a form checker
- a branded member experience
- possibly a premium upsell / PT-lite station

That’s the business.

<br/>

## The actual product
We’re selling a “Smart Squat Rack Retrofit Kit” to gyms.

Sales pitch:
“It turns any squat rack into an AI squat coach in 20 minutes.”

The gym buys a kit with:

- 2 cameras
- 1 locked-down tablet
- 1 small compute box / hub
- 1 display (optional TV)
- our software subscription

That’s the whole product.

## What the gym gets
For gym owners, this is not “AI posture analysis.”
It's:
- a premium member feature
- a personal training upsell
- a differentiator vs nearby gyms
- a way to monetize existing floor space
- a “wow” factor for social media / retention

Sell the outcome, not the model.

<br/>

## The gym owner hears:

- “members love this”
- “higher retention”
- “charge +$15/mo for smart racks”
- “reduce beginner intimidation”
- “AI coach without paying another trainer”

That’s the sale.

Recommended hardware stack (v1)

Don’t overbuild this.

v1 should be brutally practical.

# Per rack hardware
<br/>

## 1. Front camera
Mounted straight-on, chest height.
Purpose:

- knee tracking
- stance width
- bar centering
- hip shift / asymmetry
- valgus detection

Use:
- cheap USB webcam or PoE cam
- 1080p / 30fps is enough


## 2. Side camera
Mounted side profile.
Purpose:

- depth
- torso angle
- bar path
- hip hinge
- lumbar flexion estimate

Use:
- same type of camera

These two views are enough for a strong v1.
No depth sensor needed yet. No LiDAR. No fancy nonsense.

## 3. Android tablet (user interface)
Mounted to rack.
Purpose:
- choose exercise
- start set
- review cues
- read feedback
- see rep count
- login / guest mode

This is our “face” to the user.

Cheap, replaceable, easy to source.

Use:
- 10–12" Android tablet
- wall mount / VESA enclosure
- rugged case if needed

## 4. Optional TV (premium)

Big wall-mounted display.
Purpose:


mirror tablet UI


show live form overlay


make it look premium / visible across gym


This is mostly for sales/demo value.
Tablet is enough for v1. TV is upsell.

5. Compute hub (important)
This is the brains.
This should not be the tablet.
The tablet is UI only.
The hub does:


camera ingest


inference


local networking


sync to cloud


device management


updates


This is the right architecture.

Do NOT make tablet do inference
This is the big architecture call.
Do not rely on Android tablet for core inference.
Why:


Android hardware fragmentation sucks


camera handling is annoying


thermals suck


kiosk management gets harder


replacing tablet becomes painful


Instead:


tablet = UI terminal


hub = compute


cameras → hub


tablet ↔ hub over local network


That’s the right system.

Best v1 architecture
Option A (best): mini PC hub
Use a cheap mini PC / N100 box.
Examples:


Beelink


Intel N100 mini PC


used Dell OptiPlex Micro


fanless industrial mini PC later


This is probably your best v1.
Why:


cheap


powerful enough for pose estimation


runs Linux


easy remote management


easy USB camera support


easy OTA updates


no weird Pi bottlenecks


This is likely the correct answer.
Hub runs:


Linux


your inference service


local API server


websocket server


cloud sync agent


This is clean.

Option B: Raspberry Pi
Possible, but probably wrong long-term.
Pi is nice for prototyping, but:


weaker inference


USB bandwidth can get annoying


thermal throttling


SD cards die


supply chain still annoying


debugging in the field is worse


Pi is fine for prototype.
Mini PC is better for deployment.
Use Pi only to prove it works.

Software architecture
On-device (hub)
Runs locally in gym.
Services:
1. Vision service


ingests 2 cameras


runs pose estimation


computes joint landmarks


tracks reps


scores movement


This outputs structured events, not raw video.
Example:


rep_started


rep_ended


depth=0.91


knee_valgus_left=0.22


torso_pitch=18deg


cue="Drive knees out"


That’s the product.
Not “AI video.”
The product is movement events + coaching cues.

2. Session engine
Handles workout logic.


selected exercise


set / rep state machine


rest timers


cue timing


exercise-specific rules


This matters a lot.
You’re not just doing pose detection.
You’re building a lift interpreter.

3. Local UI server
Serves tablet UI over LAN.
Tablet runs:


your Android app
or


kiosk browser to local web app


This means tablet is replaceable and dumb.
Very good for ops.

4. Cloud sync
Uploads:


analytics


anonymized movement metrics


gym usage


device health


software updates


Do not stream raw video by default.
Too expensive, too creepy.
Upload metrics + short clips only when flagged.

Android tablet: how to “brick” it into one app
This part is solved. Don’t invent this.
What you want is Android Kiosk Mode using Lock Task Mode (Android’s official dedicated-device mode). It’s built specifically for single-purpose tablets and prevents users from leaving the app, opening settings, notifications, or home screen when configured correctly. 
This is what you use.
Correct way
Use:


Android Enterprise


Device Owner mode


Lock Task Mode (single-app kiosk)


This gives you:


one app only


no home screen


no notifications


no settings


no app switching


auto-launch on boot


relaunch if app crashes


That’s the official way to “brick” it.
Not root.
Not custom ROM.
Not hacky launcher tricks.
Use proper Android kiosk mode.
You build:


your app


provision tablet as dedicated device


set app as allowlisted


launch in lock task mode


That’s it.
Android literally supports this natively for kiosk devices. 

Tablet strategy (important)
You have 2 choices:
Option 1: Native Android app
Best long-term.
Pros:


better device control


better kiosk support


offline robustness


cleaner peripheral handling


Cons:


more engineering


Best for real product.

Option 2: Web app in kiosk browser
Fastest MVP.
Tablet boots directly into:


fullscreen kiosk browser


loads local hub UI


cannot leave app


Very fast to ship.
Great MVP path.

MVP recommendation
Build this in phases.
v1 (ship fast)


2 USB webcams


mini PC hub


local pose inference


tablet in kiosk browser


squat only


live rep counting


3–5 coaching cues


cloud dashboard for gym owner


That is enough to sell.
Don’t build deadlift.
Don’t build 20 exercises.
Don’t build full programming.
Just own “AI squat rack.”
That alone is a business.

v2
Add:


bench


deadlift


split squat


lunge


onboarding / member profiles


trainer analytics


branded gym reports



v3
Add:


remote coach review


trainer marketplace


premium biomechanics reports


franchise dashboards


API for gym chains



What’s defensible
Your moat is not “pose detection.”
That gets commoditized.
Your moat is:


gym-specific hardware packaging


exercise state machine


coaching logic


UX


installability


B2B sales


analytics / retention data


gym workflow integration


That’s the company.
Not the model.

What to build first
Build the ugliest possible version that proves:

members will actually walk up to a rack and use this without staff help.

That’s the whole game.
If they do, you have a company.
If they don’t, you have a cool CV demo.
Big difference.
