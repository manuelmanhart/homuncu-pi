<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://code.manhart.space/manuelmanhartit/homuncu-pi">
    <img src="docs/logo.jpg" alt="Logo" width="300">
  </a>

  <h3 align="center">Homuncu PI</h3>

  <p align="center">
    This is Homuncu PI, your ghost in a PI for plug and play homeautomation
    <br />
    <a href="https://code.manhart.space/manuelmanhartit/homuncu-pi/issues/new">Create issue</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

[![components diagram][product-components-diagram]][issues-url]

I have a homeassistant installation running on a server. For integrating multiple sensors and other stuff (like multiroom audio) I needed a solution. Since I already had some old Raspberry PIs lying around from old projects I thought I could use them. I started with a small project for reading a DHT22 for temperature & humidity, but with the upgrade to bookworm it failed due to deprecated libraries.

Also it was only taking care of temperature but nothing else and it was not very flexible / configurable. So I created a solution which I could extend easily and came up with this thing I call Homuncu PI.

In my first attempt I used REST via fastapi (for easy access) but it showed that this only works good on a raspberry pi 2 or newer. But I wanted compatibility to raspberry pi 1 as well, so I took a step back, removed the whole REST part and started thinking about mqtt for output and accessing the pi.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [![Python][Python]][Python-url]
* [![Bash][Bash]][Bash-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple example steps.

### Prerequisites

Linux and a bash / sh terminal.

### Installation

You just need to call the following bash script and it will guide you through the setup and install all neccessary dependencies:

```sh
./run.sh
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

This software was built to brigde to different IOT hardware and make them available to the raspberry pi as plug and play components. Also to power a homeautomation system like homeassistant via mqtt.

The features are

* Binary Sensors (low / high) like Reedswitches or PIR sensors - for windows/doors open/closed, intruder alert, motion detection,...
* Cameras - so you can see what is going on even when not at home
* Healthcheck - you can get healthcheck information on the Raspberry PI like temp, cpu, mem, disk usage,...
* IP Address - if your router sometimes changes IP Addresses (via DHCP), you can feed a DNS server (like unbound) always with current name & ip address combinations
* Led - power LEDs on incoming MQTT messages
* Readonly mode - so the Raspberry PI is more resilient to power outages / issues
* Squeezebox / Musicbox - For Multiroom Audio and as well so everyone can listen to their music easily
* Temperature And Humidity Sensors - To track the environment of your house / flat
* (Software) Update Service - So the Raspberry PI always stays up to date as well as Homuncu PI itself

### Configuration File

Homuncu PI uses a two-tier configuration system:

- **`default_config.yaml`** – committed to the repository, contains all available options with their defaults.
- **`config.yaml`** – your local override file (not tracked by git). You only need to set values that differ from the defaults.

On startup, `ConfigService` loads both files and performs a deep merge: keys from `config.yaml` override those in `default_config.yaml`. After merging, environment variables are expanded (`${VAR_NAME}` or `${VAR_NAME:default_value}`).

The config structure has two top-level sections:

```yaml
global:
  cacheTTL: 10
  hostname: ${HOSTNAME}

services:
  camera:
    active: True
    resolution: [1920, 1080]
  temperature:
    active: True
    gpioPin: 4
```

- **`global`** – global settings like `hostname` and `cacheTTL`.
- **`services`** – per-service configuration. Each service reads its own section via `self.getServiceConfig()`.

### Logging

By default the logging is written to stdout. The log levels are configured via `config.yaml` file. The default logging config is:

```yaml
  logging:
    active: True
    default: INFO
```

This means that logging will be made, and that the default level is INFO. 

The loglevels are:

```
DEBUG
INFO
WARN
ERROR
```

and eg. INFO will log the levels from INFO on to the last level (ERROR).

You can override levels for your service like this:

```yaml
  logging:
    active: True
    default: INFO
    mqtt: DEBUG
```

That additional line means that for the mqtt service we want to have additional logging so we can see what is happening inside the logic of this service.

This is common in software craftmanship and made so we do not flood the logs with debug messages (but log them when / where neccessary).

### MQTT

#### Reading MQTT Sensor Values

To verify what is sent to the mqtt broker, follow these steps:

1. Install an MQTT broker on a server
2. Configure homuncu-pi to use this as its broker (in `config.yaml`)
3. Set the `mqtt` logging configuration to `DEBUG` (see above on how to do this)
3. Start homuncu-pi (via `run.sh`) to see in the logs to which topic the sensor will write to
4. Subscribe to the according topic(s) in your software of choice (eg. homeassistant, mosquitto,...)
    1. To debug all mqtt traffic go into your mosquitto container (`docker exec -ti CONTAINER_NAME sh`)
    2. Then subscribe to all topics (`mosquitto_sub -h 127.0.0.1 -t home/#`)

### Squeezeboy / Musicbox / Multiroom Audio

The squeezebox service is currently only a read on the state of the linux service

Currently it needs to be installed manually but it will be integrated in a future release (into bash)

### Temperature & Humidity Sensor

This is written for DHT22, but you can use DHT11 or AM2302 as well.

1. Connect to 3.3V, GPIO 4, GND with a fitting cable
2. Then configure the yaml file (section `temperature`)

### PIR Sensor

1. Connect to 5V, GPIO 23, GND with a fitting cable
2. Then configure the yaml file (section `binarySensor`)
3. Set the potmeters on the PIR sensor accordingly

Also see [understand the two potentiometers on a PIR sensor][pir-two-pot] or [connect a PIR sensor to the raspberry pi (German)][pir-two-pot-de]

### Camera

The camera service lets you take photos on demand via MQTT. It uses `libcamera-still` (modern Raspberry Pi camera stack) and stores images to a configurable path.

#### Prerequisites

- A Raspberry Pi Camera Module (or compatible) connected via CSI
- `libcamera` tools installed on the Raspberry Pi:
  ```sh
  sudo apt install libcamera-apps
  ```
- Verify the camera works:
  ```sh
  libcamera-still -o test.jpg --nopreview
  ```

#### Configuration

```yaml
camera:
  active: True
  resolution: [1920, 1080]
  quality: 85
  storagePath: "/tmp/camera"
  mqttTopic: "camera"
  mqttFlags: "ADD_BASE_TOPIC,ADD_HOSTNAME,ADD_TIMESTAMP"
```

| Key | Default | Description |
|-----|---------|-------------|
| `resolution` | `[1920, 1080]` | Image width and height in pixels |
| `quality` | `85` | JPEG quality (0–100) |
| `storagePath` | `"/tmp/camera"` | Directory where images are saved (use `/tmp` for read-only mode) |
| `mqttTopic` | `"camera"` | MQTT topic for publishing responses |
| `mqttFlags` | `"ADD_BASE_TOPIC,ADD_HOSTNAME,ADD_TIMESTAMP"` | MQTT topic/payload flags |

#### Usage via MQTT

Send a message to the configured input topic (e.g. `home/raspi`) to trigger a capture:

```json
{
  "service": "camera",
  "action": "capture"
}
```

The service responds on the configured MQTT topic (e.g. `home/{hostname}/camera`):

```json
{
  "state": {
    "action": "capture",
    "success": true,
    "path": "/tmp/camera/capture_1717084800.jpg"
  },
  "timestamp": "2026-05-22T12:00:00"
}
```

On failure the response contains `"success": false` and an `"error"` field with details.

#### Retrieving Images

The image is stored locally at the path returned in the MQTT response. To view it remotely you can:

- **Mount the directory** via NFS / SMB on your network
- **Serve it** with a lightweight HTTP server (e.g. `python3 -m http.server 8080` in the storage path)
- **Copy it** via `scp` or `rsync`

Motion detection and periodic captures are planned for a future release.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Changelog

**1.1.0 - WIP**
* [BREAKING] improved naming from pin to gpioPin (in config)
* [BREAKING] improved naming from pullUpOrDown to pullDirection (in config)
* [BREAKING] refactored config service so it will load default_config.yaml and just overrides with the changes in config.yaml instead of replacing completely
* [BREAKING] set services to 'active: False' in default_config.yaml
* [BREAKING] refactoring service injection
* [BREAKING] renamed "ipaddress" to "ip" in json of mqtt message
* Refactored `LoggingService` to change loglevel via config file (so it can be changed on the fly)
* Refactored service lookup to a centralized registry
* Renamed project from `RaspiController` to `Homuncu PI`
* added `GitRepoService`
* implemented `CameraService`
* added autoupdate feature to `UpdateService`
* added `service.sh help` and added possibility to filter logs
* added ascii art logo :)
* changed dev version appendix (from -wip to -dev)
* bugfixes, refactorings, removed old code
* improved documentation, logging

**1.0.0**
* Switched to [Semantic Versioning 2.0.0](https://semver.org/)
* Refactored services into
  * base services (always in the system and usually global)
  * modular services (should be downloaded in the future on the fly only when used / installed)
* Switched to an mqtt only approach instead of providing REST services
* Added hasSignificantChange function to sensor service (for immediate updates if sensor data changed significantly)
* Extended bash scripts
* Implemented `BinarySensorService` for  all sensors (eg. pir, reed,...) where we just read a low / high state
  * Can be configured / used with multiple sensors

**0.5**
* Moved default_config.yaml file to project root
* Moved installService.sh to a more generic service.sh file
* Updated all services
* Added support for environment variables within the config file
* Moved config loader to global config class

**0.4**
* Refactoring of base service
* Added config loader

**0.3**
* Added camera and readonly service

**0.2**
* Added update service, squeezebox and temperature service

**0.1**
* Initial web service api

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Roadmap

- [ ] Create a service for sending logging via MQTT, like `$baseOutTopic/$hostname/logging`
- [x] Implement CameraService for communication with the PI camera
- [ ] Implement ReadonlyService for reading / changing the readonly state
- [ ] Add a feature for playing Audiobooks via RFID Cards / Tags (similar to the popular Audioboxes for kids)
- [ ] Add voice commands (via external open source projects?)
- [ ] Get the config via MQTT messages and save the configuration into `config.yaml` file
- [ ] Merge the configs read from `default_config.yaml` and `config.yaml` so one only needs to override the changes instead of copying all
- [ ] Refactor the bash scripts
- [ ] Create an easy to use setup wizard
- [ ] Write a guide on how to extend by creating own services
- [ ] Read incoming mqtt messages and forward them to the correct service

See the [open issues](https://code.manhart.space/manuelmanhartit/homuncu-pi/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT License. See [LICENSE.md][license-url] for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Contact

Manuel Manhart - [@manuel.manhart](https://twitter.com/ManuelManhart) - manuel.manhart@gmail.com

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[issues-shield]: https://img.shields.io/badge/open-issues-yellow?style=for-the-badge
[issues-url]: https://code.manhart.space/manuelmanhartit/homuncu-pi/issues
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/manuel-manhart
[license-shield]: https://img.shields.io/badge/license-mit-blue?style=for-the-badge
[license-url]: https://code.manhart.space/manuelmanhartit/homuncu-pi/src/branch/main/LICENSE.md
[product-screenshot]: docs/screenshot.png
[product-components-diagram]: docs/homuncu-pi-overview.png
[Python]: https://img.shields.io/badge/python-000000?logo=python&style=for-the-badge&
[Python-url]: https://python.org/
[Bash]: https://img.shields.io/badge/Bash-20232A?logo=gnubash&style=for-the-badge&
[Bash-url]: https://bash.org/
[pir-two-pot]: https://forum.arduino.cc/t/help-me-to-understand-the-two-potmeters-on-my-pir-sensor/372895
[pir-two-pot-de]: https://tutorials-raspberrypi.de/raspberry-pi-bewegungsmelder-sensor-pir/

## Icons

* <a href="https://www.flaticon.com/free-icons/humidity" title="humidity icons">Humidity icons created by Pixel perfect - Flaticon</a>
* <a href="https://www.flaticon.com/free-icons/fever" title="fever icons">Fever icons created by Freepik - Flaticon</a>
* <a href="https://www.flaticon.com/free-icons/alarm" title="alarm icons">Alarm icons created by Freepik - Flaticon</a>
* <a href="https://www.flaticon.com/free-icons/open-window" title="open window icons">Open window icons created by Ida Desi Mariana - Flaticon</a>
* <a href="https://www.flaticon.com/free-icons/heater" title="heater icons">Heater icons created by Nikita Golubev - Flaticon</a>
* <a href="https://www.flaticon.com/free-icons/cctv-camera" title="cctv camera icons">Cctv camera icons created by Freepik - Flaticon</a>
* <a href="https://www.flaticon.com/free-icons/audio" title="audio icons">Audio icons created by Freepik - Flaticon</a>
* <a href="https://www.flaticon.com/free-icons/audiobook" title="audiobook icons">Audiobook icons created by Andrean Prabowo - Flaticon</a>
* <a href="https://www.flaticon.com/free-icons/smart-home" title="smart home icons">Smart home icons created by bqlqn - Flaticon</a>
* <a href="https://www.flaticon.com/free-icons/motion-sensor" title="motion sensor icons">Motion sensor icons created by Nuricon - Flaticon</a>