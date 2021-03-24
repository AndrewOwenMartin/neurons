# neurons project

- [doc](./doc/)
- [res](./res/)

![Example network animation](./res/simple-network-example.mp4)

## Verbose description.

This is copy-pasted directly from the [Dear PyGui Discord](https://discord.gg/JQDPD8Vd), in response to the question "Curious to see what your project will become. What are developing?".

**AndrewOwenMartin**: So, you've heard of neural networks, right?

**discord_testpilot**: Yes

**AndrewOwenMartin**: To oversimplify, they're often layers of neurons, which themselves are often simply functions mapping a combined input to an output.

**discord_testpilot**: Yes, both in humans and AI

**AndrewOwenMartin**: If you put in some input, you'll get some output. More often than not an input maps to one output.
So you can use it as an arbitrary function, chuck in some training and you can map arbitrary data to arbitrary data. Whoop.

**discord_testpilot**: Magic

**AndrewOwenMartin**: Yep, but it's not a good analogue of biological brains, or real world activity.
Neurons in the real world are very much stateful, dynamic and real-time.
And importantly, they're connected in a very knotty way, not in layers.
So computer scientists often (but not always) talk about neural networks as layers processing information in ever more high-level ways.
An example might be: Raw stimulation -> colours -> edges -> shapes -> objects -> scene

**discord_testpilot**: Understood

**AndrewOwenMartin**: But neuroanatomists, or neurodynamicists (I'm not sure if that's a word, but I mean people who study "neurodynamics") are more likely to talk about a neural network as a thing in a location in phase space, orbiting an attractor.
Put another way, neural networks are never "dormant" and waiting for the next bit of stimulation.
But are always hives of activity.
And the important thing is that one neural network can hold many steady states.
Imagine a neural network which is a ring of neurons, you might see the neurons firing in turn in a clockwise direction, or in an anti-clockwise direction, or all even neurons firing followed by all odd neurons firing.
And what's important is not so much the configuration of the network (e.g. a list of weights between all the neurons) but the 1) the set of steady states it can be in (e.g. clockwise, anti-clockwise, even, odd), 2) the kinds of stimulation that will bump it from one state to another.
I could go on, but let me bring it back to the DPG project..
There was a paper published a few years ago which I found very interesting, they manages to train a network to control a simple agent in a simple environment, the behaviour was for the agent to roam the environment, find another agent, communicate a target location to the other agent somehow and the experiment was a "success" if the other agent then went off on its own to the communicated location and stopped there.
The interesting things are:

**discord_testpilot**: Still listening...

**AndrewOwenMartin**: (Oh, the first agent couldn't move to the destination, it was restricted as to where it could roam in the environment, the other agent could roam freely, but didn't know what to do or where to go)

 1. The network was identical for both agents.
 2. The network relied on its real time dynamics, rather than any 'feed forward' behaviour of classic networks.
 3. the network contained only 3 nodes

**discord_testpilot**: That’s just cheap!

**AndrewOwenMartin**: The agents, guided by the same network remember, would roam about seemingly randomly. Once they collided they would appear to "dance" together, after which one agent would shoot off at speed, and gradually stop at the destination.

**discord_testpilot**: Pretty amazing with 3 nodes

**AndrewOwenMartin**: 

![Example network](./doc/network.png)

I've been wanting to explore this idea for ages, my research background is in the philosophical and logical limitations of artificial intelligence and computation itself, and there are a number of "unsolvable" and "hard" problems in AI that (if true) mean the current approach is a hopeless if something like human/animal adaptive intelligence will ever be achieved.
But as it's real time and dynamic, it's only really possible to explore the conceptual space if you have a real-time interactive visualization of the activity.
I've tried before with React/Flask/Websockets, but there was too much going on.
Then DPG allows me to get something like yesterday's GIF/WEBM in a couple of hours.

**discord_testpilot**: That is pretty impressive.

**AndrewOwenMartin**: I'll point out that I'm not about to suggest there's any possibility of "true" general AI, or superintelligence. For every advantage (such as adaptability) you'll necessarily get a disadvantage (such as lack of generality).

**discord_testpilot**: So, you’re not Kurzweil :laughing:

**AndrewOwenMartin**: Put another way, if you want your calculator to also be good at composing poetry then it's going to get a bit poetic when doing arithmetic, which might not always be what you want.
Put another way, if you manage to instill an AI with something that really acts like an artistic appreciation then it's not going to want to spend all its days doing your stupid **ing image recognition task. It'll want to learn the guitar or holiday in Italy.
