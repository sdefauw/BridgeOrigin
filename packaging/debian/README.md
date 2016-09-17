#Bridge Origin Debian Package

To create an Bridge Origin DEB package:

    sudo apt-get install python-paramiko python-tornado python-setuptools curl mysql-client
    sudo apt-get install debhelper dpkg-dev git-core fakeroot devscripts
    sudo apt-get install dh-python
    curl -sL https://deb.nodesource.com/setup_4.x | sudo -E bash -
    sudo apt-get install -y nodejs
    sudo apt install npm
    sudo npm install -g bower
    git clone https://github.com/sdefauw/BridgeOrigin.git
    cd BridgeOrigin
    make deb

The debian package file will be placed in the `../` directory. This can then be added to an APT repository or installed with `dpkg -i <package-file>`.