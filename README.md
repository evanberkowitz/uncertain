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

Copyright (C) 2023  Evan Berkowitz, Forschungszentrum Jülich

Licensed under the [GNU GPLv3].

[Wikipedia]: https://en.wikipedia.org/wiki/Uncertainty#In_measurements
[NIST]: https://physics.nist.gov/cgi-bin/cuu/Info/Constants/definitions.html
[scientific E notation]: https://en.wikipedia.org/wiki/Scientific_notation#E_notation
[GNU GPLv3]: https://www.gnu.org/licenses/gpl-3.0.txt

