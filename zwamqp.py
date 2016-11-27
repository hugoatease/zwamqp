import openzwave
from louie import dispatcher, All
from openzwave.option import  ZWaveOption
from openzwave.network import ZWaveNetwork
import time
from haigha.connection import Connection
from haigha.message import Message
from json import dumps
import gevent
import gevent.event as gevent_event

connection = Connection(transport='gevent', user='zwave', password='zwave', host='192.168.2.1')

event_channel = connection.channel()
event_channel.exchange.declare('zwave-events', 'fanout', durable=True)

commands_channel = connection.channel()
commands_channel.exchange.declare('zwave-commands', 'direct')

options = ZWaveOption('/dev/ttyAMA0', config_path='/usr/local/lib/python2.7/dist-packages/libopenzwave-0.3.1-py2.7-linux-armv6l.egg/config')
options.set_append_log_file(False)
options.set_console_output(False)
options.set_save_log_level('Debug')
options.set_poll_interval(500)
options.set_interval_between_polls(True)
options.set_logging(True)
options.lock()

network = ZWaveNetwork(options, autostart=False)

def louie_node_update(network, node):
    print "Node update", network, node
    event_channel.basic.publish(Message(dumps({
        'type': 'NODE_UPDATE',
        'network': network.to_dict(),
        'node': node.to_dict()
    })), 'zwave-events', network.home_id_str)

def louie_value_update(network, node, value):
    print "Value update", network, node, value
    event_channel.basic.publish(Message(dumps({
        'type': 'VALUE_UPDATE',
        'network': network.to_dict(),
        'value': value.to_dict()
    })), 'zwave-events', network.home_id_str)

def louie_network_started(network):
    print "Started network", network
    event_channel.basic.publish(Message(dumps({
        'type': 'NETWORK_STARTED',
        'network': network.to_dict()
    })), 'zwave-events', network.home_id_str)

def louie_network_failed(network):
    print "Network failed", network
    event_channel.basic.publish(Message(dumps({
        'type': 'NETWORK_FAILED',
        'network': network.to_dict()
    })), 'zwave-events', network.home_id_str)

def louie_network_awaked(network):
   print "Network awaked", network
   event_channel.basic.publish(Message(dumps({
       'type': 'NETWORK_AWAKED',
       'network': network.to_dict()
   })), 'zwave-events', network.home_id_str)
   dispatcher.connect(louie_node_update, ZWaveNetwork.SIGNAL_NODE)
   dispatcher.connect(louie_value_update, ZWaveNetwork.SIGNAL_VALUE)

def louie_network_ready(network):
    print "Network ready", network
    event_channel.basic.publish(Message(dumps({
       'type': 'NETWORK_READY',
       'network': network.to_dict()
    })), 'zwave-events', network.home_id_str)

dispatcher.connect(louie_network_started, ZWaveNetwork.SIGNAL_NETWORK_STARTED)
dispatcher.connect(louie_network_failed, ZWaveNetwork.SIGNAL_NETWORK_FAILED)
dispatcher.connect(louie_network_ready, ZWaveNetwork.SIGNAL_NETWORK_READY)
dispatcher.connect(louie_network_awaked, ZWaveNetwork.SIGNAL_NETWORK_AWAKED)

def message_pump():
    while connection is not None:
        connection.read_frames()
        gevent.sleep()

gevent.spawn(message_pump)
network.start()
waiter = gevent_event.AsyncResult()
waiter.wait()
