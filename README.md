# pkgctl

pkgctl is zOS package manager written in Python 3.

## Installation

Use the package manager pkgctl to install pkgctl.

```bash
pkgctl --install pkgctl
```
or install it from source
```bash
git clone https://gitlab.com/zos-linux/pkgctl.git
cd pkgctl
./configure --prefix=/usr
sudo make install
```
## Usage

To install package foobar, issue as root following command:
```bash
pkgctl --install foobar
```
To remove package foobar, issue as root following command:
```bash
pkgctl --remove foobar
```
To update remote repository index, issue as root following command:
```bash
pkgctl --update
```
To list installed packages, issue as root following command:
```bash
pkgctl --list
```
To upgrade installed packagees, issue as root following command:
```bash
pkgctl --upgrade
```
## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[GPLv3](https://www.gnu.org/licenses/gpl-3.0.html)
