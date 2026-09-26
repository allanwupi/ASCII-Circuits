# ASCII-SPICE Circuit Description Language (ASCDL)
ASCDL is a compact ASCII schematic language for specifying planar analog circuits. It compiles to a standard SPICE netlist.

Initially we support steady-state analysis only (DC and AC). Transient analysis will come later.

An example circuit in ASCDL:
```text
Envelope Detector
* Used to demodulate amplitude-modulated (AM) signals
* Very cheap and easy to build

[CIRCUIT]
                           +.RX
                           |
in.+---+    +--Ro--D1--+---+--R2--+.out
   |   |    |          |   |      |
   Vi  Ri   Eo         R1  C1     C2
   |   |    |          |   |      |
   =   =    =          =   =      =

[VALUES]
Vi = 0.5 20k
Ri = 100k
Ro = 75
Eo = 20 R0
D1 = 0.7
R1 = 10k
C1 = 10n
R2 = 10k
C2 = 15n
```

## 1. File Structure
```text
<optional title>
<optional comments>

[CIRCUIT]
<ASCII circuit schematic>

[VALUES]
<branch values>
```

The first line of the file is treated as the title (optional). If no title is given, the default name is the current date/time `YYYYMMDD_HHMMSSS`.

Lines of text after the title and before [CIRCUIT] are ignored, and can be used for comments or metadata.

Any blank lines in the file are also ignored.

### Circuit Schematic

The circuit schematic is a rectangular grid of ASCII characters which represent wires and circuit elements. Missing characters at the end of a line are treated as spaces.

Tabs are not allowed in the schematic, only spaces.

## 2. Circuit Elements
All circuit elements are two-terminal.

**Passive Elements**:
```text
R  Resistor
L  Inductor
C  Capacitor
D  Diode
```
Note that diodes are modelled as *piecewise linear*.

**Active Elements**:
```text
V  Independent voltage source
I  Independent current source
E  Voltage-controlled voltage source
F  Current-controlled current source
G  Voltage-controlled current source
H  Current-controlled voltage source
```

Independent sources are sinusoidal:
```text
V(t) = Magnitude cos(2 pi Frequency + pi Phase/180)
```

## 3. Branch Names
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
Note the maximum circuit size is capped by the number of branches:
```text
10 types × 36 IDs = 360 branches
```

## 4. Wires and Nodes
Wires are orthogonal straight line segments. There are 3 wire characters:
```text
-  Horizontal wire
|  Vertical vire
+  Connection or corner
```

Horizontal wires `-` and vertical wires `|` may only intersect at `+`. We do not support wires crossing over, hence only planar circuits are possible.

A *node* is a connected network of wire characters.

### Node Labels
A node with a connection point `+` can be given a label by prefixing or suffixing with `.`:
```text
label.+
+.label
```
Labels are arbitrary-length words containing any combination of lowercase letters, uppercase letters or digits.

The label must be on the same line as `+`. Each node can have at most one label.

### Ground
Ground is a special node, represented by a special symbol:
```text
=
```

Each network in [CIRCUIT] must have at least 1 `=` ground node connected to a branch.

All occurrences of `=` represent the same global ground node in SPICE.

## 5. Branch Conventions
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
1. Another branch `Zx`
2. A connection point or corner `+`
3. Ground `=`

### Terminal Numbering
Horizontal:
```text
terminal1 = left
terminal2 = right
```
Vertical:
```text
terminal1 = top
terminal2 = bottom
```

### Sign Convention
For every branch `B`, we use the following sign convention for electrical quantities:
```
V(B) = V(B.terminal1) - V(B.terminal2)
I(B) = current entering terminal1 and leaving terminal2
P(B) = V(B) × I(B)
```

## 6. Branch Values
Every branch appearing in [CIRCUIT] must have exactly one value definition in [VALUES], and vice versa.

```text
<Branch> = <Magnitude> [<Frequency in Hz> [<Phase in deg>]]
```

- Magitude must be defined for all elements
- Frequency and phase may only be specified for independent sources V and I
- Units are Hertz for frequency and degrees for phase

Magnitude, frequency and phase are to be specified as integer or decimal values:
```
[+-]?<Integer or Float>[suffix]? 
```

The *suffix* can be scientific notation (exponential form):
```text
e+8
e-11
```

or one of the following metric prefix abbreviations (case-insensitive):
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
Metric prefixes cannot be combined with scientific notation.

### Resistor
```text
Rx = resistance
```
Resistance (ohms) must be positive.

### Inductor
```text
Lx = inductance
```
Inductance (henries) must be positive.

### Capacitor
```text
Cx = capacitance
```
Capacitance (farads) must be positive.

### Diode
```text
Dx = Von
```
We use a simple piecewise linear model:
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
Vd = V(terminal1) - V(terminal2)
```
A negative value reverses diode orientation.
Thus:
```text
D1 = 0.7
```
conducts from terminal1 to terminal2,
while:
```text
D1 = -0.7
```
conducts from terminal2 to terminal1.

### Independent Voltage Source
```text
Vx = voltage [frequency [phase]]
```
Voltage (volts) is measured from terminal1 to terminal2.
A negative value reverses polarity.

Frequency and phase are optional and will default to 0 if not specified.

Zero frequency represents DC voltage source.

### Independent Current Source
```text
Ix = current [frequency [phase]]
```
Current (amperes) flows from terminal1 to terminal2.
A negative value reverses direction.

Frequency and phase are optional and will default to 0 if not specified.

Zero frequency represents DC current source.

```text
Ix = 0
```
is equivalent to an ideal *open circuit*.

### Controlled Sources
Controlled sources are defined by a gain value and a single reference branch.

#### Voltage-Controlled Voltage Source (VCVS)
```text
Ex = gain <branch>
```
#### Voltage-Controlled Current Source (VCCS)
```text
Gx = gain <branch>
```
#### Current-Controlled Current Source (CCCS)
```text
Fx = gain <source>
```
Due to the SPICE implementation, reference branch must be a V or H element.

#### Current-Controlled Voltage Source (CCVS)
```text
Hx = gain <source>
```
Due to the SPICE implementation, reference branch must be a V or H element.

## 7. Node Assignment
The compiler must:
1. identify all wire-connected nodes,
2. merge all nodes touching a ground symbol into node `0`,
3. assign consecutive numbers to all remaining nodes.

Node `0` is the global SPICE ground.

