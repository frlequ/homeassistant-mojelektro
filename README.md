[![hacs default](https://img.shields.io/badge/HACS-Default-green.svg)](https://hacs.xyz)
[![GitHub issues](https://img.shields.io/github/issues/frlequ/homeassistant-mojelektro)](https://github.com/frlequ/homeassistant-mojelektro/issues) 
![GitHub User's stars](https://img.shields.io/github/stars/frlequ)
![GitHub Repo stars](https://img.shields.io/github/stars/frlequ/homeassistant-mojelektro)


# Home Assistant Integration of Moj Elektro electricity meter 

This is an updated version of the custom component for integrating electric utility meter data into Home Assistant. It no longer requires a local certificate to access Moj Elektro but utilizes a **new API** service provided by Informatika.si.

![Screenshot of a Moj Electro in Home Assistant using Apex Chart Card.](/assets/energy.jpg)
<sub> *Example of Moj Elektro API using Apex Chart Card. You can find yaml in https://github.com/frlequ/mojelektro-apex-chart </sub> 


> [!NOTE]
> **Note about data:** This integration gathers energy information with a **24-hour delay** because API doesn't provide real-time data. Unfortunately, this delay leads to inaccurate readings, especially between midnight and 6 a.m as data aggregates. The problem lies with Moj Elektro, and there's no way around it.


## Setup API

1. Log in to Mojelektro.si using any available login options.
2. Under `Moj Profil`, find the option to create a token `Kreiraj žeton`. Use unlimited expiration and click  `Create Token.`
4. Copy the newly generated token. You'll need it in the configuration step.
5. Your `meter_id` is `EIMM` number found und `Merilna mesta/merilne točke`


## Installation
1. **Either**
    - Method 1 _(easiest)_: Find and download `Moj Elektro` `integration` in HACS. Moj Elektro is now part of default HACS repository.
    
    - Method 2: [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=frlequ&repository=homeassistant-mojelektro&category=integration)
    
    - Method 3: Manually copy `mojelektro` folder from [latest release](https://github.com/frlequ/homeassistant-mojelektro/releases/latest) to `custom_components` folder.
2. _After download restart Home Assistant!_

## Configuration
In Home Assistant
1. Go to Settings > Add integration > search > Moj Elektro
2. Enter credentials:

![Screenshot of a Moj Electro setup in Home Assistant.](/assets/setup.jpg)

> [!NOTE]
> _As for version 0.2.0 there is no need for `configuration.yaml` file edit!_

## Network Tariff Blocks
If you are also searching for current tariff blocks (omrežnina), you can find integration here:

https://github.com/frlequ/home-assistant-network-tariff

and the custom card:

https://github.com/frlequ/network-tariff-card

## Roadmap

- [X] Add energy output sensors
- [X] Add config flow (Home Assistant UI setup)
- [X] Add decimals options for meters
- [X] Add tariff block power
- [X] Add energy consumption by blocks
- [ ] Add option to save to long term statistics
- [X] Multi-language Support
    - [X] English
    - [ ] Slovenian


## Report any issues

Thanks and consider giving me a 🌟 star

<a href="https://www.buymeacoffee.com/frlequ" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
