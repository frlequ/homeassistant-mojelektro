[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Ffrlequ%2Fhomeassistant-mojelektro&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://github.com/frlequ/homeassistant-mojelektro/)
[![GitHub issues](https://img.shields.io/github/issues/frlequ/homeassistant-mojelektro)](https://github.com/frlequ/homeassistant-mojelektro/issues) [![Github All Releases](https://img.shields.io/github/downloads/frlequ/homeassistant-mojelektro/total.svg)](https://github.com/frlequ/homeassistant-mojelektro/releases/)


# Home Assistant Integration of Moj Elektro electricity meter

This is an updated version of the custom component for integrating electric utility meter data into Home Assistant. It no longer requires a local certificate to access Mojelektro but utilizes a **new API** service provided by Informatika.si.

![Screenshot of a Mojelectro in Home Assistant using Apex Chart Card.](/energy.png)



### Warning for existing users:
This update should not erase existing sensors, ~~but will not update the energy produced _output entities.~~
(Update in the latest version)

### Note about data:
This integration gathers energy information with a 24-hour delay because API doesn't provide real-time data. Unfortunately, this delay leads to inaccurate readings, especially between midnight and 6 a.m as data aggregates. The problem lies with Mojelektro, and there's no way around it.

## Roadmap

- [X] Add energy output sensors
- [ ] Add config flow (Home Assistant UI setup)
- [ ] Add decimals options for meters
- [ ] Add option to save to long term statistics
- [ ] Multi-language Support
    - [ ] English
    - [ ] Slovenian

## Setup API:

1. Log in to Mojelektro.si using any available login options.
2. Under `Moj Profil`, find the option to create a token `Kreiraj žeton`. Use unlimited expiration and click  `Create Token.`
4. Copy the newly generated token. You'll need it in the configuration step.
5. Your `meter_id` is `EIMM` number found und `Merilna mesta/merilne točke`


## Installation

Method 1: [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=frlequ&repository=homeassistant-mojelektro&category=integration)

Method 2: HACS > Integrations > Add Integration > Mojelektro Load Platform > Install

Method 3: Manually copy `Mojelektro Load Platform` folder from latest release to `config/custom_components folder`.

_Restart Home Assistant_

## Configuration

1. Add the following entry in your `configuration.yaml`:
   
    ```yaml
    mojelektro:
      token: <your-token-from-mojelektro>
      meter_id: <your-meter-id>
    ```
