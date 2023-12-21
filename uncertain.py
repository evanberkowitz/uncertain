#!/usr/bin/env python

import numpy as np
import re

_copyright='''
    Uncertain, printing numbers with uncertainty estimates
    Copyright (C) 2023  Evan Berkowitz, Forschungszentrum Jülich

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''

def _exponent(e, sign='+', E=False):
    if e == 0:
        return ''
    exp=f'{int(e):{sign}}'
    if E:
        return f'e{exp}'
    return f' × 10^{exp}'

class Uncertain:
    r'''
Measurements from experiments and theoretical computations may have uncertainty.
A common notation for symmetric errors, explained on [Wikipedia] and by [NIST],
is to write the uncertainty as digits in parentheses that indicate an uncertainty
on the corresponding least significant digits.

So, for example, since the mass of the electron is measured to be

    (0.51099895000±0.00000000015) MeV/c^2

we can instead write 0.51099895000(15) MeV/c^2.

The `Uncertain` class takes a mean and uncertainty and helps produce this formatted
shorthand so that

```python
electron_mass = Uncertain(0.51099895000, 0.00000000015) # MeV / c^2
print(electron_mass)
# +5.1099895000(15) × 10^-1
```

automatically leveraging scientific notation.

There are a few exceptional cases.
First, if the uncertainty is 0, the resulting string is just the mean with no uncertainty.

```python
print(Uncertain(3.14159,0))
# +3.14159
```

Second, if the uncertainty is greater than the absolute value of the mean,
we resort to an explicit ± notation.

```python
print(Uncertain(1,10))
# (+1 ± 10)
```

You can just specify how many digits of uncertainty to show.
The default shown above is `u2`; `u1` shows one digit in the uncertainty,

```python
print(f'{electron_mass:u1})
# 5.109989500(2) × 10^-1
```

We can also format the mean with `.precision` as any normal float in an fstring.
If the uncertainty is too small on that scale, we still show a (0) uncertainty indicator.

```python
print(f'{electron_mass:.3}')
# 5.110(0) × 10^-1
```

But, you cannot specify both `.precision` and `u[digits]`.

We can also trade ` × 10^` for `e` by passing `e` in the format string.

```python
print(f'{electron_mass:eu3}')
# 5.10998950000(150)e-1
```

Finally, the `.from_string` method can parse many strings specifying an uncertain quantity.

```python
electron_mass = Uncertain.from_string('9.1093837015(28)e-31') # kg
print(electron_mass.mean, electron_mass.uncertainty)
# 9.1093837015e-31 2.8000000000000004e-40
```

We can use [scientific E notation] by passing ``e`` in the format string.

```python
print(f'{electron_mass:eu3}')
# 5.10998950000(150)e-1
```

To mandate a sign even for positive numbers, add a ``+``.

```python
print(f'{electron_mass:+eu3}')
# +5.10998950000(150)e-1
```


[Wikipedia]: https://en.wikipedia.org/wiki/Uncertainty#In_measurements
[NIST]: https://physics.nist.gov/cgi-bin/cuu/Info/Constants/definitions.html
[scientific E notation]: https://en.wikipedia.org/wiki/Scientific_notation#E_notation

    '''

    def __init__(self, mean, uncertainty):
        self.mean = mean
        self.uncertainty = np.abs(uncertainty)

    def __str__(self):

        return format(self, '+u2')

    def __format__(self, format_spec):

        # We want to be able to print sensibly in a few different ways.
        # We always aim for scientific notation based on the size of the mean
        # value.  In other words, if the mean is is m × 10^e then we should write
        # an uncertain value as (something) ×  10^e if |e| is >= 1
        # What that something is depends on the mean and uncertainty.
        # Importantly, if something is like m±u then 10^e needs to be
        # 'factored out' consistently.

        # We can get the three pieces in the scientific notation straightforwardly.
        sign = np.sign(self.mean)
        exponent = int(np.floor(np.log10(sign * self.mean)))
        mantissa = self.mean / 10**exponent

        if ('+' in format_spec) or format_spec == '':
            f_sign='+'
        else:
            f_sign=''

        E = ('e' in format_spec)

        # The first case we should handle is the case where the uncertainty is exactly 0.
        # In this case we can just print the number in scientific notation.
        if self.uncertainty == 0:
            return f'{mantissa:{f_sign}}{_exponent(exponent, E=E)}'
        # We could add ' exactly' to emphasize the point.

        # Now we can work on the (uncertain mantissa) × 10^exponent as long as
        # the exponent isn't zero.
        if np.abs(exponent) >= 1:
            # We can divide by 10^exponent, setting the whole part of the mantissa to be
            # less than 10.
            normalized = Uncertain(self.mean / 10**exponent, self.uncertainty / 10**exponent)
            # Formatting that normalized number and then attaching the exponent
            # gives the final scientific notation format.
            stem = format(normalized, format_spec)
            return f'{stem}{_exponent(exponent, E=E)}'

        # If you get to here you can assume the mean mantissa's integer part is 1-9.

        # The user might specify a .precision in the formatting string.
        f_precision = re.search('\.(\d*)', format_spec)
        if f_precision:
            f_precision = int(f_precision.group()[1:])
        else:
            f_precision = 0

        # If the uncertainty is bigger than the size of the mean we can't meaningfully
        # write the uncertainty as a question about the last digits.
        # So, we resort to a ± notation.
        if np.abs(self.uncertainty) >= np.abs(self.mean):
            if f_precision:
                return f'({self.mean:{f_sign}.{f_precision}f} ± {self.uncertainty:.{f_precision}f})'
            else:
                return f'({self.mean:{f_sign}} ± {self.uncertainty})'


        # Otherwise, the uncertainty expresses uncertainty about some of the digits
        # of the mean.  This is the most useful case; we infer the digits to present
        # based on the trustworthiness.
        precision = int(np.floor(np.log10(self.uncertainty)))
        digits    = -precision

        # The user might specify a u uncertainty spec
        u_precision = re.search('u(\d*)', format_spec)
        if u_precision:
            u_precision = int(u_precision.group()[1:])
        else:
            u_precision = 0

        if f_precision and u_precision:
            raise ValueError(f'Cannot specify both floating point precision .{f_precision} and uncertainty specification u{u_precision}.')

        if f_precision:
            digits = f_precision
            # In this case we want to be able to show (0), so we don't take the ceiling.
            uncertainty = int((self.uncertainty / 10**(-digits)))
        else:
            digits += (u_precision-1 if u_precision else 1)
            uncertainty = int(np.ceil(self.uncertainty / 10**(-digits)))

        return f'{self.mean:{f_sign}.{digits}f}({uncertainty})'

    @classmethod
    def from_string(cls, string):
        if 'E' in string:
            mantissa, exponent = string.split('E')
            exponent = 10**int(exponent)
            u = Uncertain.from_string(mantissa)
            return Uncertain(u.mean * exponent, u.uncertainty * exponent)
        elif '×' in string:
            mantissa, rest = string.split('×')
            exponent = rest.split('^')[1]
            exponent = 10**int(exponent)
            u = Uncertain.from_string(mantissa)
            return Uncertain(u.mean * exponent, u.uncertainty * exponent)
        elif string[0] == '(' and string[-1] == ')':
            mean, uncertainty = string[1:-1].split('±')
            return Uncertain(float(mean), float(uncertainty))
        else:
            mean, uncertainty = string.split('(') # split on the opening paren
            frac = mean.split('.')
            precision = len(frac[1])
            uncertainty = uncertainty.split(')')[0] # chop off the closing paren
            return Uncertain(float(mean), float(uncertainty)*10**(-precision))

if __name__ == '__main__':

    print(f'Some data from the PDG Table of Physical Constants')
    print(f'https://pdg.lbl.gov/2020/reviews/rpp2020-rev-phys-constants.pdf\n')

    data = (
        ('electron mass', 'm_e', Uncertain(0.51099895000, 0.00000000015), 'MeV'),
        ('electron mass', 'm_e', Uncertain.from_string('9.1093837015(28)E-31'), 'kg'),
        ('proton mass', 'm_p', Uncertain(938.27208816, 0.00000029), 'MeV'),
        ('proton mass', 'm_p', Uncertain.from_string('1.67262192369(51) × 10^-27'), 'kg'),
        ('proton mass', 'm_p', Uncertain.from_string('(1836.15267343± 0.00000011)'), 'm_e'),
        ('neutron mass', 'm_n', Uncertain.from_string('(939.56542052 ±0.00000054)'), 'MeV'),
        ('deuteron mass', 'm_d', Uncertain(1875.61294257, 0.00000057), 'MeV'),
        ('fine structure constant', 'α', Uncertain.from_string('7.2973525693(11)×10^-3'), ''),
        ('inverse fine structure constant', 'α^-1', Uncertain(137.035999084, 0.000000021), ''),
        ('classical electron radius', 'r_e', Uncertain.from_string('2.8179403262(13)E-15'), 'm'),
        ('e- Compton wavelength / 2π', 'λbar_e', Uncertain(3.8615926796E-13, 12E-23), 'm'),
        ('Bohr radius', 'a_∞', Uncertain(0.529177210903E-10, 8.0E-21), 'm'),
        ('Rydberg energy', 'R_∞', Uncertain(13.605693122994, 2.6E-11), 'eV'),
        ('Thompson cross section', 'σ_T', Uncertain(0.66524587321, 6.0E-10), 'barn'),
        ('Bohr magneton', 'µ_B', Uncertain(5.7883818060E-11, 1.7E-20), 'MeV T^-1'),
        ('Nuclear magneton', 'µ_N', Uncertain(3.15245125844E-14, 9.6E-24), 'MeV T^-1'),

        ('Gravitational constant', 'G_N', Uncertain(6.67430E-11, 1.5E-15), 'm^3 kg^-1 s^-2'),

        ('Fermi coupling constant', 'G_F', Uncertain(1.1663787E-5, 6E-12), 'GeV^-2'),
        ('Weak mixing angle', 'θ_W', Uncertain(0.23121, 0.00004), ''),
        ('W± boson mass', 'm_W', Uncertain(80.379, 0.012), 'GeV'),
        ('Z0 boson mass', 'm_Z', Uncertain(91.1876, 0.0021), 'GeV'),
        ('strong coupling constant', 'α_S(m_Z)', Uncertain(0.1179, 0.0010), ''),
        )

    width_name = max(len(d[0]) for d in data) + 1
    width_symbol= max(len(d[1]) for d in data) + 1

    for name, symbol, value, unit in data:
        print(f'{name: <{width_name}} {symbol: <{width_symbol}} {value} {unit}')

    print(_copyright)
