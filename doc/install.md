# Install
This page explains how to install and start Bridge Origin in command line. This [link](dev.md) provides information to start the server in development mode.

## Package installation
Download the latest code source.
```
git clone https://github.com/sdefauw/BridgeOrigin.git
cd BridgeOrigin
```

Install the package like this
```
python setup.py build
sudo python setup.py install
```
or via pip
```
rm -rf dist/
python setup.py sdist
sudo pip install dist/*.tar.gz
```


## Configuration
Before executing the program, you need to provide some additional information via a configuration file. The program can have multiple configuration files. This file will be taken during the [execution](#exection). For example, you can generate one file per provider network.

The first step is to generate an empty configuration file.
```
brorig -c <CONFIG_FILE_PATH> --install
```

According the [type of server](config_server.md) you will the configuration file change. However a common pattern stay the same:
 * *custom* > *server* : type of server that you will use
 * *server*: Backend daemon information of Bidge Origin
     * *log*: log file name and path name
     * *data_path*: path of data can be stored temporarily

## Execution
Finally, let's start !

Start the server with the following command:

```
brorig -c <CONFIG_FILE_PATH>
```

The web interface is accessible in the following URL:

[http://localhost:4242/](http://localhost:4242/)

Note: You can change the port number (default ```4242```) and the verbose level. see help ``` brorig -h```