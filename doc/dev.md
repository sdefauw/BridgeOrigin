# Development

## Server start
Like describes in the in [install process](install.md), you can create a configuartion file and start the server with ```python Main.py``` instead of using ```brorig``` command. For that you need to go to the directory ```brorig/``` like this:
```
cd brorig/
python main.py -vv -p 4242 -c settings/config.fake.json
```
 Here the verbose level is enabled an you bind on port 4242 and you start the *fake* server

## Create your own server
You can create your custom server based your own information. The architecture allow a flexibility of implementation to create new type of server and sniffer. It allow to match your network and debug your custom logs.

### Create custom server
To create your own type of server and so your network, you need to add a directory in ```brorig/custom/<YOUR_SERVER>```. Let’s create ```dev_sever```:
```
mkdir brorig/custom/dev_server
```

In this directory, you need to specify the ```_init_.py```python file to be detectable by the server.
```python
#!/usr/local/bin/python
# coding: utf-8

import dev_server as server
```

Create another file in the same directory where you will implement you version: ```dev_server.py```. See the section for the implementation.

The name ```dev_server``` must be reported in your configuration file to use your server see [install doc](install.md).

### Display your network
TODO

### Your protocol
TODO

### Server start
TODO
