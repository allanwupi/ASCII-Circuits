# ASCII-SPICE Circuit Description Language (ASCDL)
ASCDL is a compact ASCII schematic language for specifying planar analog circuits. It compiles to standard SPICE netlist `.net` text files, which can be opened with the free [LTSpice](https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html) program.

As a tentative future goal, we will attempt to build our own Python program for SPICE using [modified nodal analysis](https://en.wikipedia.org/wiki/Modified_nodal_analysis).

## 0. Examples
```text
Underdamped RLC Series Circuit
- Damping ratio = R/2 √(C/L) = 0.158

[SCHEMATIC]
in.+--R1--L1--+.out
   |          |
   V1         C1
   |          |
   =          =

[VALUES]
V1 = PULSE(0 1 0 1u 1u 1)
R1 = 10k
L1 = 100m
C1 = 100p

[COMMANDS]
.tran 100u
```

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
Bi = (1+0.5*sin(2*pi*1k*time))*sin(2*pi*20k*time) V
Ri = 10k
Eo = 8 Ri
Ro = 75
D1 = 0.7
R1 = 10k
C1 = 10n
R2 = 10k
C2 = 15n

[COMMANDS]
.tran 1n 4m 1m
```

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

Refer to the [LTSpice wiki page on dot commands](https://ltwiki.org/LTspiceHelpXVII/LTspiceHelp/html/DotCommands.htm) for other commands.

## Circuit Elements
All circuit elements are two-terminal.

**Passive Elements**
```text
R  Resistor
L  Inductor
C  Capacitor
D  Diode
```
Note that diodes are modeled as *piecewise linear*.

**Active Elements**
```text
V  Independent voltage source
I  Independent current source
B  Behavioral voltage/current source
E  Voltage-controlled voltage source
F  Current-controlled current source
G  Voltage-controlled current source
H  Current-controlled voltage source
```

By default, independent sources are sinusoidal:
```text
V(t) = Magnitude cos(2 pi Frequency Time + pi Phase/180)
```

Note that we use a cosine function. This is related to sine by
```
cos(t) = sin(t-90°)
```

## Branch Names
A *branch* is a circuit element, uniquely identified by a 2-character token.
```text
<Type><ID>
```
where:
```text
Type ∈ {R,L,C,D,V,I,E,F,G,H}
ID ∈ {0..9,a..z}
```
Examples:
```text
R1
Ca
Vz
```
Note the maximum number of branches in a circuit:
```text
10 types × 36 IDs = 360 branches
```

## Wires and Nodes
Wires are orthogonal straight line segments. There are 3 wire characters:
```text
-  Horizontal wire
|  Vertical wire
+  Connection or corner
```

Horizontal wires `-` and vertical wires `|` may only intersect at `+`, which connects all adjacent wires. We do not support wires crossing over, hence only planar circuits are possible.

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

Each node can have at most one label.

### Ground
Ground is the special node `0` in SPICE. It is represented by:
```text
=
```

Each disconnected network in [SCHEMATIC] must contain at least 1 connection to the ground node symbol `=`, i.e. there should be an electrical path to ground.

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

### Resistor
```text
Rx = <resistance>
```
Resistance (ohms) must be positive.

### Inductor
```text
Lx = <inductance>
```
Inductance (henries) must be positive.

### Capacitor
```text
Cx = <capacitance>
```
Capacitance (farads) must be positive.

### Diode
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

### Independent Voltage Source
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

### Independent Current Source
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

### Behavioral Sources
Behavioral sources are used to specify arbitrary voltage or current functions.

#### Behavioral Voltage Source
```text
Bx = <expression> V
```

#### Behavioral Current Source
```text
Bx = <expression> I
```

### Dependent Sources
Dependent sources, a.k.a. *controlled sources*, are defined by a gain value and a single reference branch.
- E and H are voltage sources, proportional to the reference branch voltage
- G and F are current sources, proportional to the reference branch current
- Due to SPICE implementation details, the reference branch for current-controlled sources F and H must be a voltage source (V or H element).
- The same direction conventions apply as for independent sources.

#### Voltage-Controlled Voltage Source (VCVS)
```text
Ex = <gain> <branch>
```
The voltage gain is unitless.
#### Voltage-Controlled Current Source (VCCS)
```text
Gx = <gain> <branch>
```
Gain units are amperes per volt.
#### Current-Controlled Current Source (CCCS)
```text
Fx = <gain> <source>
```
The current gain is unitless.
#### Current-Controlled Voltage Source (CCVS)
```text
Hx = <gain> <source>
```
Gain units are volts per ampere.

## Node Assignment
The compiler must:
1. Identify all wire-connected nodes.
2. Merge all nodes touching a ground symbol into node `0` (the global SPICE ground).
3. Associate user-defined labels with nodes (these replace numeric nodes).
4. Assign consecutive numbered nodes `N001,N002,...` to all unlabelled nodes.
