# ASCII-SPICE Circuit Description Language (ASCDL)
ASCDL is a compact ASCII schematic language for specifying simple analog circuits. It compiles to standard SPICE netlist `.net` text files, which can be opened with the free [LTspice](https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html) program.

As a tentative future goal, we will attempt to build our own Python version of SPICE using [modified nodal analysis](https://en.wikipedia.org/wiki/Modified_nodal_analysis).

## Example
```text
Envelope Detector with Low-Pass Filter 
- Used to demodulate amplitude-modulated (AM) signals
- Very cheap and easy to build

[SCHEMATIC]
                 +.amp    +.env         # detector has ripples
                 |        |
in.+---+    +-Ro-+-D1-+---+--R2--+.out  # LP filtered output
   |   |    |         |   |      |
   Bi  Ri   Eo        R1  C1     C2
   |   |    |         |   |      |
   =   =    =         =   =      =

[VALUES]
# Behavioral voltage source produces weak AM signal
Bi = (1 + 0.5*sin(2*pi*1k*time)) * sin(2*pi*20k*time) V
Ri = 100k
Eo = 8 Ri
Ro = 75
D1 = 0.7
R1 = 10k
C1 = 20n
R2 = 10k
C2 = 15n

[COMMANDS]
.tran 1n 4m 1m
```

See the `examples/` folder for more examples of ASCDL files and their associated netlists.

## Overview
### File Structure
```text
[optional comments]
[SCHEMATIC]
<ASCII circuit schematic>
[VALUES]
<branch values>
[COMMANDS]
<SPICE dot commands>
```

- Lines before [SCHEMATIC] can be used for a title, descriptions or metadata. They will be directly translated into comments at the top of the netlist file, prefixed with `*`.
- Any blank lines in the file are ignored.
- Inline and single-line comments can be added in the [SCHEMATIC], [VALUES] and [COMMANDS] sections using `#`.
- Multi-line comments are not supported.

### Schematic

The circuit schematic is a rectangular grid of ASCII characters which represent wires and circuit elements.
- The line width is calculated after stripping in-line comments and trailing whitespaces (leading whitespaces are preserved).
- Tabs are not allowed for separation, only spaces.
- Missing characters at the end of a line are treated as spaces.

### Values
All components in the circuit schematic must be assigned values. See the [Branch Values](#branch-values) section for details.

### Commands

At least 1 valid SPICE dot command for simulation should be included. If multiple commands are provided, a separate netlist file will be generated for each command.

**DC operating point**
```
.op
```

**Transient analysis**
```
.tran <Tstop>
.tran [Tstep] <Tstop> [Tstart [dTmax]]
```

Refer to the [LTspice wiki page on dot commands](https://ltwiki.org/LTspiceHelpXVII/LTspiceHelp/html/DotCommands.htm) for other commands.

## Circuit Elements
**Passive elements**
```text
R  Resistor
L  Inductor
C  Capacitor
D  Diode
K  Mutual inductance 
```
Note that diodes are modeled as *piecewise linear*.

**Active elements**
```text
V  Independent voltage source
I  Independent current source
B  Behavioral voltage/current source
E  Voltage-controlled voltage source
F  Current-controlled current source
G  Voltage-controlled current source
H  Current-controlled voltage source
```

All circuit elements are two-terminal, with the exception of mutual inductance K.

By default, independent sources are sinusoidal:
```text
V(t) = Magnitude cos(2 pi Frequency Time + pi Phase/180)
```

Note that we use a cosine function. This is related to sine by
```
cos(t) = sin(t-90°)
```

## Branch Names
A *branch* is a circuit element. Each branch is uniquely identified by a 2-character token in the circuit schematic.
```text
<Type><ID>
```
where:
```text
Type ∈ {R,L,C,D,K,V,I,B,E,F,G,H}
ID ∈ {0..9,a..z}
```
Examples:
```text
R1
Ca
Vz
```

Note the maximum number of branches in a circuit (excluding K-elements):
```text
11 types × 36 IDs = 396 branches
```

## Wires and Nodes
Wires are orthogonal straight line segments. There are 3 wire characters:
```text
-  Horizontal wire
|  Vertical wire
+  Connection or corner
```

Horizontal wires `-` and vertical wires `|` may only intersect at `+`, which connects all adjacent wires. We do not support wires crossing over.

A *node* is a connected network of wire characters.

### Named Nodes
A node with a connection point `+` can be given a name (net label) by prefixing or suffixing with `.`:
```text
label.+
+.label
```
- Labels may contain lowercase or uppercase letters, digits `0..9` and underscores `_`.
- The label `0` is not permitted, as it is reserved for the *ground* node. Otherwise, any arbitrary-length combination is allowed.
- No whitespaces are permitted.
- The label must be on the same line as `+`.
- Labels uniquely identify a node, that is, each node can have at most 1 label.

Named nodes are required to specify *non-planar* graphs.

### Ground
Ground is the special node `0` in SPICE. It is represented by:
```text
=
```

Each disconnected network in [SCHEMATIC] must contain at least 1 connection to the ground node symbol `=` after evaluating connectivity, i.e. there should be an electrical path to ground.

All occurrences of `=` represent the same global ground node in SPICE.

## Branch Conventions
Horizontal:
```text
+--R1--+
```
Vertical:
```text
+
|
R1
|
R2
|
=
```
Each terminal of a branch must connect to:
1. Another branch e.g. `Rx`
2. A connection point or corner `+`
3. Ground `=`

Note that [Mutual Inductance](#-mutual-inductance) is a special case that should not be connected.

### Terminal Labels
Horizontal branch:
```text
positive = left
negative = right

[+]-->[-]
```
Vertical branch:
```text
positive = top
negative = bottom

[+]
 |
 V
[-]
```

### Sign Convention
The *passive sign convention* applies to every branch `B` and defines reference signs/directions for electrical quantities.

The branch voltage, branch current and power are defined as:
```
V(B) = V(B.positive) - V(B.negative)
I(B) = current entering positive terminal and leaving negative terminal
P(B) = V(B) × I(B)
```

Note that for a source providing power to the circuit, the branch current `I(B)` will usually be negative.

## Branch Values
Every branch appearing in [SCHEMATIC] must have exactly one value definition in [VALUES], and vice versa. The value format depends on the branch type. General notes:
- Magnitude must be defined for all elements
- Magnitude units depend on the element: volts, amps, ohms, henries, farads, etc.
- For source elements, frequency units are hertz and phase units are degrees (not radians)
- SPICE expressions are also supported for sources.

Numeric values are specified as integers or decimal numbers, using a subset of SPICE syntax.
```
[<sign>]?<number>[<suffix>]? 
```

Leading decimal point and trailing decimal points are currently not supported. 

The *suffix* can be scientific notation (exponential form). Examples:
```text
-0.5e+8
1.37e-11
```

Alternatively, a value can end in one of the *metric prefix* abbreviations (case-insensitive):
```text
f = 1e-15
p = 1e-12
n = 1e-9
u = 1e-6
m = 1e-3
k = 1e3
Meg = 1e6
G = 1e9
T = 1e12
```
Note that the parser will find the longest-match to differentiate `m / meg`.

Metric prefixes cannot be combined with scientific notation.

### Parameter Values
User variables for numeric values can be defined using the following syntax.
```text
component = {<parameter>}
.<parameter> = <value>
```

Example:
```text
L1 = {L_low}
L2 = {L_high}
L3 = {L_high}
L4 = {L_low}
.L_low = 10
.L_high = 2500
```

Parameter names follow the same rules as node labels (see [Named Nodes](#-named-nodes)).

All parameters defined in the file get compiled to individual `.param <name>=<value>` SPICE commands.

### Passive Elements
#### Resistor
```text
Rx = <resistance>
```
Resistance (ohms) must be positive.

#### Inductor
```text
Lx = <inductance>
```
Inductance (henries) must be positive.

#### Capacitor
```text
Cx = <capacitance>
```
Capacitance (farads) must be positive.

#### Diode
```text
Dx = <Von>
```
We use a simple piecewise linear model where the diode is either fully conducting (ON) or non-conducting (OFF):
```text
ON state:
    Vd = Von
    I >= 0
OFF state:
    Vd < Von
    I = 0
```
where:
```text
Vd = V(positive) - V(negative)
```

This is represented in the SPICE netlist by the model:
```text
.model Dx D(Vfwd=Von)
```

A negative value is equivalent to reversing the diode orientation.
Thus:
```text
D1 = 0.7
```
conducts from positive to negative,
while:
```text
D1 = -0.7
```
conducts from negative to positive.

#### Mutual Inductance
```
Kx = L1 L2 [L3 ...] [<coefficient>]
```
Mutual inductance is a special element used to model *transformers*.
- Two or more inductors (transformer windings) may be listed in a single statement to be coupled together.
- The mutual coupling coefficient K must range between -1 and 1
- Unity coupling represents an *ideal transformer* with no leakage inductance.
- If the coefficient is not specified, it defaults to 1.
- A negative coupling value reverses the polarity of the transformer.

Each mutual inductance Kx must be labelled somewhere in the schematic, but it should *not* be connected to any network. It does not need to be placed next to the component inductors, but this is recommended for ease of reading.
```text
+     +
|     |
La Kx Lb
|     |
=     =
```

Note that *turns ratio* is determined by the inductance ratio of the individual windings:
```text
Lprimary / Lsecondary = (Nprimary / Nsecondary)^2
```

For example:
```text
L1 = 10
L2 = 160
K1 = L1 L2
```
Models a transformer of turns ratio 1:4 (with default coupling of 1).

Additionally, note that the mutual inductance M for a two-winding transformer is related to K by:
```text
M = K sqrt(L1 L2)
```

### Active Elements
#### Independent Voltage Source
```text
Vx = <voltage> [<frequency> [<phase>]] | <expression>
```
- Voltage (volts) is measured from positive to negative.
- A negative value reverses polarity.
- Frequency and phase are optional and will default to 0 if not specified.
- Zero frequency and zero phase represents a DC voltage source.

Alternatively, you can specify a standard SPICE source function, e.g.
```text
SIN(Voffset Vamplitude Freq Tdelay Theta Phi)
PULSE(V1 V2 Tdelay Trise Tfall Pwidth Period)
```
Note for `PULSE` command: if a Period is not specified, the waveform will be non-periodic and contain a single ON pulse only.

#### Independent Current Source
```text
Ix = <current> [<frequency> [<phase>]] | <expression>
```
- Current (amperes) enters from negative and leaves positive, i.e. for a positive value, the branch current is *negative*.
- A negative value reverses direction.
- Frequency and phase are optional and will default to 0 if not specified.
- Zero frequency and zero phase represents a DC current source.

Alternatively, you can specify a SPICE source function.

Note that an *ideal open circuit* can be represented by:
```text
Ix = 0
```

#### Behavioral Sources
Behavioral sources are used to specify arbitrary voltage or current functions.

For expression syntax, see the [LTspice wiki reference page on B sources](https://ltwiki.org/index.php?title=B_sources_(complete_reference)).

##### Behavioral Voltage Source
```text
Bx = <expression> V
```

##### Behavioral Current Source
```text
Bx = <expression> I
```

#### Dependent Sources
Dependent sources, a.k.a. *controlled sources*, are defined by a gain value and a single reference branch.
- E and H are voltage sources, proportional to the reference branch voltage
- G and F are current sources, proportional to the reference branch current
- Due to SPICE implementation details, the reference branch for current-controlled sources F and H must be a voltage source (V or H element).
- The same direction conventions apply as for independent sources.

##### Voltage-Controlled Voltage Source (VCVS)
```text
Ex = <gain> <branch>
```
The voltage gain is unitless.
##### Voltage-Controlled Current Source (VCCS)
```text
Gx = <gain> <branch>
```
Gain units are amperes per volt.
##### Current-Controlled Current Source (CCCS)
```text
Fx = <gain> <source>
```
The current gain is unitless.
##### Current-Controlled Voltage Source (CCVS)
```text
Hx = <gain> <source>
```
Gain units are volts per ampere.

## Node Assignment
The compiler must:
1. Identify all wire-connected nodes.
2. Collect and merge all named nodes with the same user-defined label. Assign a SPICE node to each named node using their labels.
3. Merge all nodes touching a ground symbol into node `0` (the global SPICE ground).
4. Assign consecutive numbered nodes `N001,N002,...` to all unlabelled nodes.
5. Perform ground and connectivity checks.