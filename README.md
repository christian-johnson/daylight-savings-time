# Daylight Savings Time plotting code

After the US Senate unanimously passed a bill to make daylight savings time (DST) permanent in early March, 2022, I wanted to visualize what the difference would look like. This code makes plots to help visualize what three different scenarios look like:
- Keep DST as is
- Eliminate DST
- Move to permanent DST

To run the code for your city of choice (for Albuquerque, in this case), simply clone this repo and run:

    python dst.py 'Albuquerque'

The output should be a PDF in the 'figures' folder. 
A list of acceptable cities is available on the [documentation page](https://astral.readthedocs.io/en/latest/) (scroll down) for the Astral library that computes sunrise and sunset times.

Some examples:
![Washington DC](https://github.com/christian-johnson/daylight-savings-time/figures/Washington DC.pdf)

![Seattle](https://github.com/christian-johnson/daylight-savings-time/figures/Seattle.pdf)

![Honolulu](https://github.com/christian-johnson/daylight-savings-time/figures/Honolulu.pdf)
