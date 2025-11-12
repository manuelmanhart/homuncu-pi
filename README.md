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
  <a href="https://code.manhart.space/manuelmanhartit/raspi-controller">
    <img src="docs/logo.png" alt="Logo" width="300">
  </a>

  <h3 align="center">Raspi-Controller</h3>

  <p align="center">
    This is Raspi-Controller, home automation made for easy plug and play.
    <br />
    <a href="https://code.manhart.space/manuelmanhartit/raspi-controller/issues/new">Create issue</a>
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

[![Product Name Screen Shot][product-screenshot]](https://example.com)

I have a homeassistant installation and for integrating sensors and hardware ...TBD

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

* Cameras
* Readonly mode
* Reedswitch / Open Close Sensors
* Squeezebox / Musicbox
* Temperature And Humidity Sensors
* Software Update Service

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Changelog

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

<!-- ROADMAP -->
## Roadmap

- [ ] Add threshold function to sensor service
- [ ] Add functions to camera service
- [ ] Refactor functions in base service
- [ ] Refactor update service to new sensor service
- [ ] Save the configuration into a yaml file

See the [open issues](https://code.manhart.space/manuelmanhartit/raspi-controller/issues) for a full list of proposed features (and known issues).

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
[issues-url]: https://code.manhart.space/manuelmanhartit/raspi-controller/issues
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/manuel-manhart
[license-shield]: https://img.shields.io/badge/license-mit-blue?style=for-the-badge
[license-url]: https://code.manhart.space/manuelmanhartit/raspi-controller/src/branch/main/LICENSE.md
[product-screenshot]: docs/screenshot.png
[Python]: https://img.shields.io/badge/python-000000?logo=python&style=for-the-badge&
[Python-url]: https://python.org/
[Bash]: https://img.shields.io/badge/Bash-20232A?logo=gnubash&style=for-the-badge&
[Bash-url]: https://bash.org/
